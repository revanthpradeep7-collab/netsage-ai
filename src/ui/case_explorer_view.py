import streamlit as st
import pandas as pd
import json

def render_case_explorer_view(case_mgr):
    st.markdown("## 📚 Packet Tracer Lab Case Explorer")
    st.markdown("Browse, filter, and inspect the 37 troubleshooting cases across VLAN, Gateway, DHCP, DNS, Routing, ACL, NAT, and Wireless.")
    
    cases = case_mgr.cases
    
    # Filter controls
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        concepts = ["All"] + sorted(list(set(c["concept_tag"] for c in cases)))
        sel_concept = st.selectbox("Filter by Concept:", concepts)
    with f_col2:
        layers = ["All"] + sorted(list(set(c["osi_layer"] for c in cases)))
        sel_layer = st.selectbox("Filter by OSI Layer:", layers)
    with f_col3:
        severities = ["All", "Critical", "High", "Medium", "Low"]
        sel_sev = st.selectbox("Filter by Severity:", severities)
    with f_col4:
        search = st.text_input("🔍 Search keyword:", placeholder="e.g. OSPF, trunk, 192.168...")

    filtered_cases = case_mgr.filter_cases(concept=sel_concept, layer=sel_layer, severity=sel_sev, search_term=search)
    st.caption(f"Showing {len(filtered_cases)} of {len(cases)} cases")
    
    # Download buttons
    col_d1, col_d2, _ = st.columns([1, 1, 2])
    with col_d1:
        csv_data = pd.DataFrame(filtered_cases).to_csv(index=False)
        st.download_button("📥 Export to CSV", data=csv_data, file_name="netsage_cases.csv", mime="text/csv")
    with col_d2:
        json_data = json.dumps(filtered_cases, indent=2)
        st.download_button("📥 Export to JSON", data=json_data, file_name="netsage_cases.json", mime="application/json")

    st.divider()

    # Detailed Cards
    for c in filtered_cases:
        with st.expander(f"📌 [{c['case_id']}] {c['title']} ({c['concept_tag']} | {c['osi_layer']} | {c['severity']})", expanded=False):
            st.markdown(f"**🚨 Symptom:** {c['symptom']}")
            st.markdown(f"**🗺️ Topology:** `{c['topology_note']}`")
            st.markdown(f"**🎯 Expected Root Cause:** {c['expected_fault']}")
            
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                st.markdown("**📄 Cisco IOS Show Command Outputs:**")
                st.code(c['show_outputs'], language="text")
            with c_s2:
                st.markdown("**🛠️ Recommended Fix Commands:**")
                st.code(c['recommended_fix_steps'], language="cisco")
                st.markdown("**🧪 Verification Command:**")
                st.code(c.get('verification_command', 'ping'), language="cisco")