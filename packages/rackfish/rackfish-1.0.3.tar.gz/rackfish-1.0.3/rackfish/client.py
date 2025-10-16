from __future__ import annotations

import contextlib
import json
import re
import threading
from typing import Any, ClassVar, Iterable

import requests
import urllib3

# HTTP status codes
HTTP_OK = 200

# ---------------------------
# Utilities
# ---------------------------


def _is_identifier(key: str) -> bool:
    """Return True if key is a valid Python identifier (attr-safe)."""
    return re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key) is not None


def _dtype_matches(value: Any, dtype: str) -> bool:
    """Basic datatype check against Redfish ActionInfo DataType values."""
    # Common DataType values in Redfish ActionInfo:
    # "String", "Integer", "Number", "Boolean", "Array", "Object"
    m = {
        "String": lambda v: isinstance(v, str),
        "Integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "Number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
        "Boolean": lambda v: isinstance(v, bool),
        "Array": lambda v: isinstance(v, list),
        "Object": lambda v: isinstance(v, dict),
        # Some implementations use "Password", "Enumeration"—treat like string
        # unless AllowableValues present
        "Password": lambda v: isinstance(v, str),
        "Enumeration": lambda _v: True,  # validated via AllowableValues if present
        # Fallback: accept anything
    }
    fn = m.get(dtype, lambda _v: True)
    return fn(value)


def _safe_join(base: str, path: str) -> str:
    if path.startswith("http"):
        return path
    return base.rstrip("/") + "/" + path.lstrip("/")


# ---------------------------
# HTTP Client
# ---------------------------


class RedfishError(Exception):
    pass


class RedfishClient:
    """
    Redfish HTTP client with session/basic auth and convenience verbs.
    base_url: e.g. "https://bmc.example.com" (with or without /redfish[/v1])
    """

    def __init__(
        self,
        base_url: str,
        username: str | None = None,
        password: str | None = None,
        use_session: bool = True,
        verify_ssl: bool = True,
        timeout: int = 30,
        default_headers: dict[str, str] | None = None,
    ):
        base = base_url.rstrip("/")

        self.base_url = base
        self.username = username
        self.password = password
        self.use_session_auth = use_session
        self.timeout = timeout

        self._http = requests.Session()
        self._http.verify = verify_ssl

        # Suppress SSL warnings when verify_ssl is disabled
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self._http.headers.update(default_headers or {"Accept": "application/json"})
        if username and password and not use_session:
            self._http.auth = (username, password)

        self._session_token: str | None = None
        self._session_uri: str | None = None
        self._root: RedfishResource | None = None
        self._lock = threading.RLock()

    # ---- auth ----

    def login(self) -> None:
        if not (self.username and self.password):
            raise RedfishError("Username/password required for session login")

        url = _safe_join(self.base_url, "/redfish/v1/SessionService/Sessions")
        resp = self._http.post(
            url,
            json={"UserName": self.username, "Password": self.password},
            timeout=self.timeout,
        )
        if resp.status_code not in (200, 201):
            raise RedfishError(f"Login failed: {resp.status_code} {resp.text}")

        token = resp.headers.get("X-Auth-Token")
        loc = resp.headers.get("Location")
        if token:
            self._http.headers["X-Auth-Token"] = token
            self._session_token = token
        if loc:
            self._session_uri = _safe_join(self.base_url, loc)

    def logout(self) -> None:
        try:
            if self._session_uri and self._session_token:
                self.delete(self._session_uri)
        finally:
            self._http.close()
            self._session_token = None
            self._session_uri = None
            self._root = None

    # ---- HTTP verbs ----

    def get(self, path: str) -> dict[str, Any]:
        url = _safe_join(self.base_url, path) if not path.startswith("http") else path
        resp = self._http.get(url, timeout=self.timeout)
        if resp.status_code != HTTP_OK:
            raise RedfishError(f"GET {url} -> {resp.status_code} {resp.text}")
        if not resp.content:
            return {}
        try:
            return resp.json()
        except Exception:
            raise RedfishError(f"GET {url} returned non-JSON") from None

    def post(self, path: str, data: dict[str, Any] | None = None) -> dict[str, Any] | None:
        url = _safe_join(self.base_url, path) if not path.startswith("http") else path
        resp = self._http.post(url, json=data or {}, timeout=self.timeout)
        if resp.status_code not in (200, 201, 202, 204):
            raise RedfishError(f"POST {url} -> {resp.status_code} {resp.text}")
        if resp.status_code in (200, 201) and resp.content:
            try:
                return resp.json()
            except Exception:
                return None
        return None

    def patch(self, path: str, data: dict[str, Any], etag: str | None = None) -> None:
        url = _safe_join(self.base_url, path) if not path.startswith("http") else path
        headers = {}
        if etag:
            headers["If-Match"] = etag
        resp = self._http.patch(url, json=data, headers=headers, timeout=self.timeout)
        if resp.status_code not in (200, 204):
            raise RedfishError(f"PATCH {url} -> {resp.status_code} {resp.text}")

    def delete(self, path: str) -> None:
        url = _safe_join(self.base_url, path) if not path.startswith("http") else path
        resp = self._http.delete(url, timeout=self.timeout)
        if resp.status_code not in (200, 204):
            raise RedfishError(f"DELETE {url} -> {resp.status_code} {resp.text}")

    # ---- navigation ----

    def connect(self) -> RedfishResource:
        with self._lock:
            if (
                self.use_session_auth
                and self.username
                and self.password
                and not self._session_token
            ):
                self.login()
            root_json = self.get(self.base_url + "/redfish/v1")
            self._root = RedfishResource(self, path=self.base_url, data=root_json, fetched=True)
            return self._root

    @property
    def root(self) -> RedfishResource:
        if self._root is None:
            return self.connect()
        return self._root

    def __getattr__(self, name: str) -> Any:
        # Proxy unknown attributes to root (e.g., client.Systems)
        # If attribute doesn't exist but plural form exists with single member,
        # return that member directly (e.g., client.System -> client.Systems[0])
        try:
            return getattr(self.root, name)
        except AttributeError as exc:
            # Try plural form for singular access convenience
            plural_name = name + "s"
            try:
                collection = getattr(self.root, plural_name)
                if (
                    hasattr(collection, "__len__")
                    and hasattr(collection, "__iter__")
                    and len(collection) == 1
                ):
                    return next(iter(collection))
            except (AttributeError, TypeError):
                pass
            # Re-raise original error
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            ) from exc


# ---------------------------
# Resource graph
# ---------------------------


class RedfishResource:
    """
    Generic Redfish resource.
    - data mapping recursively creates nested objects
    - links (@odata.id) are lazy and fetched on first access
    - collections support iteration over Members
    - Actions become callable methods; if ActionInfo present, inputs are validated
    """

    # Keys considered "meta" that won't be turned into normal attributes
    _META_KEYS: ClassVar[set[str]] = {
        "@odata.id",
        "@odata.type",
        "@odata.context",
        "@odata.etag",
    }

    def __init__(
        self,
        client: RedfishClient,
        path: str | None = None,
        data: dict[str, Any] | None = None,
        fetched: bool = False,
    ):
        object.__setattr__(self, "_client", client)
        object.__setattr__(self, "_path", path)  # absolute or relative
        object.__setattr__(self, "_fetched", fetched)
        object.__setattr__(self, "_raw", data or {})
        object.__setattr__(self, "_is_collection", False)

        # Internal cache for generated action validators: name -> schema
        object.__setattr__(self, "_action_info_cache", {})

        if data is None and path and not fetched:
            # Pure link stub; defer GET until used
            return

        # If we have data, map to attributes
        self._hydrate(self._raw)

    # ---- core mapping ----

    def _hydrate(self, obj: dict[str, Any]) -> None:
        # Path inference from data if needed
        if not self._path and "@odata.id" in obj:
            object.__setattr__(self, "_path", obj["@odata.id"])

        # Collection detection
        if isinstance(obj.get("Members"), list):
            object.__setattr__(self, "_is_collection", True)

        # First pass: map properties (including nested dicts/lists)
        for key, value in obj.items():
            if key in self._META_KEYS:
                continue
            self._assign_property(key, value)

        # Second pass: surface OEM child objects and actions to main object
        oem = obj.get("Oem", {})
        if isinstance(oem, dict):
            self._surface_oem_content(oem)

        # Third pass: surface Links child objects to main object
        links = obj.get("Links", {})
        if isinstance(links, dict):
            self._surface_links_content(links)

        # Fourth pass: generate action methods (including OEM actions)
        actions = obj.get("Actions", {})
        if isinstance(actions, dict):
            self._install_actions(actions)

    def _assign_property(self, key: str, value: Any) -> None:
        """
        Convert value into nested RedfishResource(s) where appropriate and attach as attribute or
        make accessible via item access if key is not a valid identifier.
        """
        converted = self._convert(value)
        if _is_identifier(key):
            object.__setattr__(self, key, converted)
        else:
            # Put non-identifier keys into the raw dict; accessible via __getitem__
            self._raw[key] = value  # keep exact original for special keys
            # Try to surface helper for AllowableValues patterns
            # e.g., "BootSourceOverrideTarget@Redfish.AllowableValues"
            # Expose via helper .get_allowable_values("BootSourceOverrideTarget")
        # Keep an easy view of JSON primitives when needed
        # (we already keep _raw)

    def _surface_oem_content(self, oem: dict[str, Any]) -> None:
        """
        Surface vendor-specific OEM child objects and properties to main object.
        Avoids name collisions by checking if attribute already exists.
        """
        for _vendor, vendor_data in oem.items():
            if not isinstance(vendor_data, dict):
                continue
            for key, value in vendor_data.items():
                # Skip if key already exists or is not a valid identifier
                if not _is_identifier(key) or hasattr(self, key):
                    continue
                # Skip action keys (handled separately)
                if key.startswith("#"):
                    continue
                # Surface the OEM child object/property to main object
                converted = self._convert(value)
                object.__setattr__(self, key, converted)

    def _surface_links_content(self, links: dict[str, Any]) -> None:
        """
        Surface Links child objects to main object for easier navigation.
        Avoids name collisions by checking if attribute already exists.
        """
        for key, value in links.items():
            # Skip meta keys and existing attributes
            if key in self._META_KEYS or not _is_identifier(key) or hasattr(self, key):
                continue
            # Surface the linked resource to main object
            converted = self._convert(value)
            object.__setattr__(self, key, converted)

    def _convert(self, value: Any) -> Any:
        """
        Recursively convert dicts/lists:
        - If dict has only @odata.id -> link stub (lazy)
        - If dict contains '@odata.id' + other keys -> embedded object
          (also lazy to avoid deep recursion)
        - Lists -> convert each element
        - Primitives -> return as-is
        """
        if isinstance(value, dict):
            if set(value.keys()) == {"@odata.id"}:
                return RedfishResource(
                    self._client, path=value["@odata.id"], data=None, fetched=False
                )
            # Even if it has @odata.id plus fields, defer hydration to avoid recursion depth issues
            # Store the data but don't hydrate until first access
            return RedfishResource(
                self._client, path=value.get("@odata.id"), data=value, fetched=False
            )
        if isinstance(value, list):
            out = []
            for elem in value:
                out.append(self._convert(elem))
            return out
        return value

    # ---- lazy load ----

    def _ensure_fetched(self) -> None:
        if self._fetched:
            return
        # If we have data already (embedded resource), just hydrate it without fetching
        if self._raw:
            object.__setattr__(self, "_fetched", True)
            object.__setattr__(self, "_is_collection", isinstance(self._raw.get("Members"), list))
            self._hydrate(self._raw)
            return
        # Otherwise, fetch from server if we have a path
        if not self._path:
            return
        data = self._client.get(self._path)
        object.__setattr__(self, "_raw", data)
        object.__setattr__(self, "_fetched", True)
        object.__setattr__(self, "_is_collection", isinstance(data.get("Members"), list))
        self._hydrate(data)

    # ---- dict-like access for special keys ----

    def __getitem__(self, key: str) -> Any:
        self._ensure_fetched()
        return self._raw[key]

    def get(self, key: str, default: Any = None) -> Any:
        self._ensure_fetched()
        return self._raw.get(key, default)

    # ---- attribute access overrides ----

    def __getattr__(self, name: str) -> Any:
        # Trigger lazy fetch for link stubs on first unknown attribute access
        self._ensure_fetched()
        try:
            return object.__getattribute__(self, name)
        except AttributeError as exc:
            # Not an attribute; maybe a JSON property with non-identifier key
            if name in self._raw:
                return self._raw[name]

            # Try plural form for singular access convenience
            # e.g., resource.Chassis -> resource.Chassis[0] if len == 1
            plural_name = name + "s"
            try:
                collection = object.__getattribute__(self, plural_name)
                if (
                    hasattr(collection, "__len__")
                    and hasattr(collection, "__iter__")
                    and len(collection) == 1
                ):
                    return next(iter(collection))
            except (AttributeError, TypeError):
                pass

            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            ) from exc

    def __setattr__(self, name: str, value: Any) -> None:
        # Allow setting simple existing properties via PATCH
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        # If not yet fetched (link stub), fetch first so we know what's writable
        self._ensure_fetched()

        if name in self._raw and not isinstance(self._raw[name], (dict, list)):
            # PATCH only simple properties by default; complex updates via .patch()
            etag = self._raw.get("@odata.etag")
            self._client.patch(self._path, {name: value}, etag=etag)
            self._raw[name] = value
            object.__setattr__(self, name, value)
        else:
            # Set as a Python-side attribute (or ask user to use .patch for complex)
            object.__setattr__(self, name, value)

    # ---- collection protocols ----

    def __iter__(self) -> Iterable[RedfishResource]:
        self._ensure_fetched()
        if not self._is_collection:
            raise TypeError(f"Resource at {self.identity} is not a collection")
        members = self._raw.get("Members", [])
        for m in members:
            if isinstance(m, dict) and "@odata.id" in m:
                yield RedfishResource(self._client, path=m["@odata.id"], data=None, fetched=False)
            else:
                # very rare, but support raw members
                yield RedfishResource(self._client, data=m, fetched=True)

    def __len__(self) -> int:
        self._ensure_fetched()
        if not self._is_collection:
            raise TypeError("Resource is not a collection")
        return len(self._raw.get("Members", []))

    # ---- CRUD convenience ----

    @property
    def path(self) -> str | None:
        return self._path

    @property
    def identity(self) -> str:
        self._ensure_fetched()
        return self._raw.get("Id") or self._raw.get("Name") or (self._path or "<unknown>")

    @property
    def odata_type(self) -> str:
        self._ensure_fetched()
        return self._raw.get("@odata.type", "Resource")

    def refresh(self) -> RedfishResource:
        self._ensure_fetched()
        data = self._client.get(self._path)
        object.__setattr__(self, "_raw", data)
        # reset attributes (re-hydrate). Start clean:
        for k in list(self.__dict__.keys()):
            if not k.startswith("_") and hasattr(self, k):
                with contextlib.suppress(Exception):
                    delattr(self, k)
        self._hydrate(data)
        return self

    def patch(self, updates: dict[str, Any]) -> None:
        if not self._path:
            raise RedfishError("PATCH requires a resource path")
        self._ensure_fetched()
        etag = self._raw.get("@odata.etag")
        self._client.patch(self._path, updates, etag=etag)
        self.refresh()

    def delete(self) -> None:
        if not self._path:
            raise RedfishError("DELETE requires a resource path")
        self._client.delete(self._path)

    def create(self, new_data: dict[str, Any]) -> RedfishResource:
        self._ensure_fetched()
        if not self._is_collection:
            raise RedfishError("create() only valid on collection resources")
        resp = self._client.post(self._path, new_data)
        # Some BMCs return the new object body, others return Location only
        # (handled by caller via follow-up get)
        if resp and "@odata.id" in resp:
            return RedfishResource(self._client, path=resp["@odata.id"], data=resp, fetched=True)
        # Try reading collection again or follow Location header is not exposed
        # here; user may .refresh()
        return self.refresh()  # so caller can find the new member

    # ---- Actions handling ----

    def _install_actions(self, actions: dict[str, Any]) -> None:
        # Standard actions and OEM nested under "Oem"
        for k, v in actions.items():
            if k == "Oem" and isinstance(v, dict):
                # OEM -> vendors e.g. {"Huawei": {"#ComputerSystem.FruControl": {...}}}
                for _vendor, vendor_actions in v.items():
                    if not isinstance(vendor_actions, dict):
                        continue
                    for ak, av in vendor_actions.items():
                        if ak.startswith("#"):
                            self._bind_action(ak, av)
            elif k.startswith("#"):
                self._bind_action(k, v)

    def _bind_action(self, action_name_with_hash: str, info: dict[str, Any]) -> None:
        """
        Create a method on this instance for the given action.
        If @Redfish.ActionInfo is present, we pull parameter schema and validate kwargs on call.
        """
        target = info.get("target")
        action_info_uri = info.get("@Redfish.ActionInfo")

        clean_name = action_name_with_hash.lstrip("#").split(".")[-1]  # e.g., "Reset"
        validator = None
        sig_hint = None

        if action_info_uri:
            try:
                schema = self._client.get(action_info_uri)
                validator, sig_hint = self._compile_action_validator(schema)
                self._action_info_cache[clean_name] = schema
            except Exception:
                # Best-effort; if fetch fails, still expose action without validation
                validator = None

        def _action_method(this: RedfishResource, **kwargs):
            if not target:
                raise RedfishError(f"Action '{clean_name}' has no target")
            if validator:
                validator(kwargs)
            # POST to action target with kwargs (or {} if none)
            return this._client.post(target, data=(kwargs or {}))

        # Attach __name__ for nicer repr; include signature hint as doc
        _action_method.__name__ = clean_name
        doc_hint = f"Dynamic Redfish action {clean_name}"
        if sig_hint:
            doc_hint += f" | params: {sig_hint}"
        _action_method.__doc__ = doc_hint

        # Bind to instance
        object.__setattr__(self, clean_name, _action_method.__get__(self, RedfishResource))

    def _compile_action_validator(self, schema: dict[str, Any]):
        """
        Build a validator function from ActionInfo schema.
        Expected shape:
          {
            "Parameters": [
              {"Name": "ResetType", "Required": True, "DataType": "String",
               "AllowableValues": ["On", "ForceOff", ...]}
            ]
          }
        Returns (validator_callable, signature_hint_string)
        """
        params = schema.get("Parameters") or schema.get("parameters") or []
        expected = {p.get("Name"): p for p in params if isinstance(p, dict) and p.get("Name")}

        def validator(kwargs: dict[str, Any]) -> None:
            # required
            missing = [n for n, p in expected.items() if p.get("Required") and n not in kwargs]
            if missing:
                raise RedfishError(f"Missing required action parameter(s): {', '.join(missing)}")

            # unknown
            unknown = [k for k in kwargs if k not in expected]
            if unknown:
                raise RedfishError(f"Unknown action parameter(s): {', '.join(unknown)}")

            # types & allowable values
            for name, p in expected.items():
                if name not in kwargs:
                    continue
                val = kwargs[name]
                dtype = p.get("DataType")
                if dtype and not _dtype_matches(val, dtype):
                    raise RedfishError(
                        f"Parameter '{name}' expects {dtype}, got {type(val).__name__}"
                    )
                allow = p.get("AllowableValues")
                if allow and val not in allow:
                    raise RedfishError(f"Parameter '{name}' must be one of {allow}; got '{val}'")

        # Signature hint string (human-readable)
        parts = []
        for n, p in expected.items():
            t = p.get("DataType") or "Any"
            req = "required" if p.get("Required") else "optional"
            allow = p.get("AllowableValues")
            if allow:
                parts.append(f"{n}:{t} {req} in {allow}")
            else:
                parts.append(f"{n}:{t} {req}")
        hint = ", ".join(parts) if parts else "no parameters"

        return validator, hint

    # ---- helpers ----

    def get_allowable_values(self, prop_name: str) -> list[Any] | None:
        """
        Return AllowableValues list for a property if present as '<prop>@Redfish.AllowableValues'.
        """
        self._ensure_fetched()
        key = f"{prop_name}@Redfish.AllowableValues"
        return self._raw.get(key)

    def to_dict(self) -> dict[str, Any]:
        """Return the raw JSON (fetched on demand)."""
        self._ensure_fetched()
        return json.loads(json.dumps(self._raw))  # deep copy

    def __repr__(self) -> str:
        t = self._raw.get("@odata.type", "Resource")
        ident = self._raw.get("Id") or self._raw.get("Name") or (self._path or "?")
        return f"<RedfishResource {t} ({ident})>"
