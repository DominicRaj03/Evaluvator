import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

# --- 1. Login & Professional Styling ---
def check_password():
    st.markdown("""
        <style>
        .login-container {
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            padding: 40px; background-color: #1E1E2E; border-radius: 15px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5); max-width: 400px; margin: auto;
        }
        .stTextInput > div > div > input { background-color: #2D2D44; color: white; border: 1px solid #3E3E5E; }
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
    # FIXED: Using 'gemini-1.5-flash-latest' to resolve the NotFound error
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as e:
        st.error(f"Configuration Error: {e}")

    def call_ai(prompt):
        try:
            response = model.generate_content(prompt)
            # Cleans common AI markdown wrapper if present
            clean = response.text.strip().replace('```json', '').replace('```', '')
            return json.loads(clean)
        except Exception as e:
            st.warning("The AI returned an unexpected format. Please try again.")
            return None

    # Sidebar Logout
    if st.sidebar.button("Log Out"):
        st.session_state["password_correct"] = False
        st.rerun()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📖 User Story", "🧪 Test Case", "📝 Generator", "📊 Bulk Stories", "📋 Bulk Tests"])

    # ============= TAB 1: USER STORY =============
    with tab1:
        st.title("📖 User Story Evaluator")
        us_text = st.text_area("Enter User Story", key="us_single", height=150)
        if st.button("Evaluate User Story", type="primary"):
            if us_text:
                with st.spinner("AI is evaluating..."):
                    prompt = f"""
                    Evaluate this User Story: '{us_text}'
                    Return ONLY valid JSON with:
                    "totalScore": (0-30), "grade": (string), "status": (string), 
                    "recommendation": (string), 
                    "invest": {{"Independent": 5, "Negotiable": 5, "Valuable": 5, "Estimable": 5, "Small": 5, "Testable": 5}}
                    """
                    data = call_ai(prompt)
                    if data:
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Total Score", f"{data['totalScore']}/30")
                        c2.metric("Grade", data['grade'])
                        c3.metric("Status", data['status'])
                        st.success(f"**Recommendation:** {data['recommendation']}")
                        
                        # Display INVEST Breakdown
                        st.subheader("INVEST Breakdown")
                        cols = st.columns(6)
                        for idx, (crit, score) in enumerate(data['invest'].items()):
                            cols[idx].metric(crit, f"{score}/5")

    # ============= TABS 4 & 5: SEARCH & BULK =============
    # (Including the search fix from our previous step)
    with tab4:
        st.title("📊 Bulk User Stories")
        up_us = st.file_uploader("Upload CSV", type=['csv'], key="up_us_bulk")
        if up_us:
            df = pd.read_csv(up_us)
            search = st.text_input("🔍 Live Search Stories", key="search_us")
            filtered_df = df[df.iloc[:,0].str.contains(search, case=False, na=False)] if search else df
            st.dataframe(filtered_df, use_container_width=True)
            
            if st.button("🚀 Process Visible Rows"):
                results = []
                bar = st.progress(0)
                for i, row in filtered_df.iterrows():
                    res = call_ai(f"Score Story: {row.iloc[0]}. Return JSON: {{'score': 10, 'note': 'text'}}")
                    results.append({"Story": row.iloc[0], "Score": res.get('score', 0) if res else "Error"})
                    bar.progress((i + 1) / len(filtered_df))
                st.write("Done!", pd.DataFrame(results))
