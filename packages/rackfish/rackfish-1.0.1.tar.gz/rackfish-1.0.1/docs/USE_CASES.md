# rackfish - Complete Use Cases Documentation

This document provides a comprehensive index of all supported Redfish use cases and their implementation in rackfish.

## Quick Navigation

- [User Management](#user-management)
- [Event Subscriptions](#event-subscriptions)
- [Storage & Logical Drives](#storage--logical-drives)
- [BIOS & Firmware](#bios--firmware)
- [Certificates & Security](#certificates--security)
- [Power & FRU Control](#power--fru-control)
- [Storage Processor (SP)](#storage-processor-sp)
- [Network & VLAN](#network--vlan)
- [System Health & Sensors](#system-health--sensors)
- [Sessions & Authentication](#sessions--authentication)
- [Logs (SEL)](#logs-sel)
- [KVM, VMM, VNC](#kvm-vmm-vnc)
- [LDAP](#ldap)
- [Miscellaneous](#miscellaneous)

---

## User Management

| Use Case | Function | Implementation |
|----------|----------|----------------|
| Add user | `add_user` | `accounts.create({"UserName": "...", "Password": "...", "RoleId": "..."})` |
| Delete user | `delete_user` | `user.delete()` |
| Set user password | `set_user_password` | `user.Password = "newpass"` |
| Set user role | `set_user_role` | `user.RoleId = "Administrator"` |
| Get user | `get_user` | `for user in client.AccountService.Accounts:` |
| Set custom role | `set_custom_role` | `roles.create({"RoleId": "...", "AssignedPrivileges": [...]})` |
| Get role | `get_role` | `for role in client.AccountService.Roles:` |
| Set login rule | `set_loginrule` | `acct_service.patch({"AccountLockoutDuration": 300})` |
| Get login rule | `get_loginrule` | `print(acct_service.AccountLockoutThreshold)` |
| Set password policy | `set_password_policy` | `acct_service.patch({"MinPasswordLength": 8})` |
| Get password policy | `get_password_policy` | `print(acct_service.to_dict())` |

---

## Event Subscriptions

| Use Case | Function | Implementation |
|----------|----------|----------------|
| Add event subscription | `add_event_subscription` | `subs.create({"Destination": "...", "EventTypes": [...]})` |
| Delete event subscription | `del_event_subscription` | `sub.delete()` |
| Get event subscription | `get_event_subscription` | `for sub in client.EventService.Subscriptions:` |

---

## Storage & Logical Drives

| Use Case | Function | Implementation |
|----------|----------|----------------|
| Add logical drive | `add_logicaldrive` | `storage.Volumes.create({"Name": "...", "CapacityBytes": ...})` |
| Delete logical drive | `del_logicaldrive` | `volume.delete()` |
| Get logical drive | `get_logicaldrive` | `for vol in storage.Volumes:` |
| Set logical drive | `set_logicaldrive` | `volume.patch({...})` |
| Get storage | `get_storage` | `for storage in system.Storage:` |
| Get drive info | `get_drive_info` | `for drive in storage.Drives:` |
| Set drive | `set_drive` | `drive.patch({...})` |
| Reset storage controller | `reset_storage_controller` | `storage.ResetController()` |
| Restore storage controller | `restore_storage_controller` | `storage.RestoreDefaults()` |
| Set storage controller | `set_storage_controller` | `storage.patch({...})` |
| Get disk backplane | `get_disk_bp` | `for bp in chassis.Backplanes:` |

---

## BIOS & Firmware

| Use Case | Function | Implementation |
|----------|----------|----------------|
| Get BIOS | `get_bios` | `bios = system.Bios` |
| Get BIOS details | `get_bios_details` | `print(bios.to_dict())` |
| Set BIOS | `set_bios` | `bios.patch({"Attributes": {...}})` |
| Set BIOS default | `set_bios_default` | `bios.ResetBios()` |
| Get system boot | `get_sys_boot` | `boot = system.Boot` |
| Set system boot | `set_sys_boot` | `system.patch({"Boot": {...}})` |
| Upgrade BMC firmware | `upgrade_bmc_firmware` | `update_service.SimpleUpdate(ImageURI="...")` |
| Get BMC firmware | `get_bmc_firmware` | `for fw in update_service.FirmwareInventory:` |
| Reset BMC | `reset_bmc` | `bmc.Reset(ResetType="GracefulRestart")` |
| Rollback BMC | `rollback_bmc` | `bmc.Rollback()` |
| Get OS firmware | `get_os_firmware` | `print(system.OperatingSystem)` (OEM) |
| Upgrade driver | `upgrade_driver` | `system.UpdateDriver(DriverURI="...")` (OEM) |
| Get OS driver | `get_os_driver` | `print(system.Drivers)` (OEM) |

---

## Certificates & Security

| Use Case | Function | Implementation |
|----------|----------|----------------|
| Add CSR | `add_csr` | `cert_service.GenerateCSR(CommonName="...", ...)` |
| Export CSR | `export_csr` | `print(cert.CertificateString)` |
| Get CSR | `get_csr` | `for cert in certs:` |
| Import SSL cert | `import_ssl_cert` | `certs.create({"CertificateString": "..."})` |
| Get SSL cert | `get_ssl_cert` | `for cert in manager.NetworkProtocol.HTTPS.Certificates:` |
| Import LDAP cert | `import_ldap_cert` | `ldap_certs.create({"CertificateString": "..."})` |
| Import syslog cert | `import_syslog_cert` | `syslog_certs.create({"CertificateString": "..."})` |
| Get syslog cert | `get_syslog_cert` | `for cert in syslog.Certificates:` |
| Import two-factor cert | `import_twofactor_cert` | `mfa_certs.create({"CertificateString": "..."})` |
| Get two-factor cert | `get_twofactor_cert` | `for cert in mfa.Certificates:` |
| Delete two-factor cert | `del_twofactor_cert` | `cert.delete()` |
| Import SSH public key | `import_ssh_public_key` | `ssh_keys.create({"KeyString": "..."})` |
| Get SSH public key | `get_ssh_public_key` | `for key in account.Keys:` |
| Delete SSH public key | `del_ssh_public_key` | `key.delete()` |
| Import remote HTTPS cert | `import_remote_https_server_cert` | `remote_certs.create({"CertificateString": "..."})` |
| Delete remote HTTPS cert | `del_remote_https_server_cert` | `cert.delete()` |
| Get security service | `get_security_service` | `print(manager.SecurityService)` |
| Set security service | `set_security_service` | `sec_service.patch({...})` |

---

## Power & FRU Control

| Use Case | Function | Implementation |
|----------|----------|----------------|
| Control OS power | `control_os_power` | `system.Reset(ResetType="ForceOff")` |
| Control FRU power | `control_fru_power` | `system.FruControl(Operation="PowerOn")` (OEM) |
| Get power limit | `get_power_limit` | `print(power.PowerControl[0].PowerLimit)` |
| Set power limit | `set_power_limit` | `power.patch({"PowerControl": [{"PowerLimit": {...}}]})` |
| Get power supply | `get_powersupply` | `for ps in power.PowerSupplies:` |
| Get PS redundancy | `get_ps_redundancy` | `print(power.Redundancy)` |
| Set PS redundancy | `set_ps_redundancy` | `power.patch({"Redundancy": [...]})` |
| Restore factory | `restore_factory` | `manager.ResetToDefaults(ResetType="ResetAll")` |

---

## Storage Processor (SP)

| Use Case | Function | Implementation |
|----------|----------|----------------|
| Add SP config | `add_sp_cfg` | `sp_service.CreateConfig(ConfigData={...})` |
| Get SP config | `get_sp_cfg` | `for cfg in sp_service.Configurations:` |
| Delete SP config | `del_sp_cfg` | `cfg.delete()` |
| Get SP diagnose | `get_sp_diagnose` | `print(sp_service.DiagnosticResults)` |
| Add SP diagnose | `add_sp_diagnose` | `sp_service.RunDiagnostics(Type="Quick")` |
| Get SP drive erase | `get_sp_drive_erase` | `print(sp_service.DriveEraseStatus)` |
| Add SP drive erase | `add_sp_drive_erase` | `sp_service.SecureErase(DriveId="...")` |
| Get SP file list | `get_sp_filelist` | `for f in sp_service.Files:` |
| Delete SP file | `delete_sp_file` | `file.delete()` |
| Get SP hardware | `get_sp_hardware` | `print(sp_service.Hardware)` |
| Get SP info | `get_sp_info` | `print(sp_service.to_dict())` |
| Set SP info | `set_sp_info` | `sp_service.patch({...})` |
| Get SP result | `get_sp_result` | `print(sp_service.Results)` |
| Upgrade SP | `upgrade_sp` | `sp_service.UploadFile(FileURI="...")` |

---

## Network & VLAN

| Use Case | Function | Implementation |
|----------|----------|----------------|
| Change port mode | `change_port_mode` | `port.InterfaceEnabled = True` |
| Set IPv4 | `set_ipv4` | `port.patch({"IPv4Addresses": [...]})` |
| Set IPv6 | `set_ipv6` | `port.patch({"IPv6Addresses": [...]})` |
| Set IP version | `set_ipversion` | `port.patch({"IPAddressPolicy": "..."})` |
| Get IP | `get_ip` | `print(port.IPv4Addresses)` |
| Get net port | `get_netport` | `for port in manager.EthernetInterfaces:` |
| Set management port | `set_mgmtport` | `port.patch({...})` |
| Set DNS | `set_dns` | `net_proto.patch({"DNS": {"DNSServers": [...]}})` |
| Get DNS | `get_dns` | `print(net_proto.DNS)` |
| Set NTP | `set_ntp` | `net_proto.patch({"NTP": {"NTPServers": [...]}})` |
| Get NTP | `get_ntp` | `print(net_proto.NTP)` |
| Upload NTP group key | `upload_ntpgroupkey` | `ntp.UploadKey(KeyData="...")` |
| Set VLAN | `set_vlan` | `vlans.create({"VLANId": 100, "VLANEnable": True})` |
| Get VLAN | `get_vlan` | `for vlan in port.VLANs:` |
| Set network service | `set_net_service` | `net_proto.patch({"SNMP": {"ProtocolEnabled": True}})` |
| Get network service | `get_net_service` | `print(net_proto.SNMP)` |
| Set SNMP trap | `set_snmp_trap` | `snmp.patch({"TrapDestinations": [...]})` |
| Set community name | `set_community_name` | `snmp.patch({"CommunityStrings": [...]})` |
| Set protocol | `set_protocol` | `net_proto.patch({"HTTP": {"ProtocolEnabled": False}})` |
| Set network mode | `set_netmode` | `port.patch({"LinkTechnology": "..."})` |
| Set adaptive port | `set_adaptiveport` | `port.patch({"AdaptivePortEnabled": True})` (OEM) |
| Set communication mode | `set_communication_mode` | `manager.patch({"CommunicationMode": "..."})` (OEM) |
| Get system Ethernet | `get_sys_eth` | `for eth in system.EthernetInterfaces:` |

---

## System Health & Sensors

| Use Case | Function | Implementation |
|----------|----------|----------------|
| Get system health | `get_sys_health` | `print(system.Status)` |
| Get health events | `get_health_events` | `for entry in log_service.Entries:` |
| Get sensor list | `get_sensor_list` | `for sensor in chassis.Sensors:` |
| Get sensor | `get_sensor` | `print(sensor.Reading)` |
| Get temperature | `get_temperature` | `for temp in thermal.Temperatures:` |
| Get fan | `get_fan` | `for fan in thermal.Fans:` |
| Set fan | `set_fan` | `fan.patch({"Oem": {...}})` (OEM) |
| Get voltage | `get_voltage` | `for volt in power.Voltages:` |
| Get CPU | `get_cpu` | `for proc in system.Processors:` |
| Get processor | `get_processor` | `print(proc.TotalCores)` |
| Get memory | `get_memory` | `for mem in system.Memory:` |
| Get memory count | `get_memory_count` | `print(len(system.Memory))` |
| Get PCIe devices | `get_pcie_devices` | `for pcie in system.PCIeDevices:` |
| Get PCIe SSD card | `get_pcie_ssd_card` | `for ssd in system.PCIeSSDs:` (OEM) |
| Get FRU | `get_fru` | `for fru in system.FRUs:` (OEM) |
| Get FRU info | `get_fru_info` | `print(fru.to_dict())` |
| Get net card info | `get_net_card_info` | `for nic in system.NetworkAdapters:` |
| Get device info | `get_device_info` | `print(system.Devices)` (OEM) |
| Get diag info | `get_diag_info` | `print(system.Diagnostics)` (OEM) |
| Get system performance | `get_sys_performance` | `print(system.Performance)` (OEM) |
| Set system performance | `set_sys_performance` | `system.patch({"Performance": {...}})` (OEM) |
| Get SD controller | `get_sd_controller` | `for sd in system.SDControllers:` (OEM) |

---

## Sessions & Authentication

| Use Case | Function | Implementation |
|----------|----------|----------------|
| Get session | `get_session` | `for sess in client.SessionService.Sessions:` |
| Delete session | `del_session` | `sess.delete()` |

---

## Logs (SEL)

| Use Case | Function | Implementation |
|----------|----------|----------------|
| Get SEL | `get_sel` | `for entry in sel.Entries:` |
| Clear SEL | `clear_sel` | `sel.ClearLog()` |
| Collect SEL | `collect_sel` | `entries = [e.to_dict() for e in sel.Entries]` |

---

## KVM, VMM, VNC

| Use Case | Function | Implementation |
|----------|----------|----------------|
| Get KVM | `get_kvm` | `kvm = manager.GraphicalConsole` |
| Set KVM | `set_kvm` | `kvm.patch({"ServiceEnabled": True})` |
| Get VNC | `get_vnc` | `vnc = manager.SerialConsole` |
| Set VNC | `set_vnc` | `vnc.patch({"ServiceEnabled": True})` |
| Get VMM | `get_vmm` | `for media in manager.VirtualMedia:` |
| Set VMM | `set_vmm` | `media.patch({"Image": "..."})` |
| Operate VMM | `operate_vmm` | `media.InsertMedia(Image="...", Inserted=True)` |
| Get screenshot | `get_screen_shot` | `screenshot = manager.Screenshot()` (OEM) |
| Delete screenshot | `del_screen_shot` | `screenshot.delete()` (OEM) |
| Get USB stick | `get_usbstick` | `print(manager.USBStick)` (OEM) |

---

## LDAP

| Use Case | Function | Implementation |
|----------|----------|----------------|
| Get LDAP info | `get_ldap_info` | `ldap = client.AccountService.LDAP` |
| Set LDAP state | `set_ldap_state` | `ldap.patch({"ServiceEnabled": True})` |
| Set LDAP controller | `set_ldap_controller` | `ldap.patch({"ServiceAddresses": [...]})` |
| Set LDAP group | `set_ldap_group` | `ldap.RemoteRoleMapping.create({...})` |

---

## Miscellaneous

| Use Case | Function | Implementation |
|----------|----------|----------------|
| Get product info | `get_product_info` | `print(system.Manufacturer, system.Model)` |
| Set product info | `set_product_info` | `system.AssetTag = "TAG123"` |
| Get license info | `get_license_info` | `for lic in client.LicenseService.Licenses:` |
| Install license | `install_license` | `client.LicenseService.InstallLicense(LicenseString="...")` |
| Get time | `get_time` | `print(manager.DateTime)` |
| Set time | `set_time` | `manager.DateTime = "2025-10-15T12:00:00Z"` |
| Set timezone | `set_timezone` | `manager.DateTimeLocalOffset = "+00:00"` |
| Get stateless | `get_stateless` | `print(system.Stateless)` (OEM) |
| Set stateless | `set_stateless` | `system.patch({"Stateless": {"Enabled": True}})` (OEM) |
| Get OS info | `get_os_info` | `print(system.OperatingSystem)` (OEM) |
| Get devirtualization service | `get_devirtualization_service` | `print(system.Devirtualization)` (OEM) |
| Set devirtualization service | `set_devirtualization_service` | `system.patch({"Devirtualization": {...}})` (OEM) |
| Get CDEV channel | `get_cdev_channel` | `print(manager.CDEVChannel)` (OEM) |
| Set CDEV channel | `set_cdev_channel` | `manager.patch({"CDEVChannel": {...}})` (OEM) |
| Common function | `common_function` | `client.get("/redfish/v1/custom/path")` |
| Common request | `common_request` | `client.post("/path", data={...})` |

---

## File Organization

- **[README.md](README.md)** - Main documentation with quick start
- **[EXAMPLES.md](EXAMPLES.md)** - Detailed code examples for all use cases
- **[TESTS.md](TESTS.md)** - Test suite documentation
- **[OEM_LINKS_SURFACING.md](OEM_LINKS_SURFACING.md)** - OEM/Links surfacing details
- **[test_common_usage.py](test_common_usage.py)** - Common usage tests
- **[test_oem_links_surfacing.py](test_oem_links_surfacing.py)** - OEM/Links tests
- **[test_recursion_fix.py](test_recursion_fix.py)** - Recursion guard tests
- **[examples_comprehensive.py](examples_comprehensive.py)** - Full working examples

---

## Summary

**Total Use Cases Covered: 150+**

All common Redfish operations are supported through:
- Direct property access
- Action method invocation
- Collection CRUD operations
- OEM extension surfacing
- Generic HTTP helpers

See [EXAMPLES.md](EXAMPLES.md) for complete code samples.
