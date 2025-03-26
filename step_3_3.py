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

    for idx, quiz, answ_list, audio in zipped:
        # 퀴즈 내 빈칸("_____") 개수를 세어서 정답 입력칸 생성
        num_blanks = quiz.count("_____")

        # answ_list를 빈칸 개수와 맞추기 위해 재조정
        if not isinstance(answ_list, list):
            answ_list = [answ_list]
        answ_list = answ_list[:num_blanks]

        with st.form(f"form_question_{idx}", border=True):
            st.success(f"### {quiz}")
            st.audio(audio)

            user_inputs = []

            # 빈칸 수만큼 입력창 생성
            for answ_idx in range(num_blanks):
                key_input = f"input_{idx}_{answ_idx}"
                init_session({key_input: ""})

                user_input = st.text_input(
                    label=f"정답 입력 {answ_idx + 1}",
                    key=key_input,
                    value=st.session_state[key_input]
                )
                user_inputs.append(user_input)

            submitted = st.form_submit_button("정답 제출", use_container_width=True)

            if submitted:
                with st.spinner():
                    feedbacks = []

                    # 입력값과 정답을 개수만큼 비교하여 피드백 생성
                    for input_val, correct_ans in zip(user_inputs, answ_list):
                        feedback = generate_feedback(input_val, correct_ans)
                        feedbacks.append(feedback)

                    # 피드백 세션 저장
                    st.session_state[f"feedback_{idx}"] = feedbacks

            # 피드백 출력
            feedbacks = st.session_state.get(f"feedback_{idx}", [])
            if feedbacks:
                with st.expander("해설 보기", expanded=True):
                    for f_idx, fb in enumerate(feedbacks, start=1):
                        st.markdown(f"**정답 {f_idx}에 대한 피드백:** {fb}")


if __name__ == "__main__":
    init_page()  # 페이지 초기화
    if img := uploaded_image(on_change=clear_session):  # 이미지 등록
        set_quiz(img)  # 퀴즈 출제
        show_quiz()  # 퀴즈 출력
        reset_quiz()  # 퀴즈 재출제
