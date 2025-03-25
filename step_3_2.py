import streamlit as st
from PIL import ImageFile
from pathlib import Path
from step_1_1 import OUT_DIR
from step_1_2 import uploaded_image
from step_1_3 import clear_session, init_session
from step_2_2 import synth_speech
from step_3_1 import generate_quiz
from step_3_1 import generate_feedback


def init_page():
    st.set_page_config(layout="wide")
    st.markdown(
        """
        <h1 style='text-align: left; background: -webkit-linear-gradient(left, #1E90FF, #000080); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>🔊 영어 받아쓰기 연습 웹 앱</h1>
        """, unsafe_allow_html=True)

    st.markdown(
        """
        #### 📌 서비스 소개
        이 서비스는 이미지에서 영어 문장을 생성하고 이를 듣고 받아쓰면서 영어 실력을 향상시키는 연습을 할 수 있도록 도와주는 웹 앱입니다. 왼쪽의 **이미지 붙여넣기**를 클릭해 원하는 이미지를 업로드하면 자동으로 문제가 생성됩니다.
        """)

    init_session(dict(quiz=[], answ=[], voice="en-US-Journey-F"))


def set_quiz(img: ImageFile.ImageFile):
    if img and not st.session_state["quiz"]:
        with st.spinner("문제를 출제중입니다...🤯"):
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
    zipped = zip(
        range(len(st.session_state["quiz"])),
        st.session_state["quiz"],
        st.session_state["answ"],
        st.session_state["audio"],
    )

    st.write("### 다음 문항의 빈칸을 듣고 채우시오.")

    for idx, quiz, answ, audio in zipped:
        key_input, key_feedback = f"input_{idx}", f"feedback_{idx}"
        init_session({key_input: "", key_feedback: ""})

        with st.form(f"form_question_{idx}", border=True):
            st.success(f"### {quiz}")
            st.audio(audio)

            col_user_input, col_submit = st.columns([8, 2])
            with col_user_input:
                user_input = st.text_input(
                    key_input,
                    value=st.session_state[key_input],
                    key=key_input,
                    label_visibility="collapsed",
                    placeholder="정답을 입력하세요"
                )
            with col_submit:
                submitted = st.form_submit_button("정답 제출", use_container_width=True)

            if user_input and submitted:
                with st.spinner("채점 중입니다..."):
                    feedback = generate_feedback(user_input, answ)
                    st.session_state[key_feedback] = feedback

            if st.session_state[key_feedback]:
                with st.expander("해설 보기", expanded=True):
                    st.markdown(st.session_state[key_feedback])


def reset_quiz():
    if st.session_state["quiz"]:
        with st.form("form_reset", border=False):
            if st.form_submit_button(label="새로운 문제 풀어보기",
                                     use_container_width=True, type="primary"):
                clear_session()
                st.rerun()


if __name__ == "__main__":
    init_page()
    if img := uploaded_image(on_change=clear_session):
        set_quiz(img)
        show_quiz()
        reset_quiz()
