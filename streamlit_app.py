import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import re
import time

# --- 1. UI Styling & Visual Config ---
def apply_styles():
    st.markdown("""
        <style>
        .status-header { display: flex; align-items: center; justify-content: space-between; padding: 10px; background: #262730; border-radius: 8px; margin-bottom: 20px; }
        .stMetric { background: #1E1E2E; padding: 10px; border-radius: 8px; border: 1px solid #3E3E5E; }
        .score-bubble { padding: 5px 10px; border-radius: 15px; font-weight: bold; color: black; }
        </style>
    """, unsafe_allow_html=True)

def get_color(score):
    if score >= 20: return "#2ecc71" # Green
    if score >= 10: return "#f1c40f" # Yellow
    return "#e74c3c" # Red

# --- 2. Core AI Logic (Lazy & Safe) ---
def call_ai(prompt, provider, model_name):
    start_time = time.time()
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

        st.session_state.last_latency = int((time.time() - start_time) * 1000)
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else {"score": 0, "findings": text, "tests": []}
    except Exception as e:
        st.error(f"❌ AI Error: {str(e)}")
        return None

# --- 3. App Initialization ---
st.set_page_config(page_title="Jarvis Evaluator", layout="wide")
apply_styles()

if "password_correct" not in st.session_state:
    st.title("🎯 Jarvis AI Access")
    pwd = st.text_input("Access Key", type="password")
    if st.button("Unlock"):
        if pwd == st.secrets["APP_PASSWORD"]: st.session_state.password_correct = True; st.rerun()
    st.stop()

# --- 4. Sidebar Controls ---
with st.sidebar:
    st.title("⚙️ Control Panel")
    provider = st.radio("Provider", ["Gemini", "Groq"])
    models = ["gemini-1.5-flash-latest", "gemini-1.5-pro-latest"] if provider == "Gemini" else ["llama-3.3-70b-versatile"]
    selected_model = st.selectbox("Model", models)
    st.metric("Last Latency", f"{st.session_state.get('last_latency', 0)} ms")
    if st.button("🗑️ Reset Application"): st.session_state.clear(); st.rerun()

st.markdown(f'<div class="status-header"><h2>📊 Jarvis AI Evaluator</h2><b>Engine: {selected_model}</b></div>', unsafe_allow_html=True)

# --- 5. Main Content Tabs ---
tabs = st.tabs(["📖 User Stories", "🧪 Test Cases", "📝 Test Generator", "📊 Bulk Evaluation"])

# TAB 1 & 2: Individual Evaluation
for i, label in enumerate(["User Story", "Test Case"]):
    with tabs[i]:
        content = st.text_area(f"Input {label}", height=150, placeholder=f"Enter your {label.lower()} here...")
        if st.button(f"Evaluate {label}", type="primary"):
            with st.spinner("Analyzing..."):
                res = call_ai(f"Evaluate this {label}: '{content}'. Return JSON: {{'score': 0-30, 'findings': 'str'}}", provider, selected_model)
                if res:
                    st.divider()
                    c1, c2 = st.columns([1, 3])
                    c1.metric("Quality Score", f"{res['score']}/30")
                    c2.info(f"**Findings:** {res['findings']}")

# TAB 3: Test Case Generator
with tabs[2]:
    st.subheader("📝 AI Test Case Generator")
    feature_desc = st.text_area("Describe the Feature or Requirement", height=150)
    if st.button("Generate Test Cases"):
        with st.spinner("Writing tests..."):
            res = call_ai(f"Generate 5 test cases for: {feature_desc}. Return JSON: {{'tests': [{{'title': 'str', 'steps': 'str'}}]}}", provider, selected_model)
            if res and 'tests' in res:
                for t in res['tests']:
                    with st.expander(t['title']): st.write(t['steps'])

# TAB 4: Bulk CSV Processing & Charts
with tabs[3]:
    st.subheader("📊 Bulk Evaluation Dashboard")
    up = st.file_uploader("Upload CSV (Requirement in 1st Column)", type=['csv'])
    if up:
        df = pd.read_csv(up)
        st.write("Data Preview:")
        edited_df = st.data_editor(df, use_container_width=True)
        
        if st.button("🚀 Process Bulk Batch"):
            results = []
            progress = st.progress(0)
            for idx, row in edited_df.iterrows():
                out = call_ai(f"Score: {row.iloc[0]}", provider, selected_model)
                results.append({"Item": row.iloc[0], "Score": out.get('score', 0) if out else 0, "Findings": out.get('findings', 'N/A')})
                progress.progress((idx + 1) / len(edited_df))
            
            res_df = pd.DataFrame(results)
            
            # --- EVALUATOR CHART ---
            st.divider()
            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.subheader("📈 Quality Distribution")
                st.bar_chart(res_df.set_index("Item")["Score"])
            with col_b:
                st.subheader("📋 Results Table")
                st.dataframe(res_df.style.background_gradient(subset=['Score'], cmap='RdYlGn'), use_container_width=True)
            
            st.download_button("📥 Export Results", res_df.to_csv(index=False), "jarvis_results.csv")
