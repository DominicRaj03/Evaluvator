import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
import re
import time

# --- 1. UI & Results Styling ---
def apply_styles():
    st.markdown("""
        <style>
        .status-header { display: flex; align-items: center; justify-content: space-between; padding: 10px; background: #262730; border-radius: 8px; margin-bottom: 20px; }
        .main-card { background-color: #1E1E2E; padding: 20px; border-radius: 10px; border: 1px solid #3E3E5E; }
        </style>
    """, unsafe_allow_html=True)

def color_scores(val):
    """Applies green for high scores and red for low scores."""
    color = '#2ecc71' if val >= 20 else '#e74c3c' if val < 10 else '#f1c40f'
    return f'background-color: {color}; color: black; font-weight: bold'

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

# --- 2. AI Logic (Optimized for JSON Response) ---
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
            chat = client.chat.completions.create(
                messages=[{"role":"user","content":prompt}], 
                model=model_name
            )
            text = chat.choices[0].message.content.strip()

        # Extract JSON from potential AI conversational filler
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else json.loads(text)
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

# --- 3. Main App ---
st.set_page_config(page_title="Jarvis Evaluator", layout="wide")
apply_styles()

if check_password():
    with st.sidebar:
        st.title("⚙️ Control Panel")
        provider = st.radio("AI Provider", ["Gemini", "Groq"])
        models = ["gemini-1.5-flash-latest", "gemini-1.5-pro-latest"] if provider == "Gemini" else ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]
        selected_model = st.selectbox("Model", models)
        if st.button("🗑️ Reset App"): st.session_state.clear(); st.rerun()

    st.markdown(f'<div class="status-header"><h2>🎯 Jarvis Results Dashboard</h2><b>Active: {selected_model}</b></div>', unsafe_allow_html=True)

    tabs = st.tabs(["📖 User Stories", "🧪 Test Cases"])

    # Shared logic for both tabs to ensure consistent result formatting
    for i, tab_name in enumerate(["Story", "Test Case"]):
        with tabs[i]:
            up = st.file_uploader(f"Upload {tab_name} CSV", type=['csv'], key=f"up_{i}")
            if up:
                df = pd.read_csv(up)
                st.write(f"Previewing {len(df)} items:")
                edited_df = st.data_editor(df, use_container_width=True, key=f"editor_{i}")
                
                if st.button(f"🚀 Evaluate All {tab_name}s", key=f"btn_{i}"):
                    results = []
                    progress = st.progress(0)
                    for index, row in edited_df.iterrows():
                        content = row.iloc[0] # Assuming first column is the text
                        prompt = f"Evaluate the following {tab_name}: '{content}'. Return ONLY a JSON object with keys 'score' (0-30) and 'findings' (brief string)."
                        
                        out = call_ai(prompt, provider, selected_model)
                        results.append({
                            tab_name: content,
                            "Score": out.get("score", 0) if out else 0,
                            "Findings & Recommendations": out.get("findings", "Error processing") if out else "Failed"
                        })
                        progress.progress((index + 1) / len(edited_df))
                    
                    # --- DASHBOARD RESULTS VIEW ---
                    res_df = pd.DataFrame(results)
                    st.subheader(f"📊 {tab_name} Evaluation Summary")
                    
                    # Apply conditional formatting to the Score column
                    styled_res = res_df.style.applymap(color_scores, subset=['Score'])
                    
                    st.dataframe(styled_res, use_container_width=True, hide_index=True)
                    st.download_button("📥 Export Results", res_df.to_csv(index=False), f"{tab_name}_results.csv")
