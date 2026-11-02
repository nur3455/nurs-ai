#python -m streamlit run app.py
import streamlit as st
from google import genai

# =========================
# APP CONFIGURATION
# =========================

st.set_page_config(
    page_title="Nur's AI Assistant",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Nur's AI Assistant")
st.caption("Your personal AI assistant")
st.write("Hello! 👋 Welcome to Nur's AI Assistant. How can I help you today?")


# =========================
# GEMINI API CONFIGURATION
# =========================

try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)

except Exception:
    st.error(
        "API key not found. Please check your "
        ".streamlit/secrets.toml file."
    )
    st.stop()


# =========================
# AVAILABLE MODELS
# =========================

# If one model fails, the app will try the next model.
# Make sure these model IDs are available to your API project.

MODELS = [
    "gemini-3.5-flash-lite",
]


# =========================
# CHAT HISTORY
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = []


# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# =========================
# CHAT INPUT
# =========================

prompt = st.chat_input("Message Nur's AI Assistant...")


if prompt:

    # Save the user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Build the conversation history
    conversation = []

    for message in st.session_state.messages:
        role = (
            "User"
            if message["role"] == "user"
            else "Assistant"
        )

        conversation.append(
            f"{role}: {message['content']}"
        )

    chat_history = "\n".join(conversation)

    # =========================
    # AI RESPONSE WITH FALLBACK
    # =========================

    with st.chat_message("assistant"):

        answer = None
        errors = []

        status_box = st.status(
            "Starting AI response...",
            expanded=True
        )

        try:
            for model_name in MODELS:

                status_box.write(
                    f"Trying model: {model_name}"
                )

                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=chat_history,
                        config={
                            "http_options": {
                                "timeout": 30000
                            }
                        }
                    )

                    answer = response.text

                    if answer:
                        status_box.update(
                            label=f"Success: {model_name}",
                            state="complete",
                            expanded=False
                        )
                        break

                    errors.append(
                        f"{model_name}: The model returned an empty response."
                    )

                except Exception as e:
                    error_message = str(e)

                    errors.append(
                        f"{model_name}: {error_message}"
                    )

                    status_box.write(
                        f"Model failed: {model_name}"
                    )

        finally:
            if not answer:
                status_box.update(
                    label="AI response failed",
                    state="error",
                    expanded=True
                )

        if answer:

            st.markdown(answer)

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

        else:

            st.error(
                "Sorry, the AI could not generate a response. "
                "Check the error details below."
            )

            with st.expander(
                "Technical Error Details",
                expanded=True
            ):
                for error in errors:
                    st.code(error)

# =========================
# SIDEBAR
# =========================

with st.sidebar:

    st.title("🤖 Nur's AI Assistant")

    st.write(
        "Your personal AI assistant, "
        "ready to help with your questions."
    )

    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption("Powered by Google Gemini")