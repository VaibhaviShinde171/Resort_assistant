import streamlit as st
from streamlit_mic_recorder import mic_recorder
import base64
import tempfile
from openai import OpenAI
from agents import run_agent
import os

# ---------------------- OPENAI CLIENT ----------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(
    page_title="Resort AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------- BACKGROUND IMAGE ----------------------
def set_background(image_path):
    with open(image_path, "rb") as img_file:
        encoded_str = base64.b64encode(img_file.read()).decode()

    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/jpg;base64,{encoded_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .main-block {{
        background: rgba(255, 255, 255, 0.55);
        backdrop-filter: blur(12px);
        padding: 25px;
        border-radius: 18px;
        margin-top: 20px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.25);
    }}
    h2 {{
    color: #ffffff !important; 
    text-shadow: 0px 0px 6px rgba(0,0,0,0.8);
     }}

     label[data-testid="stWidgetLabel"] {{
    color: #ffffff !important;
    font-size: 20px !important;
    font-weight: 600 !important;
    text-shadow: 0 0 8px rgba(0,0,0,0.7);
    }}
    .chat-bubble {{
        padding: 14px;
        margin: 12px 0;
        border-radius: 16px;
        max-width: 70%;
        backdrop-filter: blur(4px);
    }}
    .user-bubble {{
        background: rgba(0, 140, 255, 0.40);
        color: white;
        margin-left: auto;
    }}
    .ai-bubble {{
        background: rgba(255, 255, 255, 0.70);
        color: black;
        margin-right: auto;
    }}
    [data-testid="stSidebar"] {{
        background: rgba(255,255,255,0.6);
        backdrop-filter: blur(10px);
    }}
    
    </style>
    """, unsafe_allow_html=True)

set_background("assets/my_image.jpg")

# ---------------------- SESSION STATE ----------------------
if "chat" not in st.session_state:
    st.session_state.chat = []

if "latest_input" not in st.session_state:
    st.session_state.latest_input = ""

# ---------------------- SIDEBAR ----------------------
st.sidebar.markdown("## Chat History")

if "all_chats" not in st.session_state:
    st.session_state.all_chats = [] 

if "current_chat" not in st.session_state:
    st.session_state.current_chat = [] 
st.session_state.current_chat = st.session_state.chat.copy()
for idx, chat in enumerate(st.session_state.all_chats, start=1):
    with st.sidebar.expander(f"Chat {idx}", expanded=False):
        for role, msg in chat:
            icon = "🧑" if role == "user" else "🤖"
            st.markdown(f"**{icon} {role.capitalize()}:** {msg[:50]}")  
            st.markdown("---")
if st.session_state.current_chat:
    with st.sidebar.expander(f"Chat {len(st.session_state.all_chats)+1} (Current)", expanded=True):
        for role, msg in st.session_state.current_chat:
            icon = "🧑" if role == "user" else "🤖"
            st.markdown(f"**{icon} {role.capitalize()}:** {msg[:50]}")
            st.markdown("---")


# ---------------------- HEADER ----------------------
st.markdown("""
<div class="main-block" style="text-align:center;">
    <h1 style="font-size:46px; margin-bottom:5px; color:#0a1f44;">🌴 Resort AI Assistant</h1>
    <p style="font-size:20px; color:#0a1f44;">Your smart resort manager — bookings, billing & more</p>
</div>
""", unsafe_allow_html=True)

# ---------------------- MAIN BLOCK ----------------------
st.markdown('<div class="main-block">', unsafe_allow_html=True)
st.header(" Chat & Voice Input")

# ========================= INPUT LOGIC =========================

# ---------- VOICE INPUT ----------
audio = mic_recorder(
    start_prompt="🎤 Voice Input",
    stop_prompt="⏹️ Stop",
    format="wav",
    key="voice_recorder_unique"
)

if audio:
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(audio["bytes"])
            tmp_path = tmp_file.name

        with open(tmp_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=f,
                language="en"
            )

        voice_text = transcription.text
        st.success(f"Voice Input: {voice_text}")

        st.session_state.latest_input = voice_text

    except Exception as e:
        st.error(f"Transcription error: {e}")

# ---------- TEXT INPUT ----------
user_typed = st.text_input(
    "Type or speak your message here",
    key="text_box"
)

if user_typed:
    st.session_state.latest_input = user_typed

# ---------- SEND TO AGENT ----------
if st.session_state.latest_input:
    user_msg = st.session_state.latest_input

    st.session_state.chat.append(("user", user_msg))

    with st.spinner("Thinking..."):
        try:
            ai_reply = run_agent(user_msg)
            st.session_state.chat.append(("ai", ai_reply))
        except Exception as e:
            st.session_state.chat.append(("ai", f"Error: {str(e)}"))

    st.session_state.latest_input = ""  # reset


RECENT_COUNT = 2
recent_messages = st.session_state.chat[-RECENT_COUNT:]


def chat_bubble(role, text):
    bubble = "user-bubble" if role == "user" else "ai-bubble"
    st.markdown(f"""
    <div class="chat-bubble {bubble}">
        {text}
    </div>
    """, unsafe_allow_html=True)


for role, msg in recent_messages:
    chat_bubble(role, msg)

st.markdown("</div>", unsafe_allow_html=True)