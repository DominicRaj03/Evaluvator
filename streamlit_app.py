import streamlit as st
import pandas as pd
import google.generativeai as genai
import json
from io import BytesIO

# --- Configuration & AI Setup ---
st.set_page_config(page_title="US Evaluator", layout="wide")

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # Using the most stable model string
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except Exception as e:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets!")

def call_gemini_ai(prompt):
    try:
        response = model.generate_content(prompt)
        # Clean the response to ensure it's pure JSON
        raw_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(raw_text)
    except Exception as e:
        st.error(f"AI Error: {str(e)}")
        return None

# --- UI Layout ---
st.sidebar.title("🎯 US Evaluator")
st.sidebar.info("Integrated AI Mode Active")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📖 User Story", "🧪 Test Case", "📝 Generator", "📊 Bulk Stories", "📋 Bulk Tests"
])

# ============= TAB 1: USER STORY =============
with tab1:
    st.title("📖 User Story Evaluator")
    user_story = st.text_area("Enter User Story", key="us_main_input")
    
    if st.button("🚀 Evaluate", key="btn_us"):
        if user_story:
            prompt = f"Analyze this User Story based on INVEST criteria: '{user_story}'. Return ONLY a JSON with: totalScore(30), grade, status, executiveSummary(dict with readinessScore, recommendation), parameters(list of dicts with name, score, finding)."
            data = call_gemini_ai(prompt)
            if data:
                c1, c2, c3 = st.columns(3)
                c1.metric("Score", f"{data.get('totalScore')}/30")
                c2.metric("Grade", data.get('grade'))
                c3.metric("Readiness", f"{data.get('executiveSummary', {}).get('readinessScore')}%")
                st.success(data.get('executiveSummary', {}).get('recommendation'))
                
                for p in data.get('parameters', []):
                    with st.expander(f"{p['name']} - {p['score']}/5"):
                        st.write(p['finding'])

# ============= TAB 2: TEST CASE =============
with tab2:
    st.title("🧪 Test Case Evaluator")
    tc_input = st.text_area("Enter Test Case", key="tc_main_input")
    if st.button("🚀 Evaluate TC", key="btn_tc"):
        prompt = f"Evaluate this Test Case for quality: '{tc_input}'. Return ONLY JSON with totalScore(25), status, and parameters(list with name, score, finding)."
        data = call_gemini_ai(prompt)
        if data:
            st.metric("Quality Score", f"{data.get('totalScore')}/25")
            st.table(data.get('parameters'))

# ============= TAB 3: GENERATOR =============
with tab3:
    st.title("📝 Test Case Generator")
    feat = st.text_area("Feature Description", key="gen_input")
    if st.button("✨ Generate", key="btn_gen"):
        prompt = f"Generate 3 test cases for: '{feat}'. Return ONLY JSON: {{'testCases': [{{'name', 'steps', 'expected'}}]}}"
        data = call_gemini_ai(prompt)
        if data:
            for tc in data.get('testCases', []):
                with st.expander(tc['name']):
                    st.write(tc['steps'])
                    st.write(f"**Expected:** {tc['expected']}")

# ============= TAB 4 & 5: BULK (Placeholders) =============
with tab4:
    st.title("📊 Bulk Stories")
    st.file_uploader("Upload CSV", type=['csv'], key="bulk_us")

with tab5:
    st.title("📋 Bulk Tests")
    st.file_uploader("Upload CSV", type=['csv'], key="bulk_tc")
