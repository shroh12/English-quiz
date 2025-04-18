import streamlit as st
from step_1_2 import uploaded_image
from step_1_3 import clear_session, init_session
from step_3_1 import generate_quiz, generate_feedback
from step_3_2 import img_to_base64, init_page, set_quiz, reset_quiz, show_quiz, init_score, update_score
import pandas as pd

def init_score():
    if "total_score" not in st.session_state:
        st.session_state["total_score"] = 0
    if "quiz_data" not in st.session_state:
        st.session_state["quiz_data"] = []

def update_score(is_correct: bool):
    # 점수만 조건부 초기화 (퀴즈 기록은 건드리지 않음)
    if "total_score" not in st.session_state:
        st.session_state["total_score"] = 0

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
                    is_correct = user_choice == answ[0]
                    update_score(is_correct)  # ✅ 점수 누적
                    
                    if is_correct:
                        feedback = "✅ 정답입니다! 🎉"
                    else:
                        try:
                        # 오답일 경우 해설 생성
                            feedback_detail = generate_feedback(user_choice, answ[0])
                            feedback = f"❌ 오답입니다.\n\n{feedback_detail}"
                        except Exception as e:
                            feedback = f"⚠️ 피드백 생성 중 오류 발생: {e}"
                    
                    if "quiz_data" not in st.session_state:
                        st.session_state["quiz_data"] = []

                    if not any(q["question"] == quiz_display for q in st.session_state["quiz_data"]):
                        st.session_state["quiz_data"].append({
                            "question": quiz_display,
                            "correct": is_correct,
                            "difficulty": global_difficulty
                        })
                    with st.expander("📚 해설 보기", expanded=True):
                        st.markdown(f"**정답:** {answ[0]}")    
                        st.markdown(feedback, unsafe_allow_html=True)
                        
def show_score_summary():
    if "quiz_data" not in st.session_state or not st.session_state["quiz_data"]:
        return

    total = len(st.session_state["quiz_data"])
    correct = sum(1 for q in st.session_state["quiz_data"] if q.get("correct") is True)

    score = correct * 10  # ✅ 문제당 10점 기준
    accuracy = round((correct / total) * 100, 1) if total else 0.0

    st.markdown("---")
    st.markdown("### 🏁 총 점수")
    st.success(f"총 {total}문제 중 **{correct}문제**를 맞췄어요! (**정답률: {accuracy}%**)")
    st.progress(accuracy / 100)
    st.markdown(f"<h3 style='text-align:center;'>{score}점</h3>", unsafe_allow_html=True)

    
if __name__ == "__main__":
    init_page()

    # 1. 그룹 선택
    group_display = st.selectbox("연령대를 선택하세요.", ["초등학생", "중학생", "고등학생", "성인"])
    group_mapping = {
        "초등학생": "elementary",
        "중학생": "middle",
        "고등학생": "high",
        "성인": "adult"
    }
    group_code = group_mapping.get(group_display, "default")

    # 2. 난이도 선택
    difficulty_display = st.selectbox("문제 난이도를 선택하세요.", ["쉬움", "중간", "어려움"])
    difficulty_mapping = {
        "쉬움": "easy",
        "중간": "normal",
        "어려움": "hard"
    }
    global_difficulty = difficulty_mapping.get(difficulty_display, "normal")

    # 3. 이미지 업로드 or 복원
    if st.session_state.get("new_problem") and "img_bytes" in st.session_state:
        img = Image.open(BytesIO(st.session_state["img_bytes"]))
        st.session_state["new_problem"] = False
    else:
        img = uploaded_image()

    if img:
        st.session_state["img"] = img

        if "total_score" not in st.session_state or "quiz_data" not in st.session_state:
            init_score()

        set_quiz(img, group_code, global_difficulty)
        show_quiz(global_difficulty)

        if st.session_state.get("quiz_data"):
            show_score_summary()

        reset_quiz()


