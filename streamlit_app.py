import streamlit as st
import pandas as pd
import google.generativeai as genai
from groq import Groq
import json
import re
import time

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
        .history-item { padding: 8px; border-bottom: 1px solid #3E3E5E; font-size: 0.8rem; color: #BBB; }
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

# --- 2. Multi-Provider AI Wrapper ---
def call_ai(prompt, provider, model_name, is_json=True):
    start_time = time.time()
    try:
        if provider == "Gemini":
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            text = response.text.strip()
        else:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model_name,
            )
            text = chat_completion.choices[0].message.content.strip()

        latency = int((time.time() - start_time) * 1000)
        st.session_state.last_latency = latency
        
        # Log to history
        log_entry = {"time": time.strftime("%H:%M:%S"), "provider": provider, "latency": f"{latency}ms"}
        if "latency_history" not in st.session_state: st.session_state.latency_history = []
        st.session_state.latency_history.insert(0, log_entry)
        st.session_state.latency_history = st.session_state.latency_history[:10]

        if is_json:
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            return json.loads(json_match.group(0)) if json_match else json.loads(text)
        return text
    except Exception as e:
        st.session_state.last_err = str(e)
        return None

# --- 3. Main Logic ---
st.set_page_config(page_title="Jarvis Evaluator", layout="wide")

if check_password():
    with st.sidebar:
        st.title("⚙️ Settings")
        provider = st.radio("Select Provider", ["Gemini", "Groq"])
        models = ["gemini-1.5-flash-latest", "gemini-1.5-pro-latest"] if provider == "Gemini" else ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]
        selected_model = st.selectbox("Select AI Model", models)
        
        st.markdown("---")
        st.subheader("⚡ Performance")
        st.metric("Last Latency", f"{st.session_state.get('last_latency', 0)} ms")
        
        with st.expander("🕒 Latency Log"):
            for entry in st.session_state.get("latency_history", []):
                st.markdown(f"<div class='history-item'>{entry['time']} - {entry['provider']}: {entry['latency']}</div>", unsafe_allow_html=True)

        if st.button("🛠️ Refresh Connection"): st.rerun()
        if st.button("🧹 Clear All Data"):
            st.session_state.clear()
            st.rerun()

    # Status Monitor
    ping = call_ai("Ping", provider, selected_model, is_json=False)
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

    tabs = st.tabs(["📖 User Story", "🧪 Test Case", "📝 Generator", "📊 Bulk Stories", "📋 Bulk Tests"])

    # --- Individual Tabs ---
    with tabs[0]:
        us_val = st.text_area("Input User Story", height=150, key="us_single")
        if st.button("Evaluate Story", type="primary") and is_active:
            res = call_ai(f"Evaluate US: '{us_val}'. Return JSON: {{'score': 20, 'feedback': 'str'}}", provider, selected_model)
            if res:
                st.metric("Score", f"{res.get('score')}/30")
                st.success(res.get('feedback'))

    with tabs[1]:
        tc_val = st.text_area("Input Test Case", height=150, key="tc_single")
        if st.button("Analyze Case", type="primary") and is_active:
            res = call_ai(f"Evaluate TC: '{tc_val}'. Return JSON: {{'score': 15, 'status': 'str'}}", provider, selected_model)
            if res:
                st.metric("Quality", f"{res.get('score')}/25")
                st.info(res.get('status'))

    with tabs[2]:
        feat = st.text_area("Feature Name", key="gen_feat")
        if st.button("Generate Tests") and is_active:
            res = call_ai(f"Generate 3 tests for: '{feat}'. Return JSON: {{'testCases': [{{'name': 'str', 'steps': 'str'}}]}}", provider, selected_model)
            if res:
                for t in res.get('testCases', []):
                    with st.expander(t['name']): st.write(t['steps'])

    # --- Bulk Processing ---
    with tabs[3]:
        st.title("📊 Bulk User Stories")
        up_us = st.file_uploader("Upload CSV", type=['csv'], key="bulk_us_up")
        if up_us:
            df = pd.read_csv(up_us)
            df.insert(0, "Select", True)
            if st.button("🪄 Auto-Format Selected"):
                for i, row in df.iterrows():
                    if row["Select"]:
                        fmt = call_ai(f"Rewrite as 'As a... I want... So that...': {row.iloc[2]}", provider, selected_model, is_json=False)
                        if fmt: df.iloc[i, 2] = fmt
                st.rerun()
            edited_df = st.data_editor(df, hide_index=True)
            if st.button("🚀 Process Stories") and is_active:
                sel = edited_df[edited_df["Select"]]
                results = []
                for _, row in sel.iterrows():
                    out = call_ai(f"Score: {row.iloc[2]}", provider, selected_model)
                    results.append({"Story": row.iloc[2], "Score": out.get('score', 0) if out else 0})
                res_df = pd.DataFrame(results)
                st.dataframe(res_df)
                st.download_button("📥 Download", res_df.to_csv(index=False), "us_results.csv")

    with tabs[4]:
        st.title("📋 Bulk Test Cases")
        up_tc = st.file_uploader("Upload CSV", type=['csv'], key="bulk_tc_up")
        if up_tc:
            df_t = pd.read_csv(up_tc)
            df_t.insert(0, "Select", True)
            edited_t = st.data_editor(df_t, hide_index=True)
            if st.button("🚀 Process Tests") and is_active:
                sel_t = edited_t[edited_t["Select"]]
                results_t = []
                for _, row in sel_t.iterrows():
                    out = call_ai(f"Score: {row.iloc[2]}", provider, selected_model)
                    results_t.append({"Test": row.iloc[2], "Score": out.get('score', 0) if out else 0})
                res_t_df = pd.DataFrame(results_t)
                st.dataframe(res_t_df)
                st.download_button("📥 Download", res_t_df.to_csv(index=False), "tc_results.csv")
