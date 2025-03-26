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
        # answ_list가 리스트 형태로 정답이 여러 개 있을 수 있음
        if not isinstance(answ_list, list):
            answ_list = [answ_list]  # 단일 정답을 리스트로 변환

        with st.form(f"form_question_{idx}", border=True):
            st.success(f"### {quiz}")
            st.audio(audio)

            user_inputs = []  # 입력값 저장할 리스트

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

            submitted = st.form_submit_button("정답 제출", use_container_width=True)

            if submitted:
                with st.spinner():
                    feedbacks = []
                    # 입력값과 정답을 하나씩 비교하여 피드백 생성
                    for input_val, correct_ans in zip(user_inputs, answ_list):
                        feedback = generate_feedback(input_val, correct_ans)
                        feedbacks.append(feedback)

                    # 피드백 세션값 저장
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
