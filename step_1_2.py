from pathlib import Path
import google.generativeai as genai
import streamlit as st 
from PIL import Image, ImageFile
from step_1_1 import OUT_DIR

def get_model(sys_prompt: str = None) -> genai.GenerativeModel:
    GEMINI_KEY = "AIzaSyAOFZ1Gy2E9jrGI4p92jNEtjOLZ9MDojh0"
    GEMINI_MODEL = "gemini-2.0-flash"
    genai.configure(api_key=GEMINI_KEY, transport="rest")
    return genai.GenerativeModel(GEMINI_MODEL,
                                 system_instruction=sys_prompt)
    
def uploaded_image(on_change=None, args=None) -> ImageFile.ImageFile | None:
    with st.sidebar:
        uploaded = st.file_uploader(
            "이미지 붙여넣기",  # 여기서 텍스트 변경
            label_visibility="visible",  # 텍스트가 보이도록 설정
            on_change=on_change,
            args=args
        )
        if uploaded is not None:
            with st.container(border=True):
                tmp_path = OUT_DIR / f"{Path(__file__).stem}.tmp"
                tmp_path.write_bytes(uploaded.getvalue())
                img = Image.open(tmp_path)
                st.image(img, use_column_width=True)
                return img
            
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    st.title("✨ 만들면서 배우는 멀티모달 AI")
    if img := uploaded_image():
        prompt = "공연은 어디에서 몇 시에 시작해? 한글로 대답해 줘."
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("✨"):
            with st.spinner("대화를 생성하는 중입니다."):
                model = get_model()
                chat = model.start_chat()
                resp = chat.send_message([img, prompt])
                st.markdown(resp.text)
