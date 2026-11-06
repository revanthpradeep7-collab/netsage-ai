"""
NetSage AI - AI-Assisted Cisco Packet Tracer Troubleshooter with Human Review
Main Streamlit Application
"""

import streamlit as st
import os
import json
from src.case_manager import CaseManager
from src.ui.dashboard_view import render_dashboard_view
from src.ui.troubleshooter_view import render_troubleshooter_view
from src.ui.responsible_ai_view import render_responsible_ai_view
from src.ui.case_explorer_view import render_case_explorer_view
from src.ui.demo_view import render_demo_view

# Page Config
st.set_page_config(
    page_title="NetSage AI - Packet Tracer Troubleshooter",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e3d59;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4a4a4a;
        margin-bottom: 20px;
    }
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    case_mgr = CaseManager(base_dir=base_dir)
    
    # Load batch diagnosis results if available
    results_path = os.path.join(base_dir, "data", "diagnosis_results.json")
    results = []
    if os.path.exists(results_path):
        with open(results_path, "r", encoding="utf-8") as f:
            results = json.load(f)
            
    # Sidebar
    st.sidebar.image("https://img.icons8.com/color/96/network-switch.png", width=70)
    st.sidebar.markdown("## **NetSage AI**")
    st.sidebar.caption("AI Troubleshooting Helper with Human Review")
    st.sidebar.divider()
    
    nav = st.sidebar.radio(
        "Navigation",
        [
            "📊 Executive Dashboard",
            "🔍 Live Troubleshooter",
            "🛡️ Responsible AI Safety Log",
            "📚 Case Dataset Explorer",
            "🎬 Guided Broken Lab Demo"
        ]
    )
    
    st.sidebar.divider()
    stats = case_mgr.get_review_stats()
    st.sidebar.markdown(f"**Dataset:** {stats['total_cases']} Cases")
    st.sidebar.markdown(f"**Reviewed:** {stats['total_reviewed']} ({stats['agreement_rate']}% Accepted)")
    st.sidebar.markdown("**Safety Rule:** Human Review Mandatory")
    st.sidebar.caption("Google DeepMind Pair Programming")

    # Header
    st.markdown('<p class="main-header">🌐 NetSage AI</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Packet Tracer AI Troubleshooting Helper with Evidence Grounding & Mandatory Human Oversight</p>', unsafe_allow_html=True)

    # Route navigation
    if nav == "📊 Executive Dashboard":
        render_dashboard_view(case_mgr, results)
    elif nav == "🔍 Live Troubleshooter":
        render_troubleshooter_view(case_mgr, results)
    elif nav == "🛡️ Responsible AI Safety Log":
        render_responsible_ai_view(case_mgr)
    elif nav == "📚 Case Dataset Explorer":
        render_case_explorer_view(case_mgr)
    elif nav == "🎬 Guided Broken Lab Demo":
        render_demo_view(case_mgr)

if __name__ == "__main__":
    main()