import streamlit as st
from step_1_2 import uploaded_image
from step_1_3 import clear_session, init_session
from step_3_1 import generate_feedback
from step_3_2 import init_page, reset_quiz, set_quiz
import random

def show_quiz():
    # 각 퀴즈 문항의 인덱스, 문제, 정답, 오디오, 보기 리스트를 함께 묶어서 처리
    zipped = zip(
        range(len(st.session_state["quiz"])),
        st.session_state["quiz"],
        st.session_state["answ"],
        st.session_state["audio"],
        st.session_state["choices"],
    )
    # 묶은 데이터를 풀어 각 문항을 순서대로 처리
    for idx, quiz, answ, audio, choices in zipped:
        key_choice = f"choice_{idx}"
        key_feedback = f"feedback_{idx}"
        init_session({key_choice: "", key_feedback: ""})
        
         # 각 문항을 개별적인 Streamlit 폼으로 표시
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

    # ✅ 학령 구분 기준 선택 UI
    group_input = st.selectbox("대상 학습자 연령대를 선택하세요.", ["초등학생", "중학생", "고등학생", "성인"])

    # 이미지 업로드 + 퀴즈 실행
    if img := uploaded_image(on_change=clear_session):  # 이미지 등록
        set_quiz(img, group_input)  # ✅ 학령 그룹으로 전달
        show_quiz()
        reset_quiz()

