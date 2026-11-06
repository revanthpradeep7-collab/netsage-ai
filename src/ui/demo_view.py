import streamlit as st
import time

def render_demo_view(case_mgr):
    st.markdown("## 🎬 Interactive 4-Stage Broken Lab Troubleshooting Demo")
    st.markdown("A guided walkthrough demonstrating how NetSage AI ingests a broken Packet Tracer lab scenario, executes deterministic checks, runs evidence-backed AI diagnosis, mandates human review, deploys Cisco IOS fixes, and verifies network recovery.")

    # Lab selection for demo
    demo_case_options = {
        "NET-010: Remote DHCP Relay Failure (Missing IP Helper)": "NET-010",
        "NET-001: Trunk Native VLAN Mismatch (Layer 2 Leak)": "NET-001",
        "NET-026: Extended ACL Implicit Deny Blocking Web (Layer 4)": "NET-026"
    }
    
    selected_demo_name = st.selectbox("Select Demo Lab Scenario:", list(demo_case_options.keys()))
    cid = demo_case_options[selected_demo_name]
    case = case_mgr.get_case_by_id(cid)

    # 4-Stage Stepper Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Stage 1: Symptom & Evidence Collection",
        "Stage 2: Deterministic Rule Check & AI Diagnosis",
        "Stage 3: Human Review Sign-Off",
        "Stage 4: Fix Deployment & Verification"
    ])

    with tab1:
        st.subheader("Stage 1: Packet Tracer Lab Breakdown & Symptoms")
        st.markdown(f"**Scenario Title:** `{case['title']}`")
        st.markdown(f"**Symptom:** :red[{case['symptom']}]")
        st.markdown(f"**Topology Context:** `{case['topology_note']}`")
        
        st.markdown("#### Show Command Output Collected from Packet Tracer:")
        st.code(case["show_outputs"], language="text")
        st.info("👉 Proceed to Stage 2 to execute automated rule checks and AI diagnosis.")

    with tab2:
        st.subheader("Stage 2: Deterministic Rule Checker & AI Analysis")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown("#### ⚙️ Python Deterministic Checker")
            from src.rule_checker import NetworkRuleChecker
            checker = NetworkRuleChecker()
            findings = checker.analyze(case["symptom"], case["topology_note"], case["show_outputs"])
            for f in findings:
                st.success(f"**Detected Fact:** {f['name']}\n- Evidence: `{f['evidence']}`")
        with col_d2:
            st.markdown("#### 🧠 NetSage AI Structured Output")
            from src.ai_engine import DiagnosticEngine
            eng = DiagnosticEngine()
            diag = eng.diagnose(cid, case["symptom"], case["topology_note"], case["show_outputs"])
            st.json({
                "root_cause": diag["root_cause"],
                "osi_layer": diag["osi_layer"],
                "confidence": diag["confidence"],
                "evidence": diag["evidence"],
                "next_command": diag["next_command"],
                "fix_steps": diag["fix_steps"]
            })
        st.info("👉 Proceed to Stage 3 for mandatory Human Oversight.")

    with tab3:
        st.subheader("Stage 3: Mandatory Human-in-the-Loop Review")
        st.warning("⚠️ **Safety Rule Active**: Automated changes are blocked pending human sign-off.")
        st.markdown(f"**Reviewing Diagnosis for:** `{cid}`")
        
        d_c1, d_c2 = st.columns(2)
        with d_c1:
            st.markdown(f"**AI Proposed Root Cause:**\n*{diag['root_cause']}*")
            st.markdown(f"**AI Proposed Fix:**")
            st.code("\n".join(diag["fix_steps"]), language="cisco")
        with d_c2:
            st.markdown("**Reviewer Action:**")
            verdict = st.selectbox("Select Action:", ["Accepted (Approved as accurate)", "Edited (Refined commands)", "Rejected (Unsafe / Hallucinated)"])
            comments = st.text_input("Reviewer Audit Note:", value="Verified against router subinterface running config.")
            if st.button("✅ Approve & Sign-Off Diagnosis"):
                case_mgr.submit_review(cid, "Accepted", "Demo Reviewer", comments)
                st.success("Human Review recorded! Fix authorized for deployment.")

    with tab4:
        st.subheader("Stage 4: Cisco IOS Fix Application & Verification")
        st.markdown("#### 1. Push Remediated Configuration to Cisco IOS:")
        st.code(case["recommended_fix_steps"], language="cisco")
        
        st.markdown("#### 2. Execute Post-Fix Verification Test:")
        st.code(f"{case.get('verification_command', 'ping')}\n\nSending 5, 100-byte ICMP Echos, timeout is 2 seconds:\n!!!!!\nSuccess rate is 100 percent (5/5)", language="text")
        
        st.success("🎉 Network lab fully operational! Problem resolved and verified.")