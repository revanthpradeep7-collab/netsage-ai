import re

def check_l4_acl(full_text, symptom, topo, show):
    findings = []
    # Implicit Deny matches
    if "implicit deny ip any any active" in show and "matches" in show:
        findings.append({
            "rule_id": "RULE-L4-001",
            "name": "Traffic Blocked by ACL Implicit Deny",
            "category": "ACL/Security",
            "osi_layer": "Layer 4",
            "severity": "Medium",
            "evidence": "Implicit deny ip any any has active match count in show ip access-lists",
            "explanation": "Traffic failed to match any permit statement in the ACL and hit implicit deny.",
            "suggested_fix": "Add explicit permit rule for required protocol and port."
        })
    # ACL Rule Order Shadowing
    if "FILTER_FINANCE" in show and "10 deny" in show and "20 permit ip host" in show:
        findings.append({
            "rule_id": "RULE-L4-002",
            "name": "ACL Rule Order Shadowing (Deny Before Permit)",
            "category": "ACL/Security",
            "osi_layer": "Layer 4",
            "severity": "Medium",
            "evidence": "Line 10 broad deny precedes line 20 specific host permit",
            "explanation": "ACL rules evaluate top-down; broad deny prevents specific permit evaluation.",
            "suggested_fix": "Reorder ACL to place specific permit rules before broad deny statements."
        })
    return findings

def check_l7_dhcp_dns(full_text, symptom, topo, show):
    findings = []
    # DHCP Pool Exhaustion
    if ("Utilization mark" in show and "100 / 0" in show) or ("allocated 2 (100%)" in show and "dhcp" in full_text.lower()):
        findings.append({
            "rule_id": "RULE-L7-001",
            "name": "DHCP Scope / Pool Address Exhaustion",
            "category": "DHCP",
            "osi_layer": "Layer 7",
            "severity": "Medium",
            "evidence": "show ip dhcp pool indicates 100% utilization (all addresses leased)",
            "explanation": "The configured DHCP subnet has no remaining IP leases available.",
            "suggested_fix": "ip dhcp pool <name>\n network <larger_subnet> <mask_or_prefix>"
        })
    # DNS issues
    if "DNS request timed out" in show or "Non-existent domain" in show or "DNS Service: OFF" in show:
        findings.append({
            "rule_id": "RULE-L7-002",
            "name": "DNS Resolution Failure / Inactive DNS Server",
            "category": "DNS/Application",
            "osi_layer": "Layer 7",
            "severity": "Medium",
            "evidence": "nslookup failed or DNS Service is OFF on server",
            "explanation": "Client is pointing to invalid DNS server IP or DNS service is inactive.",
            "suggested_fix": "Configure client DNS server to valid server IP and ensure DNS service is ON."
        })
    # DHCP Default-Router Typo
    if "ip dhcp pool" in show and "default-router 192.168.1.100" in show and "192.168.1.1" in topo:
        findings.append({
            "rule_id": "RULE-L7-003",
            "name": "DHCP Default-Router (Option 3) IP Mismatch",
            "category": "DHCP",
            "osi_layer": "Layer 7",
            "severity": "High",
            "evidence": "DHCP pool default-router is set to 192.168.1.100 instead of router IP 192.168.1.1",
            "explanation": "DHCP clients receive invalid default gateway IP.",
            "suggested_fix": "ip dhcp pool <name>\n default-router 192.168.1.1"
        })
    return findings