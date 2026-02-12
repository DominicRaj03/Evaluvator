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
        .stButton>button { width: 100%; border-radius: 5px; }
        .status-header { display: flex; align-items: center; justify-content: space-between; padding: 10px; background: #262730; border-radius: 8px; margin-bottom: 20px; }
        .status-dot { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 5px; }
        .history-item { padding: 10px; border-bottom: 1px solid #3E3E5E; font-size: 0.85rem; }
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

# --- 2. Logic & Status Check ---
st.set_page_config(page_title="Jarvis - Evaluator", layout="wide")

if check_password():
    if "history" not in st.session_state: st.session_state.history = []

    def call_ai(prompt, is_json=True):
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            text = response.text.strip()
            if is_json:
                json_match = re.search(r"\{.*\}", text, re.DOTALL)
                return json.loads(json_match.group(0)) if json_match else json.loads(text)
            return text
        except Exception: return None

    # Silent Status Check
    is_active = call_ai("Ping", is_json=False) is not None
    dot_color = "#00FF00" if is_active else "#FF0000"
    status_text = "SYSTEM ACTIVE" if is_active else "CONNECTION OFFLINE"

    # Header with Status
    st.markdown(f"""
        <div class="status-header">
            <h2 style='margin:0;'>🎯 Jarvis Evaluator</h2>
            <div><span class="status-dot" style="background-color: {dot_color};"></span><b>{status_text}</b></div>
        </div>
    """, unsafe_allow_html=True)

    # --- Sidebar ---
    st.sidebar.title("🛠️ Controls")
    if st.sidebar.button("🧹 Clear All Data"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.title("🕒 Recent History")
    for item in st.session_state.history:
        st.sidebar.markdown(f"<div class='history-item'><b>{item['type']}</b><br>{item['title']}</div>", unsafe_allow_html=True)

    tabs = st.tabs(["📖 User Story", "🧪 Test Case", "📝 Generator", "📊 Bulk Stories", "📋 Bulk Tests"])

    # --- Tab Logic ---
    with tabs[0]:
        st.title("📖 User Story Evaluator")
        us_text = st.text_area("Enter Story", height=150, key="us_input")
        if st.button("Evaluate Story", type="primary"):
            if us_text:
                with st.spinner("Analyzing..."):
                    p = f"Evaluate US: '{us_text}'. Return ONLY JSON: {{ 'score': 25, 'feedback': 'text' }}"
                    data = call_ai(p)
                    if data:
                        st.metric("Score", f"{data.get('score', 0)}/30")
                        st.success(f"**Feedback:** {data.get('feedback')}")
                        st.session_state.history.insert(0, {"type": "US", "title": us_text[:30]})
                    else: st.error("AI returned invalid format. Try again.")

    with tabs[1]:
        st.title("🧪 Test Case Evaluator")
        tc_text = st.text_area("Enter Test Case", height=150, key="tc_input")
        if st.button("Evaluate Test Case", type="primary"):
            if tc_text:
                with st.spinner("Analyzing..."):
                    p = f"Evaluate TC: '{tc_text}'. Return ONLY JSON: {{ 'score': 20, 'status': 'Pass' }}"
                    data = call_ai(p)
                    if data:
                        st.metric("Quality Score", f"{data.get('score', 0)}/25")
                        st.info(f"Status: {data.get('status')}")
                        st.session_state.history.insert(0, {"type": "TC", "title": tc_text[:30]})

    with tabs[2]:
        st.title("📝 Test Case Generator")
        feat = st.text_area("Feature Description")
        if st.button("Generate"):
            with st.spinner("Generating..."):
                p = f"Generate 3 test cases for: '{feat}'. Return ONLY JSON: {{ 'testCases': [{{ 'name': 'str', 'steps': 'str' }}] }}"
                data = call_ai(p)
                if data:
                    for t in data.get('testCases', []):
                        with st.expander(t['name']): st.code(t['steps'])
