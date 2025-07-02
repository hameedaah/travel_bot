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
# Custom styling
st.markdown("""
    <style>
            .st-emotion-cache-1nwdr1w a {
    color: black;
    text-decoration: none;
    cursor: pointer;
    text-align: center;
}

.st-emotion-cache-1nwdr1w a:hover {
    color: #edab24; 
    text-decoration: underline;
    transition: color 0.3s ease;
}
    

    
.centered-intro {
    height: 75vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
}
.intro-title {
    font-size: 3.3em;
    margin-bottom: 0.3em;
}
.intro-subtitle {
    font-size: 1.2em;
    max-width: 500px;
    color: #333;
}
.intro-note {
    font-size: 1.0em;
    color: gray;
    margin-top: 0.5em;
}
    
.st-emotion-cache-ajtf3x {
    display: flex;
    justify-content: left;
    align-items: center;
    margin-bottom: 40px;
}

.st-emotion-cache-sd8pwa, .st-emotion-cache-1knad0q {
    width: auto;
    flex: 0 0 auto;
}

.st-emotion-cache-1nwdr1w h1 {
    line-height: 0px;
    padding: 0px;
    padding-bottom: 10px;
}

.st-emotion-cache-1knad0q {
    display: flex;
    justify-content: left;
    align-items: center;
    height: 70px;
}
        
.stVerticalBlock st-emotion-cache-gsx7k2 eertqu03{
    height: 100%;
}
    
.centered-intro {
    height: auto;
}
    
.st-emotion-cache-1cei9z1{
    padding: 3rem 2rem 2rem;
}

.st-emotion-cache-7czcpc > img {
    border-radius: 50%;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    object-fit: cover;
    width: 70px !important;
    height: 70px !important;
}
    
button.st-emotion-cache-1rwb540  {
    background-color: #edab24;
    color: white;
    border: none;
    padding: 10px;
    border-radius: 10px;
    cursor: pointer;
    font-weight: bold;
    font-size: 30px;
}



button.st-emotion-cache-1rwb540:hover {
    background-color: white;
    color: #edab24;
    border: 2px solid #edab24;
    box-shadow: 0 4px 10px rgba(237, 171, 36, 0.4);
    transition: all 0.3s ease;
}

    
@media (max-width: 768px) {    
    .st-emotion-cache-ajtf3x {
        display: block;
    }

    .st-emotion-cache-ajtf3x > div{
        margin: 0 auto 32px;
    }
        
    .st-emotion-cache-ajtf3x  div.st-emotion-cache-1cyexbd, .st-emotion-cache-ajtf3x  div.st-emotion-cache-8atqhb, .st-emotion-cache-ajtf3x  div.st-emotion-cache-1nwdr1w {
        width: auto;
        display: flex;
        justify-content: center;
    }
      
    .st-emotion-cache-7czcpc > img {
    width: 100px !important;
    height: 100px !important;
    }
        
    .st-emotion-cache-1nwdr1w h1 {
        font-size: 36px;
    }
        
    button.st-emotion-cache-1rwb540  {
        padding: 10px 15px;
        font-size: 40px;
    }
}
</style>
""", unsafe_allow_html=True)

# with open("styles.css") as f:
#     st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

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