"""
NetSage AI - Command Line Interface (CLI)
Allows network engineers to run diagnoses and rule checks directly from terminal.
"""

import sys
import os
import argparse
import json

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from src.case_manager import CaseManager
from src.rule_checker import NetworkRuleChecker
from src.ai_engine import DiagnosticEngine

def main():
    parser = argparse.ArgumentParser(description="NetSage AI - Cisco Packet Tracer Troubleshooting Assistant")
    parser.add_argument("--case", type=str, help="Case ID to diagnose (e.g. NET-001)")
    parser.add_argument("--list", action="store_true", help="List all available cases")
    parser.add_argument("--rule-check", action="store_true", help="Run deterministic rule checker only")
    parser.add_argument("--diagnose-all", action="store_true", help="Run AI diagnosis on all cases")
    parser.add_argument("--simulate-error", action="store_true", help="Simulate AI error for responsible AI audit")

    args = parser.parse_args()
    case_mgr = CaseManager()
    rule_checker = NetworkRuleChecker()
    ai_engine = DiagnosticEngine()

    if args.list:
        print(f"\n{'ID':<10} | {'Concept':<12} | {'Layer':<8} | {'Severity':<9} | {'Title'}")
        print("-" * 75)
        for c in case_mgr.cases:
            print(f"{c['case_id']:<10} | {c['concept_tag']:<12} | {c['osi_layer']:<8} | {c['severity']:<9} | {c['title']}")
        print(f"\nTotal: {len(case_mgr.cases)} cases")
        return

    if args.diagnose_all:
        from src.diagnose_runner import run_evaluation
        run_evaluation()
        return

    if args.case:
        case = case_mgr.get_case_by_id(args.case.upper())
        if not case:
            print(f"Error: Case '{args.case}' not found.")
            sys.exit(1)

        print(f"\n=======================================================")
        print(f" NetSage AI Diagnostic Report: [{case['case_id']}]")
        print(f" Title: {case['title']}")
        print(f" Concept: {case['concept_tag']} | Layer: {case['osi_layer']} | Severity: {case['severity']}")
        print(f"=======================================================\n")
        print(f"[*] Symptom:\n{case['symptom']}\n")
        print(f"[*] Topology:\n{case['topology_note']}\n")

        # Rule checker
        findings = rule_checker.analyze(case["symptom"], case["topology_note"], case["show_outputs"])
        print(f"[#] Deterministic Rule Checker Findings ({len(findings)} detected):")
        for f in findings:
            print(f"  - [{f['rule_id']}] {f['name']} ({f['osi_layer']} | {f['severity']}): {f['evidence']}")

        if not args.rule_check:
            print(f"\n[AI] Diagnosis:")
            diag = ai_engine.diagnose(case["case_id"], case["symptom"], case["topology_note"], case["show_outputs"], simulate_ai_error=args.simulate_error)
            print(f"  - Root Cause: {diag['root_cause']}")
            print(f"  - OSI Layer:  {diag['osi_layer']}")
            print(f"  - Confidence: {diag['confidence']} ({int(diag['confidence_score']*100)}%)")
            print(f"  - Evidence Cited:")
            for ev in diag["evidence"]:
                print(f"      * {ev}")
            print(f"  - Next Command: {diag['next_command']}")
            print(f"\n[Fix] Proposed Fix Commands:")
            for cmd in diag["fix_steps"]:
                print(f"    {cmd}")
            print(f"\n[Verify] Verification Commands:")
            for v in diag["verification_steps"]:
                print(f"    {v}")
            print(f"\n[Review] Human Review Mandatory: {diag['human_review_required']}")
        return

    parser.print_help()

if __name__ == "__main__":
    main()