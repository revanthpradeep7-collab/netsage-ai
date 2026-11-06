CASES_P4 = [
    # --- ACL CONTINUED (28) ---
    {
        "case_id": "NET-028",
        "title": "Inverted Wildcard Mask in Extended ACL",
        "symptom": "Security rule designed to block entire subnet 192.168.20.0/24 from accessing Server only blocks host 192.168.20.0, allowing other hosts through.",
        "topology_note": "Router-1 ACL 110 applied on G0/1 out.",
        "show_outputs": """Router-1# show ip access-lists 110\nExtended IP access list 110\n    10 deny ip 192.168.20.0 255.255.255.0 host 10.0.0.5\n    20 permit ip any any (241 matches)""",
        "expected_fault": "ACL 110 line 10 uses subnet mask '255.255.255.0' instead of wildcard mask '0.0.0.255'.",
        "osi_layer": "Layer 3",
        "concept_tag": "ACL",
        "severity": "Medium",
        "recommended_fix_steps": "Router-1(config)# ip access-list extended 110\nRouter-1(config-ext-nacl)# no 10\nRouter-1(config-ext-nacl)# 10 deny ip 192.168.20.0 0.0.0.255 host 10.0.0.5",
        "verification_command": "Router-1# show ip access-lists 110"
    },

    # --- NAT / PAT (29-32) ---
    {
        "case_id": "NET-029",
        "title": "Missing IP NAT Inside/Outside Interface Designation",
        "symptom": "Internal hosts (192.168.1.0/24) cannot connect to external web servers. 'show ip nat translations' is completely empty.",
        "topology_note": "Edge Router with LAN on G0/0 and ISP on G0/1.",
        "show_outputs": """Edge-Router# show running-config | section nat\nip nat inside source list 1 interface GigabitEthernet0/1 overload\naccess-list 1 permit 192.168.1.0 0.0.0.255\n\nEdge-Router# show running-config interface GigabitEthernet0/0\ninterface GigabitEthernet0/0\n ip address 192.168.1.1 255.255.255.0\n\nEdge-Router# show running-config interface GigabitEthernet0/1\ninterface GigabitEthernet0/1\n ip address 203.0.113.2 255.255.255.252\n ip nat outside\n\nEdge-Router# show ip nat translations\n(Empty)""",
        "expected_fault": "Interface GigabitEthernet0/0 is missing 'ip nat inside' configuration.",
        "osi_layer": "Layer 3",
        "concept_tag": "NAT",
        "severity": "High",
        "recommended_fix_steps": "Edge-Router(config)# interface GigabitEthernet0/0\nEdge-Router(config-if)# ip nat inside",
        "verification_command": "Edge-Router# show running-config interface GigabitEthernet0/0 | include ip nat"
    },
    {
        "case_id": "NET-030",
        "title": "NAT Overload ACL Subnet Mismatch",
        "symptom": "LAN hosts in subnet 192.168.2.0/24 cannot browse the Internet through Edge Router. NAT translation table remains empty.",
        "topology_note": "LAN upgraded to 192.168.2.0/24. Edge Router NAT config still references old subnet.",
        "show_outputs": """Edge-Router# show ip nat translations\n(Empty)\n\nEdge-Router# show running-config | section nat\nip nat inside source list 5 interface GigabitEthernet0/1 overload\n\nEdge-Router# show ip access-lists 5\nStandard IP access list 5\n    10 permit 192.168.1.0 0.0.0.255 (0 matches)\n\nEdge-Router# show ip interface brief\nInterface              IP-Address      OK? Method Status                Protocol\nGigabitEthernet0/0     192.168.2.1     YES manual up                    up      \nGigabitEthernet0/1     198.51.100.2    YES manual up                    up      """,
        "expected_fault": "NAT ACL 5 permits old subnet 192.168.1.0/24 instead of the active LAN subnet 192.168.2.0/24.",
        "osi_layer": "Layer 3",
        "concept_tag": "NAT",
        "severity": "High",
        "recommended_fix_steps": "Edge-Router(config)# access-list 5 permit 192.168.2.0 0.0.0.255\nEdge-Router(config)# no access-list 5 permit 192.168.1.0 0.0.0.255",
        "verification_command": "Edge-Router# show ip access-lists 5"
    },
    {
        "case_id": "NET-031",
        "title": "Static NAT Local IP Mapping Error",
        "symptom": "External clients cannot reach internal Web Server via public IP 203.0.113.10. Internal server has IP 192.168.1.10.",
        "topology_note": "Static NAT mapping configured for DMZ Web Server.",
        "show_outputs": """Router-GW# show running-config | include ip nat inside source static\nip nat inside source static 192.168.1.100 203.0.113.10\n\nRouter-GW# show ip interface brief\nInterface              IP-Address      OK? Method Status                Protocol\nGig0/0 (LAN)           192.168.1.1     YES manual up                    up      \nGig0/1 (WAN)           203.0.113.1     YES manual up                    up      \n\nWeb-Server> ipconfig\nIP Address: 192.168.1.10\nDefault Gateway: 192.168.1.1""",
        "expected_fault": "Static NAT rule maps public IP 203.0.113.10 to 192.168.1.100 instead of the real server address 192.168.1.10.",
        "osi_layer": "Layer 3",
        "concept_tag": "NAT",
        "severity": "High",
        "recommended_fix_steps": "Router-GW(config)# no ip nat inside source static 192.168.1.100 203.0.113.10\nRouter-GW(config)# ip nat inside source static 192.168.1.10 203.0.113.10",
        "verification_command": "Router-GW# show ip nat translations"
    },
    {
        "case_id": "NET-032",
        "title": "NAT Pool Exhaustion Missing Overload Keyword",
        "symptom": "First 2 users can access the web, but subsequent users fail with connection timeout. NAT pool contains only 2 public IP addresses.",
        "topology_note": "NAT pool 'PUBLIC_POOL' with range 203.0.113.10 to 203.0.113.11 for 50 internal hosts.",
        "show_outputs": """Router-1# show ip nat statistics\nTotal active translations: 2 (0 static, 2 dynamic; 0 extended)\nOutside interfaces: GigabitEthernet0/1\nInside interfaces: GigabitEthernet0/0\nHits: 120  Misses: 45\nPool : PUBLIC_POOL\n  start 203.0.113.10 end 203.0.113.11\n  type generic, total addresses 2, allocated 2 (100%)\n\nRouter-1# show running-config | include ip nat inside source\nip nat inside source list 1 pool PUBLIC_POOL""",
        "expected_fault": "NAT pool configuration is missing the 'overload' (PAT) keyword, causing 1-to-1 dynamic NAT to consume all pool IPs after 2 connections.",
        "osi_layer": "Layer 3",
        "concept_tag": "NAT",
        "severity": "High",
        "recommended_fix_steps": "Router-1(config)# no ip nat inside source list 1 pool PUBLIC_POOL\nRouter-1(config)# ip nat inside source list 1 pool PUBLIC_POOL overload",
        "verification_command": "Router-1# show ip nat statistics"
    },

    # --- WIRELESS (33-35) ---
    {
        "case_id": "NET-033",
        "title": "Guest Wi-Fi VLAN Isolation Security Breach",
        "symptom": "Guest Wi-Fi users connected to SSID 'Company-Guest' can ping internal accounting servers (10.10.10.50). Guest traffic should be isolated in VLAN 90.",
        "topology_note": "Wireless LAN Controller (WLC) / AP mapped WLAN 'Company-Guest' to VLAN 1 (Corporate Management) instead of VLAN 90 (Guest).",
        "show_outputs": """WLC-1# show wlan summary\nNumber of WLANs.................................. 2\nWLAN ID  WLAN Profile Name / SSID      Status    Interface Name (VLAN ID)\n1        Corp-Secure / Corp-Net        Enabled   management (1)\n2        Guest-Access / Company-Guest  Enabled   management (1)\n\nSwitch-1# show interfaces trunk\nPort        Mode             Encapsulation  Status        Native vlan\nGig0/1      on               802.1q         trunking      1\nGig0/1 allowed: 1,10,20,90""",
        "expected_fault": "WLAN profile 'Guest-Access' is mapped to 'management' interface (VLAN 1) instead of the isolated 'guest' interface (VLAN 90).",
        "osi_layer": "Layer 2",
        "concept_tag": "Wireless",
        "severity": "Critical",
        "recommended_fix_steps": "WLC-1(config)# wlan 2\nWLC-1(config-wlan)# interface-name guest-vlan90\nWLC-1(config-wlan)# end",
        "verification_command": "WLC-1# show wlan summary"
    },
    {
        "case_id": "NET-034",
        "title": "Wireless Client WPA2 Pre-Shared Key / Auth Mismatch",
        "symptom": "Laptop-1 cannot associate with Access Point 'AP-Warehouse'. Wireless connection status stays in 'Authenticating...' then disconnects.",
        "topology_note": "AP configured with WPA2-PSK (AES) and SSID 'Warehouse-Ops'.",
        "show_outputs": """AP-Warehouse# show dot11 ssid Warehouse-Ops\nSSID: Warehouse-Ops\n  VLAN: 10\n  Authentication: WPA2 Pre-shared Key\n  Key Management: WPAv2\n  Encryption: CCMP (AES)\n\nLaptop-1 Wireless Config Profile:\nSSID: Warehouse-Ops\nSecurity: WPA-PSK (TKIP)\nPre-Shared Key: [Mismatch / TKIP chosen instead of AES]""",
        "expected_fault": "Laptop-1 encryption and security profile is configured for WPA-TKIP instead of WPA2-AES / PSK as enforced by AP-Warehouse.",
        "osi_layer": "Layer 2",
        "concept_tag": "Wireless",
        "severity": "Medium",
        "recommended_fix_steps": "On Laptop-1 Wireless Properties: Select WPA2-Personal, AES Encryption, and enter correct Pre-Shared Key.",
        "verification_command": "AP-Warehouse# show dot11 associations"
    },
    {
        "case_id": "NET-035",
        "title": "Access Point Switchport Configured as Access Instead of Trunk",
        "symptom": "Lightweight / Multi-SSID AP boots, but users on secondary SSID (VLAN 30) get no IP address and cannot pass traffic. Only native SSID works.",
        "topology_note": "AP-1 connected to Switch-1 Fa0/12. AP broadcasts Corporate (VLAN 10) and Guest (VLAN 30).",
        "show_outputs": """Switch-1# show interfaces FastEthernet0/12 switchport\nName: Fa0/12\nSwitchport: Enabled\nAdministrative Mode: static access\nOperational Mode: static access\nAccess Mode VLAN: 10 (Corporate)\nTrunking Native Mode VLAN: 1 (default)\n\nSwitch-1# show interfaces trunk\nPort        Mode             Encapsulation  Status        Native vlan\nGig0/1      on               802.1q         trunking      1\n(Fa0/12 is not listed in trunk ports)""",
        "expected_fault": "Switchport Fa0/12 connecting to multi-VLAN Access Point is configured in access mode (VLAN 10), dropping tagged frames for VLAN 30.",
        "osi_layer": "Layer 2",
        "concept_tag": "Wireless",
        "severity": "High",
        "recommended_fix_steps": "Switch-1(config)# interface FastEthernet0/12\nSwitch-1(config-if)# switchport mode trunk\nSwitch-1(config-if)# switchport trunk native vlan 10",
        "verification_command": "Switch-1# show interfaces trunk | include Fa0/12"
    },

    # --- PHYSICAL / INTERFACE (36-37) ---
    {
        "case_id": "NET-036",
        "title": "Core Router Interface Administratively Shutdown",
        "symptom": "Complete branch network outage. Router-Core cannot communicate with Branch-1 across serial link.",
        "topology_note": "Router-Core Serial0/0/0 connected to Branch-1 Serial0/0/0.",
        "show_outputs": """Router-Core# show ip interface brief\nInterface              IP-Address      OK? Method Status                Protocol\nGigabitEthernet0/0     192.168.1.1     YES manual up                    up      \nSerial0/0/0            10.1.1.1        YES manual administratively down down    \nSerial0/0/1            unassigned      YES unset  administratively down down    \n\nBranch-1# show ip interface brief Serial0/0/0\nInterface              IP-Address      OK? Method Status                Protocol\nSerial0/0/0            10.1.1.2        YES manual down                  down    """,
        "expected_fault": "Interface Serial0/0/0 on Router-Core is administratively down (shutdown).",
        "osi_layer": "Layer 1",
        "concept_tag": "Physical/Interface",
        "severity": "Critical",
        "recommended_fix_steps": "Router-Core(config)# interface Serial0/0/0\nRouter-Core(config-if)# no shutdown",
        "verification_command": "Router-Core# show ip interface brief Serial0/0/0"
    },
    {
        "case_id": "NET-037",
        "title": "Duplicate IP Address Assigned to Static Host and Server",
        "symptom": "HR Server and PC-Finance experience intermittent network disconnection and packet loss. Switch logs MAC flapping.",
        "topology_note": "Both devices connected to Switch-1 in VLAN 10.",
        "show_outputs": """Switch-1# show logging\n%SW_MATM-4-MACFLAP_NOTIF: Host 0001.9654.1102 in vlan 10 is flapping between port Fa0/2 and port Fa0/10\n\nHR-Server> ipconfig\nIP Address: 192.168.10.50\nSubnet Mask: 255.255.255.0\n\nPC-Finance> ipconfig\nIP Address: 192.168.10.50\nSubnet Mask: 255.255.255.0""",
        "expected_fault": "Duplicate IP address 192.168.10.50 statically assigned to both HR-Server and PC-Finance in the same broadcast domain.",
        "osi_layer": "Layer 3",
        "concept_tag": "Gateway",
        "severity": "High",
        "recommended_fix_steps": "On PC-Finance: Reassign IP address to an unused IP address (e.g., 192.168.10.51) or configure DHCP.",
        "verification_command": "Switch-1# show mac address-table dynamic"
    }
]