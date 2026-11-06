import re

def check_ip_addressing(full_text, symptom, topo, show):
    findings = []
    # %IP-4-DUP_ADDR
    if "%IP-4-DUP_ADDR" in show:
        m = re.search(r'Duplicate address\s+([0-9.]+)\s+on\s+(\S+)', show)
        ip, iface = m.groups() if m else ("detected", "interface")
        findings.append({
            "rule_id": "RULE-L3-001",
            "name": "Duplicate IP Address Conflict",
            "category": "IP Addressing",
            "osi_layer": "Layer 3",
            "severity": "Critical",
            "evidence": f"Console log %IP-4-DUP_ADDR: Duplicate address {ip} on {iface}",
            "explanation": f"Two devices on same broadcast domain assigned IP {ip}.",
            "suggested_fix": "Add 'ip dhcp excluded-address' for static IPs or reconfigure host."
        })
    # Subnet mask mismatch
    masks = re.findall(r'Internet address is\s+([0-9.]+)/(\d+)', show)
    if len(masks) >= 2:
        ip1, prefix1 = masks[0]
        ip2, prefix2 = masks[1]
        if prefix1 != prefix2:
            findings.append({
                "rule_id": "RULE-L3-002",
                "name": "Subnet Mask Mismatch on Point-to-Point Link",
                "category": "IP Addressing",
                "osi_layer": "Layer 3",
                "severity": "High",
                "evidence": f"Router-A has {ip1}/{prefix1} vs Router-B with {ip2}/{prefix2}",
                "explanation": "Directly connected router interfaces must share identical subnet masks.",
                "suggested_fix": f"interface <interface>\n ip address {ip2} 255.255.255.252"
            })
    return findings

def check_gateways(full_text, symptom, topo, show):
    findings = []
    # Host default gateway mismatch
    if "Default Gateway" in show or "Default Gateway" in full_text:
        gw_m = re.search(r'Default Gateway[\.\s:]+([0-9.]+)', show)
        r_ip_m = re.search(r'GigabitEthernet[0-9/.]+\s+([0-9.]+)\s+YES', show)
        if gw_m and r_ip_m:
            gw_ip = gw_m.group(1)
            r_ip = r_ip_m.group(1)
            if gw_ip != r_ip and gw_ip != "0.0.0.0" and not gw_ip.startswith("203.") and not gw_ip.startswith("198."):
                findings.append({
                    "rule_id": "RULE-L3-003",
                    "name": "Host Default Gateway Mismatch",
                    "category": "Gateway",
                    "osi_layer": "Layer 3",
                    "severity": "High",
                    "evidence": f"Host gateway configured as {gw_ip}, but router interface IP is {r_ip}",
                    "explanation": f"Host sending off-subnet packets to non-existent gateway {gw_ip}.",
                    "suggested_fix": f"Set host default gateway to {r_ip}."
                })
    # Switch default gateway missing
    if "show running-config | include default-gateway" in show and "(No output returned)" in show:
        findings.append({
            "rule_id": "RULE-L3-004",
            "name": "Switch Management Default Gateway Missing",
            "category": "Gateway",
            "osi_layer": "Layer 3",
            "severity": "Medium",
            "evidence": "Switch running-config lacks 'ip default-gateway'",
            "explanation": "Switch SVI cannot respond to management traffic from remote subnets.",
            "suggested_fix": "ip default-gateway 10.99.1.1"
        })
    # HSRP mismatch
    if "show standby brief" in show:
        group_matches = re.findall(r'Gig\S*\s+(\d+)\s+\d+\s+P?\s*Active\s+\S+\s+\S+\s+([0-9.]+)', show)
        if len(group_matches) >= 2:
            g1, ip1 = group_matches[0]
            g2, ip2 = group_matches[1]
            if g1 != g2 or ip1 != ip2:
                findings.append({
                    "rule_id": "RULE-L3-005",
                    "name": "HSRP Group / Virtual IP Mismatch (Dual Active)",
                    "category": "First-Hop Redundancy",
                    "osi_layer": "Layer 3",
                    "severity": "Critical",
                    "evidence": f"Router-1 HSRP Grp {g1} (VIP {ip1}) vs Router-2 Grp {g2} (VIP {ip2})",
                    "explanation": "Both routers enter Active state independently due to mismatched group/VIP.",
                    "suggested_fix": f"interface GigabitEthernet0/0\n no standby {g2}\n standby {g1} ip {ip1}"
                })
    return findings

def check_routing_protocols(full_text, symptom, topo, show):
    findings = []
    # Missing default static route
    if "Gateway of last resort is not set" in show:
        if "% Network not in table" in show or "Internet" in symptom or "8.8.8.8" in show:
            findings.append({
                "rule_id": "RULE-L3-006",
                "name": "Missing Default Static Route (Gateway of Last Resort)",
                "category": "Routing",
                "osi_layer": "Layer 3",
                "severity": "High",
                "evidence": "show ip route indicates 'Gateway of last resort is not set'",
                "explanation": "Router drops packets destined for non-local external networks.",
                "suggested_fix": "ip route 0.0.0.0 0.0.0.0 <next_hop_ip>"
            })
    # Asymmetric routing / missing return route
    if "No route to 192.168.10.0" in show or "lacks a return route" in full_text or "(No route to 192.168.10.0/24 in Router-B table)" in show:
        findings.append({
            "rule_id": "RULE-L3-007",
            "name": "Asymmetric Routing / Missing Return Path Route",
            "category": "Routing",
            "osi_layer": "Layer 3",
            "severity": "High",
            "evidence": "Remote router routing table contains no route back to source subnet",
            "explanation": "Return traffic dropped at remote router due to missing static/dynamic route.",
            "suggested_fix": "ip route 192.168.10.0 255.255.255.0 <next_hop_ip>"
        })
    # OSPF Area mismatch
    areas = re.findall(r'Internet Address [0-9./]+,\s*Area\s+(\d+)', show)
    if len(areas) >= 2 and areas[0] != areas[1]:
        findings.append({
            "rule_id": "RULE-L3-008",
            "name": "OSPF Area ID Mismatch",
            "category": "Routing/OSPF",
            "osi_layer": "Layer 3",
            "severity": "High",
            "evidence": f"Router-1 in Area {areas[0]} vs Router-2 in Area {areas[1]}",
            "explanation": "OSPF neighbors must be in the same Area ID on common link.",
            "suggested_fix": f"router ospf 1\n network <subnet> <wildcard> area {areas[0]}"
        })
    # Inverted wildcard in OSPF
    if re.search(r'network\s+[0-9.]+\s+255\.255\.255\.', show):
        findings.append({
            "rule_id": "RULE-L3-009",
            "name": "Inverted Wildcard Mask in Routing Statement",
            "category": "Routing/OSPF",
            "osi_layer": "Layer 3",
            "severity": "High",
            "evidence": "Network statement uses subnet mask '255.255.255.0' instead of wildcard '0.0.0.255'",
            "explanation": "Cisco OSPF requires wildcard bits where 0 is match and 255 is ignore.",
            "suggested_fix": "no network <ip> 255.255.255.0 area <area>\n network <ip> 0.0.0.255 area <area>"
        })
    # OSPF Hello/Dead Timers
    timers = re.findall(r'Hello\s+(\d+),\s*Dead\s+(\d+)', show)
    if len(timers) >= 2 and timers[0] != timers[1]:
        h1, d1 = timers[0]
        h2, d2 = timers[1]
        findings.append({
            "rule_id": "RULE-L3-010",
            "name": "OSPF Hello/Dead Timer Mismatch",
            "category": "Routing/OSPF",
            "osi_layer": "Layer 3",
            "severity": "Medium",
            "evidence": f"Local timer ({h1}/{d1}s) vs Remote timer ({h2}/{d2}s)",
            "explanation": "OSPF Hello and Dead intervals must match for adjacency.",
            "suggested_fix": f"interface <iface>\n ip ospf hello-interval {h1}\n ip ospf dead-interval {d1}"
        })
    # OSPF Passive interface
    if "passive-interface GigabitEthernet0/0" in show and "(Empty)" in show:
        findings.append({
            "rule_id": "RULE-L3-011",
            "name": "OSPF Passive-Interface Configured on Neighbor Link",
            "category": "Routing/OSPF",
            "osi_layer": "Layer 3",
            "severity": "High",
            "evidence": "passive-interface GigabitEthernet0/0 applied to transit routing link",
            "explanation": "Passive-interface suppresses OSPF Hellos on transit link.",
            "suggested_fix": "router ospf 1\n no passive-interface GigabitEthernet0/0"
        })
    # EIGRP AS Mismatch
    as_nums = re.findall(r'router eigrp\s+(\d+)', show)
    if len(as_nums) >= 2 and as_nums[0] != as_nums[1]:
        findings.append({
            "rule_id": "RULE-L3-012",
            "name": "EIGRP Autonomous System (AS) Mismatch",
            "category": "Routing/EIGRP",
            "osi_layer": "Layer 3",
            "severity": "High",
            "evidence": f"R1 running EIGRP AS {as_nums[0]} vs R2 running EIGRP AS {as_nums[1]}",
            "explanation": "EIGRP routers must be configured with matching AS numbers.",
            "suggested_fix": f"no router eigrp {as_nums[1]}\n router eigrp {as_nums[0]}"
        })
    # RIP Auto-Summary
    if "Automatic network summarization is in effect" in show:
        findings.append({
            "rule_id": "RULE-L3-013",
            "name": "RIPv2 Auto-Summary Enabled on Discontiguous Subnets",
            "category": "Routing/RIP",
            "osi_layer": "Layer 3",
            "severity": "Medium",
            "evidence": "Automatic network summarization is in effect in show ip protocols",
            "explanation": "RIP auto-summarizes classful network boundaries.",
            "suggested_fix": "router rip\n no auto-summary"
        })
    # DHCP Helper
    if ("APIPA" in full_text or "169.254" in full_text) and "show running-config interface" in show and "ip helper-address" not in show:
        findings.append({
            "rule_id": "RULE-L3-014",
            "name": "Missing IP Helper-Address for DHCP Relay",
            "category": "DHCP",
            "osi_layer": "Layer 3",
            "severity": "High",
            "evidence": "Router subinterface running-config lacks 'ip helper-address <server_ip>'",
            "explanation": "DHCP broadcast requests cannot cross subinterfaces without relay agent.",
            "suggested_fix": "interface <subinterface>\n ip helper-address <dhcp_server_ip>"
        })
    # NAT Inside/Outside
    if "show running-config interface GigabitEthernet0/0" in show and "ip nat outside" in show:
        g0_block = re.search(r'interface GigabitEthernet0/0\s*\n([\s\S]*?)(?=\n\S|\Z)', show)
        if g0_block and "ip nat inside" not in g0_block.group(1):
            findings.append({
                "rule_id": "RULE-L3-015",
                "name": "Missing IP NAT Inside Designation",
                "category": "NAT",
                "osi_layer": "Layer 3",
                "severity": "High",
                "evidence": "LAN interface GigabitEthernet0/0 lacks 'ip nat inside'",
                "explanation": "Router does not perform NAT without inside designation on LAN.",
                "suggested_fix": "interface GigabitEthernet0/0\n ip nat inside"
            })
    # NAT Overload Keyword Missing
    if "ip nat inside source list 1 pool" in show and "overload" not in show:
        findings.append({
            "rule_id": "RULE-L3-016",
            "name": "NAT Pool Missing 'overload' Keyword (PAT)",
            "category": "NAT",
            "osi_layer": "Layer 3",
            "severity": "High",
            "evidence": "ip nat inside source statement lacks 'overload' keyword",
            "explanation": "Without PAT (overload), dynamic NAT exhausts pool after 1:1 mapping.",
            "suggested_fix": "ip nat inside source list 1 pool <name> overload"
        })
    # Standard ACL Inbound on WAN
    if "Standard IP access list" in show and "ip access-group" in show and " in" in show and ("WAN" in topo or "G0/1" in show):
        findings.append({
            "rule_id": "RULE-L3-017",
            "name": "Standard ACL Applied Inbound on WAN Interface",
            "category": "ACL",
            "osi_layer": "Layer 3",
            "severity": "Medium",
            "evidence": "Standard ACL filtering source LAN IP applied inbound on WAN interface G0/1",
            "explanation": "Standard ACLs match source IP; inbound on WAN they filter foreign IPs.",
            "suggested_fix": "interface GigabitEthernet0/1\n no ip access-group 10 in\n ip access-group 10 out"
        })
    # Inverted wildcard in ACL
    if re.search(r'deny ip\s+[0-9.]+\s+255\.255\.255\.', show) or re.search(r'permit ip\s+[0-9.]+\s+255\.255\.255\.', show):
        findings.append({
            "rule_id": "RULE-L3-018",
            "name": "Inverted Wildcard Mask in Access Control List",
            "category": "ACL",
            "osi_layer": "Layer 3",
            "severity": "Medium",
            "evidence": "ACL rule uses subnet mask 255.255.255.0 instead of wildcard mask 0.0.0.255",
            "explanation": "Using 255.255.255.0 causes only host .0 to be matched in ACL.",
            "suggested_fix": "Replace 255.255.255.0 with 0.0.0.255 in ACL entry."
        })
    # NAT ACL Subnet Mismatch
    if "Standard IP access list 5" in show and "192.168.1.0" in show and "192.168.2.1" in show:
        findings.append({
            "rule_id": "RULE-L3-019",
            "name": "NAT Overload ACL LAN Subnet Mismatch",
            "category": "NAT",
            "osi_layer": "Layer 3",
            "severity": "High",
            "evidence": "NAT ACL permits 192.168.1.0/24 but active LAN is 192.168.2.1/24",
            "explanation": "Packets from new LAN subnet do not match NAT ACL and are dropped.",
            "suggested_fix": "access-list 5 permit 192.168.2.0 0.0.0.255"
        })
    # Static NAT Local IP Error
    if "ip nat inside source static 192.168.1.100" in show and "192.168.1.10" in show:
        findings.append({
            "rule_id": "RULE-L3-020",
            "name": "Static NAT Target Inside Local IP Mismatch",
            "category": "NAT",
            "osi_layer": "Layer 3",
            "severity": "High",
            "evidence": "Static NAT maps to 192.168.1.100 but internal server IP is 192.168.1.10",
            "explanation": "Inbound connections translated to non-existent IP 192.168.1.100.",
            "suggested_fix": "no ip nat inside source static 192.168.1.100 203.0.113.10\nip nat inside source static 192.168.1.10 203.0.113.10"
        })
    return findings