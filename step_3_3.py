import streamlit as st
from step_1_2 import uploaded_image
from step_1_3 import clear_session, init_session
from step_3_1 import generate_feedback
from step_3_2 import init_page, reset_quiz, set_quiz


def show_quiz():
    zipped = zip(
        range(len(st.session_state["quiz"])),
        st.session_state["quiz"],
        st.session_state["answ"],
        st.session_state["audio"],
    )
    for idx, quiz, answ_list, audio in zipped:
        if not isinstance(answ_list, list):
            answ_list = [answ_list]

        with st.form(f"form_question_{idx}", border=True):
            st.success(f"### {quiz}")
            st.audio(audio)

            user_inputs = []
            # 정답 개수만큼 입력창 생성
            for answ_idx in range(len(answ_list)):
                key_input = f"input_{idx}_{answ_idx}"
                init_session({key_input: ""})

                user_input = st.text_input(
                    label=f"정답 입력 {answ_idx + 1}",
                    key=key_input,
                    value=st.session_state[key_input]
                )
                user_inputs.append(user_input)

            # 모든 필드가 채워져야 버튼 활성화 (옵션)
            is_ready_to_submit = all(user_inputs)

            submitted = st.form_submit_button(
                "정답 제출",
                use_container_width=True,
                disabled=not is_ready_to_submit  # 필수입력 다 안하면 비활성화
            )

            if submitted and is_ready_to_submit:
                with st.spinner():
                    feedbacks = []
                    for input_val, correct_ans in zip(user_inputs, answ_list):
                        feedback = generate_feedback(input_val, correct_ans)
                        feedbacks.append(feedback)

                    st.session_state[f"feedback_{idx}"] = feedbacks

            feedbacks = st.session_state.get(f"feedback_{idx}", [])
            if feedbacks:
                with st.expander("해설 보기", expanded=True):
                    for f_idx, fb in enumerate(feedbacks, start=1):
                        st.markdown(f"**정답 {f_idx}에 대한 피드백:** {fb}")


if __name__ == "__main__":
    init_page()
    if img := uploaded_image(on_change=clear_session):
        set_quiz(img)
        show_quiz()
        reset_quiz()

        set_quiz(img)  # 퀴즈 출제
        show_quiz()  # 퀴즈 출력
        reset_quiz()  # 퀴즈 재출제
