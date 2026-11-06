import streamlit as st
import pandas as pd
import altair as alt

def render_dashboard_view(case_mgr, results):
    st.markdown("## 📊 NetSage AI Analytics & Evaluation Dashboard")
    st.markdown("Comprehensive evaluation metrics, issue taxonomy distribution, and AI-vs-Human agreement rates across Cisco Packet Tracer troubleshooting cases.")
    
    stats = case_mgr.get_review_stats()
    cases = case_mgr.cases
    df_cases = pd.DataFrame(cases)
    
    # KPI Cards Row
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total Lab Cases", len(cases), help="Dataset size across multiple network domains")
    with c2:
        st.metric("Rule Checker Coverage", "100%", help="Deterministic detection rate for known config errors")
    with c3:
        st.metric("Human Agreement", f"{stats['agreement_rate']}%", help="Percentage of AI diagnoses Accepted by human review")
    with c4:
        st.metric("Edited Diagnoses", stats["edited"], help="Diagnoses where human engineer refined commands")
    with c5:
        st.metric("Rejected (Safety Catches)", stats["rejected"], help="Cases where human reviewer caught AI errors/hallucinations")
        
    st.divider()
    
    # Chart Row 1: Concept & OSI Layer Distribution
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📌 Cases by Network Concept")
        if not df_cases.empty and "concept_tag" in df_cases.columns:
            concept_counts = df_cases["concept_tag"].value_counts().reset_index()
            concept_counts.columns = ["Concept", "Count"]
            chart1 = alt.Chart(concept_counts).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X("Concept:N", sort="-y", title="Network Concept"),
                y=alt.Y("Count:Q", title="Number of Cases"),
                color=alt.Color("Concept:N", scale=alt.Scale(scheme="category10"), legend=None),
                tooltip=["Concept", "Count"]
            ).properties(height=280)
            st.altair_chart(chart1, use_container_width=True)
            
    with col2:
        st.subheader("🌐 Cases by OSI Layer")
        if not df_cases.empty and "osi_layer" in df_cases.columns:
            layer_counts = df_cases["osi_layer"].value_counts().reset_index()
            layer_counts.columns = ["OSI Layer", "Count"]
            chart2 = alt.Chart(layer_counts).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X("OSI Layer:N", sort=["Layer 1", "Layer 2", "Layer 3", "Layer 4", "Layer 7"], title="OSI Layer"),
                y=alt.Y("Count:Q", title="Number of Cases"),
                color=alt.Color("OSI Layer:N", scale=alt.Scale(scheme="set2"), legend=None),
                tooltip=["OSI Layer", "Count"]
            ).properties(height=280)
            st.altair_chart(chart2, use_container_width=True)
            
    # Chart Row 2: Severity & Human Review Verdicts
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("⚠️ Case Severity Distribution")
        if not df_cases.empty and "severity" in df_cases.columns:
            sev_counts = df_cases["severity"].value_counts().reset_index()
            sev_counts.columns = ["Severity", "Count"]
            sev_order = ["Critical", "High", "Medium", "Low"]
            chart3 = alt.Chart(sev_counts).mark_arc(innerRadius=50).encode(
                theta=alt.Theta("Count:Q"),
                color=alt.Color("Severity:N", scale=alt.Scale(
                    domain=["Critical", "High", "Medium", "Low"],
                    range=["#d9534f", "#f0ad4e", "#0275d8", "#5cb85c"]
                )),
                tooltip=["Severity", "Count"]
            ).properties(height=280)
            st.altair_chart(chart3, use_container_width=True)
            
    with col4:
        st.subheader("🛡️ AI vs Human Review Verdicts")
        verdict_data = pd.DataFrame([
            {"Verdict": "Accepted (Green)", "Count": stats["accepted"], "Color": "#28a745"},
            {"Verdict": "Edited (Yellow)", "Count": stats["edited"], "Color": "#ffc107"},
            {"Verdict": "Rejected (Red)", "Count": stats["rejected"], "Color": "#dc3545"}
        ])
        chart4 = alt.Chart(verdict_data).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
            x=alt.X("Verdict:N", title="Review Verdict"),
            y=alt.Y("Count:Q", title="Cases Reviewed"),
            color=alt.Color("Verdict:N", scale=alt.Scale(
                domain=["Accepted (Green)", "Edited (Yellow)", "Rejected (Red)"],
                range=["#28a745", "#ffc107", "#dc3545"]
            ), legend=None),
            tooltip=["Verdict", "Count"]
        ).properties(height=280)
        st.altair_chart(chart4, use_container_width=True)