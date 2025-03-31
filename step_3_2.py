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
        page_title="앵무새 객관식 퀴즈",
        layout="wide",
        page_icon="🦜"
    )

    # 타이틀
    st.markdown(
        """
        <h1 style='text-align: center; font-size:48px; color: #4B89DC;'>🔊앵무새 객관식 퀴즈</h1>
        """, unsafe_allow_html=True)

    # 설명 텍스트
    st.markdown(
        """
        <p style='text-align: center; font-size: 20px; color: #555;'>
        <b>다 함께 퀴즈를 풀어봅시다!</b>
        </p>
        """, unsafe_allow_html=True)

    init_session(dict(quiz=[], answ=[], voice="en-US-Journey-F"))

# 퀴즈 세팅
def set_quiz(img: ImageFile.ImageFile):
    if img and not st.session_state["quiz"]:
        with st.spinner("문제를 준비 중입니다...🦜"):
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
    st.markdown("### 📌 문장을 듣고 알맞은 단어를 고르세요!")

    for idx, (quiz, answ, audio) in enumerate(zip(
        st.session_state["quiz"],
        st.session_state["answ"],
        st.session_state["audio"]
    )):
        key_choice = f"choice_{idx}"
        key_feedback = f"feedback_{idx}"
        init_session({key_choice: "", key_feedback: ""})

        with stylable_container(key=f"form_question_{idx}"):

            st.markdown(f"####  문제 {idx + 1}")
            st.audio(audio)

            # 보기 생성
            choices, correct_idx = generate_choices_with_answer(answ, DISTRACTOR_POOL)

            # 퀴즈 문장 표시
            quiz_display = quiz.replace("_____", "🔲")
            st.markdown(f"**문제:** {quiz_display}")
            
            # 힌트 보기
            with st.expander("💡 힌트 보기"):
                st.markdown(generate_hint(answ))
            # 객관식 보기 선택
            selected = st.radio("보기 중 하나를 선택하세요👇", choices, key=key_choice)

            # 제출 버튼
            if st.button("정답 제출 ✅", key=f"submit_{idx}"):
                if selected == choices[correct_idx]:
                    st.session_state[key_feedback] = "✅ 정답입니다! 🎉"
                else:
                    feedback = generate_feedback(selected, answ)
                    st.session_state[key_feedback] = f"❌ 오답입니다.\n\n{feedback}"

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
