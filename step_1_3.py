import google.generativeai as genai
import streamlit as st 
from PIL import ImageFile
from step_1_2 import get_model, uploaded_image

def init_session(keys: dict):
    for key, value in keys.items():
        if key not in st.session_state:
            st.session_state[key] = value
            
def clear_session(*exclude):
    for key in st.session_state.keys():
        if exclude is None or key not in exclude:
            del st.session_state[key]

def init_page():
    st.set_page_config(layout="wide")
    st.title("✨ 만들면서 배우는 멀티모달 AI")
    model = get_model()
    chat = model.start_chat()
    init_session(dict(chat=chat, msgs=[]))

def show_messages():
    for row in st.session_state["msgs"]:
        with st.chat_message(row["role"]):
            st.markdown(row["content"])
            
def send_image(img: ImageFile):
    chat: genai.ChatSession = st.session_state["chat"]
    if not chat.history:
        with st.spinner("이미지를 분석하는 중입니다."):
            chat.send_message([img, "이미지를 분석하고, 내 질문에 대답해줘."])
            
def send_user_input():
    if prompt := st.chat_input("여기에 대화를 입력하세요."):
        msgs: list = st.session_state["msgs"]
        with st.chat_message("user"):
            st.markdown(prompt)
            msgs.append(dict(role="user", content=prompt))
        with st.chat_message("✨"):
            with st.spinner("대화를 생성하는 중입니다."):
                chat: genai.ChatSession = st.session_state["chat"]
                resp = chat.send_message(prompt)
                st.markdown(resp.text)
                msgs.append(dict(role="✨", content=resp.text))

if __name__ == "__main__":
    init_page()
    if img := uploaded_image(on_change=clear_session):
        show_messages()
        send_image(img)
        send_user_input()