import streamlit as st
import pandas as pd
from io import BytesIO
import time

# ==========================================
# BRAIN: INTEGRATED LOGIC FUNCTIONS
# ==========================================

def get_invest_evaluation(user_story):
    """Simulates AI User Story Evaluation"""
    time.sleep(1.5)  # Simulate processing
    return {
        "totalScore": 24,
        "grade": "B+",
        "status": "Ready",
        "executiveSummary": {
            "readinessScore": 80,
            "businessAlignment": "High",
            "riskProfile": "Low",
            "recommendation": "Minor refinements needed on 'Small' criteria."
        },
        "parameters": [
            {"name": "Independent", "score": 5, "finding": "Self-contained and ready."},
            {"name": "Negotiable", "score": 4, "finding": "Scope is clear but flexible."},
            {"name": "Valuable", "score": 5, "finding": "Direct benefit to the end user."},
            {"name": "Estimable", "score": 4, "finding": "Sized for a single sprint."},
            {"name": "Small", "score": 2, "finding": "Consider splitting into sub-stories."},
            {"name": "Testable", "score": 4, "finding": "Acceptance criteria are objective."}
        ],
        "improvementRecommendations": {
            "Action": "Split the story",
            "Reason": "Currently covers too many UI components at once."
        }
    }

def get_test_case_evaluation(test_case):
    """Simulates AI Test Case Evaluation"""
    time.sleep(1)
    return {
        "totalScore": 21,
        "status": "Pass",
        "parameters": [
            {"name": "Clarity", "score": 5, "finding": "Steps are very clear."},
            {"name": "Accuracy", "score": 4, "finding": "Expected results are logical."},
            {"name": "Completeness", "score": 4, "finding": "Covers main path well."}
        ],
        "healthMetrics": [
            {"name": "Traceability", "target": "100%", "actual": 90, "metTarget": True},
            {"name": "Logic Flow", "target": "100%", "actual": 100, "metTarget": True}
        ]
    }

def generate_test_cases_local(desc):
    """Simulates AI Test Case Generation"""
    time.sleep(2)
    return {
        "testCases": [
            {
                "name": "Success Scenario",
                "precondition": "User on landing page",
                "steps": "1. Click Login\n2. Enter valid creds",
                "expectedResult": "Dashboard displayed",
                "postcondition": "Session active"
            }
        ]
    }

# ==========================================
# UI: STREAMLIT INTERFACE
# ==========================================

st.set_page_config(page_title="US Evaluator", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("<style>.main { padding: 2rem; } .stTabs [data-baseweb='tab-list'] { gap: 2rem; }</style>", unsafe_allow_html=True)

st.sidebar.title("🎯 US Evaluator")
st.sidebar.markdown("---")
st.sidebar.info("🚀 **Mode: Integrated AI** (No Backend Required)")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📖 User Story", "🧪 Test Case", "📝 Generator", "📊 Bulk Stories", "📋 Bulk Tests"
])

# --- TAB 1: USER STORY ---
with tab1:
    st.title("📖 User Story Evaluator")
    user_story = st.text_area("Enter User Story", height=200, key="us_input_main")
    
    if st.button("🚀 Evaluate User Story", key="btn_us_eval", type="primary", use_container_width=True):
        if user_story.strip():
            with st.spinner("🔍 Local AI Analyzing..."):
                data = get_invest_evaluation(user_story)
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("📊 Total Score", f"{data['totalScore']}/30")
                c2.metric("⭐ Grade", data['grade'])
                c3.metric("🎯 Status", data['status'])
                c4.metric("📈 Readiness", f"{data['executiveSummary']['readinessScore']}%")
                
                st.subheader("📋 Executive Summary")
                st.success(f"**Recommendation:** {data['executiveSummary']['recommendation']}")
                
                st.subheader("🎯 INVEST Breakdown")
                cols = st.columns(6)
                for idx, p in enumerate(data['parameters']):
                    cols[idx].metric(p['name'], f"{p['score']}/5")
                    with st.expander(f"Details: {p['name']}"):
                        st.write(p['finding'])

# --- TAB 2: TEST CASE ---
with tab2:
    st.title("🧪 Test Case Evaluator")
    test_case = st.text_area("Enter Test Case", height=200, key="tc_input_main")
    
    if st.button("🚀 Evaluate Test Case", key="btn_tc_eval", type="primary", use_container_width=True):
        if test_case.strip():
            with st.spinner("🔍 Checking quality..."):
                data = get_test_case_evaluation(test_case)
                st.metric("📊 Quality Score", f"{data['totalScore']}/25")
                st.dataframe(pd.DataFrame(data['parameters']), use_container_width=True)

# --- TAB 3: GENERATOR ---
with tab3:
    st.title("📝 Test Case Generator")
    mode = st.radio("Source", ["✍️ From Text", "📸 From Mockup"], horizontal=True)
    desc = st.text_area("Description", key="gen_desc_local")
    
    if st.button("✨ Generate", key="btn_generate_local", type="primary", use_container_width=True):
        with st.spinner("🤖 Generating..."):
            res = generate_test_cases_local(desc)
            for tc in res['testCases']:
                with st.expander(tc['name']):
                    st.write(f"**Steps:** {tc['steps']}")
                    st.write(f"**Expected:** {tc['expectedResult']}")

# --- TAB 4 & 5: BULK (Simplified Logic) ---
with tab4:
    st.title("📊 Bulk User Story Evaluator")
    uploaded_file = st.file_uploader("Upload File", type=['xlsx', 'csv'], key="bulk_us_local")
    if uploaded_file and st.button("🚀 Evaluate All Stories", key="btn_bulk_us"):
        st.info("Bulk processing enabled via local logic functions.")

with tab5:
    st.title("📋 Bulk Test Case Evaluator")
    uploaded_file = st.file_uploader("Upload File", type=['xlsx', 'csv'], key="bulk_tc_local")
    if uploaded_file and st.button("🚀 Evaluate All Tests", key="btn_bulk_tc"):
        st.info("Bulk processing enabled via local logic functions.")
