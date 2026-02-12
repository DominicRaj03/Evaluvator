import streamlit as st
import pandas as pd
import google.generativeai as genai
import json

# Setup Gemini
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("API Key missing! Add GEMINI_API_KEY to Streamlit Secrets.")

# --- Real Logic Function ---
def evaluate_with_ai(prompt_type, input_text):
    prompt = f"""
    Analyze the following {prompt_type}: "{input_text}"
    Provide a JSON response with:
    - totalScore (0-30)
    - grade (A to F)
    - status (Ready/Not Ready)
    - readinessScore (0-100)
    - recommendation (text)
    - parameters (list of name, score 1-5, and finding) based on INVEST criteria.
    Only return valid JSON.
    """
    
    response = model.generate_content(prompt)
    # Extract JSON from response text
    try:
        cleaned_json = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned_json)
    except:
        return None

# --- UI Snippet for Tab 1 ---
st.title("📖 User Story Evaluator")
user_story = st.text_area("Enter User Story", key="us_input")

if st.button("🚀 Evaluate", type="primary"):
    if user_story:
        with st.spinner("AI is thinking..."):
            data = evaluate_with_ai("User Story", user_story)
            if data:
                # This will now change every time based on your input!
                st.metric("Total Score", f"{data['totalScore']}/30")
                st.write(data['recommendation'])
                st.json(data) # To see the full dynamic breakdown
            else:
                st.error("AI failed to format the response. Try again.")
