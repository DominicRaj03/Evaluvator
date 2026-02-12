import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import re
from io import BytesIO

# --- 1. Security & Styling ---
def check_password():
    st.markdown("""
        <style>
        .login-container {
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            padding: 40px; background-color: #1E1E2E; border-radius: 15px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5); max-width: 400px; margin: auto;
        }
        .stTextInput > div > div > input { background-color: #2D2D44; color: white; border: 1px solid #3E3E5E; }
        .stButton>button { width: 100%; border-radius: 5px; }
        </style>
    """, unsafe_allow_html=True)

    if "password_correct" not in st.session_state:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            st.title("🎯 Jarvis AI")
            st.text_input("Access Key", type="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state["password"] == st.secrets["APP_PASSWORD"]}), key="password")
            st.markdown('</div>', unsafe_allow_html=True)
        return False
    return st.session_state["password_correct"]

# --- 2. Main App Logic ---
st.set_page_config(page_title="Jarvis - US Evaluator", layout="wide")

if check_password():
    # Model Configuration
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as e:
        st.error(f"Configuration Error: {e}")

    def call_ai(prompt):
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            # Regex to extract JSON block even if AI adds conversational text
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(text)
        except Exception:
            return None

    # --- Sidebar Controls ---
    st.sidebar.title("🛠️ Controls")
    if st.sidebar.button("🧹 Clear All Data"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()
        
    if st.sidebar.button("🚪 Log Out"):
        st.session_state["password_correct"] = False
        st.rerun()

    tabs = st.tabs(["📖 User Story", "🧪 Test Case", "📝 Generator", "📊 Bulk Stories", "📋 Bulk Tests"])

    # ============= TAB 1: USER STORY =============
    with tabs[0]:
        st.title("📖 User Story Evaluator")
        us_text = st.text_area("Enter User Story", key="us_single", height=150)
        if st.button("Evaluate User Story", type="primary"):
            if us_text:
                with st.spinner("AI is evaluating..."):
                    prompt = f"""Evaluate this User Story: '{us_text}'. Return ONLY JSON: 
                    {{"totalScore": 0-30, "grade": "string", "status": "string", "recommendation": "string", 
                    "invest": {{"Independent": 0-5, "Negotiable": 0-5, "Valuable": 0-5, "Estimable": 0-5, "Small": 0-5, "Testable": 0-5}}}}"""
                    data = call_ai(prompt)
                    if data:
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Score", f"{data.get('totalScore')}/30")
                        c2.metric("Grade", data.get('grade'))
                        c3.metric("Status", data.get('status'))
                        st.success(data.get('recommendation'))
                        st.subheader("INVEST Breakdown")
                        cols = st.columns(6)
                        for i, (k, v) in enumerate(data.get('invest', {}).items()):
                            cols[i].metric(k, f"{v}/5")
                    else:
                        st.error("The AI returned an unexpected format. Please try again.")

    # ============= TAB 2: TEST CASE =============
    with tabs[1]:
        st.title("🧪 Test Case Evaluator")
        tc_text = st.text_area("Enter Test Case", key="tc_single", height=150)
        if st.button("Evaluate Test Case", type="primary"):
            if tc_text:
                with st.spinner("Analyzing..."):
                    prompt = f"Evaluate Test Case: '{tc_text}'. Return ONLY JSON: {{"totalScore": 0-25, "status": "string", "parameters": [{{"name": "str", "score": 0-5, "finding": "str"}}]}}"
                    data = call_ai(prompt)
                    if data:
                        st.metric("Quality Score", f"{data.get('totalScore')}/25")
                        st.table(data.get('parameters'))

    # ============= TAB 3: GENERATOR =============
    with tabs[2]:
        st.title("📝 Test Case Generator")
        feat = st.text_area("Feature Description")
        if st.button("Generate Test Cases"):
            prompt = f"Generate 3 test cases for: '{feat}'. Return ONLY JSON: {{'testCases': [{{'name':'str', 'steps':'str', 'expected':'str'}}]}}"
            data = call_ai(prompt)
            if data:
                for t in data.get('testCases', []):
                    with st.expander(t['name']):
                        st.write(f"**Steps:**\n{t['steps']}")
                        st.caption(f"**Expected:** {t['expected']}")

    # ============= TAB 4: BULK STORIES =============
    with tabs[3]:
        st.title("📊 Bulk User Stories")
        st.download_button("📥 Template", pd.DataFrame({"User Story": ["As a..."]}).to_csv(index=False), "us_template.csv")
        up_us = st.file_uploader("Upload CSV", type=['csv'], key="bulk_us")
        if up_us:
            df = pd.read_csv(up_us)
            search = st.text_input("🔍 Search Stories", key="search_us")
            filtered = df[df.iloc[:,0].str.contains(search, case=False, na=False)] if search else df
            st.dataframe(filtered, use_container_width=True)
            if st.button("🚀 Process Filtered Stories"):
                results = []
                bar = st.progress(0)
                for i, row in filtered.iterrows():
                    res = call_ai(f"Score Story: {row.iloc[0]}. Return ONLY JSON: {{'score': 0-30, 'note': 'str'}}")
                    results.append({"Story": row.iloc[0], "Score": res.get('score', 'N/A') if res else "Error", "Recommendation": res.get('note', 'N/A') if res else "Error"})
                    bar.progress((len(results)) / len(filtered))
                st.dataframe(pd.DataFrame(results))

    # ============= TAB 5: BULK TESTS =============
    with tabs[4]:
        st.title("📋 Bulk Test Cases")
        st.download_button("📥 Template", pd.DataFrame({"Test Case": ["Step 1..."]}).to_csv(index=False), "tc_template.csv")
        up_tc = st.file_uploader("Upload CSV", type=['csv'], key="bulk_tc")
        if up_tc:
            df_tc = pd.read_csv(up_tc)
            search_tc = st.text_input("🔍 Search Tests", key="search_tc_input")
            filtered_tc = df_tc[df_tc.iloc[:,0].str.contains(search_tc, case=False, na=False)] if search_tc else df_tc
            st.dataframe(filtered_tc, use_container_width=True)
            if st.button("🚀 Process Filtered Tests"):
                results_tc = []
                bar_tc = st.progress(0)
                for i, row in filtered_tc.iterrows():
                    res = call_ai(f"Score Test: {row.iloc[0]}. Return ONLY JSON: {{'score': 0-25, 'status': 'str'}}")
                    results_tc.append({"Test Case": row.iloc[0], "Score": res.get('score', 'N/A') if res else "Error", "Status": res.get('status', 'N/A') if res else "Error"})
                    bar_tc.progress((len(results_tc)) / len(filtered_tc))
                st.dataframe(pd.DataFrame(results_tc))
