CASES_P3 = [
    # --- ROUTING CONTINUED (19-24) ---
    {
        "case_id": "NET-019",
        "title": "OSPF Inverted Wildcard Mask in Network Statement",
        "symptom": "Router-HQ does not advertise subnet 192.168.100.0/24 into OSPF. Downstream routers cannot reach HQ server LAN.",
        "topology_note": "HQ LAN is 192.168.100.0/24 on G0/1. OSPF Process 10 running.",
        "show_outputs": """Router-HQ# show running-config | section router ospf\nrouter ospf 10\n router-id 10.10.10.10\n network 192.168.100.0 255.255.255.0 area 0\n\nRouter-HQ# show ip ospf interface brief\nInterface    PID   Area            IP Address/Mask    Cost  State Nbrs F/C\nGi0/0        10    0               10.1.1.1/30        1     P2P   1/1\n(Gi0/1 is missing from OSPF enabled interfaces)""",
        "expected_fault": "OSPF network command used subnet mask 255.255.255.0 instead of wildcard mask 0.0.0.255, failing to match interface Gi0/1.",
        "osi_layer": "Layer 3",
        "concept_tag": "Routing",
        "severity": "High",
        "recommended_fix_steps": "Router-HQ(config)# router ospf 10\nRouter-HQ(config-router)# no network 192.168.100.0 255.255.255.0 area 0\nRouter-HQ(config-router)# network 192.168.100.0 0.0.0.255 area 0",
        "verification_command": "Router-HQ# show ip ospf interface brief"
    },
    {
        "case_id": "NET-020",
        "title": "OSPF Hello and Dead Timer Mismatch",
        "symptom": "OSPF neighbor state between R1 and R2 stays in DOWN or cycles continuously with %OSPF-5-ADJCHG warnings.",
        "topology_note": "R1 and R2 connected on WAN link 10.10.10.0/30.",
        "show_outputs": """R1# show ip ospf interface Serial0/0/0\nSerial0/0/0 is up, line protocol is up\n  Internet Address 10.10.10.1/30, Area 0\n  Timer intervals configured, Hello 10, Dead 40, Wait 40, Retransmit 5\n\nR2# show ip ospf interface Serial0/0/0\nSerial0/0/0 is up, line protocol is up\n  Internet Address 10.10.10.2/30, Area 0\n  Timer intervals configured, Hello 5, Dead 20, Wait 20, Retransmit 5""",
        "expected_fault": "OSPF Hello/Dead timer mismatch: R1 is using 10/40 seconds while R2 is using 5/20 seconds.",
        "osi_layer": "Layer 3",
        "concept_tag": "Routing",
        "severity": "Medium",
        "recommended_fix_steps": "R2(config)# interface Serial0/0/0\nR2(config-if)# ip ospf hello-interval 10\nR2(config-if)# ip ospf dead-interval 40",
        "verification_command": "R1# show ip ospf neighbor"
    },
    {
        "case_id": "NET-021",
        "title": "OSPF Passive-Interface Misconfigured on Routing Link",
        "symptom": "Branch router R-BR1 fails to form OSPF adjacency with Core router R-CORE across link G0/0.",
        "topology_note": "R-BR1 G0/0 connects to R-CORE G0/0. R-BR1 G0/1 connects to User LAN.",
        "show_outputs": """R-BR1# show running-config | section router ospf\nrouter ospf 1\n passive-interface GigabitEthernet0/0\n network 10.0.0.0 0.0.0.3 area 0\n network 192.168.10.0 0.0.0.255 area 0\n\nR-BR1# show ip ospf neighbor\n(Empty)""",
        "expected_fault": "Interface GigabitEthernet0/0 (the transit link to R-CORE) is configured as passive-interface, suppressing OSPF Hellos.",
        "osi_layer": "Layer 3",
        "concept_tag": "Routing",
        "severity": "High",
        "recommended_fix_steps": "R-BR1(config)# router ospf 1\nR-BR1(config-router)# no passive-interface GigabitEthernet0/0\nR-BR1(config-router)# passive-interface GigabitEthernet0/1",
        "verification_command": "R-BR1# show ip ospf neighbor"
    },
    {
        "case_id": "NET-022",
        "title": "Asymmetric Routing / Missing Return Static Route",
        "symptom": "Site-A PC (192.168.10.5) sends packets to Site-B Server (10.20.30.100), but never gets a reply. Router-A show ip route has route to 10.20.30.0/24.",
        "topology_note": "Site-A (192.168.10.0/24) <-> Router-A <-> WAN <-> Router-B <-> Site-B (10.20.30.0/24). Static routing used.",
        "show_outputs": """Router-A# show ip route 10.20.30.0\nRouting entry for 10.20.30.0/24\n  Known via "static", distance 1, metric 0\n  * 172.16.1.2\n\nRouter-B# show ip route\nGateway of last resort is not set\n      10.0.0.0/8 is variably subnetted, 2 subnets, 2 masks\nC        10.20.30.0/24 is directly connected, GigabitEthernet0/0\n      172.16.0.0/16 is variably subnetted, 2 subnets, 2 masks\nC        172.16.1.0/30 is directly connected, Serial0/0/0\n(No route to 192.168.10.0/24 in Router-B table)""",
        "expected_fault": "Router-B lacks a return route for Site-A subnet 192.168.10.0/24, causing reply packets to be dropped at Router-B.",
        "osi_layer": "Layer 3",
        "concept_tag": "Routing",
        "severity": "High",
        "recommended_fix_steps": "Router-B(config)# ip route 192.168.10.0 255.255.255.0 172.16.1.1",
        "verification_command": "Router-B# show ip route 192.168.10.0"
    },
    {
        "case_id": "NET-023",
        "title": "RIPv2 Auto-Summary Discontiguous Subnet Drop",
        "symptom": "Routers running RIPv2 experience erratic routing to 172.16.1.0/24 and 172.16.2.0/24 separated by a 192.168.1.0/24 link.",
        "topology_note": "R1 (172.16.1.0/24) <-> R2 (192.168.1.0/24) <-> R3 (172.16.2.0/24). Discontiguous classful boundary.",
        "show_outputs": """R1# show ip protocols\nRouting Protocol is "rip"\n  Sending updates every 30 seconds\n  Automatic network summarization is in effect\n  Routing for Networks:\n    172.16.0.0\n    192.168.1.0\n\nR2# show ip route rip\nR    172.16.0.0/16 [120/1] via 192.168.1.1, FastEthernet0/0\n                   [120/1] via 192.168.1.6, FastEthernet0/1""",
        "expected_fault": "RIPv2 automatic summarization is enabled, summarizing discontiguous /24 subnets into a single 172.16.0.0/16 classful route.",
        "osi_layer": "Layer 3",
        "concept_tag": "Routing",
        "severity": "Medium",
        "recommended_fix_steps": "R1(config)# router rip\nR1(config-router)# no auto-summary\n\nR2(config)# router rip\nR2(config-router)# no auto-summary\n\nR3(config)# router rip\nR3(config-router)# no auto-summary",
        "verification_command": "R2# show ip route rip"
    },
    {
        "case_id": "NET-024",
        "title": "EIGRP Autonomous System (AS) Number Mismatch",
        "symptom": "R1 and R2 fail to form EIGRP adjacency. 'show ip eigrp neighbors' is empty on both routers.",
        "topology_note": "R1 (G0/0: 10.1.1.1/30) and R2 (G0/0: 10.1.1.2/30).",
        "show_outputs": """R1# show running-config | section router eigrp\nrouter eigrp 100\n network 10.1.1.0 0.0.0.3\n no auto-summary\n\nR2# show running-config | section router eigrp\nrouter eigrp 200\n network 10.1.1.0 0.0.0.3\n no auto-summary""",
        "expected_fault": "EIGRP AS number mismatch: R1 is running EIGRP AS 100 while R2 is running EIGRP AS 200.",
        "osi_layer": "Layer 3",
        "concept_tag": "Routing",
        "severity": "High",
        "recommended_fix_steps": "R2(config)# no router eigrp 200\nR2(config)# router eigrp 100\nR2(config-router)# network 10.1.1.0 0.0.0.3\nR2(config-router)# no auto-summary",
        "verification_command": "R1# show ip eigrp neighbors"
    },

    # --- ACCESS CONTROL LISTS (25-27) ---
    {
        "case_id": "NET-025",
        "title": "Standard ACL Applied in Wrong Direction",
        "symptom": "Admin applied an ACL to block Host-B (192.168.1.50) from accessing Server (10.0.0.10), but now ALL hosts in LAN cannot access ANY external network.",
        "topology_note": "Router-1 G0/0 (LAN 192.168.1.0/24), G0/1 (WAN 10.0.0.1/24).",
        "show_outputs": """Router-1# show ip access-lists\nStandard IP access list 10\n    10 deny 192.168.1.50 (20 matches)\n    20 permit any (145 matches)\n\nRouter-1# show running-config interface GigabitEthernet0/1\ninterface GigabitEthernet0/1\n ip address 10.0.0.1 255.255.255.0\n ip access-group 10 in""",
        "expected_fault": "Standard ACL 10 filters source IP 192.168.1.50 but was applied inbound ('in') on G0/1 (WAN interface), where incoming packets have source IPs in 10.0.0.0/24 or public ranges.",
        "osi_layer": "Layer 3",
        "concept_tag": "ACL",
        "severity": "Medium",
        "recommended_fix_steps": "Router-1(config)# interface GigabitEthernet0/1\nRouter-1(config-if)# no ip access-group 10 in\nRouter-1(config-if)# ip access-group 10 out",
        "verification_command": "Router-1# show running-config interface GigabitEthernet0/1"
    },
    {
        "case_id": "NET-026",
        "title": "Extended ACL Implicit Deny Blocking Legitimate Web Traffic",
        "symptom": "Sales PC (192.168.10.15) cannot browse the intranet web server at 10.1.1.80 on HTTP port 80. Ping to server is blocked.",
        "topology_note": "Router-1 G0/0 has inbound ACL 101.",
        "show_outputs": """Router-1# show ip access-lists 101\nExtended IP access list 101\n    10 permit tcp 192.168.10.0 0.0.0.255 host 10.1.1.80 eq 443\n    20 permit udp any any eq domain\n    (implicit deny ip any any active - 84 matches)\n\nRouter-1# show running-config interface GigabitEthernet0/0\ninterface GigabitEthernet0/0\n ip address 192.168.10.1 255.255.255.0\n ip access-group 101 in""",
        "expected_fault": "ACL 101 permits HTTPS (port 443) but lacks a permit statement for HTTP (port 80), hitting the implicit deny.",
        "osi_layer": "Layer 4",
        "concept_tag": "ACL",
        "severity": "Medium",
        "recommended_fix_steps": "Router-1(config)# ip access-list extended 101\nRouter-1(config-ext-nacl)# 15 permit tcp 192.168.10.0 0.0.0.255 host 10.1.1.80 eq www",
        "verification_command": "Router-1# show ip access-lists 101"
    },
    {
        "case_id": "NET-027",
        "title": "ACL Rule Order Shadowing Specific Permit",
        "symptom": "Network Manager PC (192.168.10.5) is unable to access the Finance Database (10.50.1.10), even though a permit rule was written for it.",
        "topology_note": "Core Router G0/0 inbound ACL 'FILTER_FINANCE'.",
        "show_outputs": """Core-Router# show access-lists FILTER_FINANCE\nExtended IP access list FILTER_FINANCE\n    10 deny ip 192.168.10.0 0.0.0.255 10.50.1.0 0.0.0.255 (152 matches)\n    20 permit ip host 192.168.10.5 host 10.50.1.10 (0 matches)\n    30 permit ip any any (530 matches)""",
        "expected_fault": "Broad deny rule (line 10) shadows and precedes specific permit rule (line 20), denying Host 192.168.10.5 before line 20 is ever evaluated.",
        "osi_layer": "Layer 4",
        "concept_tag": "ACL",
        "severity": "Medium",
        "recommended_fix_steps": "Core-Router(config)# ip access-list extended FILTER_FINANCE\nCore-Router(config-ext-nacl)# no 10\nCore-Router(config-ext-nacl)# no 20\nCore-Router(config-ext-nacl)# 10 permit ip host 192.168.10.5 host 10.50.1.10\nCore-Router(config-ext-nacl)# 20 deny ip 192.168.10.0 0.0.0.255 10.50.1.0 0.0.0.255",
        "verification_command": "Core-Router# show access-lists FILTER_FINANCE"
    }
]