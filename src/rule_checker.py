"""
NetSage AI - Deterministic Network Configuration Rule Checker
Unified analyzer combining Layer 1-7 deterministic rules.
"""

from typing import List, Dict, Any
from src.rules.rules_l1_l2 import (
    check_interface_down,
    check_native_vlan_mismatch,
    check_missing_vlan_or_pruning,
    check_router_on_a_stick_dot1q,
    check_dtp_and_switching
)
from src.rules.rules_l3 import (
    check_ip_addressing,
    check_gateways,
    check_routing_protocols
)
from src.rules.rules_l4_l7 import (
    check_l4_acl,
    check_l7_dhcp_dns
)

class NetworkRuleChecker:
    def __init__(self):
        self.rules = [
            check_interface_down,
            check_native_vlan_mismatch,
            check_missing_vlan_or_pruning,
            check_router_on_a_stick_dot1q,
            check_dtp_and_switching,
            check_ip_addressing,
            check_gateways,
            check_routing_protocols,
            check_l4_acl,
            check_l7_dhcp_dns
        ]

    def analyze(self, symptom: str, topology_note: str, show_outputs: str) -> List[Dict[str, Any]]:
        findings = []
        combined_text = f"{symptom}\n{topology_note}\n{show_outputs}"
        
        for rule in self.rules:
            try:
                res = rule(combined_text, symptom, topology_note, show_outputs)
                if res:
                    if isinstance(res, list):
                        findings.extend(res)
                    else:
                        findings.append(res)
            except Exception:
                pass
                
        return findings

if __name__ == "__main__":
    from src.cases_data import CASES
    checker = NetworkRuleChecker()
    total_findings = 0
    covered_cases = 0
    print("Testing NetworkRuleChecker across all 37 cases...")
    for c in CASES:
        f = checker.analyze(c["symptom"], c["topology_note"], c["show_outputs"])
        total_findings += len(f)
        if len(f) > 0:
            covered_cases += 1
        print(f"[{c['case_id']}] {c['title'][:40]}... -> {len(f)} findings")
    print(f"\nRule Checker Result: {covered_cases}/{len(CASES)} cases detected with {total_findings} total findings!")