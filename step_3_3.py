import streamlit as st
from step_1_2 import uploaded_image
from step_1_3 import clear_session, init_session
from step_3_1 import generate_feedback
from step_3_2 import init_page, reset_quiz, set_quiz
import random

def show_quiz():
    zipped = zip(
        range(len(st.session_state["quiz"])),
        st.session_state["quiz"],
        st.session_state["answ"],
        st.session_state["audio"],
        st.session_state["choices"],
    )

    for idx, quiz, answ, audio, choices in zipped:
    key_choice = f"choice_{idx}"
    key_feedback = f"feedback_{idx}"
    init_session({key_choice: "", key_feedback: ""})

    with st.form(f"form_question_{idx}", border=True):
        st.markdown("""
        <div style="background-color:#e6f4ea; padding:10px; border-radius:10px; text-align: center;">
            <h4 style="color:#006d2c; margin: 0;">문제</h4>
        </div>
        """, unsafe_allow_html=True)

        st.audio(audio)

            quiz_display = quiz
            st.markdown(f"**문제:** {quiz_display}")

            if not choices or not isinstance(choices, list):
                st.error("선택지가 없습니다. 다시 문제를 생성하세요.")
                continue
            
            # 기본값 유효성 검증
            if st.session_state[key_choice] not in choices:
                st.session_state[key_choice] = choices[0]

            user_choice = st.radio(
                "보기 중 하나를 선택하세요👇",
                choices,
                key=key_choice
            )

            # 반드시 form_submit_button 포함
            submitted = st.form_submit_button("정답 제출 ✅", use_container_width=True)

            if submitted:
                with st.spinner("채점 중입니다..."):
                    if user_choice == answ:
                        st.session_state[key_feedback] = "✅ 정답입니다! 🎉"
                    else:
                        feedback = generate_feedback(user_choice, answ)
                        st.session_state[key_feedback] = f"❌ 오답입니다.\n\n{feedback}"

        # 피드백 출력
        feedback = st.session_state.get(key_feedback, "")
        if feedback:
            with st.expander("📚 해설 보기", expanded=True):
                st.markdown(f"**정답:** {answ}")
                st.markdown(feedback)

if __name__ == "__main__":
    init_page()  # 페이지 초기화
    if img := uploaded_image(on_change=clear_session):  # 이미지 등록
        set_quiz(img)  # 퀴즈 출제 (객관식용)
        show_quiz()  # 객관식 퀴즈 출력
        reset_quiz()  # 퀴즈 재출제

