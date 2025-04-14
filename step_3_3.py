import streamlit as st
from step_1_2 import uploaded_image
from step_1_3 import clear_session, init_session
from step_3_1 import generate_feedback
from step_3_2 import (
    init_page, reset_quiz, show_score_summary, 
    init_score, update_score, set_quiz
)
import pandas as pd

def init_score():
    st.session_state["total_score"] = 0
    st.session_state["quiz_data"] = []

def update_score(is_correct: bool):
    if "total_score" not in st.session_state:
        init_score()
    if is_correct:
        st.session_state["total_score"] += 10

def show_quiz(global_difficulty="medium"):
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
            quiz_display = quiz.replace("**", "")
            st.markdown(f"문제: {quiz_display}")
 
            if not choices or not isinstance(choices, list):
                st.error("선택지가 없습니다. 다시 문제를 생성하세요.")
                continue
 
            # 여기서부터 '빈칸 1 보기' 부분이 있었던 곳 (삭제/주석 처리)
            # st.markdown("🔸 **빈칸 1 보기:**")
            # for i, choice in enumerate(choices, start=1):
            #     st.markdown(f"{i}. {choice}")
 
            # 기본값 유효성 검증
            if st.session_state[key_choice] not in choices:
                st.session_state[key_choice] = choices[0]
 
            # 객관식 보기만 남김
            user_choice = st.radio(
                "보기 중 하나를 선택하세요👇",
                choices,
                key=key_choice
            )
 
            submitted = st.form_submit_button("정답 제출 ✅", use_container_width=True)
            submitted_flag_key = f"submitted_{idx}"
 
            if submitted and not st.session_state.get(submitted_flag_key):
                st.session_state[submitted_flag_key] = True  # 중복 제출 방지
                
                with st.spinner("채점 중입니다..."):
                    user_choices = [user_choice]
                    is_correct = [user_choice] == answ

                    update_score(is_correct)  # ✅ 점수 누적
                    
                    if is_correct:
                        feedback = "✅ 정답입니다! 🎉"
                    else:
                        # 오답일 경우 해설 생성
                        student_word = user_choices[0]  # 첫 번째 빈칸 기준
                        correct_word = answ[0]
                        feedback_detail = generate_feedback(student_word, correct_word)
                        feedback = f"❌ 오답입니다.\n\n{feedback_detail}"
 
                    if "quiz_data" not in st.session_state:
                        st.session_state["quiz_data"] = []
 
                    st.session_state["quiz_data"].append({
                        "question": quiz_display,
                        "correct": is_correct,
                        "difficulty": global_difficulty
                    })
                    with st.expander("📚 해설 보기", expanded=True):
                        if len(answ) == 1:
                            st.markdown(f"**정답:** {answ[0]}")
                        else:
                            st.markdown(f"**정답:** {', '.join(answ)}") 
                            
                        st.markdown(feedback, unsafe_allow_html=True)
                        
if __name__ == "__main__":
    init_page()  # 페이지 초기화

    # ✅ 1. 학습자 그룹 선택
    group_display = st.selectbox("연령대를 선택하세요.", ["초등학생", "중학생", "고등학생", "성인"])
    group_mapping = {
        "초등학생": "elementary",
        "중학생": "middle",
        "고등학생": "high",
        "성인": "adult"
    }
    group_code = group_mapping.get(group_display, "default")

    # ✅ 2. 난이도 선택
    difficulty_display = st.selectbox("문제 난이도를 선택하세요.", ["쉬움", "중간", "어려움"])
    difficulty_mapping = {
        "쉬움": "easy",
        "중간": "normal",
        "어려움": "hard"
    }
    global_difficulty = difficulty_mapping.get(difficulty_display, "normal")

    # ✅ 3. 이미지 업로드 → 퀴즈 생성
    if img := uploaded_image(on_change=clear_session):
        init_score()

        set_quiz(img, group_code, global_difficulty)  # 퀴즈 세팅
        show_quiz(global_difficulty)  # 퀴즈 출력 (정답 제출 포함)

        if st.session_state.get("quiz_data"):
            show_score_summary()

        reset_quiz()  # 리셋 버튼
