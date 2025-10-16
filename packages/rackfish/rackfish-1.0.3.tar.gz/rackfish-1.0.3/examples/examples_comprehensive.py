#!/usr/bin/env python3
"""
Comprehensive examples demonstrating common Redfish use cases with pyredfisher.
This file shows real-world patterns for managing servers, storage, network, users, and more.
"""

from rackfish import RedfishClient

# ============================================================================
# SETUP: Connect to BMC
# ============================================================================


def connect_to_bmc(host, username, password):
    """Establish connection to Redfish BMC with session authentication."""
    client = RedfishClient(
        f"https://{host}",
        username=username,
        password=password,
        use_session=True,
        verify_ssl=False,  # For testing; use True in production with valid certs
    )
    root = client.connect()
    print(f"Connected to {host}")
    return client


# ============================================================================
# USER MANAGEMENT
# ============================================================================


def manage_users(client):
    """Demonstrate user account creation, modification, and deletion."""
    print("\n=== User Management ===")

    accounts = client.AccountService.Accounts

    # Create a new user
    new_user = accounts.create(
        {"UserName": "operator1", "Password": "SecurePass123!", "RoleId": "Operator"}
    )
    print(f"Created user: {new_user.UserName}")

    # Update user password
    new_user.Password = "NewSecurePass456!"
    print(f"Updated password for {new_user.UserName}")

    # Change user role
    new_user.RoleId = "Administrator"
    print(f"Updated role for {new_user.UserName} to Administrator")

    # List all users
    print("Current users:")
    for user in accounts:
        print(f"  - {user.UserName} ({user.RoleId})")

    # Delete user
    new_user.delete()
    print(f"Deleted user: operator1")


# ============================================================================
# SYSTEM POWER CONTROL
# ============================================================================


def control_system_power(client):
    """Demonstrate system power operations."""
    print("\n=== System Power Control ===")

    for system in client.Systems:
        print(f"System: {system.Name}")
        print(f"  Current Power State: {system.PowerState}")

        # Get allowable reset types
        reset_types = system.get_allowable_values("ResetType")
        if reset_types:
            print(f"  Available Reset Types: {reset_types}")

        # Perform reset (commented to avoid actually resetting)
        # system.Reset(ResetType="GracefulRestart")
        # print(f"  Initiated GracefulRestart")

        # OEM power control (if available)
        if hasattr(system, "FruControl"):
            print(f"  OEM FruControl action available")
            # system.FruControl(Operation="PowerCycle")


# ============================================================================
# BIOS CONFIGURATION
# ============================================================================


def configure_bios(client):
    """Demonstrate BIOS settings management."""
    print("\n=== BIOS Configuration ===")

    system = next(iter(client.Systems))
    bios = system.Bios

    print(f"Current BIOS attributes:")
    bios_attrs = bios.Attributes
    for key in list(bios_attrs.keys())[:5]:  # Show first 5
        print(f"  {key}: {bios_attrs[key]}")

    # Update BIOS settings
    # bios.patch({"Attributes": {"BootMode": "UEFI"}})
    # print("Updated BootMode to UEFI")

    # Reset BIOS to defaults (if action available)
    if hasattr(bios, "ResetBios"):
        # bios.ResetBios()
        print("ResetBios action available")


# ============================================================================
# STORAGE MANAGEMENT
# ============================================================================


def manage_storage(client):
    """Demonstrate storage and volume management."""
    print("\n=== Storage Management ===")

    system = next(iter(client.Systems))

    for storage in system.Storage:
        print(f"Storage Controller: {storage.Name}")

        # List drives
        for drive in storage.Drives:
            print(f"  Drive: {drive.Name}")
            print(f"    Capacity: {drive.CapacityBytes / (1024**3):.2f} GB")
            print(f"    Media Type: {drive.MediaType}")
            print(f"    Status: {drive.Status['Health']}")

        # List volumes (logical drives)
        if hasattr(storage, "Volumes"):
            print(f"  Volumes:")
            for vol in storage.Volumes:
                print(f"    - {vol.Name}: {vol.CapacityBytes / (1024**3):.2f} GB")

            # Create a new volume
            # new_vol = storage.Volumes.create({
            #     "Name": "DataVolume",
            #     "CapacityBytes": 500 * 1024**3,
            #     "VolumeType": "RawDevice"
            # })
            # print(f"Created volume: {new_vol.Name}")


# ============================================================================
# NETWORK CONFIGURATION
# ============================================================================


def configure_network(client):
    """Demonstrate network interface and protocol configuration."""
    print("\n=== Network Configuration ===")

    manager = next(iter(client.Managers))

    # Ethernet interfaces
    for eth in manager.EthernetInterfaces:
        print(f"Interface: {eth.Name}")
        print(f"  MAC Address: {eth.MACAddress}")
        print(f"  Speed: {eth.SpeedMbps} Mbps")

        # IPv4 configuration
        if hasattr(eth, "IPv4Addresses"):
            for ipv4 in eth.IPv4Addresses:
                print(f"  IPv4: {ipv4.get('Address')} / {ipv4.get('SubnetMask')}")

        # Update network settings (example)
        # eth.patch({
        #     "IPv4Addresses": [{
        #         "Address": "192.168.1.100",
        #         "SubnetMask": "255.255.255.0",
        #         "Gateway": "192.168.1.1"
        #     }]
        # })

    # Network protocols (DNS, NTP, SNMP, etc.)
    net_proto = manager.NetworkProtocol
    print(f"\nNetwork Protocols:")

    if hasattr(net_proto, "NTP"):
        ntp = net_proto.NTP
        if hasattr(ntp, "NTPServers"):
            print(f"  NTP Servers: {ntp.NTPServers}")

    # Update NTP servers
    # net_proto.patch({"NTP": {"NTPServers": ["time.google.com", "time.nist.gov"]}})


# ============================================================================
# VLAN CONFIGURATION
# ============================================================================


def configure_vlan(client):
    """Demonstrate VLAN management."""
    print("\n=== VLAN Configuration ===")

    manager = next(iter(client.Managers))
    eth = manager.EthernetInterfaces[0]

    if hasattr(eth, "VLANs"):
        vlans = eth.VLANs

        # List existing VLANs
        print("Existing VLANs:")
        for vlan in vlans:
            print(f"  VLAN {vlan.VLANId}: Enabled={vlan.VLANEnable}")

        # Create new VLAN
        # new_vlan = vlans.create({
        #     "VLANId": 100,
        #     "VLANEnable": True
        # })
        # print(f"Created VLAN {new_vlan.VLANId}")


# ============================================================================
# EVENT SUBSCRIPTION
# ============================================================================


def manage_event_subscriptions(client):
    """Demonstrate event subscription management."""
    print("\n=== Event Subscriptions ===")

    event_service = client.EventService
    subs = event_service.Subscriptions

    # List existing subscriptions
    print("Current subscriptions:")
    for sub in subs:
        print(f"  {sub.Id}: {sub.Destination}")
        print(f"    Protocol: {sub.Protocol}")
        print(f"    Event Types: {sub.EventTypes}")

    # Create new subscription
    # new_sub = subs.create({
    #     "Destination": "https://my.listener.com/events",
    #     "EventTypes": ["Alert", "StatusChange"],
    #     "Protocol": "Redfish",
    #     "Context": "MyEventSubscription"
    # })
    # print(f"Created subscription: {new_sub.Id}")

    # Delete subscription
    # for sub in subs:
    #     if sub.Destination == "https://my.listener.com/events":
    #         sub.delete()
    #         print(f"Deleted subscription {sub.Id}")


# ============================================================================
# CERTIFICATE MANAGEMENT
# ============================================================================


def manage_certificates(client):
    """Demonstrate certificate import and management."""
    print("\n=== Certificate Management ===")

    manager = next(iter(client.Managers))

    # HTTPS certificates
    if hasattr(manager.NetworkProtocol, "HTTPS"):
        https = manager.NetworkProtocol.HTTPS
        if hasattr(https, "Certificates"):
            print("HTTPS Certificates:")
            for cert in https.Certificates:
                print(f"  Subject: {cert.Subject}")
                print(f"  Issuer: {cert.Issuer}")
                print(f"  Valid From: {cert.ValidNotBefore}")
                print(f"  Valid Until: {cert.ValidNotAfter}")

    # Generate CSR (Certificate Signing Request)
    if hasattr(client, "CertificateService"):
        cert_service = client.CertificateService
        # csr = cert_service.GenerateCSR(
        #     CommonName="bmc.example.com",
        #     Country="US",
        #     State="CA",
        #     City="San Francisco",
        #     Organization="MyCompany"
        # )
        # print(f"Generated CSR:\n{csr}")


# ============================================================================
# FIRMWARE UPDATE
# ============================================================================


def update_firmware(client):
    """Demonstrate firmware update operations."""
    print("\n=== Firmware Update ===")

    update_service = client.UpdateService

    print(f"Update Service:")
    print(f"  HTTP Push URI Supported: {update_service.HttpPushUriTargets}")

    # Get current firmware inventory
    if hasattr(update_service, "FirmwareInventory"):
        print("\nCurrent Firmware:")
        for fw in update_service.FirmwareInventory:
            print(f"  {fw.Name}: {fw.Version}")

    # Simple update (HTTP pull)
    # update_service.SimpleUpdate(
    #     ImageURI="http://fileserver.local/firmware/bmc_v3.20.bin",
    #     TransferProtocol="HTTP"
    # )

    # Check update task status
    if hasattr(client, "TaskService"):
        tasks = client.TaskService.Tasks
        for task in tasks:
            print(f"Task {task.Id}: {task.TaskState} - {task.TaskStatus}")


# ============================================================================
# SYSTEM HEALTH MONITORING
# ============================================================================


def monitor_system_health(client):
    """Demonstrate health and sensor monitoring."""
    print("\n=== System Health Monitoring ===")

    system = next(iter(client.Systems))

    # Overall system health
    print(f"System: {system.Name}")
    print(f"  Health: {system.Status['Health']}")
    print(f"  State: {system.Status['State']}")

    # Chassis and sensors
    for chassis in system.Chassis:
        print(f"\nChassis: {chassis.Name}")

        # Temperature sensors
        if hasattr(chassis, "Thermal"):
            thermal = chassis.Thermal
            if hasattr(thermal, "Temperatures"):
                print("  Temperatures:")
                for temp in thermal.Temperatures:
                    print(f"    {temp.Name}: {temp.ReadingCelsius}°C")

            # Fans
            if hasattr(thermal, "Fans"):
                print("  Fans:")
                for fan in thermal.Fans:
                    print(f"    {fan.Name}: {fan.Reading} RPM")

        # Power and voltages
        if hasattr(chassis, "Power"):
            power = chassis.Power
            if hasattr(power, "Voltages"):
                print("  Voltages:")
                for volt in power.Voltages:
                    print(f"    {volt.Name}: {volt.ReadingVolts}V")

            # Power supplies
            if hasattr(power, "PowerSupplies"):
                print("  Power Supplies:")
                for ps in power.PowerSupplies:
                    print(f"    {ps.Name}: {ps.Status['Health']}")


# ============================================================================
# SYSTEM EVENT LOG (SEL)
# ============================================================================


def collect_system_logs(client):
    """Demonstrate system event log collection."""
    print("\n=== System Event Logs ===")

    manager = next(iter(client.Managers))

    for log_service in manager.LogServices:
        print(f"\nLog Service: {log_service.Name}")
        print(f"  Max Records: {log_service.MaxNumberOfRecords}")
        print(f"  Overflow Policy: {log_service.OverWritePolicy}")

        # Get recent entries
        if hasattr(log_service, "Entries"):
            print("  Recent Entries:")
            for entry in list(log_service.Entries)[:5]:  # Last 5 entries
                print(f"    [{entry.Created}] {entry.Severity}: {entry.Message}")

        # Clear log (if action available)
        if hasattr(log_service, "ClearLog"):
            # log_service.ClearLog()
            print("  ClearLog action available")


# ============================================================================
# BOOT ORDER CONFIGURATION
# ============================================================================


def configure_boot_order(client):
    """Demonstrate boot configuration management."""
    print("\n=== Boot Configuration ===")

    system = next(iter(client.Systems))
    boot = system.Boot

    print(f"Current Boot Configuration:")
    print(f"  Boot Source Override: {boot['BootSourceOverrideTarget']}")
    print(f"  Boot Mode: {boot.get('BootSourceOverrideMode', 'N/A')}")
    print(f"  UEFI Target: {boot.get('UefiTargetBootSourceOverride', 'N/A')}")

    # Get allowable boot sources
    allowable = system.get_allowable_values("BootSourceOverrideTarget")
    if allowable:
        print(f"  Allowable Boot Sources: {allowable}")

    # Set PXE boot for next boot
    # system.patch({
    #     "Boot": {
    #         "BootSourceOverrideTarget": "Pxe",
    #         "BootSourceOverrideEnabled": "Once"
    #     }
    # })
    # print("Set boot to PXE for next boot")


# ============================================================================
# VIRTUAL MEDIA (KVM)
# ============================================================================


def manage_virtual_media(client):
    """Demonstrate virtual media (remote ISO) management."""
    print("\n=== Virtual Media ===")

    manager = next(iter(client.Managers))

    if hasattr(manager, "VirtualMedia"):
        for media in manager.VirtualMedia:
            print(f"Media: {media.Name}")
            print(f"  Media Type: {media.MediaTypes}")
            print(f"  Inserted: {media.Inserted}")
            if media.Inserted:
                print(f"  Image: {media.Image}")

            # Insert ISO image
            # if hasattr(media, "InsertMedia"):
            #     media.InsertMedia(
            #         Image="http://fileserver.local/isos/ubuntu-22.04.iso",
            #         Inserted=True
            #     )
            #     print(f"Inserted ISO into {media.Name}")

            # Eject media
            # if hasattr(media, "EjectMedia"):
            #     media.EjectMedia()
            #     print(f"Ejected media from {media.Name}")


# ============================================================================
# LDAP CONFIGURATION
# ============================================================================


def configure_ldap(client):
    """Demonstrate LDAP authentication configuration."""
    print("\n=== LDAP Configuration ===")

    acct_service = client.AccountService

    if hasattr(acct_service, "LDAP"):
        ldap = acct_service.LDAP

        print(f"LDAP Configuration:")
        print(f"  Enabled: {ldap.ServiceEnabled}")
        if hasattr(ldap, "ServiceAddresses"):
            print(f"  Servers: {ldap.ServiceAddresses}")

        # Update LDAP settings
        # ldap.patch({
        #     "ServiceEnabled": True,
        #     "ServiceAddresses": ["ldap://ldap.example.com:389"],
        #     "Authentication": {
        #         "AuthenticationType": "UsernameAndPassword",
        #         "Username": "cn=admin,dc=example,dc=com",
        #         "Password": "ldap_password"
        #     }
        # })

        # Configure LDAP role mapping
        if hasattr(ldap, "RemoteRoleMapping"):
            print("  LDAP Role Mappings:")
            for mapping in ldap.RemoteRoleMapping:
                print(f"    {mapping.RemoteGroup} -> {mapping.LocalRole}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main():
    """Main function demonstrating all use cases."""
    # NOTE: Update these with your actual BMC credentials
    HOST = "192.168.1.100"
    USERNAME = "admin"
    PASSWORD = "password"

    print("=" * 80)
    print("pyredfisher Comprehensive Examples")
    print("=" * 80)
    print("\nNOTE: Most write operations are commented out to prevent")
    print("      accidental changes. Uncomment carefully for testing.")
    print("=" * 80)

    try:
        # Connect to BMC
        client = connect_to_bmc(HOST, USERNAME, PASSWORD)

        # Run example demonstrations
        # manage_users(client)
        control_system_power(client)
        # configure_bios(client)
        manage_storage(client)
        configure_network(client)
        # configure_vlan(client)
        # manage_event_subscriptions(client)
        # manage_certificates(client)
        # update_firmware(client)
        monitor_system_health(client)
        collect_system_logs(client)
        # configure_boot_order(client)
        # manage_virtual_media(client)
        # configure_ldap(client)

        # Logout
        client.logout()
        print("\n" + "=" * 80)
        print("Disconnected successfully")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
