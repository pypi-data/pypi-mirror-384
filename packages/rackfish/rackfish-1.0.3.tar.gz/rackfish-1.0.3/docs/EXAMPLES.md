# rackfish: Common Redfish Usage Examples

This document demonstrates the most common usage patterns for the rackfish dynamic Redfish client.

## 1. Connect to a Redfish BMC

```python
from rackfish import RedfishClient

client = RedfishClient("https://bmc.example.com", "admin", "password", use_session=True, verify_ssl=False)
root = client.connect()
```

## 2. Traverse and List Systems

```python
for system in client.Systems:
    print(f"System: {system.Id} - {system.Name} - Power: {system.PowerState}")
```

### Alternative: Singular Access for Single-Member Collections

If you know there's only one system (common in 1U servers), use singular form:

```python
# Only works if Systems collection has exactly 1 member
system = client.System
print(f"System: {system.Id} - {system.Name} - Power: {system.PowerState}")

# Traditional methods also work:
# system = next(iter(client.Systems))
# system = client.Systems.Members[0]
```

See [SINGULAR_COLLECTION_ACCESS.md](SINGULAR_COLLECTION_ACCESS.md) for details.

## 3. Access OEM and Links Properties (Surfaced)

```python
# OEM properties (e.g., Huawei)
if hasattr(system, "BootMode"):
    print(f"Boot Mode: {system.BootMode}")

# Linked resources (e.g., Chassis)
for chassis in system.Chassis:
    print(f"Chassis: {chassis.Id} - {chassis.Name}")
```

## 4. Invoke Actions (e.g., Reset)

```python
if hasattr(system, "Reset"):
    system.Reset(ResetType="GracefulRestart")
```

## 5. Update Properties (PATCH)

```python
system.AssetTag = "NewTag123"  # Triggers PATCH
```

## 6. Create and Delete Resources

```python
# Create a new user account
accounts = client.AccountService.Accounts
new_account = accounts.create({"UserName": "test", "Password": "pass", "RoleId": "Administrator"})

# Delete a resource
new_account.delete()
```

## 7. Get Allowable Values

```python
values = system.get_allowable_values("ResetType")
print("Allowable ResetTypes:", values)
```

## 8. Full Example

```python
client = RedfishClient("https://bmc", "admin", "password", use_session=True, verify_ssl=False)
root = client.connect()
for system in client.Systems:
    print(system.PowerState)
    if hasattr(system, "BootMode"):
        print("OEM Boot Mode:", system.BootMode)
    for chassis in system.Chassis:
        print("Chassis:", chassis.Id)
    if hasattr(system, "Reset"):
        system.Reset(ResetType="GracefulRestart")
client.logout()
```

See also: [OEM_LINKS_SURFACING.md](OEM_LINKS_SURFACING.md) for advanced surfacing details.

---

# Common Redfish Use Case Examples

Below are code patterns for the most common Redfish operations using rackfish. Replace `client` and resource names as appropriate for your environment.

## User Management

### Add User
```python
accounts = client.AccountService.Accounts
new_user = accounts.create({"UserName": "testuser", "Password": "pass", "RoleId": "Operator"})
```

### Delete User
```python
user = accounts["testuser"]  # or iterate accounts to find
user.delete()
```

### Set User Password
```python
user = accounts["testuser"]
user.Password = "newpass"  # Triggers PATCH
```

### Set User Role
```python
user = accounts["testuser"]
user.RoleId = "Administrator"
```

## Event Subscription

### Add Event Subscription
```python
subs = client.EventService.Subscriptions
new_sub = subs.create({
    "Destination": "https://my.listener/endpoint",
    "EventTypes": ["Alert"],
    "Protocol": "Redfish"
})
```

### Delete Event Subscription
```python
for sub in subs:
    if sub.Destination == "https://my.listener/endpoint":
        sub.delete()
```

## Storage and Logical Drives

### Add Logical Drive
```python
storage = next(iter(client.Systems)).Storage[0]
ldrive = storage.Volumes.create({
    "Name": "MyVolume",
    "CapacityBytes": 100*1024**3,
    "VolumeType": "RawDevice"
})
```

### Delete Logical Drive

```python
for vol in storage.Volumes:
    if vol.Name == "MyVolume":
        vol.delete()
```

## BIOS and Firmware

### Get BIOS Details

```python
bios = next(iter(client.Systems)).Bios
print(bios.to_dict())
```

### Set BIOS Attribute

```python
bios = next(iter(client.Systems)).Bios
bios.patch({"BootMode": "UEFI"})
```

### Reset BIOS to Default

```python
bios.ResetBios()  # If action available
```

### Upgrade BMC Firmware

```python
update_service = client.UpdateService
update_service.SimpleUpdate(ImageURI="http://server/fw.bin", TransferProtocol="HTTP")
```

### Reset BMC

```python
bmc = next(iter(client.Managers))
bmc.Reset(ResetType="GracefulRestart")
```

### Rollback BMC

```python
if hasattr(bmc, "Rollback"):
    bmc.Rollback()
```

## Certificates and Security

### Add CSR (Certificate Signing Request)

```python
cert_service = client.CertificateService
csr = cert_service.GenerateCSR(CommonName="bmc.example.com", Country="US", Organization="MyOrg")
```

### Export CSR

```python
# Access existing CSR from certificate locations
cert_loc = client.Managers[0].NetworkProtocol.HTTPS.Certificates[0]
print(cert_loc.CertificateString)
```

### Import SSL Certificate

```python
certs = client.Managers[0].NetworkProtocol.HTTPS.Certificates
certs.create({"CertificateString": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"})
```

### Import LDAP Certificate

```python
ldap_certs = client.AccountService.LDAP.Certificates
ldap_certs.create({"CertificateString": "...PEM..."})
```

### Import SSH Public Key

```python
ssh_keys = client.AccountService.Accounts["admin"].Keys
ssh_keys.create({"KeyString": "ssh-rsa AAAA..."})
```

### Delete SSH Public Key

```python
for key in ssh_keys:
    if "mykey" in key.KeyString:
        key.delete()
```

### Import Two-Factor Certificate

```python
twofactor_certs = client.AccountService.MultiFactorAuth.Certificates
twofactor_certs.create({"CertificateString": "...PEM..."})
```

### Delete Remote HTTPS Server Certificate

```python
remote_certs = client.Managers[0].RemoteServerCertificates
for cert in remote_certs:
    cert.delete()
```

## Power and FRU Control

### Control OS Power (Reset System)

```python
system = next(iter(client.Systems))
system.Reset(ResetType="ForceOff")  # Options: On, ForceOff, GracefulRestart, etc.
```

### Control FRU Power (OEM Action)

```python
if hasattr(system, "FruControl"):
    system.FruControl(Operation="PowerOn")
```

### Set Power Limit

```python
power = system.Power
power.PowerControl[0].PowerLimit.LimitInWatts = 500
power.patch(power.to_dict())
```

### Get Power Supply Status

```python
for ps in system.Power.PowerSupplies:
    print(f"{ps.Name}: {ps.Status}")
```

## Storage Processor (SP) Operations

### Add SP Configuration

```python
sp_service = client.StorageServices[0]
sp_service.CreateConfig(ConfigData={"setting": "value"})
```

### Get SP Configuration

```python
sp_cfg = sp_service.Configurations[0]
print(sp_cfg.to_dict())
```

### Delete SP Configuration

```python
sp_cfg.delete()
```

### Diagnose SP

```python
if hasattr(sp_service, "RunDiagnostics"):
    sp_service.RunDiagnostics(DiagnosticType="Quick")
```

### Erase SP Drive

```python
if hasattr(sp_service, "SecureErase"):
    sp_service.SecureErase(DriveId="Drive1")
```

### Get SP File List

```python
files = sp_service.Files
for f in files:
    print(f.FileName)
```

### Delete SP File

```python
for f in files:
    if f.FileName == "old_config.dat":
        f.delete()
```

### Upload to SP / Upgrade SP

```python
sp_service.UploadFile(FileURI="http://server/file.bin")
```

## Network and VLAN

### Change Port Mode

```python
port = client.Managers[0].EthernetInterfaces[0]
port.InterfaceEnabled = True
```

### Set IPv4

```python
port.IPv4Addresses = [{"Address": "192.168.1.10", "SubnetMask": "255.255.255.0", "Gateway": "192.168.1.1"}]
port.patch({"IPv4Addresses": port.IPv4Addresses})
```

### Set IPv6

```python
port.patch({"IPv6Addresses": [{"Address": "fe80::1", "PrefixLength": 64}]})
```

### Set DNS

```python
net_proto = client.Managers[0].NetworkProtocol
net_proto.patch({"DNS": {"DNSServers": ["8.8.8.8", "8.8.4.4"]}})
```

### Set NTP

```python
net_proto.patch({"NTP": {"NTPServers": ["time.google.com"]}})
```

### Upload NTP Group Key

```python
if hasattr(net_proto.NTP, "UploadKey"):
    net_proto.NTP.UploadKey(KeyData="base64encodedkey")
```

### Set VLAN

```python
vlans = port.VLANs
vlan = vlans.create({"VLANId": 100, "VLANEnable": True})
```

### Get VLAN

```python
for vlan in vlans:
    print(f"VLAN {vlan.VLANId}: Enabled={vlan.VLANEnable}")
```

### Set Network Service (SNMP, etc.)

```python
net_proto.patch({"SNMP": {"ProtocolEnabled": True}})
```

### Set SNMP Trap

```python
snmp_service = net_proto.SNMP
if hasattr(snmp_service, "TrapDestinations"):
    snmp_service.patch({"TrapDestinations": ["192.168.1.100"]})
```

## System and Health

### Get System Health

```python
system = next(iter(client.Systems))
print(f"Health: {system.Status['Health']}, State: {system.Status['State']}")
```

### Get Health Events

```python
log_service = client.Managers[0].LogServices["EventLog"]
for entry in log_service.Entries:
    if entry.Severity in ["Warning", "Critical"]:
        print(entry.Message)
```

### Get Sensor List

```python
chassis = client.Chassis[0]
for sensor in chassis.Sensors:
    print(f"{sensor.Name}: {sensor.Reading} {sensor.ReadingUnits}")
```

### Get Temperature

```python
thermal = chassis.Thermal
for temp in thermal.Temperatures:
    print(f"{temp.Name}: {temp.ReadingCelsius}°C")
```

### Get Fan

```python
for fan in thermal.Fans:
    print(f"{fan.Name}: {fan.Reading} RPM")
```

### Get Voltage

```python
power = chassis.Power
for volt in power.Voltages:
    print(f"{volt.Name}: {volt.ReadingVolts}V")
```

### Get CPU / Processor

```python
system = next(iter(client.Systems))
for proc in system.Processors:
    print(f"{proc.Name}: {proc.TotalCores} cores, {proc.MaxSpeedMHz} MHz")
```

### Get Memory

```python
for mem in system.Memory:
    print(f"{mem.Name}: {mem.CapacityMiB} MiB")
```

### Get PCIe Devices

```python
for pcie in system.PCIeDevices:
    print(f"{pcie.Name}: {pcie.DeviceType}")
```

### Get Storage

```python
for storage in system.Storage:
    print(f"Storage Controller: {storage.Name}")
    for drive in storage.Drives:
        print(f"  Drive: {drive.Name} - {drive.CapacityBytes} bytes")
```

### Get Disk Backplane

```python
# Access via Chassis or Storage depending on BMC implementation
if hasattr(chassis, "Backplanes"):
    for bp in chassis.Backplanes:
        print(bp.Name)
```

## Session and Login

### Get Session

```python
sessions = client.SessionService.Sessions
for sess in sessions:
    print(f"Session: {sess.UserName} - {sess.Id}")
```

### Delete Session

```python
for sess in sessions:
    if sess.UserName == "testuser":
        sess.delete()
```

### Set Login Rule / Password Policy

```python
acct_service = client.AccountService
acct_service.patch({"AccountLockoutDuration": 300, "AccountLockoutThreshold": 5})
```

## SEL and Logs

### Get SEL (System Event Log)

```python
sel = client.Managers[0].LogServices["SEL"]
for entry in sel.Entries:
    print(f"{entry.Created}: {entry.Message}")
```

### Clear SEL

```python
sel.ClearLog()
```

### Collect SEL (Export)

```python
# Download entries programmatically or via export action if available
entries = [e.to_dict() for e in sel.Entries]
```

## KVM, VMM, VNC

### Get KVM

```python
kvm = client.Managers[0].GraphicalConsole
print(f"KVM Enabled: {kvm.ServiceEnabled}")
```

### Set KVM

```python
kvm.patch({"ServiceEnabled": True, "MaxConcurrentSessions": 4})
```

### Get VNC

```python
vnc = client.Managers[0].SerialConsole
print(vnc.to_dict())
```

### Set VNC

```python
vnc.patch({"ServiceEnabled": True})
```

### Get VMM (Virtual Media)

```python
vmm = client.Managers[0].VirtualMedia
for media in vmm:
    print(f"{media.Name}: {media.Image}")
```

### Set VMM / Operate VMM

```python
media = vmm[0]
media.InsertMedia(Image="http://server/iso/ubuntu.iso", Inserted=True)
```

### Eject VMM

```python
media.EjectMedia()
```

## LDAP and Authentication

### Get LDAP Info

```python
ldap = client.AccountService.LDAP
print(ldap.to_dict())
```

### Set LDAP State

```python
ldap.patch({"ServiceEnabled": True})
```

### Set LDAP Controller

```python
ldap.patch({"ServiceAddresses": ["ldap://ldap.example.com"]})
```

### Set LDAP Group

```python
ldap_groups = ldap.RemoteRoleMapping
ldap_groups.create({"RemoteGroup": "admins", "LocalRole": "Administrator"})
```

## Miscellaneous Operations

### Get Product Info

```python
system = next(iter(client.Systems))
print(f"Manufacturer: {system.Manufacturer}, Model: {system.Model}, SerialNumber: {system.SerialNumber}")
```

### Set Product Info (OEM)

```python
if hasattr(system, "AssetTag"):
    system.AssetTag = "TAG12345"
```

### Get License Info

```python
if hasattr(client, "LicenseService"):
    for lic in client.LicenseService.Licenses:
        print(f"{lic.Name}: Expires {lic.ExpirationDate}")
```

### Install License

```python
if hasattr(client.LicenseService, "InstallLicense"):
    client.LicenseService.InstallLicense(LicenseString="...base64...")
```

### Get Screenshot

```python
# Typically OEM action or virtual media related
if hasattr(client.Managers[0], "Screenshot"):
    screenshot = client.Managers[0].Screenshot()
```

### Delete Screenshot

```python
# Delete cached screenshot if stored as resource
if hasattr(client.Managers[0], "Screenshots"):
    for ss in client.Managers[0].Screenshots:
        ss.delete()
```

### Restore Factory Settings

```python
manager = client.Managers[0]
if hasattr(manager, "ResetToDefaults"):
    manager.ResetToDefaults(ResetType="ResetAll")
```

### Get Time / Set Time

```python
# Get
manager = client.Managers[0]
print(manager.DateTime)

# Set (if writable)
manager.DateTime = "2025-10-15T12:00:00Z"
```

### Set Timezone

```python
manager.DateTimeLocalOffset = "+00:00"
```

### Get System Boot

```python
system = next(iter(client.Systems))
boot = system.Boot
print(f"BootSourceOverrideTarget: {boot['BootSourceOverrideTarget']}")
```

### Set System Boot

```python
system.patch({"Boot": {"BootSourceOverrideTarget": "Pxe", "BootSourceOverrideEnabled": "Once"}})
```

### Get Stateless / Set Stateless

```python
# OEM feature for stateless compute
if hasattr(system, "Stateless"):
    print(system.Stateless)
    system.patch({"Stateless": {"Enabled": True}})
```

### Get Device Info

```python
# Generic device inventory
for device in system.get("Devices", []):
    print(device)
```

### Reset Storage Controller

```python
storage = system.Storage[0]
if hasattr(storage, "ResetController"):
    storage.ResetController()
```

### Restore Storage Controller

```python
if hasattr(storage, "RestoreDefaults"):
    storage.RestoreDefaults()
```

### Get OS Info / OS Driver / OS Firmware

```python
# OEM extensions for OS-related details
if hasattr(system, "OperatingSystem"):
    os_info = system.OperatingSystem
    print(os_info.to_dict())
```

### Upgrade Driver

```python
# OEM action for driver updates
if hasattr(system, "UpdateDriver"):
    system.UpdateDriver(DriverURI="http://server/driver.bin")
```

### Get Role

```python
roles = client.AccountService.Roles
for role in roles:
    print(f"Role: {role.Id} - Privileges: {role.AssignedPrivileges}")
```

### Set Custom Role

```python
roles.create({"RoleId": "CustomRole", "AssignedPrivileges": ["Login", "ConfigureManager"]})
```

### Common Function / Request Helpers

```python
# For generic GET/POST/PATCH/DELETE operations not surfaced as methods:
response = client.get("/redfish/v1/some/custom/path")
client.post("/redfish/v1/Actions/Custom", data={"param": "value"})
client.patch("/redfish/v1/Systems/1", data={"AssetTag": "NEW"})
client.delete("/redfish/v1/SomeCollection/Item")
```

---

**See also:**

- [OEM_LINKS_SURFACING.md](OEM_LINKS_SURFACING.md) for advanced surfacing details
- [../tests/test_common_usage.py](../tests/test_common_usage.py) for test examples

