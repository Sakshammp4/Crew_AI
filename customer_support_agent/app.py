"""
Streamlit UI for Glowmart Customer Support Agent
Run with: streamlit run app.py
"""
import streamlit as st
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from customer_support_agent.main import run, is_valid_support_query

# Page config
st.set_page_config(
    page_title="Glowmart Support",
    page_icon="🛒",
    layout="centered"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "email_set" not in st.session_state:
    st.session_state.email_set = False

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    if not st.session_state.email_set:
        email = st.text_input("Enter your email:", placeholder="you@email.com")
        if st.button("Start Chat"):
            if email:
                st.session_state.user_email = email
            else:
                st.session_state.user_email = "guest@glowmart.in"
            st.session_state.email_set = True
            st.rerun()
    else:
        st.success(f"Email: {st.session_state.user_email}")
        if st.button("Reset / New Chat"):
            st.session_state.messages = []
            st.session_state.email_set = False
            st.rerun()

    st.divider()
    st.markdown("**Example questions:**")
    st.markdown("- What is your return policy?")
    st.markdown("- Where is my order ORD-8821?")
    st.markdown("- I received a broken item")

# Main chat area
st.title("🛒 Glowmart Customer Support")

if not st.session_state.email_set:
    st.info("👈 Please enter your email in the sidebar to start chatting.")
else:
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Check guardrail first (fast, no LLM cost)
        is_valid, fallback = is_valid_support_query(prompt)

        with st.chat_message("assistant"):
            if not is_valid:
                # Guardrail blocked - instant response, no LLM cost
                st.info("🛡️ Guardrail: This doesn't look like a support question.")
                st.markdown(fallback)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": fallback
                })
            else:
                # Valid query - run full agent with spinner
                with st.spinner("Thinking..."):
                    try:
                        result = run(prompt, st.session_state.user_email)

                        # Extract response text
                        try:
                            parsed = json.loads(str(result))
                            response_text = parsed.get("response", str(result))
                        except:
                            response_text = str(result)

                        st.markdown(response_text)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response_text
                        })

                    except Exception as e:
                        error_msg = f"Sorry, an error occurred: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })
