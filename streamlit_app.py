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
        .stTextInput > div > div > input { background-color: #2D2D44; color: white; border: 1px solid #3E3E5E; }
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
    def call_ai(prompt, is_json=True):
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            
            if not response or not hasattr(response, 'text'):
                return None
            
            text = response.text.strip()
            if is_json:
                # Extracts JSON even if AI adds conversational text
                json_match = re.search(r"\{.*\}", text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                return json.loads(text)
            return text
        except Exception as e:
            st.session_state.debug_info = str(e)
            return None

    # Status Monitor
    ping = call_ai("Respond 'OK'", is_json=False)
    is_active = ping is not None
    
    # Header
    st.markdown(f"""
        <div class="status-header">
            <h2 style='margin:0;'>🎯 Jarvis Evaluator</h2>
            <div><span class="status-dot" style="background-color: {'#00FF00' if is_active else '#FF0000'};"></span>
            <b>{'ONLINE' if is_active else 'OFFLINE'}</b></div>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar Debug
    with st.sidebar:
        st.title("🛠️ Tools")
        if st.button("🧹 Clear All"):
            st.session_state.clear()
            st.rerun()
        st.markdown("---")
        with st.expander("🐞 Debug Logs"):
            st.code(st.session_state.get('debug_info', 'No errors recorded.'))

    # Tabs
    t1, t2, t3 = st.tabs(["📖 User Story", "🧪 Test Case", "📝 Generator"])

    with t1:
        st.title("📖 User Story Evaluator")
        val = st.text_area("Input", height=150, key="us_final")
        if st.button("Evaluate", type="primary", disabled=not is_active):
            with st.spinner("Processing..."):
                res = call_ai(f"Evaluate US: '{val}'. Return ONLY JSON: {{ 'score': 25, 'feedback': 'text' }}")
                if res:
                    st.metric("Score", f"{res.get('score')}/30")
                    st.success(res.get('feedback'))
                else:
                    st.error("Check Debug Logs in sidebar.")

    with t2:
        st.title("🧪 Test Case Evaluator")
        tc_val = st.text_area("Input", height=150, key="tc_final")
        if st.button("Analyze", type="primary", disabled=not is_active):
            with st.spinner("Analyzing..."):
                res = call_ai(f"Evaluate TC: '{tc_val}'. Return ONLY JSON: {{ 'score': 20, 'status': 'Pass' }}")
                if res:
                    st.metric("Quality", f"{res.get('score')}/25")
                    st.info(f"Status: {res.get('status')}")
