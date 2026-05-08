import streamlit as st

def render_interview_chat(messages, chat_history):
    with messages:
        for msg in chat_history:
            avatar = "static/Element 20.png" if msg["role"] == "assistant" else "static/Element 21.png"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])
