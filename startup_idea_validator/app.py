#!/usr/bin/env python
import sys
import os
# Add src directory to Python path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import streamlit as st
from io import StringIO
from startup_idea_validator.crew import StartupIdeaValidator
from dotenv import load_dotenv
import os
import re

load_dotenv()

st.set_page_config(
    page_title="Startup Idea Validator",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 Startup Idea Validator")
st.markdown("Enter your startup idea and our AI agents will analyze it for you.")

# Initialize session state
if 'running' not in st.session_state:
    st.session_state.running = False
if 'result' not in st.session_state:
    st.session_state.result = None
if 'logs' not in st.session_state:
    st.session_state.logs = []

# Input section
idea = st.text_area(
    "💡 Your Startup Idea (max 500 chars to avoid rate limits)",
    placeholder="e.g., I want to build an app that converts Instagram reels into structured notes for content creators...",
    height=100,
    max_chars=500
)

if idea and len(idea) > 500:
    st.warning("⚠️ Idea too long! Keep it under 500 characters to avoid rate limits.")

col1, col2 = st.columns([1, 4])
with col1:
    run_button = st.button("🚀 Validate Idea", type="primary", disabled=st.session_state.running)

# Progress tracking placeholder
status_placeholder = st.empty()
progress_placeholder = st.empty()

# Results section
if st.session_state.result:
    st.success("✅ Analysis Complete!")
    
    # Display final score prominently
    result_text = st.session_state.result.raw if hasattr(st.session_state.result, 'raw') else str(st.session_state.result)
    
    # Try to extract score
    score_match = re.search(r'(\d+(?:\.\d+)?)\s*/\s*10', result_text)
    
    if score_match:
        score = float(score_match.group(1))
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.metric("Final Score", f"{score}/10")
            if score >= 7:
                st.success("🟢 Good Idea - Worth Pursuing!")
            elif score >= 5:
                st.warning("🟡 Average Idea - Needs Refinement")
            else:
                st.error("🔴 Weak Idea - Consider Pivoting")
    
    # Tabs for different outputs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Final Report", "💡 Idea Analysis", "🔍 Market Analysis", "👤 Customer Research"])
    
    output_dir = "output"
    
    with tab1:
        st.markdown("### Final Validation Report")
        st.markdown(result_text)
    
    with tab2:
        file_path = os.path.join(output_dir, "01_idea_analysis.md")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                st.markdown(f.read())
        else:
            st.info("Idea analysis output not found. Check output directory.")
    
    with tab3:
        file_path = os.path.join(output_dir, "02_market_analysis.md")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                st.markdown(f.read())
        else:
            st.info("Market analysis output not found.")
    
    with tab4:
        file_path = os.path.join(output_dir, "03_customer_research.md")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                st.markdown(f.read())
        else:
            st.info("Customer research output not found.")

# Run the crew when button is clicked
if run_button and idea:
    st.session_state.running = True
    st.session_state.result = None
    
    try:
        inputs = {'idea': idea}
        
        # Show initial status
        with status_placeholder.container():
            st.info("🤖 Starting AI Agents...")
        
        # Create progress indicators
        with progress_placeholder.container():
            agent_status = st.empty()
            agent_status.text("🧠 Idea Analyst: Analyzing your startup idea...")
        
        # Run the crew
        result = StartupIdeaValidator().crew().kickoff(inputs=inputs)
        
        st.session_state.result = result
        st.session_state.running = False
        
        # Clear progress
        status_placeholder.empty()
        progress_placeholder.empty()
        
        st.rerun()
        
    except Exception as e:
        st.session_state.running = False
        status_placeholder.empty()
        progress_placeholder.empty()
        
        error_msg = str(e)
        if "RateLimitError" in error_msg or "rate_limit_exceeded" in error_msg:
            st.error("""
            ❌ **Rate Limit Hit!**
            
            OpenAI has rate limits. Your idea was too long or too many requests.
            
            **Fix:** 
            - Shorten your idea (keep under 300 characters)
            - Wait 60 seconds and try again
            - Check your OpenAI billing at https://platform.openai.com/settings/billing
            - Or switch to a different model in your .env file
            """)
        else:
            st.error(f"❌ Error: {e}")

# Verbose logs section
with st.expander("🔧 Verbose Logs (Agent Activity)", expanded=False):
    st.info("Run validation to see agent activity.")
    st.markdown("""
    **Agent Flow:**
    1. 🧠 **Idea Analyst** - Breaks down your idea into problem, user, and validation
    2. 🔍 **Market Analyst** - Researches competitors and market gaps
    3. 👤 **Customer Insight** - Creates interview questions for validation
    4. ⚖️ **Final Decision** - Combines all insights and gives score
    """)

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using CrewAI + Streamlit")
