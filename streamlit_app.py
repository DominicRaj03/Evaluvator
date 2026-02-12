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
    with st.sidebar:
        st.title("⚙️ Settings")
        selected_model = st.selectbox("Select AI Model", ["gemini-1.5-flash-latest", "gemini-1.5-pro-latest"])
        if st.button("🛠️ Refresh Connection"): st.rerun()
        st.markdown("---")
        if st.button("🧹 Clear All Data"):
            st.session_state.clear()
            st.rerun()

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
            st.session_state.last_error = str(e)
            return None

    def color_coding(val, max_val):
        color = 'red' if val < (max_val * 0.5) else 'orange' if val < (max_val * 0.8) else 'green'
        return f'background-color: {color}; color: white'

    # Status Monitor
    ping = call_ai("Respond 'OK'", is_json=False)
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

    # Individual Tabs 1-3 omitted for brevity, logic remains same as previous version...

    # --- Tab 4: Bulk Stories with Auto-Format ---
    with tabs[3]:
        st.title("📊 Bulk User Stories")
        up_us = st.file_uploader("Upload Stories CSV", type=['csv'], key="up_bulk_us")
        if up_us:
            df = pd.read_csv(up_us)
            df.insert(0, "Select", True)
            
            col_a, col_b = st.columns([1, 4])
            with col_a:
                if st.button("🪄 Auto-Format Selected"):
                    with st.spinner("Formatting..."):
                        for idx, row in df.iterrows():
                            if row["Select"]:
                                formatted = call_ai(f"Rewrite this as a standard User Story (As a... I want... So that...): '{row.iloc[2]}'. Return ONLY the text.", is_json=False)
                                if formatted: df.iloc[idx, 2] = formatted
                    st.rerun()

            edited_df = st.data_editor(df, hide_index=True, use_container_width=True)
            selected = edited_df[edited_df["Select"] == True]
            
            if st.button(f"🚀 Process {len(selected)} Stories", key="proc_us"):
                results = []
                bar = st.progress(0)
                for i, (idx, row) in enumerate(selected.iterrows()):
                    out = call_ai(f"Score Story: {row.iloc[2]}. Return ONLY JSON: {{ 'score': 20 }}")
                    results.append({"Story": row.iloc[2], "Score": out.get('score', 0) if out else 0})
                    bar.progress((i+1)/len(selected))
                res_df = pd.DataFrame(results)
                st.bar_chart(res_df.set_index("Story")["Score"])
                st.dataframe(res_df.style.applymap(lambda v: color_coding(v, 30), subset=['Score']))
                st.download_button("📥 Download Results (CSV)", res_df.to_csv(index=False), "us_evaluations.csv")

    # Tab 5 (Bulk Tests) remains as per the previous version...
