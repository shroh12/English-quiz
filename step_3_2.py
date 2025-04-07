import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from PIL import ImageFile, Image
from pathlib import Path
from step_1_1 import OUT_DIR
from step_1_2 import uploaded_image
from step_1_3 import clear_session, init_session
from step_2_2 import synth_speech
from step_3_1 import generate_quiz, generate_feedback

import base64
from io import BytesIO

# 이미지 base64 인코딩 (필요한 경우 유지)
def img_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# 초기 페이지 설정
def init_page():
    st.set_page_config(
        page_title="앵무새 객관식 퀴즈",
        layout="wide",
        page_icon="🦜"
    )

    # 타이틀
    st.markdown(
        """
        <h1 style='text-align: center; font-size:48px; color: #4B89DC;'>🔊앵무새 객관식 퀴즈</h1>
        """, unsafe_allow_html=True)

    # 설명 텍스트
    st.markdown(
        """
        <p style='text-align: center; font-size: 20px; color: #555;'>
        <b>다 함께 퀴즈를 풀어봅시다!</b>
        </p>
        """, unsafe_allow_html=True)

    init_session(dict(quiz=[], answ=[], audio=[], choices=[], voice="en-US-Journey-F"))

# 퀴즈 세팅 (객관식 보기 포함)
def set_quiz_batch(img: ImageFile.ImageFile, group: str, difficulty: str):
    if img and not st.session_state.get("quiz"):
        with st.spinner("10문제 퀴즈를 준비 중입니다...📚"):
            st.session_state["quiz"] = []
            st.session_state["answ"] = []
            st.session_state["choices"] = []
            st.session_state["audio"] = []

            for i in range(10):
                quiz_sentence, answer_word, choices, full_desc = generate_quiz(img, group, difficulty)

                # 중첩 리스트 처리
                if isinstance(choices[0], list):
                    choices = choices[0]

                wav_file = synth_speech(full_desc, st.session_state["voice"], "wav")
                audio_path = OUT_DIR / f"{Path(__file__).stem}_{i}.wav"
                with open(audio_path, "wb") as fp:
                    fp.write(wav_file)

                st.session_state["quiz"].append(quiz_sentence)
                st.session_state["answ"].append(answer_word)
                st.session_state["choices"].append(choices)
                st.session_state["audio"].append(audio_path.as_posix())
                
def show_quiz_batch(difficulty: str):
    total = len(st.session_state["quiz"])

    with st.form("quiz_form", clear_on_submit=False):
        for idx in range(total):
            quiz = st.session_state["quiz"][idx]
            answer = st.session_state["answ"][idx]
            audio = st.session_state["audio"][idx]
            choices = st.session_state["choices"][idx]

            key_choice = f"choice_{idx}"
            if key_choice not in st.session_state:
                st.session_state[key_choice] = ""

            # 문제 영역
            quiz_highlighted = quiz.replace("_____", "<span style='color:red; font-weight:bold;'>_____</span>")
            st.markdown(f"""
                <div style="background-color:#f0f8ff;padding:15px;border-radius:12px;margin:10px 0;">
                    <p style="font-size:16px;">📝 문제 {idx+1}</p>
                    <audio controls style="width:100%; margin-bottom: 10px;">
                        <source src="{audio}" type="audio/wav">
                    </audio>
                    <p>{quiz_highlighted}</p>
                </div>
            """, unsafe_allow_html=True)

            if isinstance(choices[0], list):
                choices = choices[0]

            st.radio("보기", choices, key=key_choice, label_visibility="collapsed")

        submitted = st.form_submit_button("정답 제출 ✅", use_container_width=True)

    # 결과 출력
    if submitted:
        score = 0
        st.markdown("---")
        st.subheader("📊 결과")

        for idx in range(total):
            user = st.session_state.get(f"choice_{idx}", "")
            correct = st.session_state["answ"][idx]
            if user == correct:
                score += 1
                st.success(f"문제 {idx + 1}: ✅ 정답 ({user})")
            else:
                st.error(f"문제 {idx + 1}: ❌ 오답 (선택: {user}, 정답: {correct})")

        st.markdown(f"## 🏁 총점: **{score} / {total}**")
        if score >= 9:
            st.success("🎉 대단해요! 퀴즈 마스터!")
        elif score >= 6:
            st.info("👍 좋은 성적이에요! 조금만 더 연습해요!")
        else:
            st.warning("📚 괜찮아요! 복습하고 다시 도전해보세요!")
# 퀴즈 리셋
def reset_quiz():
    if st.button("🔄 다시 풀기", type="primary"):
        for key in list(st.session_state.keys()):
            if key.startswith("choice_") or key in ["quiz", "answ", "choices", "audio"]:
                del st.session_state[key]
        st.rerun()


# 실행
if __name__ == "__main__":
    init_page()

    if img := uploaded_image(on_change=clear_session):
        # 🔁 단일 문제 대신 10문제 세팅
        set_quiz_batch(img, group_code, global_difficulty)

        # 🔁 전체 퀴즈 보여주기 + 점수 계산
        show_quiz_batch(global_difficulty)

        # 🔁 리셋 버튼
        reset_quiz()
