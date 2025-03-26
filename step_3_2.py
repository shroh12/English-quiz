import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from PIL import ImageFile, Image
from pathlib import Path
from step_1_1 import OUT_DIR
from step_1_2 import uploaded_image
from step_1_3 import clear_session, init_session
from step_2_2 import synth_speech
from step_3_1 import generate_quiz, generate_feedback


def init_page():
    st.set_page_config(
    layout="wide", 
    page_icon="🦜",  # 앵무새 이모지로 변경
)

    st.markdown(
        """
        <h1 style='text-align: center; font-size:48px; color: #4B89DC;'>🔊 영어 받아쓰기 연습</h1>
        """, unsafe_allow_html=True)	

    img = Image.open('img/angmose.jpg')
    img = img.resize((500, 500))

# 중앙 정렬된 이미지 렌더링
    st.markdown(
        f"""
        <div style='text-align: center;'>
            <img src='data:image/png;base64,{Image_to_base64(img)}' width='500'/>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style='text-align: center; font-size: 20px; color: #555;'>
        이미지를 올려주시면, AI가 문장을 생성해 문제를 출제합니다. 문장을 잘 듣고 빈칸을 채워보세요!<br>
        왼쪽의 <b>이미지 붙여넣기 📷</b> 에서 시작할 수 있습니다.
        </p>
        """, unsafe_allow_html=True)

    init_session(dict(quiz=[], answ=[], voice="en-US-Journey-F"))

def set_quiz(img: ImageFile.ImageFile):
    if img and not st.session_state["quiz"]:
        with st.spinner("문제를 준비 중입니다...🤔"):
            quiz, answ = generate_quiz(img)

            audio = []
            for idx, sent in enumerate(answ):
                wav_file = synth_speech(sent, st.session_state["voice"], "wav")
                path = OUT_DIR / f"{Path(__file__).stem}_{idx}.wav"
                with open(path, "wb") as fp:
                    fp.write(wav_file)
                    audio.append(path.as_posix())

            st.session_state["quiz"] = quiz
            st.session_state["answ"] = answ
            st.session_state["audio"] = audio


def show_quiz():
    st.divider()
    st.markdown("### 📌 문장을 듣고 빈칸을 채워주세요!")

    for idx, (quiz, answ, audio) in enumerate(zip(st.session_state["quiz"], st.session_state["answ"], st.session_state["audio"])):
        key_input, key_feedback = f"input_{idx}", f"feedback_{idx}"
        init_session({key_input: "", key_feedback: ""})

        with stylable_container(key=f"form_question_{idx}", css_styles="""
            {
                background-color: #F0F8FF;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0px 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            """):
            st.audio(audio)

            quiz_display = quiz.replace("_____", "🔲")
            st.markdown(f"<p style='font-size:20px; color:#333;'><b>문제:</b> {quiz_display}</p>", unsafe_allow_html=True)

            user_input = st.text_input(
                "정답을 입력하세요👇",
                value=st.session_state[key_input],
                key=key_input,
                placeholder="빈칸에 들어갈 단어를 정확히 입력하세요!",
            )

            submitted = st.button("정답 제출 ✅", key=f"submit_{idx}")

            if user_input and submitted:
                with st.spinner("정답 확인 중입니다...🔍"):
                    feedback = generate_feedback(user_input, answ)
                    st.session_state[key_feedback] = feedback

            if st.session_state[key_feedback]:
                with st.expander("📚 해설 및 정답 보기", expanded=True):
                    st.markdown(f"**정답:** {answ}")
                    st.markdown(st.session_state[key_feedback])


def reset_quiz():
    if st.session_state["quiz"]:
        if st.button("🔄 새로운 문제로 연습하기", type="primary"):
            clear_session()
            st.rerun()


if __name__ == "__main__":
    init_page()
    if img := uploaded_image(on_change=clear_session):
        set_quiz(img)
        show_quiz()
        reset_quiz()
