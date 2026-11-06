CASES_P2 = [
    # --- DHCP (10-14) ---
    {
        "case_id": "NET-010",
        "title": "Missing IP Helper-Address for Remote DHCP Relay",
        "symptom": "PCs in VLAN 10 (192.168.10.0/24) receive APIPA 169.254.x.x addresses. Central DHCP Server is located in Server VLAN 50 (192.168.50.2).",
        "topology_note": "PC (VLAN 10) -> Switch -> Router-1 (G0/0.10) <---> Server Farm (G0/0.50, DHCP Server 192.168.50.2).",
        "show_outputs": """Router-1# show running-config interface GigabitEthernet0/0.10\ninterface GigabitEthernet0/0.10\n encapsulation dot1Q 10\n ip address 192.168.10.1 255.255.255.0\n\nRouter-1# ping 192.168.50.2\nType escape sequence to abort.\nSending 5, 100-byte ICMP Echos to 192.168.50.2, timeout is 2 seconds:\n!!!!!\nSuccess rate is 100 percent (5/5)""",
        "expected_fault": "Router-1 subinterface G0/0.10 is missing 'ip helper-address 192.168.50.2' to relay DHCP broadcast requests across subnets.",
        "osi_layer": "Layer 3",
        "concept_tag": "DHCP",
        "severity": "High",
        "recommended_fix_steps": "Router-1(config)# interface GigabitEthernet0/0.10\nRouter-1(config-subif)# ip helper-address 192.168.50.2",
        "verification_command": "Router-1# show running-config interface GigabitEthernet0/0.10 | include ip helper-address"
    },
    {
        "case_id": "NET-011",
        "title": "DHCP Scope Pool Range Exhaustion",
        "symptom": "Newly added workstations in Office Floor 2 fail to obtain an IP address and time out with DHCPDISCOVER failed.",
        "topology_note": "Router-1 provides DHCP pool 'FLOOR2' for 192.168.2.0/28 (only 14 usable host IPs). 14 devices are already online.",
        "show_outputs": """Router-1# show ip dhcp pool FLOOR2\nPool FLOOR2 :\n Utilization mark (high/low)    : 100 / 0\n Subnet size (total/usable)     : 16/14\n Total addresses                : 16\n Leased addresses               : 14\n Excluded addresses             : 2\n Pending event                  : none\n\nRouter-1# show ip dhcp binding\nIP address       Client-ID/Hardware address     Lease expiration        Type\n192.168.2.2      0001.6421.33A1                 Infinite                Automatic""",
        "expected_fault": "DHCP address pool FLOOR2 is completely exhausted (100% utilization) due to overly restrictive /28 subnet mask.",
        "osi_layer": "Layer 7",
        "concept_tag": "DHCP",
        "severity": "Medium",
        "recommended_fix_steps": "Router-1(config)# ip dhcp pool FLOOR2\nRouter-1(config-dhcp)# network 192.168.2.0 255.255.255.0",
        "verification_command": "Router-1# show ip dhcp pool FLOOR2"
    },
    {
        "case_id": "NET-012",
        "title": "Missing DHCP Excluded Addresses Causing Gateway IP Conflict",
        "symptom": "Users intermittently lose internet access. Router console throws %IP-4-DUP_ADDR: Duplicate address 192.168.1.1 on GigabitEthernet0/0.",
        "topology_note": "Router-1 G0/0 IP: 192.168.1.1/24. DHCP pool assigns 192.168.1.0/24.",
        "show_outputs": """Router-1# show running-config | section dhcp\nip dhcp pool LAN_POOL\n network 192.168.1.0 255.255.255.0\n default-router 192.168.1.1\n dns-server 8.8.8.8\n\nRouter-1# show ip dhcp binding\nIP address       Client-ID/Hardware address     Lease expiration        Type\n192.168.1.1      0050.7966.6801                 Infinite                Automatic\n192.168.1.2      0050.7966.6802                 Infinite                Automatic""",
        "expected_fault": "DHCP server leased the router's own IP address (192.168.1.1) to a host because no 'ip dhcp excluded-address' was configured.",
        "osi_layer": "Layer 3",
        "concept_tag": "DHCP",
        "severity": "Critical",
        "recommended_fix_steps": "Router-1(config)# ip dhcp excluded-address 192.168.1.1 192.168.1.10\nRouter-1# clear ip dhcp binding *",
        "verification_command": "Router-1# show running-config | include ip dhcp excluded-address"
    },
    {
        "case_id": "NET-013",
        "title": "DHCP Pool Incorrect Default Gateway (Option 3)",
        "symptom": "DHCP clients obtain IP address 192.168.1.50 and DNS successfully, but cannot ping beyond their local subnet. Default gateway in ipconfig is wrong.",
        "topology_note": "Router LAN IP is 192.168.1.1. DHCP pool config has typo in default-router.",
        "show_outputs": """Router-1# show running-config | section dhcp\nip dhcp pool OFFICE\n network 192.168.1.0 255.255.255.0\n default-router 192.168.1.100\n dns-server 8.8.8.8\n\nPC-1> ipconfig\nIP Address......................: 192.168.1.50\nDefault Gateway.................: 192.168.1.100""",
        "expected_fault": "DHCP pool default-router option is configured with 192.168.1.100 instead of active router interface 192.168.1.1.",
        "osi_layer": "Layer 7",
        "concept_tag": "DHCP",
        "severity": "High",
        "recommended_fix_steps": "Router-1(config)# ip dhcp pool OFFICE\nRouter-1(config-dhcp)# default-router 192.168.1.1",
        "verification_command": "Router-1# show running-config | section dhcp"
    },
    {
        "case_id": "NET-014",
        "title": "DHCP Snooping Untrusted Uplink Port",
        "symptom": "DHCP clients fail to receive IP addresses after enabling DHCP Snooping on Switch-1. DHCP Server is connected to G0/1.",
        "topology_note": "Switch-1 has DHCP Snooping enabled globally and on VLAN 10. Uplink port G0/1 goes to DHCP Server.",
        "show_outputs": """Switch-1# show ip dhcp snooping\nSwitch DHCP snooping is enabled\nDHCP snooping is configured on following VLANs:\n10\nInsertion of option 82 is enabled\nInterface                  Trusted    Rate limit (pps)\n-----------------------    -------    ----------------\nGigabitEthernet0/1         no         unlimited\nFastEthernet0/1            no         unlimited\n\nSwitch-1# show ip dhcp snooping statistics\nPackets Forwarded = 0\nPackets Dropped = 24""",
        "expected_fault": "Switch-1 interface Gig0/1 connecting to the legitimate DHCP server is untrusted in DHCP snooping, causing DHCP OFFERs to be dropped.",
        "osi_layer": "Layer 2",
        "concept_tag": "DHCP",
        "severity": "High",
        "recommended_fix_steps": "Switch-1(config)# interface GigabitEthernet0/1\nSwitch-1(config-if)# ip dhcp snooping trust",
        "verification_command": "Switch-1# show ip dhcp snooping | include GigabitEthernet0/1"
    },

    # --- DNS & APPLICATION (15-16) ---
    {
        "case_id": "NET-015",
        "title": "Client Wrong DNS Server Configuration",
        "symptom": "User can ping public web server by IP (93.184.216.34) but web browser displays 'Server Not Found' when browsing www.example.com.",
        "topology_note": "Host PC-1 connected to Router-1 with access to internal DNS Server at 192.168.1.2.",
        "show_outputs": """PC-1> ping 93.184.216.34\nPinging 93.184.216.34 with 32 bytes of data:\nReply from 93.184.216.34: bytes=32 time=18ms TTL=54\n\nPC-1> nslookup www.example.com\nDNS request timed out.\n    timeout was 2 seconds.\n*** Can't find address for server 192.168.1.200: Timed out\n\nPC-1> ipconfig /all\nDNS Servers.....................: 192.168.1.200""",
        "expected_fault": "Host PC-1 is statically configured with non-existent DNS server IP 192.168.1.200 instead of active DNS server 192.168.1.2.",
        "osi_layer": "Layer 7",
        "concept_tag": "DNS",
        "severity": "Medium",
        "recommended_fix_steps": "On PC-1: Change static DNS Server address to 192.168.1.2 (or configure DHCP to supply correct DNS).",
        "verification_command": "PC-1> nslookup www.example.com 192.168.1.2"
    },
    {
        "case_id": "NET-016",
        "title": "DNS Server Service Disabled / Record Missing",
        "symptom": "All clients query the internal DNS Server 10.0.0.53, but name resolution for intranet.corp fails with server failure (SERVFAIL).",
        "topology_note": "Packet Tracer Server acting as DNS Server on 10.0.0.53. Router routing is healthy.",
        "show_outputs": """DNS-Server# show ip interface brief\nInterface              IP-Address      OK? Method Status                Protocol\nFastEthernet0          10.0.0.53       YES manual up                    up      \n\nClient-1> nslookup intranet.corp\nServer: 10.0.0.53\nAddress: 10.0.0.53\n*** 10.0.0.53 can't find intranet.corp: Non-existent domain\n\nDNS-Server Configuration State:\nDNS Service: OFF\nResource Records: [Empty]""",
        "expected_fault": "DNS Server service is turned OFF in Server configuration, and missing A record for 'intranet.corp'.",
        "osi_layer": "Layer 7",
        "concept_tag": "DNS",
        "severity": "Medium",
        "recommended_fix_steps": "On DNS-Server GUI/CLI: Turn DNS Service ON, add A-record: Name 'intranet.corp' -> IP '10.0.0.100'.",
        "verification_command": "Client-1> nslookup intranet.corp"
    },

    # --- ROUTING (17-18) ---
    {
        "case_id": "NET-017",
        "title": "Missing Default Static Route on Edge Router",
        "symptom": "Branch office PCs can reach all internal Branch LAN subnets, but all outbound traffic to the ISP/Internet fails with 'Destination host unreachable'.",
        "topology_note": "Branch-Router G0/0 connected to LAN (192.168.5.0/24), G0/1 connected to ISP Router (203.0.113.1/30).",
        "show_outputs": """Branch-Router# show ip route\nGateway of last resort is not set\n\n      192.168.5.0/24 is variably subnetted, 2 subnets, 2 masks\nC        192.168.5.0/24 is directly connected, GigabitEthernet0/0\nL        192.168.5.1/32 is directly connected, GigabitEthernet0/0\n      203.0.113.0/30 is variably subnetted, 2 subnets, 2 masks\nC        203.0.113.0/30 is directly connected, GigabitEthernet0/1\nL        203.0.113.2/32 is directly connected, GigabitEthernet0/1\n\nBranch-Router# ping 8.8.8.8\n% Network not in table""",
        "expected_fault": "Branch-Router has no default static route ('Gateway of last resort is not set') pointing to next-hop ISP gateway 203.0.113.1.",
        "osi_layer": "Layer 3",
        "concept_tag": "Routing",
        "severity": "High",
        "recommended_fix_steps": "Branch-Router(config)# ip route 0.0.0.0 0.0.0.0 203.0.113.1",
        "verification_command": "Branch-Router# show ip route | include Gateway of last resort"
    },
    {
        "case_id": "NET-018",
        "title": "OSPF Area ID Mismatch on Point-to-Point Link",
        "symptom": "Router-1 and Router-2 are directly connected via GigabitEthernet0/0/0, but OSPF neighbor adjacency is never formed.",
        "topology_note": "Link subnet 10.0.12.0/30. Router-1 (ID 1.1.1.1), Router-2 (ID 2.2.2.2).",
        "show_outputs": """Router-1# show ip ospf neighbor\n(Empty output - no neighbors)\n\nRouter-1# show ip ospf interface GigabitEthernet0/0/0\nGigabitEthernet0/0/0 is up, line protocol is up\n  Internet Address 10.0.12.1/30, Area 0\n  Process ID 1, Router ID 1.1.1.1, Network Type BROADCAST, Cost: 1\n\nRouter-2# show ip ospf interface GigabitEthernet0/0/0\nGigabitEthernet0/0/0 is up, line protocol is up\n  Internet Address 10.0.12.2/30, Area 1\n  Process ID 1, Router ID 2.2.2.2, Network Type BROADCAST, Cost: 1""",
        "expected_fault": "OSPF Area ID mismatch: Router-1 interface is in Area 0 while Router-2 interface is in Area 1.",
        "osi_layer": "Layer 3",
        "concept_tag": "Routing",
        "severity": "High",
        "recommended_fix_steps": "Router-2(config)# router ospf 1\nRouter-2(config-router)# no network 10.0.12.0 0.0.0.3 area 1\nRouter-2(config-router)# network 10.0.12.0 0.0.0.3 area 0",
        "verification_command": "Router-1# show ip ospf neighbor"
    }
]