import streamlit as st
import json
from datetime import datetime
from src.rule_checker import NetworkRuleChecker
from src.ai_engine import DiagnosticEngine

def render_troubleshooter_view(case_mgr, results_dict):
    st.markdown("## 🔍 Interactive Live Troubleshooter & Human Review Console")
    st.markdown("Diagnose broken Cisco Packet Tracer labs, verify with deterministic rule checks, inspect AI evidence, and enforce mandatory human sign-off before applying fixes.")
    
    rule_checker = NetworkRuleChecker()
    ai_engine = DiagnosticEngine()
    
    # Selection Mode
    mode = st.radio("Select Input Mode:", ["📁 Choose Pre-loaded Packet Tracer Lab Case", "✍️ Custom Lab Case Input"], horizontal=True)
    
    if mode == "📁 Choose Pre-loaded Packet Tracer Lab Case":
        case_options = [f"{c['case_id']} - {c['title']} ({c['concept_tag']} | {c['severity']})" for c in case_mgr.cases]
        selected_option = st.selectbox("Select Troubleshooting Case:", case_options, index=0)
        selected_cid = selected_option.split(" - ")[0]
        case_data = case_mgr.get_case_by_id(selected_cid) or {}
        
        case_title = case_data.get("title", f"Scenario {selected_cid}")
        symptom = case_data.get("symptom", "")
        topology = case_data.get("topology_note", "")
        show_outputs = case_data.get("show_outputs", "")
        expected_fault = case_data.get("expected_fault", "")
        osi_layer = case_data.get("osi_layer", "Layer 3")
        severity = case_data.get("severity", "Medium")
        concept = case_data.get("concept_tag", "General")
    else:
        # Each custom submission needs its own unique case_id, or every
        # custom review would overwrite the same row in review_log.csv /
        # the audit log instead of adding a new entry. Generate one ID per
        # "session" of custom input (stored in session_state so it stays
        # stable across Streamlit reruns while you're still editing the
        # same submission) rather than a hardcoded constant.
        if "custom_case_id" not in st.session_state:
            st.session_state["custom_case_id"] = f"CUSTOM-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        selected_cid = st.session_state["custom_case_id"]

        col_new, col_id = st.columns([1, 3])
        with col_new:
            if st.button("🆕 Start a New Custom Case", use_container_width=True):
                st.session_state["custom_case_id"] = f"CUSTOM-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                st.rerun()
        with col_id:
            st.caption(f"This submission's unique Case ID: `{selected_cid}` — click **Start a New Custom Case** before your next scenario so it gets its own audit log entry instead of overwriting this one.")

        st.subheader("Enter Custom Broken Lab Details:")
        case_title = st.text_input("Case Title / Scenario Name:", value="Custom Switchport Security Lab")
        symptom = st.text_area("Symptom Description:", value="Finance PC connected to Switch-1 Fa0/10 has lost network connectivity. Port LED is solid amber and host cannot ping gateway.")
        topology = st.text_input("Topology Notes:", value="Finance PC (192.168.10.25/24) -> Switch-1 Fa0/10 (VLAN 10) -> Router-1 G0/0.10 (Gateway: 192.168.10.1)")
        show_outputs = st.text_area("Cisco IOS Show Commands Output:", value="""Switch-1# show interfaces FastEthernet0/10 status
Port      Name               Status       Vlan       Duplex  Speed Type
Fa0/10                       err-disabled 10           auto   auto 10/100BaseTX

Switch-1# show port-security interface FastEthernet0/10
Port Security              : Enabled
Port Status                : Secure-shutdown
Violation Mode             : Shutdown
Maximum MAC Addresses      : 1
Total MAC Addresses        : 1
Configured MAC Addresses   : 1
Sticky MAC Addresses       : 0
Last Source Address:Vlan   : 0001.9642.BC55:10
Security Violation Count   : 1

Switch-1# show logging
%PM-4-ERR_DISABLE: psecure-violation error detected on Fa0/10, putting Fa0/10 in err-disable state
%PORT_SECURITY-2-PSECURE_VIOLATION: Security violation occurred, caused by MAC 0001.9642.BC55 on port FastEthernet0/10.""", height=180)
        expected_fault = "Port-security violation caused port to enter err-disabled state"
        osi_layer = "Layer 2"
        severity = "High"
        concept = "Port-Security"
        case_data = {
            "case_id": selected_cid,
            "title": case_title,
            "symptom": symptom,
            "topology_note": topology,
            "show_outputs": show_outputs,
            "expected_fault": expected_fault,
            "osi_layer": osi_layer,
            "severity": severity,
            "concept_tag": concept,
            "recommended_fix_steps": "Switch-1(config)# interface FastEthernet0/10\nSwitch-1(config-if)# shutdown\nSwitch-1(config-if)# switchport port-security mac-address sticky\nSwitch-1(config-if)# no shutdown",
            "verification_command": "Switch-1# show interfaces FastEthernet0/10 status"
        }

    st.divider()

    # Step 1: Lab Context & Raw Show Output
    st.subheader(f"1️⃣ Scenario Context: {selected_cid}")
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.markdown(f"**📌 Title:** `{case_title}`")
        st.markdown(f"**🚨 Symptom:** {symptom}")
        st.markdown(f"**🗺️ Topology:** `{topology}`")
        st.markdown(f"**🏷️ Concept Tag:** `{concept}` | **Layer:** `{osi_layer}` | **Severity:** `{severity}`")
    with col_b:
        with st.expander("📄 View Raw Show Command Output", expanded=True):
            st.code(show_outputs, language="text")

    st.divider()

    # Step 2: Deterministic Rule Checker
    st.subheader("2️⃣ Deterministic Rule Checker (Pre-AI Safety Gate)")
    rule_findings = rule_checker.analyze(symptom, topology, show_outputs)
    
    if rule_findings:
        st.success(f"✅ Rule Checker detected {len(rule_findings)} deterministic configuration fact(s):")
        for f in rule_findings:
            with st.container():
                st.markdown(f"**[{f['rule_id']}] {f['name']}** ({f['osi_layer']} | Severity: `{f['severity']}`)")
                st.markdown(f"- **Evidence:** `{f['evidence']}`")
                st.markdown(f"- **Explanation:** {f['explanation']}")
                st.markdown(f"- **Deterministic Recommendation:**\n```cisco\n{f['suggested_fix']}\n```")
    else:
        st.info("ℹ️ No simple syntax rule violations found. Proceeding to deep semantic AI reasoning.")

    st.divider()

    # Step 3: AI Diagnosis Engine
    st.subheader("3️⃣ NetSage AI Diagnosis & Root Cause Analysis")
    
    is_sim_error = selected_cid in ["NET-022", "NET-005", "NET-033", "NET-015", "NET-028", "NET-001"]
    
    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        run_ai = st.button("🚀 Run AI Diagnosis", type="primary", use_container_width=True)
    with col_btn2:
        simulate_error = st.checkbox("Simulate Unfiltered AI Error Mode (for Responsible AI testing)", value=is_sim_error)

    diag_key = f"diag_{selected_cid}"
    
    if run_ai:
        with st.spinner("Analyzing Packet Tracer topology and show outputs..."):
            diagnosis = ai_engine.diagnose(selected_cid, symptom, topology, show_outputs, simulate_ai_error=simulate_error)
            st.session_state[diag_key] = diagnosis
            st.session_state[f"ran_{selected_cid}"] = True

    if diag_key in st.session_state and st.session_state.get(f"ran_{selected_cid}", False):
        diagnosis = st.session_state[diag_key]
        
        # Display AI Result Card
        conf_color = "#28a745" if diagnosis["confidence"] == "High" else "#ffc107" if diagnosis["confidence"] == "Medium" else "#dc3545"
        
        st.markdown(f"""
        <div style="border-left: 5px solid {conf_color}; background-color: #f8f9fa; padding: 15px; border-radius: 4px; margin-bottom: 15px;">
            <h4 style="margin: 0; color: #212529;">🧠 AI Diagnosed Root Cause</h4>
            <p style="font-size: 1.1em; margin-top: 5px; color: #333;">{diagnosis['root_cause']}</p>
            <span style="background-color: #e9ecef; padding: 3px 8px; border-radius: 3px; font-weight: bold; color: #333;">OSI Layer: {diagnosis['osi_layer']}</span>
            <span style="background-color: #e9ecef; padding: 3px 8px; border-radius: 3px; font-weight: bold; margin-left: 10px; color: #333;">Confidence: {diagnosis['confidence']} ({int(diagnosis['confidence_score']*100)}%)</span>
            <span style="background-color: #e9ecef; padding: 3px 8px; border-radius: 3px; font-weight: bold; margin-left: 10px; color: #333;">Safety Risk: {diagnosis['safety_risk']}</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**🔎 Cited Evidence from Show Commands:**")
        for ev in diagnosis["evidence"]:
            st.markdown(f"- 📌 `{ev}`")
            
        st.markdown("**💡 AI Reasoning Rationale:**")
        st.info(diagnosis["rationale"])
        
        col_cmd1, col_cmd2 = st.columns(2)
        with col_cmd1:
            st.markdown("**🔬 Next Investigative / Verification Command:**")
            st.code(diagnosis["next_command"], language="cisco")
        with col_cmd2:
            st.markdown("**🛠️ Proposed Remediation Commands:**")
            st.code("\n".join(diagnosis["fix_steps"]), language="cisco")

        st.divider()

        # Step 4: Mandatory Human-in-the-Loop Review Console
        st.subheader("4️⃣ Mandatory Human-in-the-Loop Review & Approval Gate")
        st.markdown("As required by Cisco safety standards, an engineer must review, edit, or reject the AI diagnosis before any configuration change is applied.")

        existing_review = case_mgr.reviews.get(selected_cid)
        default_verdict = existing_review["verdict"] if existing_review else "Accepted"
        
        review_col1, review_col2 = st.columns([1, 1])
        with review_col1:
            verdict = st.radio("Engineer Review Decision:", ["Accepted", "Edited", "Rejected"], index=["Accepted", "Edited", "Rejected"].index(default_verdict), horizontal=True)
            reviewer_name = st.text_input("Reviewer Name / Role:", value=existing_review["reviewer"] if existing_review else "Senior TAC Engineer")
            review_notes = st.text_area("Engineer Review Notes / Correction Reason:", value=existing_review["comments"] if existing_review else "Diagnosis verified against topology. Fix commands verified.")

        default_fix_content = "\n".join(diagnosis["fix_steps"]) if diagnosis else ""
        if case_data and case_data.get("recommended_fix_steps"):
            default_fix_content = case_data.get("recommended_fix_steps")

        with review_col2:
            if verdict in ["Edited", "Rejected"]:
                curr_cause = existing_review.get("edited_root_cause") if (existing_review and existing_review.get("edited_root_cause")) else expected_fault
                curr_fix = existing_review.get("edited_fix") if (existing_review and existing_review.get("edited_fix")) else default_fix_content
                
                edited_cause = st.text_area("Human Corrected Root Cause:", value=curr_cause)
                edited_fix = st.text_area("Human Approved Cisco IOS Fix Commands:", value=curr_fix)
            else:
                edited_cause = diagnosis["root_cause"]
                edited_fix = "\n".join(diagnosis["fix_steps"])
                st.success("✅ Diagnosis approved as accurate. Fix commands ready for deployment.")

        if st.button("💾 Submit & Record Human Review Sign-Off", type="primary"):
            record = case_mgr.submit_review(
                case_id=selected_cid,
                verdict=verdict,
                reviewer=reviewer_name,
                comments=review_notes,
                edited_root_cause=edited_cause,
                edited_fix=edited_fix,
                title=case_title,
                symptom=symptom,
                ai_output_cause=diagnosis["root_cause"],
                ai_proposed_fix="; ".join(diagnosis["fix_steps"]),
                failure_category="Human Override / Lab Correction" if verdict in ["Edited", "Rejected"] else "Approved"
            )
            st.success(f"🎉 Review successfully recorded for **{selected_cid}** with verdict: **{verdict}**! (Updated both review log & Responsible AI center)")
            st.balloons()

        st.divider()

        # Step 5: Verification & Remediation Simulator
        st.subheader("5️⃣ Remediation Deployment & End-to-End Verification")
        final_fix = edited_fix if (verdict in ["Edited", "Rejected"]) else "\n".join(diagnosis["fix_steps"])
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.markdown("**📋 Final Approved Cisco IOS Configuration Block:**")
            st.code(final_fix, language="cisco")
        with col_f2:
            st.markdown("**🧪 Post-Fix Verification Test:**")
            verify_cmd = case_data.get("verification_command", "ping 192.168.20.1") if case_data else "ping 192.168.20.1"
            st.code(f"{verify_cmd}\n\nSending 5, 100-byte ICMP Echos, timeout is 2 seconds:\n!!!!!\nSuccess rate is 100 percent (5/5) - ICMP Echo Replies Received!", language="text")
    else:
        st.info("👆 Click **'🚀 Run AI Diagnosis'** above to generate the AI root-cause analysis, evidence citation, and unlock the Human Review console.")