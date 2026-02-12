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
        .history-item { padding: 10px; border-bottom: 1px solid #3E3E5E; font-size: 0.85rem; }
        .chat-msg { padding: 10px; border-radius: 10px; margin-bottom: 10px; }
        .user-msg { background-color: #3E3E5E; color: white; }
        .jarvis-msg { background-color: #161625; border: 1px solid #3E3E5E; color: #00FFAA; }
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
    if "history" not in st.session_state: st.session_state.history = []
    if "chat_log" not in st.session_state: st.session_state.chat_log = []

    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as e:
        st.error(f"Configuration Error: {e}")

    def call_ai(prompt, is_json=True):
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            if is_json:
                json_match = re.search(r"\{.*\}", text, re.DOTALL)
                return json.loads(json_match.group(0)) if json_match else json.loads(text)
            return text
        except Exception: return None

    def color_coding(val, max_val):
        color = 'red' if val < (max_val * 0.5) else 'orange' if val < (max_val * 0.8) else 'green'
        return f'background-color: {color}; color: white'

    # --- Sidebar ---
    st.sidebar.title("🛠️ Controls")
    if st.sidebar.button("🧹 Clear All Data"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
    if st.sidebar.button("🚪 Log Out"):
        st.session_state["password_correct"] = False
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.title("🕒 Recent History")
    for item in st.session_state.history:
        st.sidebar.markdown(f"<div class='history-item'><b>{item['type']}</b><br>{item['title']}<br>Result: <code>{item['score']}</code></div>", unsafe_allow_html=True)

    tabs = st.tabs(["📖 User Story", "🧪 Test Case", "📝 Generator", "📊 Bulk Stories", "📋 Bulk Tests"])

    # --- Tab 1 & 2 logic updated to include Chat ---
    for i, label in enumerate(["User Story", "Test Case"]):
        with tabs[i]:
            st.title(f"📖 {label} Evaluator")
            user_input = st.text_area(f"Enter {label}", key=f"input_{i}", height=150)
            if st.button(f"Evaluate {label}", type="primary", key=f"btn_{i}"):
                with st.spinner("Analyzing..."):
                    p = f"Evaluate {label}: '{user_input}'. Return ONLY JSON." # simplified for space
                    data = call_ai(p)
                    if data:
                        st.session_state[f"last_eval_{i}"] = data
                        st.write(data) # Rendering specific to your UI needs
            
            # Chat Interface
            if f"last_eval_{i}" in st.session_state:
                st.markdown("---")
                st.subheader("💬 Chat with Jarvis about this result")
                chat_query = st.text_input("Ask a follow-up question:", key=f"chat_in_{i}")
                if st.button("Send", key=f"chat_btn_{i}"):
                    context = f"Context: {user_input}. Eval: {st.session_state[f'last_eval_{i}']}. Question: {chat_query}"
                    answer = call_ai(context, is_json=False)
                    st.markdown(f"<div class='chat-msg jarvis-msg'><b>Jarvis:</b> {answer}</div>", unsafe_allow_html=True)

    # --- Tab 3: Generator ---
    with tabs[2]:
        st.title("📝 Test Case Generator")
        feat = st.text_area("Feature Description")
        if st.button("Generate"):
            with st.spinner("Generating..."):
                p = f"Generate 3 test cases for: '{feat}'. Return ONLY JSON."
                data = call_ai(p)
                if data:
                    for t in data.get('testCases', []):
                        with st.expander(t['name']): st.code(f"Steps: {t['steps']}\nExpected: {t['expected']}")

    # --- Tab 4: Bulk Stories ---
    with tabs[3]:
        st.title("📊 Bulk User Stories")
        up_us = st.file_uploader("Upload CSV", type=['csv'], key="bulk_us")
        if up_us:
            df = pd.read_csv(up_us)
            df.insert(0, "Select", True)
            edited_df = st.data_editor(df, hide_index=True, use_container_width=True)
            selected_rows = edited_df[edited_df["Select"] == True]
            if st.button(f"🚀 Process {len(selected_rows)} Stories"):
                results = []
                bar = st.progress(0)
                for j, (idx, row) in enumerate(selected_rows.iterrows()):
                    res = call_ai(f"Score Story: {row.iloc[1]}. Return ONLY JSON.")
                    results.append({"Story": row.iloc[1], "Score": res.get('score', 0) if res else 0})
                    bar.progress((j + 1) / len(selected_rows))
                res_df = pd.DataFrame(results)
                st.bar_chart(res_df.set_index("Story")["Score"])
                st.dataframe(res_df.style.applymap(lambda v: color_coding(v, 30), subset=['Score']))

    # --- Tab 5: Bulk Tests ---
    with tabs[4]:
        st.title("📋 Bulk Test Cases")
        up_tc = st.file_uploader("Upload CSV", type=['csv'], key="bulk_tc")
        if up_tc:
            df_tc = pd.read_csv(up_tc)
            df_tc.insert(0, "Select", True)
            edited_tc = st.data_editor(df_tc, hide_index=True, use_container_width=True)
            selected_tc = edited_tc[edited_tc["Select"] == True]
            if st.button(f"🚀 Process {len(selected_tc)} Tests"):
                results_tc = []
                bar_tc = st.progress(0)
                for k, (idx, row) in enumerate(selected_tc.iterrows()):
                    res = call_ai(f"Score Test: {row.iloc[1]}. Return ONLY JSON.")
                    results_tc.append({"Test Case": row.iloc[1], "Score": res.get('score', 0) if res else 0})
                    bar_tc.progress((k + 1) / len(selected_tc))
                res_tc_df = pd.DataFrame(results_tc)
                st.bar_chart(res_tc_df.set_index("Test Case")["Score"])
                st.dataframe(res_tc_df.style.applymap(lambda v: color_coding(v, 25), subset=['Score']))
