import streamlit as st
from step_1_2 import uploaded_image
from step_1_3 import clear_session, init_session
from step_3_1 import generate_feedback
from step_3_2 import init_page, reset_quiz, set_quiz
import random
import pandas as  pd

def show_jimunhwa_percentage(quiz_data):
    df = pd.DataFrame(quiz_data)

    # 필수 컬럼이 없으면 경고
    if not all(col in df.columns for col in ["topic", "correct", "difficulty"]):
        st.error("❌ topic, correct, difficulty 정보가 부족합니다.")
        return

    # 가중치 설정 (틀렸을 때 감점 정도)
    difficulty_weights = {
        "easy": 1.0,
        "medium": 1.5,
        "hard": 2.0
    }

    total = len(df)
    jimunhwa_total = len(df[df["topic"] == "지문화"])

    # ❌ 틀린 지문화 문제에만 패널티 적용
    penalty = sum(
        difficulty_weights.get(row["difficulty"], 1.0)
        for _, row in df.iterrows()
        if row["topic"] == "지문화" and not row["correct"]
    )

    # 감점 반영된 지문화 점수
    adjusted_score = max(jimunhwa_total - penalty, 0)
    percentage = round((adjusted_score / total) * 100, 2) if total > 0 else 0.0

    st.subheader("📊 '지문화' 문제 비율")
    st.metric(label="지문화 비율", value=f"{percentage}%", delta=f"{int(adjusted_score)} / {total}")
    
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

    # ✅ 1. 학습자 그룹 선택
    group_display = st.selectbox("연령대를 선택하세요.", ["초등학생", "중학생", "고등학생", "성인"])
    group_mapping = {
        "초등학생": "elementary",
        "중학생": "middle",
        "고등학생": "high",
        "성인": "adult"
    }
    group_code = group_mapping.get(group_display, "default")

    # ✅ 2. 이미지 업로드 → 퀴즈 생성
    if img := uploaded_image(on_change=clear_session):
        set_quiz(img, group_code)
        
        # ✅ 3. 퀴즈 출력
        show_quiz()
        
        # ✅ 4. '지문화' 문제 비율 출력
        if "quiz_data" in st.session_state:
            show_jimunhwa_percentage(st.session_state["quiz_data"])
        elif "quiz" in st.session_state and "choices" in st.session_state:
            # 예: topic이 포함되어 있다면 여기에 커스터마이징
            st.info("문제 데이터에 'topic' 정보가 없어서 분석할 수 없습니다.")
        else:
            st.info("지문 데이터가 없어 비율을 계산할 수 없습니다.")

        reset_quiz()

