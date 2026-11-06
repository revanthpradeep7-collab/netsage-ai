import streamlit as st
import pandas as pd
import os

def render_responsible_ai_view(case_mgr):
    st.markdown("## 🛡️ Responsible AI Safety Center & Error Interception Log")
    st.markdown("In-depth analysis of cases where raw AI models generated hallucinations, destructive commands, or false attributions that were intercepted by the human review safety gate.")
    
    # Load responsible AI csv
    csv_path = os.path.join(case_mgr.data_dir, "responsible_ai_log.csv")
    if os.path.exists(csv_path):
        df_resp = pd.read_csv(csv_path)
    else:
        df_resp = pd.DataFrame()
        
    st.info(f"📋 **{len(df_resp)} AI Error Scenarios Documented & Audited** (Requirement: At least 5 cases)")

    # Key Principles Summary
    with st.expander("📖 Responsible AI Principles in Network Engineering", expanded=False):
        st.markdown("""
        1. **Zero Unsupervised Config Changes**: No AI output is ever pushed directly to network infrastructure without explicit human review.
        2. **Verifiable Grounding**: Every claim made by the assistant must quote verbatim lines from `show` outputs.
        3. **Deterministic Pre-Validation**: Python rule checkers parse configuration syntax to catch deterministic errors before or alongside AI inference.
        4. **Transparent Failure Taxonomy**: Mistakes are categorized into Hallucinations, Destructive Commands, Asymmetric Blindspots, and Layer Misattributions.
        """)

    # Interactive failure drilldown
    if not df_resp.empty:
        for idx, row in df_resp.iterrows():
            with st.container():
                st.markdown(f"### 🛑 [{row['case_id']}] {row['title']}")
                st.markdown(f"**Failure Category:** :red[**{row['failure_category']}**]")
                st.markdown(f"**Symptom:** {row['symptom']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### ❌ Flawed AI Output")
                    st.error(f"**Diagnosed Cause:**\n{row['ai_output_cause']}")
                    st.markdown("**AI Proposed Fix:**")
                    st.code(row['ai_proposed_fix'], language="cisco")
                    
                with col2:
                    st.markdown("#### ✅ Human Reviewer Correction")
                    st.success(f"**True Root Cause:**\n{row['human_correction']}")
                    st.markdown("**Corrected Safe Fix:**")
                    st.code(row['correct_fix'], language="cisco")
                    
                st.markdown(f"💡 **Responsible AI Safety Guardrail & Takeaway:**\n*{row['responsible_ai_lesson']}*")
                st.divider()

    # Full Review Audit Log
    st.subheader("📜 Complete Human Review Audit Log")
    reviews = case_mgr.reviews
    if reviews:
        df_rev = pd.DataFrame(list(reviews.values()))
        st.dataframe(df_rev, use_container_width=True)