import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from PIL import ImageFile, Image
from pathlib import Path
from step_1_1 import OUT_DIR
from step_1_2 import uploaded_image
from step_1_3 import clear_session, init_session
from step_2_2 import synth_speech
from step_3_1 import generate_quiz, generate_feedback

import base64
from io import BytesIO

# 이미지 base64 인코딩
def img_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# 초기 페이지 설정
def init_page():
    st.set_page_config(
        page_title="영어 받아쓰기 연습",
        layout="wide",
        page_icon="🦜"
    )

    # 타이틀
    st.markdown(
        """
        <h1 style='text-align: center; font-size:48px; color: #4B89DC;'>🔊 영어 받아쓰기 연습</h1>
        """, unsafe_allow_html=True)

    # 설명 텍스트
    st.markdown(
        """
        <p style='text-align: center; font-size: 20px; color: #555;'>
        이미지를 올려주시면, AI가 문장을 생성해 문제를 출제합니다.<br>
        문장을 잘 듣고 빈칸을 채워보세요!<br>
        왼쪽의 <b>이미지 붙여넣기 📷</b> 에서 시작할 수 있습니다.
        </p>
        """, unsafe_allow_html=True)

    init_session(dict(quiz=[], answ=[], voice="en-US-Journey-F"))

# 퀴즈 세팅
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

# 퀴즈 표시
def show_quiz():
    st.divider()
    st.markdown("### 📌 문장을 듣고 빈칸을 채워주세요!")

    for idx, (quiz, answ, audio) in enumerate(zip(
        st.session_state["quiz"],
        st.session_state["answ"],
        st.session_state["audio"]
    )):
        key_input = f"input_{idx}"
        key_feedback = f"feedback_{idx}"
        init_session({key_input: "", key_feedback: ""})
        st.markdown(
            f"""
            테스트2324343
            """,
            unsafe_allow_html=True
        )
        with stylable_container(key=f"form_question_{idx}", css_styles="""{
            background-color: #F0F8FF;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0px 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }"""):
            # ✅ 중앙 정렬된 큰 숫자 문제 번호
            st.markdown(
                f"""
                <div style='text-align:center; font-size: 36px; font-weight: bold; color: #4B89DC; margin-bottom: 10px;'>
                    {idx + 1}
                </div>
                """,
                unsafe_allow_html=True
            )

            # 오디오
            st.audio(audio)

            # 퀴즈 문장
            quiz_display = quiz.replace("_____", "🔲")
            st.markdown(
                f"<p style='font-size:20px; color:#333;'><b>문제:</b> {quiz_display}</p>",
                unsafe_allow_html=True
            )

            # 입력란
            user_input = st.text_input(
                "정답을 입력하세요👇",
                value=st.session_state[key_input],
                key=key_input,
                placeholder="빈칸에 들어갈 단어를 정확히 입력하세요!",
            )

            # 제출 버튼
            submitted = st.button("정답 제출 ✅", key=f"submit_{idx}")

            # 피드백 생성
            if user_input and submitted:
                with st.spinner("정답 확인 중입니다...🔍"):
                    feedback = generate_feedback(user_input, answ)
                    st.session_state[key_feedback] = feedback

            # 해설 출력
            if st.session_state[key_feedback]:
                with st.expander("📚 해설 및 정답 보기", expanded=True):
                    st.markdown(f"**정답:** {answ}")
                    st.markdown(st.session_state[key_feedback])

# 퀴즈 리셋
def reset_quiz():
    if st.session_state["quiz"]:
        if st.button("🔄 새로운 문제로 연습하기", type="primary"):
            clear_session()
            st.rerun()

# 실행
if __name__ == "__main__":
    init_page()
    if img := uploaded_image(on_change=clear_session):
        set_quiz(img)
        show_quiz()
        reset_quiz()
