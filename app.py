import streamlit as st
from PIL import Image
import requests
import os
import uuid

st.session_state.setdefault("session_id", str(uuid.uuid4()))

st.set_page_config(page_title="WanderBot", page_icon=":luggage:")

st.sidebar.title("Explore WanderBot")


if "current_page" not in st.session_state:
    st.session_state.current_page = "Chat with WanderBot"

if st.sidebar.button("Chat with WanderBot"):
    st.session_state.current_page = "Chat with WanderBot"

if st.sidebar.button("Weather-Based Trip Guide"):
    st.session_state.current_page = "Weather Based Trip Guide"

page = st.session_state.current_page



# Read and apply custom CSS
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# API URL
API_URL = os.getenv("FASTAPI_URL", "http://localhost:8000/chat")

# Initialize chat history
st.session_state.setdefault("messages", [])
st.session_state.setdefault("show_intro", True)

#Header Columns
with st.container():
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
        if st.session_state.messages:
            if st.button("Clear Conversation", help="Delete all messages", key="clear-btn"):
                st.session_state.messages.clear()
                st.session_state.session_id = str(uuid.uuid4())
                st.rerun()
            else:
                st.empty() 


# Chat input
if page == "Chat with WanderBot":     
    # Show existing chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask me travel-related questions…")

    if prompt:
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("WanderBot is thinking... 💭"):
            try:
                response = requests.post(API_URL, json={
                "session_id": st.session_state.session_id,
                "message": prompt
                })

                response.raise_for_status()
                bot_reply = response.json().get("reply", "No reply.")
            except Exception:
                bot_reply = "WanderBot ran into an issue. Please try again later."

        st.chat_message("assistant").markdown(bot_reply)
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        st.rerun()

    # If no chats yet, show intro in center
    if not st.session_state.messages:
        st.markdown("""
            <div class="centered-intro">
                <div class="intro-title">👋 Hi, I'm <span style="color:#78afa5;">WanderBot</span></div>
                <div class="intro-subtitle">
                    Your friendly travel companion. I can help you plan trips, give you travel tips tailored to your destination and any other travel related information.
                </div>
                <div class="intro-note">
                    Just tell me where you're going, and I'll help you get there! ✈️
                </div>
            </div>
        """, unsafe_allow_html=True)

#Weather Form
elif page == "Weather Based Trip Guide":
    st.markdown("### 🌦️ Adapt Your Trip Plan to the Weather")

    with st.form("trip_planner_form"):
        city = st.text_input("Enter the city")
        country = st.text_input("Enter the country")

        from datetime import date
        today = date.today()
        start_date = st.date_input("Start Date", min_value=today)
        end_date = st.date_input("End Date", min_value=start_date)

        submit = st.form_submit_button("Get Suggestions")

    if submit and city and country:
        message = (
        f"I'm planning a trip to {city}, {country} from "
        f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}. "
        "Please check the weather forecast for those dates and use it to recommend suitable activities. "
        "For example, if the weather is mostly sunny, Recommend ideas for outdoor sightseeing, parks, or walking tours. "
        "If it is likely to rain or be very cold, suggest indoor options like museums, food experiences, or cultural attractions. "
        "Let me know the places in the city where I can find these activities."
        "Also let me know what I should pack based on the expected weather."
        )


        with st.spinner("WanderBot is planning your trip..."):
            try:
                response = requests.post(API_URL, json={
                    "session_id": st.session_state.session_id,
                    "message": message
                })
                response.raise_for_status()
                bot_reply = response.json().get("reply", "No reply.")
            except Exception:
                bot_reply = "WanderBot ran into an issue. Please try again later."

        st.markdown("### ✈️ Here's your travel insight:")
        st.success(bot_reply)
