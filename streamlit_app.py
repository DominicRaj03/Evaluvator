import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
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
    # AI Setup
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
    except:
        st.error("Check Secrets for API Key!")

    def call_ai(prompt):
        try:
            response = model.generate_content(prompt)
            clean = response.text.strip().replace('```json', '').replace('```', '')
            return json.loads(clean)
        except: return None

    # Sidebar
    if st.sidebar.button("Log Out"):
        st.session_state["password_correct"] = False
        st.rerun()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📖 User Story", "🧪 Test Case", "📝 Generator", "📊 Bulk Stories", "📋 Bulk Tests"])

    # --- Tab 1 & 2: Single Evaluators ---
    with tab1:
        st.title("📖 User Story Evaluator")
        us_text = st.text_area("Enter Story", key="us_single")
        if st.button("Evaluate Story", type="primary"):
            res = call_ai(f"Evaluate: {us_text}. Return JSON: totalScore, grade, status, recommendation.")
            if res:
                st.metric("Score", f"{res['totalScore']}/30")
                st.info(res['recommendation'])

    with tab2:
        st.title("🧪 Test Case Evaluator")
        tc_text = st.text_area("Enter Test Case", key="tc_single")
        if st.button("Evaluate Test Case", type="primary"):
            res = call_ai(f"Evaluate: {tc_text}. Return JSON: totalScore, status, parameters.")
            if res:
                st.metric("Quality", f"{res['totalScore']}/25")
                st.table(res['parameters'])

    # --- Tab 3: Generator ---
    with tab3:
        st.title("📝 Test Case Generator")
        feat = st.text_area("Feature Description")
        if st.button("Generate"):
            res = call_ai(f"Generate 3 test cases for {feat}. Return JSON: testCases: [{{name, steps, expected}}]")
            if res:
                for t in res['testCases']:
                    with st.expander(t['name']):
                        st.write(t['steps'])
                        st.caption(f"Expected: {t['expected']}")

    # --- Tab 4: Bulk Stories with SEARCH ---
    with tab4:
        st.title("📊 Bulk User Stories")
        # Template
        st.download_button("📥 Template", pd.DataFrame({"User Story": ["As a..."]}).to_csv(index=False), "template.csv")
        
        up_us = st.file_uploader("Upload CSV", type=['csv'], key="up_us")
        if up_us:
            df = pd.read_csv(up_us)
            
            # --- LIVE SEARCH ---
            search = st.text_input("🔍 Search/Filter Stories", key="search_us")
            filtered_df = df[df.iloc[:,0].str.contains(search, case=False, na=False)] if search else df
            
            st.write(f"Filtered: {len(filtered_df)} rows")
            st.dataframe(filtered_df, use_container_width=True)
            
            if st.button("🚀 Process Filtered"):
                results = []
                bar = st.progress(0)
                for i, row in filtered_df.iterrows():
                    data = call_ai(f"Score: {row.iloc[0]}. Return JSON: score, recommendation")
                    results.append({"Story": row.iloc[0], "Score": data.get('score', 0), "Note": data.get('recommendation', 'Error')})
                    bar.progress((results.__len__()) / len(filtered_df))
                
                res_df = pd.DataFrame(results)
                st.dataframe(res_df)
                st.download_button("📥 Download Results", res_df.to_csv(index=False), "results.csv")

    # --- Tab 5: Bulk Test Cases with SEARCH ---
    with tab5:
        st.title("📋 Bulk Test Cases")
        st.download_button("📥 Template", pd.DataFrame({"Test Case": ["1. Open..."]}).to_csv(index=False), "template_tc.csv")
        
        up_tc = st.file_uploader("Upload CSV", type=['csv'], key="up_tc")
        if up_tc:
            df_tc = pd.read_csv(up_tc)
            
            # --- LIVE SEARCH ---
            search_tc = st.text_input("🔍 Search/Filter Tests", key="search_tc")
            filtered_tc = df_tc[df_tc.iloc[:,0].str.contains(search_tc, case=False, na=False)] if search_tc else df_tc
            
            st.dataframe(filtered_tc, use_container_width=True)
            
            if st.button("🚀 Process Filtered Tests"):
                results_tc = []
                bar_tc = st.progress(0)
                for i, row in filtered_tc.iterrows():
                    data = call_ai(f"Score: {row.iloc[0]}. Return JSON: score, status")
                    results_tc.append({"Test Case": row.iloc[0], "Score": data.get('score', 0), "Status": data.get('status', 'Error')})
                    bar_tc.progress((results_tc.__len__()) / len(filtered_tc))
                
                st.dataframe(pd.DataFrame(results_tc))
