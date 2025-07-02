import streamlit as st
from PIL import Image
import requests
import os

st.set_page_config(page_title="WanderBot", page_icon=":luggage:")

st.markdown("""
    <div class="github-link">
        <a href="https://github.com/hameedaah/travel_bot" target="_blank" >
            View Project on GitHub
        </a>
    </div>
""", unsafe_allow_html=True)


# Read and apply custom CSS
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# API URL
API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000/chat")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_intro" not in st.session_state:
    st.session_state.show_intro = True

#Header Columns
col1, col2, col3 = st.columns([1, 6, 3])
with col1:
    logo = Image.open("images/Wander_bot_logo.png")
    st.image(logo, width=30, use_container_width= True) 
with col2:
    st.markdown(
        """
        <div style="display: flex; align-items: center; justify-content: left; gap: 0px;">
            <h1 style="margin-bottom: 0;">WanderBot</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
with col3:
    if st.button("Clear Conversation", help="Delete all messages"):
        st.session_state.messages.clear()
        st.rerun()


# Show existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
prompt = st.chat_input("Ask me travel-related questions…")

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("WanderBot is thinking... 💭"):
        try:
            response = requests.post(API_URL, json={
                "message": prompt,
                "history": st.session_state.messages
            })
            response.raise_for_status()
            bot_reply = response.json().get("reply", "No reply.")
        except Exception as e:
            bot_reply = "WanderBot ran into an issue. Please try again later."

    st.chat_message("assistant").markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})

# If no chats yet, show intro in center
if len(st.session_state.messages) == 0:
    st.markdown("""
        <div class="centered-intro">
            <div class="intro-title">👋 Hi, I'm <span style="color:#edab24;">WanderBot</span></div>
            <div class="intro-subtitle">
                Your friendly travel companion. I can help you plan trips, give you travel tips tailored to your destination and any other travel related information.
            </div>
            <div class="intro-note">
                Just tell me where you're going, and I'll help you get there! ✈️
            </div>
        </div>
    """, unsafe_allow_html=True)