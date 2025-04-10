import streamlit as st
from step_1_2 import uploaded_image
from step_1_3 import clear_session, init_session
from step_3_1 import generate_feedback
from step_3_2 import init_page, reset_quiz, set_quiz
import random
import pandas as pd

def show_quiz(global_difficulty="medium"):
    zipped = zip(
        range(len(st.session_state["quiz"])),
        st.session_state["quiz"],
        st.session_state["answ"],
        st.session_state["audio"],
        st.session_state["choices"],
    )

    for idx, quiz, answ, audio, choices in zipped:
        key_choice_1 = f"choice_{idx}_1"
        key_choice_2 = f"choice_{idx}_2"
        key_feedback = f"feedback_{idx}"
        init_session({key_choice_1: "", key_choice_2: "", key_feedback: ""})

        with st.form(f"form_question_{idx}", border=True):
            st.markdown("""
<div style="background-color:#e6f4ea; padding:10px; border-radius:10px; text-align: center;">
<h4 style="color:#006d2c; margin: 0;">문제</h4>
</div>
            """, unsafe_allow_html=True)

            st.audio(audio)

            # 문장을 빈칸 기준으로 나누기
            quiz_parts = quiz.split("_____")
            if len(quiz_parts) != 3:
                st.error("빈칸이 정확히 두 개가 아닙니다. 문제를 다시 생성해주세요.")
                continue

            st.markdown(f"{quiz_parts[0]} ____(1)____ {quiz_parts[1]} ____(2)____ {quiz_parts[2]}")

            if not choices or len(choices) != 2 or not all(isinstance(c, list) for c in choices):
                st.error("각 빈칸마다 선택지를 리스트로 제공해야 합니다. (총 2개의 리스트)")
                continue

            choice_1 = st.radio("첫 번째 빈칸을 채우세요:", choices[0], key=key_choice_1)
            choice_2 = st.radio("두 번째 빈칸을 채우세요:", choices[1], key=key_choice_2)

            submitted = st.form_submit_button("정답 제출 ✅", use_container_width=True)

            if submitted:
                with st.spinner("채점 중입니다..."):
                    user_answers = [choice_1, choice_2]
                    is_correct = user_answers == answ

                    if is_correct:
                        feedback = "✅ 정답입니다! 🎉"
                    else:
                        feedback_details = []
                        for i in range(2):
                            if user_answers[i] != answ[i]:
                                feedback_details.append(generate_feedback(user_answers[i], answ[i]))

                        feedback = f"❌ 오답입니다.\n\n" + "\n\n".join(feedback_details)

                    if "quiz_data" not in st.session_state:
                        st.session_state["quiz_data"] = []

                    st.session_state["quiz_data"].append({
                        "question": quiz,
                        "correct": is_correct,
                        "difficulty": global_difficulty
                    })

                    with st.expander("📚 해설 보기", expanded=True):
                        st.markdown(f"**정답:** {', '.join(answ)}")
                        st.markdown(feedback)

                        
if __name__ == \"__main__\":
    init_page()  # 페이지 초기화

    # ✅ 1. 학습자 그룹 선택
    group_display = st.selectbox(\"연령대를 선택하세요.\", [\"초등학생\", \"중학생\", \"고등학생\", \"성인\"])
    group_mapping = {
        \"초등학생\": \"elementary\",
        \"중학생\": \"middle\",
        \"고등학생\": \"high\",
        \"성인\": \"adult\"
    }
    group_code = group_mapping.get(group_display, \"default\")

    # ✅ 2. 난이도 선택
    difficulty_display = st.selectbox(\"문제 난이도를 선택하세요.\", [\"쉬움\", \"중간\", \"어려움\"])
    difficulty_mapping = {
        \"쉬움\": \"easy\",
        \"중간\": \"normal\",
        \"어려움\": \"hard\"
    }
    global_difficulty = difficulty_mapping.get(difficulty_display, \"normal\")

    # ✅ 3. 이미지 업로드 → 퀴즈 생성
    if img := uploaded_image(on_change=clear_session):
        st.session_state[\"total_score\"] = 0  # 점수 초기화

        set_quiz(img, group_code, global_difficulty)  # 퀴즈 세팅
        show_quiz(global_difficulty)  # 수정된 퀴즈 출력 (두 개의 빈칸 처리)

        reset_quiz()  # 리셋 버튼
