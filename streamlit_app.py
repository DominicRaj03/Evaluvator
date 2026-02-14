import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import re
import time

# --- 1. UI Styling (Matches Template) ---
def apply_styles():
    st.markdown("""
        <style>
        .main-header { font-size: 24px; font-weight: bold; color: #1E3A8A; border-bottom: 2px solid #3B82F6; padding-bottom: 10px; margin-bottom: 20px; }
        .score-box { background-color: #2ecc71; color: white; padding: 15px; border-radius: 8px; font-size: 28px; font-weight: bold; display: inline-block; }
        .param-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        .param-header { background-color: #3B82F6; color: white; padding: 10px; text-align: left; }
        .recommendations { background-color: #F0F9FF; border: 1px solid #BAE6FD; padding: 15px; border-radius: 8px; margin-top: 20px; }
        </style>
    """, unsafe_allow_html=True)

# --- 2. Core AI Logic ---
def call_ai(prompt, provider, model_name):
    try:
        if provider == "Gemini":
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            text = response.text.strip()
        else:
            from groq import Groq
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            chat = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model=model_name)
            text = chat.choices[0].message.content.strip()

        # Extracting JSON from AI response
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else None
    except Exception as e:
        st.error(f"❌ AI Error: {str(e)}")
        return None

# --- 3. Authentication ---
st.set_page_config(page_title="Jarvis Evaluator", layout="wide")
apply_styles()

if "password_correct" not in st.session_state:
    st.title("🎯 Jarvis AI Access")
    pwd = st.text_input("Access Key", type="password")
    if st.button("Unlock"):
        if pwd == st.secrets["APP_PASSWORD"]:
            st.session_state.password_correct = True
            st.rerun()
        else: st.error("Invalid Key")
    st.stop()

# --- 4. Sidebar & Config ---
with st.sidebar:
    st.title("⚙️ Settings")
    provider = st.radio("AI Provider", ["Gemini", "Groq"])
    models = ["gemini-1.5-flash-latest", "gemini-1.5-pro-latest"] if provider == "Gemini" else ["llama-3.3-70b-versatile"]
    selected_model = st.selectbox("Model", models)
    if st.button("🗑️ Reset Application"): st.session_state.clear(); st.rerun()

# --- 5. Main Application Tabs ---
tabs = st.tabs(["📖 Story Evaluator", "🧪 Test Case Evaluator", "📝 Generator", "📊 Bulk Dashboard"])

# Evaluation Template Logic
def run_evaluation(content, label):
    prompt = f"""
    Evaluate this {label}: '{content}'
    Return ONLY a JSON object with:
    'parameters': [
        {{'name': 'Clarity', 'desc': 'Easy to understand?', 'score': 0-20}},
        {{'name': 'Completeness', 'desc': 'Defined criteria?', 'score': 0-20}},
        {{'name': 'Business Value', 'desc': 'Alignment with goals?', 'score': 0-20}},
        {{'name': 'Testability', 'desc': 'Can it be verified?', 'score': 0-20}},
        {{'name': 'Technical Feasibility', 'desc': 'Implementable?', 'score': 0-20}}
    ],
    'total_score': 0-100,
    'recommendations': ['str', 'str']
    """
    res = call_ai(prompt, provider, selected_model)
    if res:
        st.markdown(f'<div class="main-header">{label} Review and Analysis</div>', unsafe_allow_html=True)
        
        # Display Table
        df = pd.DataFrame(res['parameters'])
        st.table(df.rename(columns={'name': 'Parameter', 'desc': 'Description', 'score': 'Score (out of 20)'}))
        
        # Display Total Score
        st.subheader("Overall Quality Score")
        st.markdown(f'<div class="score-box">{res["total_score"]} / 100</div>', unsafe_allow_html=True)
        
        # Display Recommendations
        st.markdown('<div class="recommendations"><b>💡 Improvement Recommendations:</b>', unsafe_allow_html=True)
        for rec in res['recommendations']:
            st.write(f"• {rec}")
        st.markdown('</div>', unsafe_allow_html=True)

# TAB 1 & 2: EVALUATORS
with tabs[0]:
    txt = st.text_area("User Story Content", height=150, placeholder="As a... I want... So that...")
    if st.button("Evaluate Story", type="primary"): run_evaluation(txt, "User Story")

with tabs[1]:
    txt = st.text_area("Test Case Content", height=150)
    if st.button("Evaluate Test Case", type="primary"): run_evaluation(txt, "Test Case")

# TAB 3: GENERATOR
with tabs[2]:
    st.subheader("📝 Generator")
    feat = st.text_input("Enter Feature Requirement")
    if st.button("Generate 3 Test Cases"):
        res = call_ai(f"Generate 3 tests for {feat}. Return JSON: {{'tests':['str']}}", provider, selected_model)
        if res: st.write(res['tests'])

# TAB 4: BULK UPLOAD
with tabs[3]:
    st.subheader("📊 Bulk Evaluation Dashboard")
    up = st.file_uploader("Upload CSV", type=['csv'])
    if up:
        df = pd.read_csv(up)
        edited_df = st.data_editor(df, use_container_width=True)
        if st.button("🚀 Process Bulk"):
            scores = []
            for _, row in edited_df.iterrows():
                # Simplified bulk score call
                out = call_ai(f"Score 0-100: {row.iloc[0]}", provider, selected_model)
                scores.append(out.get('total_score', 0) if out else 0)
            st.bar_chart(scores)
