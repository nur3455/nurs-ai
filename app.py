
import streamlit as st
from google import genai
from google.genai import types
from supabase import create_client
from datetime import datetime, timezone
from io import BytesIO
from PIL import Image
import uuid


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
STORAGE_BUCKET = "chat-images"


# =====================================
# ORIGINAL PURPLE-BLUE DESIGN
# =====================================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(
        135deg,
        #f7f8ff 0%,
        #eef0ff 55%,
        #f9f7ff 100%
    );
    color: #172044;
}

header[data-testid="stHeader"] {
    background: transparent;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #171b36,
        #10152b
    );
}

section[data-testid="stSidebar"] * {
    color: #f4f5ff;
}

.hero {
    padding: 34px 36px;
    border-radius: 24px;
    background: linear-gradient(
        115deg,
        #ffffff 0%,
        #f1efff 55%,
        #e8edff 100%
    );
    border: 1px solid #e1e4ff;
    margin: 10px 0 22px 0;
    box-shadow: 0 12px 35px rgba(53, 66, 150, .08);
}

.hero h1 {
    color: #172044;
    font-size: clamp(30px, 4vw, 48px);
    margin: 4px 0 8px 0;
}

.hero h1 span {
    background: linear-gradient(90deg, #4568f5, #9b4de8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero p {
    color: #64719c;
    font-size: 16px;
    margin-bottom: 0;
}

.feature-card {
    background: rgba(255,255,255,.88);
    border: 1px solid #e4e8ff;
    border-radius: 18px;
    padding: 19px;
    min-height: 145px;
    box-shadow: 0 8px 22px rgba(57, 75, 160, .05);
}

.feature-icon {
    font-size: 27px;
}

.feature-title {
    color: #18234b;
    font-weight: 750;
    margin-top: 8px;
}

.feature-desc {
    color: #7480a7;
    font-size: 13px;
}

.stButton > button {
    border-radius: 12px;
    border: 1px solid #d9ddff;
    background: linear-gradient(100deg, #5c67f2, #8050e8);
    color: white;
    font-weight: 650;
    min-height: 42px;
}

.stButton > button:hover {
    border-color: #9c8cff;
    color: white;
}

.stTextInput input,
.stTextArea textarea {
    border-radius: 12px;
}

div[data-testid="stChatMessage"] {
    background: rgba(255,255,255,.92);
    border: 1px solid #e3e7ff;
    border-radius: 16px;
    padding: 14px;
}

div[data-testid="stFileUploader"] {
    background: rgba(255,255,255,.7);
    border-radius: 14px;
}

hr {
    border-color: #e1e5fa;
}

.small-note {
    color: #7782a7;
    font-size: 13px;
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
            "Supabase key not found. "
            "Please check your Streamlit Secrets."
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
# GOOGLE LOGIN
# =====================================

if not st.user.is_logged_in:

    st.markdown("""
    <div class="hero">
        <h1>🤖 Welcome to <span>Nur's AI</span></h1>
        <p>
            Your personal AI assistant.
            Ask questions, explore ideas and understand images.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Welcome!")

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
    st.error("Google user ID not found. Please sign in again.")
    st.stop()


# =====================================
# SESSION STATE
# =====================================

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None


# =====================================
# DATABASE HELPERS
# =====================================

@st.cache_data(ttl=20, show_spinner=False)
def get_chats(current_user_id):

    result = (
        supabase.table("chats")
        .select("id, title, updated_at")
        .eq("user_id", current_user_id)
        .order("updated_at", desc=True)
        .limit(50)
        .execute()
    )

    return result.data or []


@st.cache_data(ttl=15, show_spinner=False)
def get_messages(current_user_id, chat_id):

    result = (
        supabase.table("chat_messages")
        .select("id, role, content, image_path, created_at")
        .eq("user_id", current_user_id)
        .eq("chat_id", chat_id)
        .order("created_at")
        .execute()
    )

    return result.data or []


def create_new_chat(title="New Chat"):

    now = datetime.now(timezone.utc).isoformat()

    result = (
        supabase.table("chats")
        .insert({
            "user_id": user_id,
            "title": title[:80] or "New Chat",
            "created_at": now,
            "updated_at": now
        })
        .execute()
    )

    get_chats.clear()

    return result.data[0]["id"] if result.data else None


def save_message(chat_id, role, content, image_path=None):

    row = {
        "user_id": user_id,
        "chat_id": chat_id,
        "role": role,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    if image_path:
        row["image_path"] = image_path

    supabase.table("chat_messages").insert(row).execute()

    get_messages.clear()


def update_chat_time(chat_id):

    supabase.table("chats").update({
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq(
        "id", chat_id
    ).eq(
        "user_id", user_id
    ).execute()

    get_chats.clear()


# =====================================
# IMAGE HELPERS
# =====================================

def prepare_image(uploaded_image):

    uploaded_image.seek(0)

    image = Image.open(uploaded_image)
    image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))

    if image.mode != "RGB":
        image = image.convert("RGB")

    output = BytesIO()

    image.save(
        output,
        format="JPEG",
        quality=IMAGE_JPEG_QUALITY,
        optimize=True
    )

    return output.getvalue()


def upload_chat_image(chat_id, image_bytes):

    image_path = (
        f"{user_id}/{chat_id}/{uuid.uuid4().hex}.jpg"
    )

    supabase.storage.from_(STORAGE_BUCKET).upload(
        image_path,
        image_bytes,
        file_options={
            "content-type": "image/jpeg",
            "upsert": "false"
        }
    )

    return image_path


def get_chat_image_url(image_path):

    result = (
        supabase.storage
        .from_(STORAGE_BUCKET)
        .create_signed_url(image_path, 3600)
    )

    return (
        result.get("signedURL")
        or result.get("signedUrl")
    )


# =====================================
# GEMINI PROCESSING
# =====================================

def process_request(prompt, image_file=None):

    prompt = (prompt or "").strip()

    if not prompt and image_file is not None:
        prompt = "Please describe or analyze this image."

    if not prompt:
        st.warning("Please enter a message or upload an image.")
        return

    chat_id = st.session_state.current_chat_id

    if not chat_id:

        chat_id = create_new_chat(prompt[:45])

        st.session_state.current_chat_id = chat_id

    if not chat_id:
        st.error("Could not create a new chat.")
        return

    try:

        previous_messages = get_messages(user_id, chat_id)

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
                    {"text": msg.get("content") or ""}
                ]
            })

        current_parts = [
            types.Part.from_text(text=prompt)
        ]

        image_path = None
        image_bytes = None

        if image_file is not None:

            image_bytes = prepare_image(image_file)

            current_parts.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg"
                )
            )

            image_path = upload_chat_image(
                chat_id,
                image_bytes
            )

        save_message(
            chat_id,
            "user",
            prompt,
            image_path=image_path
        )

        contents.append({
            "role": "user",
            "parts": current_parts
        })

        with st.chat_message("user", avatar="👤"):

            st.markdown(prompt)

            if image_bytes is not None:
                st.image(image_bytes, width=280)

        with st.chat_message("assistant", avatar="🤖"):

            stream = gemini_client.models.generate_content_stream(
                model=MODEL,
                contents=contents
            )

            def text_chunks():

                for chunk in stream:

                    if getattr(chunk, "text", None):
                        yield chunk.text

            answer = st.write_stream(text_chunks())

        if answer:

            save_message(
                chat_id,
                "assistant",
                answer
            )

            update_chat_time(chat_id)

    except Exception as e:

        st.error(f"Request error: {e}")


# =====================================
# SIDEBAR
# =====================================

with st.sidebar:

    st.markdown("## Nur's AI Assistant")

    st.caption(f"Signed in as {user_email}")

    st.divider()

    if st.button(
        "➕ New Chat",
        use_container_width=True
    ):

        st.session_state.current_chat_id = None
        st.rerun()

    st.divider()

    st.markdown("### Chat History")

    try:

        chat_list = get_chats(user_id)

        if chat_list:

            for chat in chat_list:

                chat_title = chat.get("title") or "New Chat"
                chat_id = chat["id"]

                is_selected = (
                    st.session_state.current_chat_id == chat_id
                )

                button_label = (
                    f"● {chat_title[:25]}"
                    if is_selected
                    else chat_title[:28]
                )

                if st.button(
                    button_label,
                    key=f"chat_{chat_id}",
                    use_container_width=True
                ):

                    st.session_state.current_chat_id = chat_id
                    st.rerun()

        else:

            st.caption("No chat history yet.")

    except Exception as e:

        st.error(f"Could not load chat history: {e}")

    st.divider()

    if st.session_state.current_chat_id:

        if st.button(
            "🗑️ Delete This Chat",
            use_container_width=True
        ):

            try:

                selected_chat = st.session_state.current_chat_id

                supabase.table("chat_messages").delete().eq(
                    "user_id", user_id
                ).eq(
                    "chat_id", selected_chat
                ).execute()

                supabase.table("chats").delete().eq(
                    "user_id", user_id
                ).eq(
                    "id", selected_chat
                ).execute()

                get_chats.clear()
                get_messages.clear()

                st.session_state.current_chat_id = None

                st.success("Chat deleted successfully.")

                st.rerun()

            except Exception as e:

                st.error(f"Could not delete chat: {e}")

    if st.button(
        "Log Out",
        use_container_width=True
    ):

        st.logout()


# =====================================
# HOME PAGE
# =====================================

st.markdown(
    """
    <div style="text-align:center; padding:25px 10px 15px 10px;">

        <h1 style="font-size:38px; margin-bottom:5px;">
            Nur's AI Assistant
        </h1>

        <p style="font-size:16px; color:#777;">
            Your intelligent assistant for everyday tasks
        </p>

    </div>
    """,
    unsafe_allow_html=True
)


if not st.session_state.current_chat_id:

    st.markdown("### What can I help you with today?")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("""
        <div class="feature-card">

            <div class="feature-icon">💡</div>

            <div class="feature-title">
                Ask Anything
            </div>

            <div class="feature-desc">
                Get answers, explanations and helpful ideas.
            </div>

        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card">

            <div class="feature-icon">✍️</div>

            <div class="feature-title">
                Writing Assistant
            </div>

            <div class="feature-desc">
                Write, improve and summarize your text.
            </div>

        </div>
        """, unsafe_allow_html=True)

    with col2:

        st.markdown("""
        <div class="feature-card">

            <div class="feature-icon">🖼️</div>

            <div class="feature-title">
                Image Analysis
            </div>

            <div class="feature-desc">
                Upload an image and ask questions about it.
            </div>

        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="feature-card">

            <div class="feature-icon">📚</div>

            <div class="feature-title">
                Learning Support
            </div>

            <div class="feature-desc">
                Understand topics and learn something new.
            </div>

        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.info(
        "Start a conversation by typing a message below."
    )

else:

    st.markdown("### Your Conversation")


# =====================================
# DISPLAY CHAT HISTORY
# =====================================

if st.session_state.current_chat_id:

    try:

        messages = get_messages(
            user_id,
            st.session_state.current_chat_id
        )

        for msg in messages:

            role = msg.get("role", "assistant")

            avatar = (
                "👤"
                if role == "user"
                else "🤖"
            )

            with st.chat_message(role, avatar=avatar):

                content = msg.get("content", "")

                if content:
                    st.markdown(content)

                image_path = msg.get("image_path")

                if image_path:

                    try:

                        image_url = get_chat_image_url(
                            image_path
                        )

                        if image_url:
                            st.image(image_url, width=350)

                        else:
                            st.warning(
                                "Could not load this image."
                            )

                    except Exception:

                        st.warning(
                            "Could not load this image."
                        )

    except Exception as e:

        st.error(f"Could not load messages: {e}")


# =====================================
# MESSAGE INPUT
# =====================================

st.markdown("---")

with st.form(
    "message_form",
    clear_on_submit=True
):

    uploaded_image = st.file_uploader(
        "Upload an image (optional)",
        type=["png", "jpg", "jpeg", "webp"],
        key="chat_image_uploader"
    )

    prompt = st.text_area(
        "Message Nur's AI Assistant",
        placeholder="Ask me anything...",
        height=100,
        key="chat_prompt"
    )

    send_button = st.form_submit_button(
        "Send Message",
        use_container_width=True
    )


# Process the submitted message outside the form.
if send_button:

    if prompt.strip() or uploaded_image is not None:

        process_request(
            prompt,
            uploaded_image
        )

        st.rerun()

    else:

        st.warning(
            "Please enter a message or upload an image."
        )
