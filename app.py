import os
from typing import List, Dict
import streamlit as st
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

# Streamlit page configuration
st.set_page_config(page_title="JokeBot - AI Comedian", page_icon="🎭", layout="centered")

# Session state initialization
if "chat_history" not in st.session_state:
    st.session_state.chat_history: List[Dict[str, str]] = []

if "preferences" not in st.session_state:
    st.session_state.preferences = {
        "style": "Any",
        "length": "One-liner",
        "clean": True,
        "use_emoji": True,
        "roast_mode": False,
    }

def build_preferences_instruction(prefs: Dict[str, object]) -> str:
    style = prefs.get("style", "Any")
    length = prefs.get("length", "One-liner")
    clean = prefs.get("clean", True)
    use_emoji = prefs.get("use_emoji", True)
    roast = prefs.get("roast_mode", False)

    lines = [
        "You are JokeBot, a witty stand-up comedian who crafts clever, original jokes.",
        "Follow these rules:",
        "- Keep jokes playful, light-hearted, and creative.",
        "- Avoid hate speech, harassment, or harmful/unsafe content.",
        "- If asked for offensive or unsafe content, refuse politely and pivot to a clean alternative.",
        "- Prefer concise delivery and strong punchlines.",
    ]
    if clean:
        lines.append("- Stay family-friendly (PG).")
    else:
        lines.append("- PG-13 is allowed, but never cross safety or ethics boundaries.")

    if roast:
        lines.append("- Roast mode: Good-natured, gentle roast with consent; be playful, not mean-spirited.")
    else:
        lines.append("- No roasts unless explicitly requested by the user.")

    lines.append(f"- Target style: {style}.")
    lines.append(f"- Preferred length: {length} (one-liner < short bit < mini story).")
    lines.append(f"- Emoji: {'sprinkle a couple of fitting emojis' if use_emoji else 'avoid emojis'} unless user requests otherwise.")
    lines.append("- If the user provides a topic, weave it cleverly into the setup and punchline.")
    lines.append("- If the user asks for multiple options, provide 3 distinct variants.")

    return "\n".join(lines)

def get_system_messages(prefs: Dict[str, object]) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "system", "content": build_preferences_instruction(prefs)},
    ]

def truncate_history(history: List[Dict[str, str]], max_items: int = 24) -> List[Dict[str, str]]:
    # Keeps the most recent messages to stay within token limits
    if len(history) <= max_items:
        return history
    return history[-max_items:]

def generate_response(model: str, temperature: float) -> str:
    messages = get_system_messages(st.session_state.preferences) + truncate_history(st.session_state.chat_history)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content

def render_chat():
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

def add_user_message(content: str):
    st.session_state.chat_history.append({"role": "user", "content": content})

def add_assistant_message(content: str):
    st.session_state.chat_history.append({"role": "assistant", "content": content})

# Sidebar controls
with st.sidebar:
    st.title("JokeBot Settings")
    model = st.selectbox("Model", ["gpt-3.5-turbo", "gpt-4"], index=0)
    temperature = st.slider("Creativity", min_value=0.0, max_value=1.5, value=0.9, step=0.1)
    st.markdown("---")
    st.subheader("Style & Tone")
    st.session_state.preferences["style"] = st.selectbox(
        "Style",
        ["Any", "Pun", "Dad joke", "One-liner", "Observational", "Wordplay", "Riddle", "Knock-knock", "Absurdist"],
        index=0,
    )
    st.session_state.preferences["length"] = st.selectbox(
        "Length",
        ["One-liner", "Short bit", "Mini story"],
        index=0,
    )
    st.session_state.preferences["clean"] = st.checkbox("Keep it clean (PG)", value=True)
    st.session_state.preferences["use_emoji"] = st.checkbox("Use light emoji", value=True)
    st.session_state.preferences["roast_mode"] = st.checkbox("Roast mode (gentle, consensual)", value=False)
    st.markdown("---")
    if st.button("Clear chat"):
        st.session_state.chat_history = []
        st.experimental_rerun()

# Header
st.title("🎭 JokeBot")
st.caption("An AI comedian that delivers clever, clean jokes on demand.")

# Quick prompts
with st.container():
    st.write("Quick prompts:")
    cols = st.columns(4)
    quick_prompts = [
        "Tell me a one-liner about coffee.",
        "Make a clever pun about cats.",
        "Give me a knock-knock joke about space.",
        "Roast my procrastination (gently).",
    ]
    for i, qp in enumerate(quick_prompts):
        if cols[i].button(qp):
            add_user_message(qp)
            try:
                reply = generate_response(model, temperature)
                add_assistant_message(reply)
            except Exception as e:
                add_assistant_message(f"Oops, I hit a snag: {e}")

# Render chat history
render_chat()

# Chat input
user_input = st.chat_input("Ask for a joke or give me a topic...")
if user_input:
    add_user_message(user_input)
    with st.chat_message("assistant"):
        try:
            reply = generate_response(model, temperature)
        except Exception as e:
            reply = f"Sorry, I ran into an error: {e}"
        st.write(reply)
        add_assistant_message(reply)