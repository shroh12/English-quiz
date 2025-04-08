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

    # 점수 초기화
    if "total_score" not in st.session_state:
        st.session_state["total_score"] = 0

    for idx, quiz, answ, audio, choices in zipped:
        key_choice = f"choice_{idx}"
        key_feedback = f"feedback_{idx}"
        init_session({key_choice: "", key_feedback: ""})

        with st.form(f"form_question_{idx}", border=True):
            # 🔹 문제 타이틀 블록
            st.markdown("""
            <div style="background-color:#e6f4ea; padding:12px; border-radius:12px; text-align:center;">
                <h4 style="color:#006d2c; margin:0;">🎧 문제</h4>
            </div>
            """, unsafe_allow_html=True)

            # 🔹 오디오 재생
            st.audio(audio)

            # 🔹 문제 문장 하이라이트 처리
            quiz_display = quiz.replace("**", "")
            quiz_highlighted = quiz_display.replace(
                "_____", "<span style='color:red; font-weight:bold;'>_____</span>"
            )
            st.markdown(f"<p style='font-size:17px;'>{quiz_highlighted}</p>", unsafe_allow_html=True)

            # 🔹 안내 텍스트
            st.markdown("#### ✏️ 보기 중 알맞은 단어를 선택하세요")

            # 🔹 보기 출력 (빈칸 수만큼)
            user_choices = []
            for i in range(len(answ)):
                choice_set = choices[i] if i < len(choices) else []
                user_choice = st.radio(
                    " ",
                    choice_set,
                    key=f"{key_choice}_{i}",
                    label_visibility="collapsed"
                )
                user_choices.append(user_choice)

            # 🔹 정답 제출
            submitted = st.form_submit_button("정답 제출 ✅", use_container_width=True)

            if submitted:
                with st.spinner("채점 중입니다..."):
                    is_correct = user_choices == answ
                    feedback = "✅ 정답입니다! 🎉" if is_correct else f"❌ 오답입니다.\n\n정답: {', '.join(answ)}"

                    # 점수 누적
                    if is_correct:
                        st.session_state["total_score"] += 10

                    # 퀴즈 기록 저장
                    if "quiz_data" not in st.session_state:
                        st.session_state["quiz_data"] = []

                    st.session_state["quiz_data"].append({
                        "question": quiz_display,
                        "correct": is_correct,
                        "difficulty": global_difficulty
                    })

                    # 해설 출력
                    with st.expander("📘 해설 보기", expanded=True):
                        st.markdown(feedback)

    # 🔹 최종 점수 출력
    if "total_score" in st.session_state:
        final_score = min(st.session_state["total_score"], 100)
        st.markdown("---")
        st.subheader("🎯 최종 점수")
        st.markdown(f"**{final_score}점 / 100점**")

        if final_score == 100:
            st.success("💯 완벽합니다! 퀴즈 마스터네요!")
        elif final_score >= 70:
            st.info("👍 잘했어요! 조금만 더 연습해볼까요?")
        else:
            st.warning("📚 괜찮아요! 복습하고 다시 도전해봐요 :)")
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
        # ✅ 점수 초기화는 퀴즈 시작 전에!
        st.session_state["total_score"] = 0

        # ✅ 퀴즈 세팅 및 출력
        set_quiz(img, group_code, global_difficulty)
        show_quiz(global_difficulty)

        # ✅ 리셋 버튼
        reset_quiz()
