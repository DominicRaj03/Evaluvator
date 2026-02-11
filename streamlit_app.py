import streamlit as st
import requests
import pandas as pd
from io import BytesIO
import time

st.set_page_config(page_title="US Evaluator", layout="wide", initial_sidebar_state="expanded")

# Configure backend URL from secrets
BACKEND_URL = st.secrets.get("BACKEND_URL", "http://localhost:5000")

# Custom CSS
st.markdown("""
<style>
    .main { padding: 2rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 2rem; }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🎯 US Evaluator")
st.sidebar.markdown("---")
st.sidebar.markdown("**AI-Powered Quality Assessment**")

# Navigation
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📖 User Story", 
    "🧪 Test Case", 
    "📝 Generator", 
    "📊 Bulk Stories",
    "📋 Bulk Tests"
])

# ============= TAB 1: USER STORY EVALUATOR =============
with tab1:
    st.title("📖 User Story Evaluator")
    st.markdown("Evaluate user stories using **INVEST** criteria (Independent, Negotiable, Valuable, Estimable, Small, Testable)")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        user_story = st.text_area(
            "Enter User Story",
            height=200,
            placeholder="As a [role], I want [feature] so that [benefit]...",
            key="us_input"
        )
    with col2:
        st.metric("Characters", len(user_story))
    
    if st.button("🚀 Evaluate User Story", use_container_width=True, type="primary"):
        if user_story.strip():
            with st.spinner("🔍 Analyzing your user story..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/evaluate",
                        json={"userStory": user_story},
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Score Display
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("📊 Total Score", f"{data.get('totalScore', 0)}/30")
                        with col2:
                            st.metric("⭐ Grade", data.get('grade', 'N/A'))
                        with col3:
                            st.metric("🎯 Status", data.get('status', 'N/A'))
                        with col4:
                            exec_summary = data.get('executiveSummary', {})
                            st.metric("📈 Readiness", f"{exec_summary.get('readinessScore', 0)}%")
                        
                        # Executive Summary
                        st.subheader("📋 Executive Summary")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(f"**Business Alignment:** {exec_summary.get('businessAlignment', 'N/A')}")
                        with col2:
                            st.warning(f"**Risk Profile:** {exec_summary.get('riskProfile', 'N/A')}")
                        
                        st.success(f"**Recommendation:** {exec_summary.get('recommendation', 'N/A')}")
                        
                        # INVEST Criteria
                        st.subheader("🎯 INVEST Criteria Breakdown")
                        if 'parameters' in data:
                            cols = st.columns(len(data['parameters']))
                            for idx, param in enumerate(data['parameters']):
                                with cols[idx]:
                                    score = param.get('score', 0)
                                    name = param.get('name', 'N/A')
                                    st.metric(
                                        name,
                                        f"{score}/5",
                                        delta=f"{int((score/5)*100)}%"
                                    )
                        
                        # Detailed Findings
                        st.subheader("💡 Detailed Analysis")
                        for param in data.get('parameters', []):
                            with st.expander(f"📌 {param.get('name', 'N/A')}"):
                                st.write(param.get('finding', 'No findings'))
                        
                        # Improvement Recommendations
                        st.subheader("✨ Improvement Recommendations")
                        if 'improvementRecommendations' in data:
                            for key, value in data['improvementRecommendations'].items():
                                st.write(f"**{key}:** {value}")
                    else:
                        st.error(f"❌ Error: {response.json().get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Connection Error: {str(e)}")
        else:
            st.warning("⚠️ Please enter a user story")

# ============= TAB 2: TEST CASE EVALUATOR =============
with tab2:
    st.title("🧪 Test Case Evaluator")
    st.markdown("Evaluate test cases for **Clarity, Traceability, Accuracy, Completeness, and Coverage**")
    
    test_case = st.text_area(
        "Enter Test Case",
        height=250,
        placeholder="Test Case Name: Login\nSteps: 1) Enter credentials\nExpected Result: User logged in\nPrecondition: Account exists",
        key="tc_input"
    )
    
    if st.button("🚀 Evaluate Test Case", use_container_width=True, type="primary"):
        if test_case.strip():
            with st.spinner("🔍 Analyzing your test case..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/evaluate-test-case",
                        json={"testCase": test_case},
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Score Display
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("📊 Quality Score", f"{data.get('totalScore', 0)}/25")
                        with col2:
                            st.metric("🎯 Status", data.get('status', 'N/A'))
                        with col3:
                            st.metric("✅ Grade", "Pass" if data.get('totalScore', 0) >= 18 else "Needs Work")
                        
                        # Criteria Breakdown
                        st.subheader("📊 Evaluation Criteria")
                        criteria_data = []
                        for param in data.get('parameters', []):
                            criteria_data.append({
                                'Criterion': param.get('name', 'N/A'),
                                'Score': f"{param.get('score', 0)}/5",
                                'Finding': param.get('finding', 'N/A')
                            })
                        
                        if criteria_data:
                            df = pd.DataFrame(criteria_data)
                            st.dataframe(df, use_container_width=True)
                        
                        # Health Metrics
                        st.subheader("💚 Health Score Metrics")
                        if 'healthMetrics' in data:
                            health_data = []
                            for metric in data['healthMetrics']:
                                health_data.append({
                                    'Metric': metric.get('name', 'N/A'),
                                    'Target': metric.get('target', 'N/A'),
                                    'Actual': f"{metric.get('actual', 0)}%",
                                    'Status': '✅ Met' if metric.get('metTarget') else '❌ Not Met'
                                })
                            df_health = pd.DataFrame(health_data)
                            st.dataframe(df_health, use_container_width=True)
                    else:
                        st.error(f"❌ Error: {response.json().get('error', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Connection Error: {str(e)}")
        else:
            st.warning("⚠️ Please enter a test case")

# ============= TAB 3: TEST CASE GENERATOR =============
with tab3:
    st.title("📝 Test Case Generator")
    
    mode = st.radio("Select Generation Mode", ["✍️ From Text", "📸 From Mockup"], horizontal=True)
    
    if mode == "✍️ From Text":
        st.markdown("Generate test cases from feature descriptions")
        feature_desc = st.text_area(
            "Feature/Functionality Description",
            height=200,
            placeholder="Describe the feature in detail...",
            key="gen_text"
        )
        
        if st.button("✨ Generate Test Cases", use_container_width=True, type="primary"):
            if feature_desc.strip():
                with st.spinner("🤖 Generating test cases..."):
                    try:
                        response = requests.post(
                            f"{BACKEND_URL}/generate-test-cases",
                            json={"feature": feature_desc},
                            timeout=60
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"✅ Generated {len(data.get('testCases', []))} test cases")
                            
                            for i, tc in enumerate(data.get('testCases', []), 1):
                                with st.expander(f"**TC {i}: {tc.get('name', 'N/A')}**"):
                                    st.write(f"**Precondition:** {tc.get('precondition', 'N/A')}")
                                    st.write(f"**Steps:**\n{tc.get('steps', 'N/A')}")
                                    st.write(f"**Expected Result:** {tc.get('expectedResult', 'N/A')}")
                                    st.write(f"**Postcondition:** {tc.get('postcondition', 'N/A')}")
                            
                            # Download as CSV
                            csv_data = []
                            for tc in data.get('testCases', []):
                                csv_data.append({
                                    'Name': tc.get('name', ''),
                                    'Precondition': tc.get('precondition', ''),
                                    'Steps': tc.get('steps', ''),
                                    'Expected': tc.get('expectedResult', ''),
                                    'Postcondition': tc.get('postcondition', '')
                                })
                            df = pd.DataFrame(csv_data)
                            st.download_button(
                                "📥 Download as CSV",
                                df.to_csv(index=False),
                                "test_cases.csv",
                                "text/csv"
                            )
                        else:
                            st.error(f"❌ Error: {response.json().get('error', 'Failed to generate')}")
                    except Exception as e:
                        st.error(f"❌ Connection Error: {str(e)}")
            else:
                st.warning("⚠️ Please enter a feature description")
    
    else:  # From Mockup
        st.markdown("Generate test cases from UI mockups/screenshots")
        
        col1, col2 = st.columns(2)
        with col1:
            uploaded_image = st.file_uploader("Upload Mockup Image", type=['png', 'jpg', 'jpeg', 'gif', 'webp'])
            if uploaded_image:
                st.image(uploaded_image, caption="Uploaded Mockup", use_column_width=True)
        
        with col2:
            mockup_desc = st.text_area(
                "Describe the Mockup",
                height=200,
                placeholder="Describe UI elements, fields, buttons, flows...",
                key="gen_image"
            )
        
        if st.button("✨ Generate from Mockup", use_container_width=True, type="primary"):
            if uploaded_image and mockup_desc.strip():
                with st.spinner("🤖 Analyzing mockup and generating test cases..."):
                    try:
                        files = {'image': uploaded_image.getvalue()}
                        data = {'description': mockup_desc}
                        
                        response = requests.post(
                            f"{BACKEND_URL}/generate-test-cases-from-image",
                            files=files,
                            data=data,
                            timeout=60
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success(f"✅ Generated {len(result.get('testCases', []))} test cases from mockup")
                            
                            for i, tc in enumerate(result.get('testCases', []), 1):
                                with st.expander(f"**TC {i}: {tc.get('name', 'N/A')}**"):
                                    st.write(f"**Precondition:** {tc.get('precondition', 'N/A')}")
                                    st.write(f"**Steps:**\n{tc.get('steps', 'N/A')}")
                                    st.write(f"**Expected:** {tc.get('expectedResult', 'N/A')}")
                        else:
                            st.error(f"❌ Error: {response.json().get('error', 'Failed to generate')}")
                    except Exception as e:
                        st.error(f"❌ Connection Error: {str(e)}")
            else:
                st.warning("⚠️ Please upload an image and provide a description")

# ============= TAB 4: BULK USER STORY =============
with tab4:
    st.title("📊 Bulk User Story Evaluator")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Download Excel Template", use_container_width=True):
            template_df = pd.DataFrame({
                'userStory': [
                    'As a user, I want to log in with email and password so that I can access my account',
                    'As a user, I want to reset my password so that I can regain access if forgotten'
                ]
            })
            
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                template_df.to_excel(writer, sheet_name='User Stories', index=False)
            buffer.seek(0)
            
            st.download_button(
                "Click to Download",
                buffer.getvalue(),
                "user_story_template.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col2:
        st.markdown("**Upload CSV or Excel file**")
    
    uploaded_file = st.file_uploader("Choose file", type=['xlsx', 'xls', 'csv'], key="bulk_us")
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file) if uploaded_file.type != 'text/csv' else pd.read_csv(uploaded_file)
            
            if 'userStory' not in df.columns:
                st.error("❌ Missing 'userStory' column")
            else:
                st.success(f"✅ {len(df)} user stories found")
                
                if st.button("🚀 Evaluate All", use_container_width=True, type="primary"):
                    progress_bar = st.progress(0)
                    results = []
                    
                    for idx, row in df.iterrows():
                        try:
                            response = requests.post(
                                f"{BACKEND_URL}/evaluate",
                                json={"userStory": row['userStory']},
                                timeout=60
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                result['userStory'] = row['userStory'][:50]
                                result['status'] = '✅ Success'
                            else:
                                result = {'userStory': row['userStory'][:50], 'status': '❌ Failed', 'totalScore': 'N/A'}
                            
                            results.append(result)
                        except:
                            results.append({'userStory': row['userStory'][:50], 'status': '⚠️ Error', 'totalScore': 'N/A'})
                        
                        progress_bar.progress((idx + 1) / len(df))
                    
                    results_df = pd.DataFrame(results)
                    st.dataframe(results_df[['userStory', 'totalScore', 'status']], use_container_width=True)
                    
                    csv = results_df.to_csv(index=False)
                    st.download_button("📥 Download Results", csv, "results.csv", "text/csv")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

# ============= TAB 5: BULK TEST CASES =============
with tab5:
    st.title("📋 Bulk Test Case Evaluator")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Download Excel Template", use_container_width=True):
            template_df = pd.DataFrame({
                'testCase': [
                    'Test: Login Valid\nSteps: 1) Enter email 2) Enter password 3) Click login\nExpected: Logged in',
                    'Test: Login Invalid\nSteps: 1) Enter wrong password 2) Click login\nExpected: Error shown'
                ]
            })
            
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                template_df.to_excel(writer, sheet_name='Test Cases', index=False)
            buffer.seek(0)
            
            st.download_button(
                "Click to Download",
                buffer.getvalue(),
                "test_case_template.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    uploaded_file = st.file_uploader("Choose file", type=['xlsx', 'xls', 'csv'], key="bulk_tc")
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file) if uploaded_file.type != 'text/csv' else pd.read_csv(uploaded_file)
            
            if 'testCase' not in df.columns:
                st.error("❌ Missing 'testCase' column")
            else:
                st.success(f"✅ {len(df)} test cases found")
                
                if st.button("🚀 Evaluate All", use_container_width=True, type="primary"):
                    progress_bar = st.progress(0)
                    results = []
                    
                    for idx, row in df.iterrows():
                        try:
                            response = requests.post(
                                f"{BACKEND_URL}/evaluate-test-case",
                                json={"testCase": row['testCase']},
                                timeout=60
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                result['testCase'] = row['testCase'][:50]
                                result['status'] = '✅ Success'
                            else:
                                result = {'testCase': row['testCase'][:50], 'status': '❌ Failed', 'totalScore': 'N/A'}
                            
                            results.append(result)
                        except:
                            results.append({'testCase': row['testCase'][:50], 'status': '⚠️ Error', 'totalScore': 'N/A'})
                        
                        progress_bar.progress((idx + 1) / len(df))
                    
                    results_df = pd.DataFrame(results)
                    st.dataframe(results_df[['testCase', 'totalScore', 'status']], use_container_width=True)
                    
                    csv = results_df.to_csv(index=False)
                    st.download_button("📥 Download Results", csv, "results.csv", "text/csv")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
