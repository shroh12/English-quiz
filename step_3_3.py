import streamlit as st
from step_1_2 import uploaded_image
from step_1_3 import clear_session, init_session
from step_3_1 import generate_feedback
from step_3_2 import init_page, reset_quiz, set_quiz
import random
import pandas as pd

def show_jimunhwa_percentage(quiz_data):
    """
    '지문화' 주제가 전체 문제 중 몇 퍼센트인지 계산하고 Streamlit에 시각적으로 출력합니다.
    """
    if isinstance(quiz_data, list):
        df = pd.DataFrame(quiz_data)
    else:
        df = quiz_data

    if "topic" not in df.columns:
        st.error("❌ 'topic' 컬럼이 존재하지 않습니다.")
        return

    total = len(df)
    count = len(df[df["topic"] == "지문화"])
    percentage = round((count / total) * 100, 2) if total > 0 else 0.0

    st.subheader("📊 '지문화' 문제 비율")
    st.metric(label="지문화 비율", value=f"{percentage}%", delta=f"{count} / {total}")
    
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
            
            quiz_display = quiz
            st.markdown(f"**문제:** {quiz_display}")

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

            if submitted:
                with st.spinner("채점 중입니다..."):
                    is_correct = user_choice == answ

                    if is_correct:
                        st.session_state[key_feedback] = "✅ 정답입니다! 🎉"
                    else:
                        feedback = generate_feedback(user_choice, answ)
                        st.session_state[key_feedback] = f"❌ 오답입니다.\n\n{feedback}"

                    if "quiz_data" not in st.session_state:
                        st.session_state["quiz_data"] = []

                    st.session_state["quiz_data"].append({
                        "question": quiz_display,
                        "topic": "지문화",
                        "correct": is_correct,
                        "difficulty": global_difficulty
                    })

        feedback = st.session_state.get(key_feedback, "")
        if feedback:
            with st.expander("📚 해설 보기", expanded=True):
                st.markdown(f"**정답:** {answ}")
                st.markdown(feedback)
                
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

    # ✅ 2. 난이도 선택 (공통 적용)
    difficulty_display = st.selectbox("문제 난이도를 선택하세요.", ["쉬움", "중간", "어려움"])
    difficulty_mapping = {
        "쉬움": "easy",
        "중간": "medium",
        "어려움": "hard"
    }
    global_difficulty = difficulty_mapping.get(difficulty_display, "medium")

    # ✅ 3. 이미지 업로드 → 퀴즈 생성
    if img := uploaded_image(on_change=clear_session):
        set_quiz(img, group_code)  # 퀴즈 세팅
        
        # ✅ 4. 퀴즈 출력 (난이도 전달)
        show_quiz(global_difficulty)
        
        # ✅ 5. '지문화' 문제 비율 출력
        if "quiz_data" in st.session_state:
            show_jimunhwa_percentage(st.session_state["quiz_data"])
        elif "quiz" in st.session_state and "choices" in st.session_state:
            st.info("문제 데이터에 'topic' 정보가 없어서 분석할 수 없습니다.")
        else:
            st.info("지문 데이터가 없어 비율을 계산할 수 없습니다.")

        reset_quiz()



