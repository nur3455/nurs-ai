
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

st.write(
    "Hello! 👋 Welcome to Nur's AI Assistant. "
    "How can I help you today?"
)


# =========================
# GEMINI API CONFIGURATION
# =========================

try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)

except Exception:
    st.error(
        "API key not found. Please check your "
        "Streamlit Secrets settings."
    )
    st.stop()


# =========================
# AVAILABLE MODELS
# =========================

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

    # Save user message

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)


    # Build conversation history

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
    # AI RESPONSE
    # =========================

    with st.chat_message("assistant"):

        answer = None
        errors = []

        try:

            with st.spinner("Thinking..."):

                for model_name in MODELS:

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
                            break

                        errors.append(
                            f"{model_name}: Empty response"
                        )

                    except Exception as e:

                        errors.append(
                            f"{model_name}: {str(e)}"
                        )


            if answer:

                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            else:

                st.error(
                    "Sorry, I couldn't generate a response. "
                    "Please try again later."
                )

                with st.expander("Technical Error Details"):
                    for error in errors:
                        st.code(error)

        except Exception as e:

            st.error("An unexpected error occurred.")


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

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True
    ):

        st.session_state.messages = []
        st.rerun()

    st.caption("Powered by Google Gemini")
