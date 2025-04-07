import streamlit as st
from step_1_2 import uploaded_image
from step_1_3 import clear_session, init_session
from step_3_1 import generate_feedback
from step_3_2 import set_quiz_batch, show_quiz_batch, reset_quiz
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
    
def show_quiz_batch(global_difficulty="medium"):
    total = len(st.session_state["quiz"])

    with st.form("quiz_form", clear_on_submit=False):
        for idx in range(total):
            quiz = st.session_state["quiz"][idx]
            answ = st.session_state["answ"][idx]
            audio = st.session_state["audio"][idx]
            choices = st.session_state["choices"][idx]

            key_choice = f"choice_{idx}"
            if key_choice not in st.session_state:
                st.session_state[key_choice] = ""

            st.markdown(f"""
                <div style="background-color:#e6f4ea;padding:10px;border-radius:10px;margin:10px 0;">
                    <h5>📝 문제 {idx+1}</h5>
                    <audio controls style="width:100%; margin-bottom: 10px;">
                        <source src="{audio}" type="audio/wav">
                    </audio>
                    <p><strong>{quiz}</strong></p>
                </div>
            """, unsafe_allow_html=True)

            if isinstance(choices[0], list):
                choices = choices[0]

            st.radio("보기", choices, key=key_choice, label_visibility="collapsed")

        # ✅ 전체 문제 제출 버튼
        submitted = st.form_submit_button("정답 제출 ✅", use_container_width=True)

    # ✅ 채점 및 결과 출력
    if submitted:
        score = 0
        st.subheader("📊 결과")
        for idx in range(total):
            user = st.session_state.get(f"choice_{idx}", "")
            correct = st.session_state["answ"][idx]
            if user == correct:
                score += 1
                st.success(f"문제 {idx+1}: ✅ 정답 ({user})")
            else:
                st.error(f"문제 {idx+1}: ❌ 오답 (선택: {user}, 정답: {correct})")

        st.markdown(f"## 🏁 총점: **{score} / {total}**")
        if score >= 9:
            st.success("🎉 훌륭해요! 퀴즈 마스터!")
        elif score >= 6:
            st.info("👍 꽤 잘했어요! 조금만 더 연습하면 완벽!")
        else:
            st.warning("📚 괜찮아요! 다시 도전해볼까요?")
                
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
        "중간": "normal",
        "어려움": "hard"
    }
    global_difficulty = difficulty_mapping.get(difficulty_display, "normal")

    # ✅ 3. 이미지 업로드 → 퀴즈 생성
    if img := uploaded_image(on_change=clear_session):
        set_quiz_batch(img, group_code, global_difficulty)  # 🔁 다중 문제 세팅

        # ✅ 4. 퀴즈 출력 (한 번에 10문제 + 점수 계산)
        show_quiz_batch(global_difficulty)  # 🔁 변경된 함수 사용

        # ✅ 5. '지문화' 문제 비율 출력
        if "quiz_data" in st.session_state:
            show_jimunhwa_percentage(st.session_state["quiz_data"])
        elif "quiz" in st.session_state and "choices" in st.session_state:
            st.info("문제 데이터에 'topic' 정보가 없어서 분석할 수 없습니다.")
        else:
            st.info("지문 데이터가 없어 비율을 계산할 수 없습니다.")

        reset_quiz()


