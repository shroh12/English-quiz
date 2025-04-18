import base64
from pathlib import Path
import google.generativeai as genai
import streamlit as st 
from PIL import Image, ImageFile
from step_1_1 import OUT_DIR
from io import BytesIO

def img_to_base64(img: Image.Image) -> str:
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    byte_data = buf.getvalue()
    return base64.b64encode(byte_data).decode()

def get_model(sys_prompt: str = None) -> genai.GenerativeModel:
    GEMINI_KEY = st.secrets['GEMINI_KEY']
    GEMINI_MODEL = "gemini-2.0-flash"
    genai.configure(api_key=GEMINI_KEY, transport="rest")
    return genai.GenerativeModel(GEMINI_MODEL,
                                 system_instruction=sys_prompt)

def uploaded_image(on_change=None, args=None) -> Image.Image | None:
    with st.sidebar:
        # 타이틀
        st.markdown(
            "<div style='text-align: center; font-weight: bold; font-size: 25px;'>이미지 업로드</div>",
            unsafe_allow_html=True
        )

        # 안내 이미지
        img = Image.open('img/angmose.jpg').resize((300, 300))
        st.markdown(
            f"""
            <div style="text-align: center; padding-bottom: 10px;">
                <img src="data:image/png;base64,{img_to_base64(img)}"
                    width="200"
                    style="border-radius: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);" />
            </div>
            """,
            unsafe_allow_html=True
        )

        # 설명
        st.markdown(
            """
             <div style='text-align: left; font-size: 15px; color: #444; line-height: 1.6; padding-left: 5px;'>
                이미지를 업로드 하시면<br>
                AI가 문장을 생성해 퀴즈를 출제합니다.<br>
                문장을 잘 듣고 퀴즈를 풀어보세요.
            </div>
            """,
            unsafe_allow_html=True
        )

        # 파일 업로더
        uploaded = st.file_uploader(
            label="",
            label_visibility="collapsed",
            on_change=on_change,
            args=args
        )

        if uploaded is not None:
            with st.container(border=True):
                # 이미지 열기 및 세션에 저장
                img = Image.open(uploaded).convert("RGB")
                st.image(img, use_container_width=True)

                # 세션에 이미지 객체와 바이트 저장
                st.session_state["img"] = img

                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state["img_bytes"] = buf.getvalue()

                return img

        # 업로드한 적은 있고 img_bytes가 있으면 복원
        elif "img_bytes" in st.session_state:
            img = Image.open(BytesIO(st.session_state["img_bytes"]))
            st.image(img, use_container_width=True)
            return img

        return None

if __name__ == "__main__":
    st.set_page_config(page_title="앵무 받아쓰기", layout="wide", page_icon="🦜")
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
                chat = model.start_chat()
                resp = chat.send_message([img, prompt])
                st.markdown(resp.text)
