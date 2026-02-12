import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import re
import time

# --- 1. Security & Dynamic Styling ---
def apply_styles():
    st.markdown("""
        <style>
        .status-header { display: flex; align-items: center; justify-content: space-between; padding: 10px; background: #262730; border-radius: 8px; margin-bottom: 20px; }
        .status-dot { height: 12px; width: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; }
        .main-card { background-color: #1E1E2E; padding: 20px; border-radius: 10px; border: 1px solid #3E3E5E; }
        </style>
    """, unsafe_allow_html=True)

def check_password():
    if "password_correct" not in st.session_state:
        st.title("🎯 Jarvis AI")
        pwd = st.text_input("Access Key", type="password")
        if st.button("Unlock"):
            if pwd == st.secrets["APP_PASSWORD"]:
                st.session_state.password_correct = True
                st.rerun()
            else: st.error("Incorrect Key")
        return False
    return True

# --- 2. Safe AI Client Wrapper ---
def call_ai(prompt, provider, model_name, is_json=True):
    start_time = time.time()
    try:
        if provider == "Gemini":
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            text = response.text.strip()
        else:
            from groq import Groq # Local import to prevent boot errors
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            chat = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model=model_name)
            text = chat.choices[0].message.content.strip()

        st.session_state.last_latency = int((time.time() - start_time) * 1000)
        
        if is_json:
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            return json.loads(json_match.group(0)) if json_match else json.loads(text)
        return text
    except Exception as e:
        st.error(f"Provider Error: {str(e)}")
        return None

# --- 3. Main Application Structure ---
st.set_page_config(page_title="Jarvis Evaluator", layout="wide")
apply_styles()

if check_password():
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Control Panel")
        provider = st.radio("Provider", ["Gemini", "Groq"])
        models = ["gemini-1.5-flash-latest", "gemini-1.5-pro-latest"] if provider == "Gemini" else ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]
        selected_model = st.selectbox("Model", models)
        st.metric("Latency", f"{st.session_state.get('last_latency', 0)} ms")
        if st.button("🗑️ Clear Cache"): st.session_state.clear(); st.rerun()

    # Header
    st.markdown(f'<div class="status-header"><h2>🎯 Jarvis Evaluator</h2><b>Using {provider}</b></div>', unsafe_allow_html=True)

    # Tabs (Now always visible)
    tabs = st.tabs(["📖 Story", "🧪 Test Case", "📝 Generator", "📊 Bulk"])

    with tabs[0]:
        us_input = st.text_area("User Story Content", height=150)
        if st.button("Run Evaluation", type="primary"):
            with st.spinner("Analyzing..."):
                res = call_ai(f"Score this: {us_input}. Return JSON: {{'score':10, 'feedback':'str'}}", provider, selected_model)
                if res: st.success(f"Score: {res['score']}/30 \n\n {res['feedback']}")

    with tabs[1]:
        tc_input = st.text_area("Test Case Content", height=150)
        if st.button("Run Analysis"):
            with st.spinner("Analyzing..."):
                res = call_ai(f"Evaluate TC: {tc_input}. Return JSON: {{'score':10}}", provider, selected_model)
                if res: st.info(f"Quality Score: {res['score']}/25")

    with tabs[2]:
        feature = st.text_input("Enter Feature Name")
        if st.button("Generate"):
            with st.spinner("Creating..."):
                res = call_ai(f"Create 3 tests for {feature}. Return JSON: {{'tests':['str']}}", provider, selected_model)
                if res: st.write(res['tests'])

    with tabs[3]:
        up = st.file_uploader("Upload CSV", type=['csv'])
        if up:
            df = pd.read_csv(up)
            df.insert(0, "Select", True)
            edited = st.data_editor(df)
            if st.button("🚀 Process Bulk"):
                results = []
                for _, row in edited[edited["Select"]].iterrows():
                    out = call_ai(f"Score: {row.iloc[1]}", provider, selected_model)
                    results.append(out.get('score', 0) if out else 0)
                st.line_chart(results)
