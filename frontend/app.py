import streamlit as st
import requests

st.title("Travel Chatbot")

# FastAPI backend URL
API_URL = "http://localhost:8000/chat"  # Update this if deployed remotely

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input box
if prompt := st.chat_input("Ask me about your trip..."):
    # Show user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Send to FastAPI backend
    try:
        response = requests.post(API_URL, json={"message": prompt})
        response.raise_for_status()
        bot_reply = response.json()["reply"]
    except Exception as e:
        bot_reply = f"Error: {str(e)}"

    # Show assistant message
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})