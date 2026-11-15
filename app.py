#python -m streamlit run app.py
import streamlit as st
from google import genai
from google.genai import types
from supabase import create_client
from datetime import datetime, timezone
from gtts import gTTS
from io import BytesIO
from PIL import Image

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
MAX_IMAGE_SIDE = 1600
IMAGE_JPEG_QUALITY = 85

# Theme preference (Dark Mode is the default)
if "light_mode" not in st.session_state:
    st.session_state.light_mode = False

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
    padding: 8px 12px;
    border: 1px solid #393c83;
    border-radius: 22px;
    background: linear-gradient(105deg, rgba(13, 22, 55, 0.98), rgba(17, 22, 62, 0.98));
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.38);
    backdrop-filter: blur(14px);
}

.st-key-fixed_chat_bar [data-testid="stHorizontalBlock"] {
    align-items: center;
    gap: 8px;
}

.st-key-fixed_chat_bar [data-testid="stPopover"] > button {
    min-height: 42px;
    width: 42px;
    padding: 0;
    border-radius: 50%;
    border: 0;
    background: transparent;
    color: #e8eaff;
    font-size: 21px;
    box-shadow: none;
}

.st-key-fixed_chat_bar [data-testid="stPopover"] > button:hover {
    background: rgba(125, 111, 255, 0.18);
    border: 0;
}

.st-key-fixed_chat_bar [data-testid="stTextInput"] {
    margin-bottom: 0;
}

.st-key-fixed_chat_bar [data-testid="stTextInput"] input {
    min-height: 42px;
    border: 0 !important;
    border-radius: 14px;
    background: transparent !important;
    color: #f4f2ff !important;
    box-shadow: none !important;
    padding-left: 8px;
}

.st-key-fixed_chat_bar [data-testid="stTextInput"] input::placeholder {
    color: #b9c2e8;
}

.st-key-fixed_chat_bar [data-testid="stFormSubmitButton"] button {
    min-height: 42px;
    width: 42px;
    padding: 0;
    border: 0;
    border-radius: 50%;
    background: linear-gradient(135deg, #8757ff, #5535e8);
    color: white;
    font-size: 20px;
    box-shadow: 0 3px 12px rgba(105, 75, 255, 0.35);
}

.st-key-fixed_chat_bar [data-testid="stFormSubmitButton"] button:hover {
    border: 0;
    color: white;
    filter: brightness(1.12);
}

section[data-testid="stMain"] .block-container {
    padding-bottom: 7rem;
}

@media (max-width: 900px) {

    .st-key-fixed_chat_bar {
        left: 0.65rem;
        right: 0.65rem;
        bottom: 0.5rem;
        padding: 7px 8px;
    }

    .st-key-fixed_chat_bar [data-testid="stHorizontalBlock"] {
        gap: 4px;
    }

    .st-key-fixed_chat_bar [data-testid="stPopover"] > button {
        width: 36px;
        min-height: 40px;
    }

    .st-key-fixed_chat_bar [data-testid="stFormSubmitButton"] button {
        width: 38px;
    }

}

/* =====================================
   PRESENTATION-READY HOME DASHBOARD
   ===================================== */

.showcase-hero {
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    min-height: 300px;
    padding: 34px 38px;
    margin: 8px 0 30px 0;
    border-radius: 24px;
    border: 1px solid #393c9b;
    background: radial-gradient(circle at 78% 45%, rgba(85, 73, 255, .35), transparent 34%),
                linear-gradient(115deg, #101b4b 0%, #17145a 55%, #123b91 100%);
    box-shadow: 0 18px 45px rgba(20, 30, 100, .20);
}

.showcase-copy {
    position: relative;
    z-index: 2;
    max-width: 680px;
}

.showcase-eyebrow {
    display: inline-block;
    padding: 7px 13px;
    margin-bottom: 16px;
    border: 1px solid rgba(170, 180, 255, .35);
    border-radius: 30px;
    background: rgba(255,255,255,.08);
    color: #e4e8ff;
    font-size: 13px;
    font-weight: 650;
    letter-spacing: .2px;
}

.showcase-hero h1 {
    color: #fff !important;
    font-size: clamp(30px, 4vw, 48px) !important;
    line-height: 1.12;
    margin: 0 0 15px 0;
}

.showcase-hero h1 span {
    background: linear-gradient(90deg, #e6a7ff, #8abaff);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

.showcase-hero p {
    color: #dce5ff !important;
    font-size: 15px;
    line-height: 1.75;
    max-width: 620px;
}

.showcase-robot {
    position: relative;
    z-index: 1;
    flex: 0 0 220px;
    width: 220px;
    height: 220px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    font-size: 112px;
    background: radial-gradient(circle, rgba(100,160,255,.28), rgba(120,80,255,.08) 55%, transparent 70%);
    filter: drop-shadow(0 0 26px rgba(95,145,255,.45));
}

.showcase-section-title {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 2px 0 15px 0;
    font-size: 22px;
    font-weight: 750;
}

.showcase-feature {
    min-height: 150px;
    padding: 20px 18px;
    border-radius: 19px;
    background: linear-gradient(145deg, #171b3d, #111a37);
    border: 1px solid #343b78;
    box-shadow: 0 8px 22px rgba(0,0,0,.12);
}

.showcase-feature-icon {
    display: inline-flex;
    width: 44px;
    height: 44px;
    align-items: center;
    justify-content: center;
    border-radius: 13px;
    font-size: 23px;
    margin-bottom: 12px;
    background: linear-gradient(135deg,#6d4cff,#287eea);
    box-shadow: 0 5px 16px rgba(75,90,230,.28);
}

.showcase-feature h3 {
    color: #fff;
    font-size: 16px;
    margin: 0 0 5px 0;
}

.showcase-feature p {
    color: #b8c5ee;
    font-size: 13px;
    margin: 0;
}

.showcase-ready {
    margin: 28px 0 20px 0;
    padding: 24px 26px;
    border-radius: 21px;
    border: 1px solid #393b9b;
    background: radial-gradient(circle at 95% 50%, rgba(107,74,255,.24), transparent 30%), linear-gradient(110deg,#111b4b,#17145a 65%,#202078);
}
.showcase-ready h3 {
    color: #fff;
    margin: 0 0 9px 0;
    font-size: 19px;
}

.showcase-ready p {
    color: #d4ddff;
    margin: 0;
    line-height: 1.65;
    font-size: 14px;
}

.showcase-points {
    display: flex;
    flex-wrap: wrap;
    gap: 18px;
    margin-top: 17px;
    color: #e4eaff;
    font-size: 12px;
}

.showcase-points span {
    white-space: nowrap;
}

.showcase-points b {
    color: #35d5b2;
    margin-right: 5px;
}


/* RESPONSIVE DESIGN */

@media (max-width: 760px) {
    .showcase-hero {
        min-height: 0;
        padding: 25px 22px;
    }

    .showcase-robot {
        flex-basis: 105px;
        width: 105px;
        height: 105px;
        font-size: 68px;
    }

    .showcase-hero p {
        font-size: 14px;
    }

    .showcase-feature {
        min-height: 132px;
        padding: 16px 13px;
    }

    .showcase-ready {
        padding: 20px;
    }
}

</style>
""", unsafe_allow_html=True)


# Light Mode changes the full app theme; Dark Mode keeps the original design.

if st.session_state.light_mode:

    st.markdown("""
    <style>

    .stApp {
        background: radial-gradient(circle at 10% 5%, #eef0ff 0%, transparent 38%),
                    linear-gradient(135deg, #f8faff 0%, #f1f5ff 55%, #f7f3ff 100%);
        color: #14264f;
    }

    header[data-testid="stHeader"] {
        background: rgba(248,250,255,0.82);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f4f6ff, #edf2ff);
        border-right: 1px solid #d8e2ff;
    }

    section[data-testid="stSidebar"] * {
        color: #172b5b;
    }

    .hero {
        background: linear-gradient(120deg, #e6ddff, #dceaff 58%, #d8e8ff);
        border: 1px solid #c9d7ff;
        box-shadow: 0 8px 26px rgba(70, 94, 170, 0.10);
    }

    .hero h1 {
        color: #172b67;
    }

    .hero p {
        color: #334d89;
    }

    .feature-card {
        background: linear-gradient(145deg, #ffffff, #f2f6ff);
        border: 1px solid #dce5ff;
        box-shadow: 0 5px 18px rgba(60, 85, 150, 0.06);
    }

    .feature-title {
        color: #172b5b;
    }

    .feature-desc {
        color: #6174a5;
    }

    div[data-testid="stChatMessage"] {
        background: rgba(255,255,255,0.88);
        border: 1px solid #dce5ff;
        color: #172b5b;
        box-shadow: 0 4px 14px rgba(60, 85, 150, 0.05);
    }

    div[data-testid="stChatMessage"] p,
    div[data-testid="stChatMessage"] li,
    div[data-testid="stChatMessage"] span {
        color: #172b5b;
    }

    .stTextInput input,
    .stTextArea textarea {
        background: #ffffff !important;
        color: #172b5b !important;
        border: 1px solid #d4def8 !important;
    }

    [data-testid="stChatInput"] textarea {
        background: #ffffff !important;
        color: #172b5b !important;
    }

    [data-testid="stChatInput"] {
        background: #ffffff !important;
        border-color: #d4def8 !important;
    }

    .st-key-fixed_chat_bar {
        background: linear-gradient(105deg, rgba(255,255,255,0.98), rgba(244,246,255,0.98));
        border: 1px solid #dce5ff;
        box-shadow: 0 8px 28px rgba(55, 75, 135, 0.13);
    }

    .st-key-fixed_chat_bar [data-testid="stTextInput"] input {
        color: #172b5b !important;
    }

    .st-key-fixed_chat_bar [data-testid="stTextInput"] input::placeholder {
        color: #7180a8;
    }

    .st-key-fixed_chat_bar [data-testid="stPopover"] > button {
        color: #344b86;
    }

    [data-testid="stPopover"] > button,
    [data-testid="stTabs"] button {
        color: #243b75;
    }

    hr {
        border-color: #d8e2ff;
    }

    .showcase-hero {
        background: radial-gradient(circle at 80% 45%, rgba(130,145,255,.24), transparent 34%),
                    linear-gradient(115deg, #e5e8ff 0%, #e9e6ff 52%, #dcecff 100%);
        border: 1px solid #cbd7ff;
        box-shadow: 0 18px 42px rgba(85,105,180,.13);
    }

    .showcase-eyebrow {
        background: rgba(255,255,255,.72);
        border-color: #d4dcff;
        color: #3d4d91;
    }

    .showcase-hero h1 {
        color: #142b68 !important;
    }

    .showcase-hero h1 span {
        background: linear-gradient(90deg,#8b43dc,#3478e8);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }

    .showcase-hero p {
        color: #344e8b !important;
    }

    .showcase-robot {
        filter: drop-shadow(0 0 22px rgba(92,130,255,.22));
    }

    .showcase-feature {
        background: linear-gradient(145deg,#ffffff,#f1f5ff);
        border-color: #dce5ff;
        box-shadow: 0 8px 22px rgba(65,90,155,.07);
    }

    .showcase-feature h3 {
        color: #172e68;
    }

    .showcase-feature p {
        color: #6075a8;
    }

    .showcase-ready {
        background: radial-gradient(circle at 95% 50%,rgba(150,125,255,.16),transparent 30%),linear-gradient(110deg,#e5edff,#f1eaff 65%,#e5eaff);
        border-color: #d2dcff;
    }

    .showcase-ready h3 {
        color: #172e68;
    }

    .showcase-ready p,
    .showcase-points {
        color: #425b96;
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

@st.cache_data(ttl=30, show_spinner=False)
def get_chats(uid):

    result = (
        supabase.table("chats")
        .select("*")
        .eq("user_id", uid)
        .order("updated_at", desc=True)
        .limit(50)
        .execute()
    )

    return result.data or []


@st.cache_data(ttl=15, show_spinner=False)
def get_messages(uid, chat_id):

    result = (
        supabase.table("chat_messages")
        .select("*")
        .eq("user_id", uid)
        .eq("chat_id", chat_id)
        .order("created_at")
        .execute()
    )

    return result.data or []


def create_new_chat(title="New Chat"):

    now = datetime.now(
        timezone.utc
    ).isoformat()

    result = (
        supabase.table("chats")
        .insert({
            "user_id": user_id,
            "title": title,
            "created_at": now,
            "updated_at": now
        })
        .execute()
    )

    get_chats.clear()

    if result.data:
        return result.data[0]["id"]

    return None


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

    get_messages.clear()


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

    get_chats.clear()


# =====================================
# IMAGE OPTIMIZATION
# =====================================

def optimize_image(image_file):

    image_file.seek(0)

    image = Image.open(image_file)

    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    elif image.mode == "L":
        image = image.convert("RGB")

    image.thumbnail(
        (MAX_IMAGE_SIDE, MAX_IMAGE_SIDE)
    )

    output = BytesIO()

    image.save(
        output,
        format="JPEG",
        quality=IMAGE_JPEG_QUALITY,
        optimize=True
    )

    output.seek(0)

    return output.getvalue()


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

        previous_messages = get_messages(
            user_id,
            chat_id
        )

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

        # Optimized image attachment

        if image_file is not None:

            image_bytes = optimize_image(
                image_file
            )

            current_parts.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg"
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
        # Chat History List

    chats = get_chats(user_id)

    if chats:

        for chat in chats:

            chat_title = chat.get(
                "title",
                "New Chat"
            )

            if st.button(
                f"💬 {chat_title[:28]}",
                key=f"history_{chat['id']}",
                use_container_width=True
            ):

                st.session_state.current_chat_id = chat["id"]
                st.rerun()

    else:

        st.caption("No chat history yet.")

    st.divider()

    # Delete Current Chat

    if st.session_state.current_chat_id:

        if st.button(
            "🗑️ Delete This Chat",
            use_container_width=True
        ):

            try:

                chat_id = st.session_state.current_chat_id

                supabase.table(
                    "chat_messages"
                ).delete().eq(
                    "user_id", user_id
                ).eq(
                    "chat_id", chat_id
                ).execute()

                supabase.table(
                    "chats"
                ).delete().eq(
                    "user_id", user_id
                ).eq(
                    "id", chat_id
                ).execute()

                get_chats.clear()
                get_messages.clear()

                st.session_state.current_chat_id = None

                st.success("Chat deleted!")
                st.rerun()

            except Exception as e:

                st.error(f"Delete error: {e}")

    st.divider()

    # Voice Reply Toggle

    st.session_state.voice_reply = st.toggle(
        "🔊 AI Voice Reply",
        value=st.session_state.voice_reply
    )

    # Theme Toggle

    if "light_mode" not in st.session_state:
        st.session_state.light_mode = False

    light_mode = st.toggle(
        "☀️ Light Mode",
        value=st.session_state.light_mode
    )

    if light_mode != st.session_state.light_mode:

        st.session_state.light_mode = light_mode
        st.rerun()

    st.divider()

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.logout()


# =====================================
# MAIN HOME DASHBOARD
# =====================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-tag">✦ YOUR PERSONAL AI ASSISTANT</div>
        <h1>Welcome to <span>Nur's AI</span></h1>
        <p>Your intelligent companion for creativity,
        learning, productivity and everyday tasks.</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="showcase-ready">
        <h3>✨ Ready to explore something amazing?</h3>
        <p>Ask anything, upload an image, or share your thoughts.
        Your AI assistant is ready to help.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Feature Cards

col1, col2, col3 = st.columns(3)

with col1:

    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">💬</div>
            <h4>Smart Chat</h4>
            <p>Ask questions and get intelligent answers.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:

    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">🖼️</div>
            <h4>Image Understanding</h4>
            <p>Upload images and ask AI to analyze them.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:

    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">🎙️</div>
            <h4>Voice Input</h4>
            <p>Speak naturally with your AI assistant.</p>
        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================
# CURRENT CHAT DISPLAY
# =====================================

chat_id = st.session_state.current_chat_id

if chat_id:

    messages = get_messages(
        user_id,
        chat_id
    )

    for message in messages:

        role = message.get("role", "user")

        avatar = (
            "🤖"
            if role == "assistant"
            else "👤"
        )

        with st.chat_message(
            role,
            avatar=avatar
        ):

            st.markdown(
                message.get("content", "")
            )


# =====================================
# BOTTOM COMPOSER
# =====================================

if "image_widget_version" not in st.session_state:
    st.session_state.image_widget_version = 0

if "audio_widget_version" not in st.session_state:
    st.session_state.audio_widget_version = 0


st.markdown(
    """
    <div class="composer-spacer"></div>
    """,
    unsafe_allow_html=True
)

# Composer icons row

icon_col1, icon_col2, text_col, send_col = st.columns(
    [0.65, 0.65, 5.8, 0.9],
    vertical_alignment="bottom"
)

uploaded_image = None
recorded_audio = None

with icon_col1:

    with st.popover(
        "📎",
        use_container_width=True
    ):

        st.markdown("**Upload an image**")

        uploaded_image = st.file_uploader(
            "Choose image",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp"
            ],
            key=f"image_upload_{st.session_state.image_widget_version}",
            label_visibility="collapsed"
        )

with icon_col2:

    with st.popover(
        "🎙️",
        use_container_width=True
    ):

        st.markdown("**Voice message**")

        if hasattr(st, "audio_input"):

            recorded_audio = st.audio_input(
                "Record your voice",
                key=f"audio_input_{st.session_state.audio_widget_version}"
            )

        else:

            st.warning(
                "Voice recording requires a newer Streamlit version."
            )


# Text input and Send button

with st.form(
    "bottom_message_form",
    clear_on_submit=True,
    border=False
):

    text_col, send_col = st.columns(
        [6, 1],
        vertical_alignment="bottom"
    )

    with text_col:

        user_prompt = st.text_input(
            "Message Nur's AI",
            placeholder="Message Nur's AI...",
            label_visibility="collapsed"
        )

    with send_col:

        send_clicked = st.form_submit_button(
            "➤",
            use_container_width=True
        )


# Process submitted message

if send_clicked:

    if (
        user_prompt.strip()
        or uploaded_image is not None
        or recorded_audio is not None
    ):

        process_request(
            prompt=user_prompt.strip(),
            image_file=uploaded_image,
            audio_file=recorded_audio
        )

        st.session_state.image_widget_version += 1
        st.session_state.audio_widget_version += 1

        st.rerun()

    else:

        st.warning(
            "Please write a message or attach an image/voice message."
        )
