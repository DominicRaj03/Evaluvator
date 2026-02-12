import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import re

# --- 1. Security & Styling ---
def check_password():
    st.markdown("""
        <style>
        .login-container {
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            padding: 40px; background-color: #1E1E2E; border-radius: 15px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5); max-width: 400px; margin: auto;
        }
        .status-header { display: flex; align-items: center; justify-content: space-between; padding: 10px; background: #262730; border-radius: 8px; margin-bottom: 20px; }
        .status-dot { height: 12px; width: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; }
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

# --- 2. Main Logic ---
st.set_page_config(page_title="Jarvis Evaluator", layout="wide")

if check_password():
    # Sidebar Configuration
    with st.sidebar:
        st.title("⚙️ Settings")
        selected_model = st.selectbox("Select AI Model", ["gemini-1.5-flash-latest", "gemini-1.5-pro-latest"])
        if st.button("🛠️ Refresh Connection"): st.rerun()
        st.markdown("---")
        if st.button("🧹 Clear All Data"):
            st.session_state.clear()
            st.rerun()

    # AI Wrapper
    def call_ai(prompt, is_json=True):
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel(selected_model)
            response = model.generate_content(prompt)
            if not response or not hasattr(response, 'text'): return None
            text = response.text.strip()
            if is_json:
                json_match = re.search(r"\{.*\}", text, re.DOTALL)
                return json.loads(json_match.group(0)) if json_match else json.loads(text)
            return text
        except Exception as e:
            st.session_state.last_err = str(e)
            return None

    # Status Check
    ping = call_ai("Ping", is_json=False)
    is_active = ping is not None
    
    st.markdown(f"""
        <div class="status-header">
            <h2 style='margin:0;'>🎯 Jarvis Evaluator</h2>
            <div style="display: flex; align-items: center;">
                <span class="status-dot" style="background-color: {'#00FF00' if is_active else '#FF0000'};"></span>
                <b>{selected_model.upper()} {'ONLINE' if is_active else 'OFFLINE'}</b>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if not is_active:
        st.error(f"⚠️ Connection Failed: {st.session_state.get('last_err', 'Check API Key in Secrets')}")

    tabs = st.tabs(["📖 User Story", "🧪 Test Case", "📝 Generator", "📊 Bulk Stories", "📋 Bulk Tests"])

    # --- Tab 1: User Story ---
    with tabs[0]:
        st.title("📖 User Story Evaluator")
        us_val = st.text_area("Enter User Story", height=150, key="us_in")
        if st.button("Evaluate User Story", type="primary"):
            if is_active:
                with st.spinner("Analyzing..."):
                    res = call_ai(f"Evaluate US: '{us_val}'. Return JSON: {{'score': 20, 'feedback': 'str', 'confidence': 90}}")
                    if res:
                        st.metric("Score", f"{res.get('score')}/30")
                        st.success(res.get('feedback'))
            else: st.warning("Cannot evaluate while offline.")

    # --- Tab 2: Test Case ---
    with tabs[1]:
        st.title("🧪 Test Case Evaluator")
        tc_val = st.text_area("Enter Test Case", height=150, key="tc_in")
        if st.button("Evaluate Test Case", type="primary"):
            if is_active:
                with st.spinner("Analyzing..."):
                    res = call_ai(f"Evaluate TC: '{tc_val}'. Return JSON: {{'score': 15, 'status': 'str'}}")
                    if res:
                        st.metric("Quality", f"{res.get('score')}/25")
                        st.info(res.get('status'))
            else: st.warning("Cannot evaluate while offline.")

    # --- Tab 3: Generator ---
    with tabs[2]:
        st.title("📝 Test Case Generator")
        feat = st.text_area("Feature Description", key="feat_in")
        if st.button("Generate Tests"):
            if is_active:
                with st.spinner("Generating..."):
                    res = call_ai(f"Generate 3 tests for: '{feat}'. Return JSON: {{'testCases': [{{'name': 'str', 'steps': 'str'}}]}}")
                    if res:
                        for t in res.get('testCases', []):
                            with st.expander(t['name']): st.write(t['steps'])
            else: st.warning("Cannot generate while offline.")

    # --- Tab 4: Bulk Stories ---
    with tabs[3]:
        st.title("📊 Bulk User Stories")
        up_us = st.file_uploader("Upload Stories CSV", type=['csv'], key="bulkus_up")
        if up_us:
            df = pd.read_csv(up_us)
            df.insert(0, "Select", True)
            edited_df = st.data_editor(df, hide_index=True)
            if st.button("🚀 Process Selected Stories") and is_active:
                selected = edited_df[edited_df["Select"] == True]
                results = []
                for _, row in selected.iterrows():
                    out = call_ai(f"Score Story: {row.iloc[1]}. Return JSON: {{'score': 10}}")
                    results.append({"Story": row.iloc[1], "Score": out.get('score', 0) if out else 0})
                st.dataframe(pd.DataFrame(results))

    # --- Tab 5: Bulk Tests ---
    with tabs[4]:
        st.title("📋 Bulk Test Cases")
        up_tc = st.file_uploader("Upload Tests CSV", type=['csv'], key="bulktc_up")
        if up_tc:
            df_t = pd.read_csv(up_tc)
            df_t.insert(0, "Select", True)
            edited_t = st.data_editor(df_t, hide_index=True)
            if st.button("🚀 Process Selected Tests") and is_active:
                selected_t = edited_t[edited_t["Select"] == True]
                results_t = []
                for _, row in selected_t.iterrows():
                    out = call_ai(f"Score Test: {row.iloc[1]}. Return JSON: {{'score': 10}}")
                    results_t.append({"Test": row.iloc[1], "Score": out.get('score', 0) if out else 0})
                st.dataframe(pd.DataFrame(results_t))
