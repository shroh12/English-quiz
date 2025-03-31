import streamlit as st
from step_1_2 import uploaded_image
from step_1_3 import clear_session, init_session
from step_3_1 import generate_feedback
from step_3_2 import init_page, reset_quiz, set_quiz


def show_quiz():  # 퀴즈 출력 위젯
    zipped = zip(
        range(len(st.session_state["quiz"])),
        st.session_state["quiz"],
        st.session_state["answ"],
        st.session_state["audio"],
    )

    for idx, quiz, answ, audio in zipped:
        # 정답은 항상 문자열 하나라고 가정
        key_input = f"input_{idx}"
        key_feedback = f"feedback_{idx}"
        init_session({key_input: "", key_feedback: ""})

        with st.form(f"form_question_{idx}", border=True):
            st.success(f"### {quiz}")
            st.audio(audio)

            user_input = st.text_input(
                label="정답 입력",
                key=key_input,
                value=st.session_state[key_input]
            )

            submitted = st.form_submit_button("정답 제출", use_container_width=True)

            if submitted:
                with st.spinner():
                    feedback = generate_feedback(user_input, answ)
                    st.session_state[key_feedback] = feedback

        # 피드백 출력
        feedback = st.session_state.get(key_feedback, "")
        if feedback:
            with st.expander("📚 해설 보기", expanded=True):
                st.markdown(f"**정답:** {answ}")
                st.markdown(f"**피드백:** {feedback}")


if __name__ == "__main__":
    init_page()  # 페이지 초기화
    if img := uploaded_image(on_change=clear_session):  # 이미지 등록
        set_quiz(img)  # 퀴즈 출제
        show_quiz()  # 퀴즈 출력
        reset_quiz()  # 퀴즈 재출제
