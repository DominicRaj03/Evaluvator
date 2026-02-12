import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
from io import BytesIO

# --- 1. Security & Styling Configuration ---
def check_password():
    """Returns True if the user had the correct password."""
    
    # Professional Styling for Login Page
    st.markdown("""
        <style>
        .login-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px;
            background-color: #1E1E2E;
            border-radius: 15px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            max-width: 400px;
            margin: auto;
        }
        .stTextInput > div > div > input {
            background-color: #2D2D44;
            color: white;
            border: 1px solid #3E3E5E;
        }
        </style>
    """, unsafe_allow_html=True)

    def password_entered():
        if st.session_state["password"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Centered Login UI
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.title("🎯 Jarvis AI")
            st.subheader("US & Test Evaluator")
            st.text_input("Access Key", type="password", on_change=password_entered, key="password")
            st.markdown('</div>', unsafe_allow_html=True)
        return False
    elif not st.session_state["password_correct"]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.title("🎯 Jarvis AI")
            st.text_input("Access Key", type="password", on_change=password_entered, key="password")
            st.error("❌ Access Denied")
            st.markdown('</div>', unsafe_allow_html=True)
        return False
    return True

# --- 2. Main Application Logic ---
st.set_page_config(page_title="Jarvis - US Evaluator", layout="wide")

if check_password():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
        else:
            st.error("Missing GEMINI_API_KEY in Streamlit Secrets!")
    except Exception as e:
        st.error(f"Initialization Error: {str(e)}")

    def call_gemini_ai(prompt):
        try:
            response = model.generate_content(prompt)
            raw_text = response.text.strip().replace('```json', '').replace('```', '')
            return json.loads(raw_text)
        except Exception:
            return None

    # --- UI Layout ---
    st.sidebar.title("🎯 US Evaluator")
    if st.sidebar.button("Log Out"):
        st.session_state["password_correct"] = False
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.info("🚀 **Mode: Integrated Gemini AI**")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📖 User Story", "🧪 Test Case", "📝 Generator", "📊 Bulk Stories", "📋 Bulk Tests"
    ])

    # ============= TAB 1: USER STORY =============
    with tab1:
        st.title("📖 User Story Evaluator")
        user_story = st.text_area("Enter User Story", key="us_input_main", height=150)
        if st.button("🚀 Evaluate", key="btn_us_eval", type="primary"):
            if user_story:
                with st.spinner("Analyzing..."):
                    prompt = f"Analyze this User Story based on INVEST criteria: '{user_story}'. Return ONLY JSON with: totalScore(30), grade, status, executiveSummary(dict with readinessScore, recommendation), parameters(list of dicts with name, score, finding)."
                    data = call_gemini_ai(prompt)
                    if data:
                        st.metric("Score", f"{data.get('totalScore')}/30")
                        st.success(data.get('executiveSummary', {}).get('recommendation'))
                        for p in data.get('parameters', []):
                            with st.expander(f"{p['name']} - {p['score']}/5"):
                                st.write(p['finding'])

    # ============= TAB 2: TEST CASE =============
    with tab2:
        st.title("🧪 Test Case Evaluator")
        tc_input = st.text_area("Enter Test Case", key="tc_input_main", height=150)
        if st.button("🚀 Evaluate", key="btn_tc_eval", type="primary"):
            if tc_input:
                with st.spinner("Analyzing..."):
                    prompt = f"Evaluate this Test Case: '{tc_input}'. Return ONLY JSON with totalScore(25), status, and parameters(list with name, score, finding)."
                    data = call_gemini_ai(prompt)
                    if data:
                        st.metric("Quality Score", f"{data.get('totalScore')}/25")
                        st.table(data.get('parameters'))

    # ============= TAB 3: GENERATOR =============
    with tab3:
        st.title("📝 Test Case Generator")
        feat_desc = st.text_area("Describe Feature", key="gen_input_main", height=150)
        if st.button("✨ Generate", key="btn_gen_main", type="primary"):
            if feat_desc:
                with st.spinner("Generating..."):
                    prompt = f"Generate 3 test cases for: '{feat_desc}'. Return ONLY JSON: {{'testCases': [{{'name', 'steps', 'expected'}}]}}"
                    data = call_gemini_ai(prompt)
                    if data:
                        for tc in data.get('testCases', []):
                            with st.expander(f"✅ {tc['name']}"):
                                st.write(tc['steps'])
                                st.write(f"**Expected:** {tc['expected']}")

    # ============= TAB 4: BULK USER STORIES =============
    with tab4:
        st.title("📊 Bulk User Story Evaluator")
        template_us = pd.DataFrame({"User Story": ["As a user, I want to login so I can see my dashboard.", "As a guest, I want to browse products."] })
        st.download_button("📥 Download Template", template_us.to_csv(index=False), "us_template.csv", "text/csv")
        uploaded_us = st.file_uploader("Upload CSV", type=['csv'], key="bulk_us_uploader")
        if uploaded_us:
            df = pd.read_csv(uploaded_us)
            if st.button("🚀 Process Bulk Stories"):
                results = []
                bar = st.progress(0)
                for i, row in df.iterrows():
                    story = str(row.iloc[0])
                    res = call_gemini_ai(f"Score this User Story: '{story}'. Return ONLY JSON: {{'score':(int/30), 'recommendation':(str)}}")
                    results.append({"User Story": story, "Score": res.get('score') if res else "N/A", "Recommendation": res.get('recommendation') if res else "Error"})
                    bar.progress((i + 1) / len(df))
                res_df = pd.DataFrame(results)
                st.dataframe(res_df)
                st.download_button("📥 Download Results", res_df.to_csv(index=False), "us_results.csv", "text/csv")

    # ============= TAB 5: BULK TEST CASES =============
    with tab5:
        st.title("📋 Bulk Test Case Evaluator")
        template_tc = pd.DataFrame({"Test Case": ["1. Open App. 2. Click Login. Expected: Login Screen.", "1. Enter Wrong Pass. Expected: Error Message."] })
        st.download_button("📥 Download Template", template_tc.to_csv(index=False), "tc_template.csv", "text/csv")
        uploaded_tc = st.file_uploader("Upload CSV", type=['csv'], key="bulk_tc_uploader")
        if uploaded_tc:
            df_tc = pd.read_csv(uploaded_tc)
            if st.button("🚀 Process Bulk Tests"):
                results_tc = []
                bar_tc = st.progress(0)
                for i, row in df_tc.iterrows():
                    tc = str(row.iloc[0])
                    res = call_gemini_ai(f"Score this Test Case: '{tc}'. Return ONLY JSON: {{'score':(int/25), 'status':(str)}}")
                    results_tc.append({"Test Case": tc, "Score": res.get('score') if res else "N/A", "Status": res.get('status') if res else "Error"})
                    bar_tc.progress((i + 1) / len(df_tc))
                res_tc_df = pd.DataFrame(results_tc)
                st.dataframe(res_tc_df)
                st.download_button("📥 Download Results", res_tc_df.to_csv(index=False), "tc_results.csv", "text/csv")
