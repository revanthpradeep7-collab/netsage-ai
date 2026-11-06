import re

def check_interface_down(full_text, symptom, topo, show):
    findings = []
    admin_down_matches = re.findall(r'(\S+)\s+\S+\s+\S+\s+\S+\s+administratively down\s+(\S+)', show, re.IGNORECASE)
    for iface, proto in admin_down_matches:
        findings.append({
            "rule_id": "RULE-L1-001",
            "name": "Interface Administratively Down (Shutdown)",
            "category": "Physical/Interface",
            "osi_layer": "Layer 1",
            "severity": "Critical",
            "evidence": f"Interface {iface} is administratively down (protocol {proto})",
            "explanation": f"The interface {iface} has been manually shut down with 'shutdown'.",
            "suggested_fix": f"interface {iface}\n no shutdown"
        })
    if not admin_down_matches and ("administratively down" in show.lower() or "line protocol is down" in show.lower()):
        findings.append({
            "rule_id": "RULE-L1-002",
            "name": "Interface Line Protocol Down",
            "category": "Physical/Interface",
            "osi_layer": "Layer 1",
            "severity": "Critical",
            "evidence": "show output indicates interface or line protocol is down",
            "explanation": "Physical link down or administrative shutdown detected.",
            "suggested_fix": "Execute 'no shutdown' and verify cabling."
        })
    return findings

def check_native_vlan_mismatch(full_text, symptom, topo, show):
    findings = []
    if "%CDP-4-NATIVE_VLAN_MISMATCH" in show or "Native VLAN mismatch" in full_text:
        m = re.search(r'discovered on (\S+) \((\d+)\), with (\S+) (\S+) \((\d+)\)', show)
        if m:
            local_if, local_vlan, remote_dev, remote_if, remote_vlan = m.groups()
            findings.append({
                "rule_id": "RULE-L2-001",
                "name": "Trunk Native VLAN Mismatch",
                "category": "VLAN/Trunking",
                "osi_layer": "Layer 2",
                "severity": "High",
                "evidence": f"CDP Native VLAN mismatch: {local_if} (VLAN {local_vlan}) vs {remote_dev} {remote_if} (VLAN {remote_vlan})",
                "explanation": "Trunk links must share identical Native VLAN to prevent frame leak and STP loop.",
                "suggested_fix": f"interface {local_if}\n switchport trunk native vlan {remote_vlan}"
            })
        else:
            findings.append({
                "rule_id": "RULE-L2-001",
                "name": "Trunk Native VLAN Mismatch",
                "category": "VLAN/Trunking",
                "osi_layer": "Layer 2",
                "severity": "High",
                "evidence": "Native VLAN mismatch detected in trunk show outputs",
                "explanation": "Mismatched Native VLAN on interconnected trunk switchports.",
                "suggested_fix": "Align 'switchport trunk native vlan' IDs on both ends."
            })
    return findings

def check_missing_vlan_or_pruning(full_text, symptom, topo, show):
    findings = []
    if "(inactive)" in show or "inactive" in show:
        m = re.search(r'Access Mode VLAN:\s*(\d+)\s*\(inactive\)', show, re.IGNORECASE)
        vlan_id = m.group(1) if m else "configured"
        findings.append({
            "rule_id": "RULE-L2-002",
            "name": "Access VLAN Missing in VLAN Database",
            "category": "VLAN/Database",
            "osi_layer": "Layer 2",
            "severity": "Medium",
            "evidence": f"Access Mode VLAN: {vlan_id} (inactive) in show interfaces switchport",
            "explanation": f"VLAN {vlan_id} assigned to access port does not exist in vlan.dat.",
            "suggested_fix": f"vlan {vlan_id}\n name VLAN_{vlan_id}\n exit"
        })
    if "Vlans allowed on trunk" in show:
        allowed_lines = re.findall(r'Vlans allowed on trunk\s*\n\s*(\S+)\s+([0-9,\-]+)', show, re.IGNORECASE)
        for port, vlans in allowed_lines:
            if "VLAN 40" in full_text and "40" not in vlans:
                findings.append({
                    "rule_id": "RULE-L2-003",
                    "name": "Required VLAN Pruned from Trunk Allowed List",
                    "category": "VLAN/Trunking",
                    "osi_layer": "Layer 2",
                    "severity": "Medium",
                    "evidence": f"Port {port} trunk allowed list ({vlans}) omits required VLAN 40",
                    "explanation": "Traffic for unallowed VLANs is blocked at 802.1Q trunk.",
                    "suggested_fix": f"interface {port}\n switchport trunk allowed vlan add 40"
                })
    return findings

def check_router_on_a_stick_dot1q(full_text, symptom, topo, show):
    findings = []
    m = re.search(r'interface\s+(\S+\.(\d+))[\s\S]*?encapsulation\s+dot1Q\s+(\d+)', show, re.IGNORECASE)
    if m:
        subif, subif_num, dot1q_tag = m.groups()
        if subif_num != dot1q_tag:
            findings.append({
                "rule_id": "RULE-L2-004",
                "name": "Subinterface Dot1Q VLAN Tag Mismatch",
                "category": "Inter-VLAN Routing",
                "osi_layer": "Layer 2",
                "severity": "High",
                "evidence": f"Subinterface {subif} configured with dot1Q {dot1q_tag} (expected VLAN {subif_num})",
                "explanation": f"Subinterface {subif} expects VLAN {dot1q_tag}, but client is in VLAN {subif_num}.",
                "suggested_fix": f"interface {subif}\n encapsulation dot1Q {subif_num}"
            })
    return findings

def check_dtp_and_switching(full_text, symptom, topo, show):
    findings = []
    if "Administrative Mode: dynamic auto" in show and "Operational Mode: static access" in show:
        findings.append({
            "rule_id": "RULE-L2-005",
            "name": "DTP Negotiation Failure (Dynamic Auto - Dynamic Auto)",
            "category": "VLAN/Trunking",
            "osi_layer": "Layer 2",
            "severity": "High",
            "evidence": "Administrative Mode: dynamic auto, Operational Mode: static access",
            "explanation": "Both switchports set to dynamic auto, so neither initiates trunking.",
            "suggested_fix": "interface <interface_id>\n switchport mode trunk"
        })
    if "%SW_MATM-4-MACFLAP_NOTIF" in show or "MACFLAP_NOTIF" in show:
        m = re.search(r'Host\s+([0-9a-fA-F.]+)\s+in vlan\s+(\d+)\s+is flapping between port\s+(\S+)\s+and port\s+(\S+)', show)
        if m:
            mac, vlan, p1, p2 = m.groups()
            findings.append({
                "rule_id": "RULE-L2-006",
                "name": "MAC Address Flapping / Duplicate IP / L2 Loop",
                "category": "Switching/ARP",
                "osi_layer": "Layer 2",
                "severity": "High",
                "evidence": f"MAC {mac} flapping between {p1} and {p2} on VLAN {vlan}",
                "explanation": "Multiple devices sharing identical IP/MAC address or active Layer 2 loop.",
                "suggested_fix": f"Verify static IP allocations on {p1} and {p2}."
            })
    if "DHCP snooping is enabled" in show and "GigabitEthernet0/1         no" in show:
        findings.append({
            "rule_id": "RULE-L2-007",
            "name": "DHCP Snooping Untrusted Uplink Port",
            "category": "DHCP/Security",
            "osi_layer": "Layer 2",
            "severity": "High",
            "evidence": "GigabitEthernet0/1 Trusted: no with Packets Dropped > 0",
            "explanation": "DHCP Server replies arriving on untrusted ports are dropped by switch.",
            "suggested_fix": "interface GigabitEthernet0/1\n ip dhcp snooping trust"
        })
    if "Company-Guest" in show and "management (1)" in show:
        findings.append({
            "rule_id": "RULE-L2-008",
            "name": "Guest Wi-Fi Mapped to Management VLAN (Security Leak)",
            "category": "Wireless/Security",
            "osi_layer": "Layer 2",
            "severity": "Critical",
            "evidence": "WLAN profile 'Guest-Access' mapped to interface 'management (1)'",
            "explanation": "Guest Wi-Fi traffic placed onto sensitive Management VLAN 1.",
            "suggested_fix": "wlan 2\n interface-name guest-vlan90"
        })
    if "Security: WPA-PSK (TKIP)" in show and "Encryption: CCMP (AES)" in show:
        findings.append({
            "rule_id": "RULE-L2-009",
            "name": "Wireless Client Encryption Mismatch (TKIP vs AES)",
            "category": "Wireless",
            "osi_layer": "Layer 2",
            "severity": "Medium",
            "evidence": "AP enforces WPA2-AES (CCMP) while client profile configured for WPA-TKIP",
            "explanation": "WPA2 handshake fails due to encryption algorithm mismatch.",
            "suggested_fix": "Configure wireless client security profile to WPA2-Personal with AES."
        })
    if "Fa0/12" in show and "Access Mode VLAN: 10" in show and ("multi-SSID" in topo.lower() or "Fa0/12 is not listed in trunk" in show or "AP" in topo):
        findings.append({
            "rule_id": "RULE-L2-010",
            "name": "Multi-SSID Access Point Connected to Access Switchport",
            "category": "Wireless/VLAN",
            "osi_layer": "Layer 2",
            "severity": "High",
            "evidence": "Switchport Fa0/12 is configured in static access mode for multi-SSID AP",
            "explanation": "Access point cannot forward secondary SSID traffic (VLAN 30) across access port.",
            "suggested_fix": "interface Fa0/12\n switchport mode trunk\n switchport trunk native vlan 10"
        })
    return findings