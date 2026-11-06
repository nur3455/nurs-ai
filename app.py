#python -m streamlit run app.py
import streamlit as st
from google import genai
from google.genai import types
from supabase import create_client
from datetime import datetime, timezone
from gtts import gTTS
from io import BytesIO


# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="Nur's AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

MODEL = "gemini-3.5-flash-lite"
MAX_HISTORY_MESSAGES = 12


# =====================================
# DARK PREMIUM DESIGN
# =====================================

st.markdown("""
<style>

.stApp {
    background:
        radial-gradient(circle at 10% 5%, #28204d 0%, transparent 35%),
        linear-gradient(135deg, #0b1020 0%, #111329 55%, #17132b 100%);
    color: #f4f2ff;
}

header[data-testid="stHeader"] {
    background: transparent;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #17152c, #101525);
    border-right: 1px solid #343052;
}

.hero {
    padding: 30px;
    border-radius: 22px;
    background: linear-gradient(120deg, #30205f, #172b50);
    border: 1px solid #62519b;
    margin-bottom: 22px;
}

.hero h1 {
    color: white;
    font-size: 36px;
    margin-bottom: 8px;
}

.hero p {
    color: #d5d0f5;
    font-size: 16px;
}

.feature-card {
    background: linear-gradient(145deg, #211e3c, #171d32);
    border: 1px solid #39365e;
    border-radius: 16px;
    padding: 18px;
    min-height: 120px;
}

.feature-icon {
    font-size: 27px;
}

.feature-title {
    color: #ffffff;
    font-weight: 700;
    margin-top: 8px;
}

.feature-desc {
    color: #b9b6d2;
    font-size: 13px;
}

div[data-testid="stChatMessage"] {
    background: rgba(37, 34, 65, 0.75);
    border: 1px solid #39365e;
    border-radius: 16px;
    padding: 12px;
}

.stButton > button {
    border-radius: 12px;
    border: 1px solid #6654a5;
    background: linear-gradient(100deg, #6545b8, #405caa);
    color: white;
    font-weight: 600;
    min-height: 42px;
}

.stButton > button:hover {
    border-color: #b9a5ff;
    color: white;
}

.stTextInput input,
.stTextArea textarea {
    background: #171a30;
    color: white;
}

hr {
    border-color: #39365e;
}


/* =====================================
   FIXED BOTTOM CHAT BAR
   ===================================== */

.st-key-fixed_chat_bar {
    position: fixed;
    left: 22rem;
    right: 2rem;
    bottom: 0.8rem;
    z-index: 999;
    padding: 10px 12px;
    border: 1px solid #39365e;
    border-radius: 18px;
    background: rgba(20, 20, 42, 0.96);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.38);
    backdrop-filter: blur(14px);
}

.st-key-fixed_chat_bar [data-testid="stHorizontalBlock"] {
    align-items: end;
}

.st-key-fixed_chat_bar [data-testid="stPopover"] > button {
    min-height: 48px;
    width: 100%;
    border-radius: 50%;
    font-size: 22px;
}

.st-key-fixed_chat_bar [data-testid="stChatInput"] {
    margin-bottom: 0;
}

section[data-testid="stMain"] .block-container {
    padding-bottom: 7rem;
}

@media (max-width: 900px) {

    .st-key-fixed_chat_bar {
        left: 1rem;
        right: 1rem;
        bottom: 0.5rem;
    }

}

</style>
""", unsafe_allow_html=True)


# =====================================
# SECRETS AND CONNECTIONS
# =====================================

try:

    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]

    SUPABASE_KEY = (
        st.secrets.get("SUPABASE_SECRET_KEY")
        or st.secrets.get("SUPABASE_KEY")
    )

    if not SUPABASE_KEY:
        st.error(
            "Supabase key পাওয়া যায়নি। "
            "Secrets configuration পরীক্ষা করো।"
        )
        st.stop()

    supabase = create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )

    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )

except Exception as e:

    st.error(f"Connection error: {e}")
    st.stop()


# =====================================
# LOGIN
# =====================================

if not st.user.is_logged_in:

    st.markdown("""
    <div class="hero">
        <h1>🤖 Nur's AI Assistant</h1>
        <p>Welcome back! Your intelligent assistant is ready.</p>
        <p>Ask questions • Speak naturally • Upload images • Explore ideas</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Welcome!")

    st.write(
        "Continue with your Google account "
        "to use Nur's AI Assistant."
    )

    if st.button(
        "🔐 Login with Google",
        use_container_width=True
    ):
        st.login("google")

    st.stop()


# =====================================
# USER INFORMATION
# =====================================

user_id = st.user.get("sub")
user_email = st.user.get("email", "User")

if not user_id:

    st.error(
        "Google user ID পাওয়া যায়নি। আবার login করো।"
    )

    st.stop()


# =====================================
# SESSION STATE
# =====================================

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "voice_reply" not in st.session_state:
    st.session_state.voice_reply = False


# =====================================
# DATABASE HELPERS
# =====================================

def get_chats():

    result = (
        supabase.table("chats")
        .select("*")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )

    return result.data or []


def create_new_chat(title="New Chat"):

    result = (
        supabase.table("chats")
        .insert({
            "user_id": user_id,
            "title": title,
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "updated_at": datetime.now(
                timezone.utc
            ).isoformat()
        })
        .execute()
    )

    if result.data:
        return result.data[0]["id"]

    return None


def get_messages(chat_id):

    result = (
        supabase.table("chat_messages")
        .select("*")
        .eq("user_id", user_id)
        .eq("chat_id", chat_id)
        .order("created_at")
        .execute()
    )

    return result.data or []


def save_message(chat_id, role, content):

    supabase.table("chat_messages").insert({
        "user_id": user_id,
        "chat_id": chat_id,
        "role": role,
        "content": content,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat()
    }).execute()


def update_chat_time(chat_id):

    supabase.table("chats").update({
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat()
    }).eq(
        "id", chat_id
    ).eq(
        "user_id", user_id
    ).execute()


# =====================================
# GEMINI REQUEST PROCESSING
# =====================================

def process_request(
    prompt,
    image_file=None,
    audio_file=None
):

    if not prompt:
        prompt = (
            "Please describe or analyze "
            "the attached file."
        )

    chat_id = st.session_state.current_chat_id

    if not chat_id:

        chat_id = create_new_chat(
            prompt[:40]
        )

        st.session_state.current_chat_id = chat_id

    if not chat_id:

        st.error("নতুন chat তৈরি করা যায়নি।")
        return

    try:

        previous_messages = get_messages(chat_id)

        contents = []

        for msg in previous_messages[-MAX_HISTORY_MESSAGES:]:

            role = (
                "model"
                if msg["role"] == "assistant"
                else "user"
            )

            contents.append({
                "role": role,
                "parts": [
                    {"text": msg["content"]}
                ]
            })

        # Current message parts

        current_parts = [
            types.Part.from_text(text=prompt)
        ]

        # Image attachment

        if image_file is not None:

            image_bytes = image_file.getvalue()

            current_parts.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=image_file.type or "image/jpeg"
                )
            )

        # Audio attachment

        if audio_file is not None:

            audio_bytes = audio_file.getvalue()

            current_parts.append(
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type=audio_file.type or "audio/wav"
                )
            )

        # Save user message

        save_message(
            chat_id,
            "user",
            prompt
        )

        contents.append({
            "role": "user",
            "parts": current_parts
        })

        update_chat_time(chat_id)

        # Display user message

        with st.chat_message(
            "user",
            avatar="👤"
        ):

            st.markdown(prompt)

            if image_file is not None:
                st.image(
                    image_file,
                    width=250
                )

            if audio_file is not None:
                st.audio(audio_file)

        # Gemini response

        with st.chat_message(
            "assistant",
            avatar="🤖"
        ):

            response_placeholder = st.empty()
            full_response = ""

            try:

                stream = (
                    gemini_client.models.generate_content_stream(
                        model=MODEL,
                        contents=contents
                    )
                )

                for chunk in stream:

                    if chunk.text:

                        full_response += chunk.text

                        response_placeholder.markdown(
                            full_response + "▌"
                        )

                response_placeholder.markdown(
                    full_response
                )

            except Exception as e:

                st.error(f"Gemini error: {e}")
                return

            if full_response:

                save_message(
                    chat_id,
                    "assistant",
                    full_response
                )

                update_chat_time(chat_id)

                # AI Voice Reply

                if st.session_state.voice_reply:

                    try:

                        audio_buffer = BytesIO()

                        tts = gTTS(
                            text=full_response,
                            lang="en"
                        )

                        tts.write_to_fp(audio_buffer)
                        audio_buffer.seek(0)

                        st.audio(
                            audio_buffer,
                            format="audio/mp3"
                        )

                    except Exception as e:

                        st.warning(
                            f"Voice generation error: {e}"
                        )

    except Exception as e:

        st.error(
            f"Something went wrong: {e}"
        )


# =====================================
# SIDEBAR
# =====================================

with st.sidebar:

    st.markdown(
        "## 🤖 Nur's AI Assistant"
    )

    st.caption(
        "Your personal AI companion"
    )

    st.divider()

    st.markdown(
        f"**👤 {user_email}**"
    )

    # New Chat

    if st.button(
        "＋ New Chat",
        use_container_width=True
    ):

        st.session_state.current_chat_id = None
        st.rerun()

    st.divider()

    st.markdown(
        "### 💬 Chat History"
    )

    try:

        chats = get_chats()

        for chat in chats:

            chat_title = (
                chat.get("title") or "New Chat"
            )

            chat_id = chat["id"]

            if st.button(
                f"💬 {chat_title[:28]}",
                key=f"chat_{chat_id}",
                use_container_width=True
            ):

                st.session_state.current_chat_id = chat_id
                st.rerun()

            # Delete Chat

            if (
                st.session_state.current_chat_id == chat_id
                and st.button(
                    "🗑️ Delete this chat",
                    key=f"delete_{chat_id}"
                )
            ):

                (
                    supabase.table("chat_messages")
                    .delete()
                    .eq("user_id", user_id)
                    .eq("chat_id", chat_id)
                    .execute()
                )

                (
                    supabase.table("chats")
                    .delete()
                    .eq("user_id", user_id)
                    .eq("id", chat_id)
                    .execute()
                )

                st.session_state.current_chat_id = None
                st.rerun()

    except Exception as e:

        st.warning(
            f"Chat history load error: {e}"
        )

    st.divider()

    # Settings

    st.markdown(
        "### ⚙️ Settings"
    )

    st.session_state.voice_reply = st.toggle(
        "🔊 AI Voice Reply",
        value=st.session_state.voice_reply
    )

    st.divider()

    # Logout

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.logout()


# =====================================
# FRONT PAGE
# =====================================

st.markdown("""
<div class="hero">
    <h1>🤖 Nur's AI Assistant</h1>
    <p>Welcome back! Your intelligent assistant is ready.</p>
    <p>Ask questions • Speak naturally • Upload images • Explore ideas</p>
</div>
""", unsafe_allow_html=True)


# =====================================
# FEATURE CARDS
# =====================================

if st.session_state.current_chat_id is None:

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">💬</div>
            <div class="feature-title">AI CHAT</div>
            <div class="feature-desc">Ask anything</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:

        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🎙️</div>
            <div class="feature-title">VOICE CHAT</div>
            <div class="feature-desc">Speak to your AI</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:

        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🖼️</div>
            <div class="feature-title">IMAGE UPLOAD</div>
            <div class="feature-desc">Understand pictures</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:

        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📸</div>
            <div class="feature-title">CAMERA</div>
            <div class="feature-desc">Capture and ask</div>
        </div>
        """, unsafe_allow_html=True)


# =====================================
# YOUR CONVERSATION
# =====================================

st.markdown(
    "## ✨ Your Conversation"
)


# =====================================
# LOAD CURRENT CHAT MESSAGES
# =====================================

if st.session_state.current_chat_id:

    try:

        messages = get_messages(
            st.session_state.current_chat_id
        )

        for msg in messages:

            if msg["role"] == "user":
                avatar = "👤"
            else:
                avatar = "🤖"

            with st.chat_message(
                msg["role"],
                avatar=avatar
            ):

                st.markdown(
                    msg["content"]
                )

    except Exception as e:

        st.error(
            f"Could not load messages: {e}"
        )


# =====================================
# FIXED BOTTOM CHAT INPUT WITH PLUS MENU
# =====================================

with st.container(key="fixed_chat_bar"):

    plus_col, chat_col = st.columns(
        [0.10, 0.90],
        gap="small"
    )

    # =================================
    # PLUS MENU
    # =================================

    with plus_col:

        with st.popover(
            "＋",
            use_container_width=True
        ):

            st.markdown(
                "### 📎 Attach to chat"
            )

            image_tab, camera_tab, voice_tab = st.tabs([
                "🖼️ Image",
                "📸 Camera",
                "🎙️ Voice"
            ])

            # IMAGE UPLOAD

            with image_tab:

                uploaded_image = st.file_uploader(
                    "Choose an image",
                    type=[
                        "png",
                        "jpg",
                        "jpeg",
                        "webp"
                    ],
                    key="plus_image"
                )

                image_question = st.text_input(
                    "Ask about this image",
                    key="plus_image_question"
                )

                if st.button(
                    "Send Image",
                    key="plus_send_image"
                ):

                    if uploaded_image:

                        process_request(
                            image_question,
                            image_file=uploaded_image
                        )

                        st.rerun()

                    else:

                        st.warning(
                            "Please select an image."
                        )

            # CAMERA

            with camera_tab:

                camera_image = st.camera_input(
                    "Take a picture",
                    key="plus_camera"
                )

                camera_question = st.text_input(
                    "Ask about this photo",
                    key="plus_camera_question"
                )

                if st.button(
                    "Send Photo",
                    key="plus_send_camera"
                ):

                    if camera_image:

                        process_request(
                            camera_question,
                            image_file=camera_image
                        )

                        st.rerun()

                    else:

                        st.warning(
                            "Please take a picture."
                        )

            # VOICE RECORDING

            with voice_tab:

                recorded_audio = st.audio_input(
                    "Record your voice",
                    key="plus_voice"
                )

                if recorded_audio:
                    st.audio(recorded_audio)

                if st.button(
                    "Send Voice",
                    key="plus_send_voice"
                ):

                    if recorded_audio:

                        process_request(
                            "Please listen to my voice message and answer.",
                            audio_file=recorded_audio
                        )

                        st.rerun()

                    else:

                        st.warning(
                            "Please record your voice."
                        )

    # =================================
    # NORMAL TEXT CHAT
    # =================================

    with chat_col:

        prompt = st.chat_input(
            "Message Nur's AI Assistant...",
            key="main_chat_input"
        )

        if prompt:

            process_request(prompt)
            st.rerun()
