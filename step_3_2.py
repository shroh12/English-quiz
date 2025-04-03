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
def set_quiz(img: ImageFile.ImageFile, group: str):
    if img and not st.session_state["quiz"]:
        with st.spinner("이미지 퀴즈를 준비 중입니다...🦜"):
            # 여기서 unpack
            quiz_sentence, answer_word, choices, full_desc = generate_quiz(img, group)
            
            # answer와 choices를 리스트 형태로 감싸줌 (빈칸 여러 개 대응을 위한 일관성)
            answer_words = [answer_word]
            choices_list = [choices]

            # 음성 생성
            wav_file = synth_speech(full_desc, st.session_state["voice"], "wav")
            path = OUT_DIR / f"{Path(__file__).stem}.wav"
            with open(path, "wb") as fp:
                fp.write(wav_file)

            # 퀴즈 문장 출력
            quiz_display = f"""
            이미지를 보고 설명을 잘 들은 후, 빈칸에 들어갈 알맞은 단어를 선택하세요.  
            
            **{quiz_sentence}**
            """

            # 보기 출력
            choices_display = ""
            for idx, choices in enumerate(choices_list):
                choices_display += f"\n\n🔸 **빈칸 {idx+1} 보기:**\n"
                choices_display += "\n".join(
                    [f"{i+1}. {choice}" for i, choice in enumerate(choices)]
                )

            quiz_display += choices_display

        # 세션 상태 저장
        st.session_state["img"] = img
        st.session_state["quiz"] = [quiz_display]
        st.session_state["answ"] = answer_words
        st.session_state["audio"] = [path.as_posix()]
        st.session_state["choices"] = choices_list
        st.session_state["quiz_data"] = [{
            "question": quiz_sentence,
            "topic": "지문화"
        }]

def show_quiz(difficulty):
    # 세션 상태에서 문제 데이터 묶기
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
            st.audio(audio)

            quiz_highlighted = quiz.replace(
                "_____", "<span style='color:red; font-weight:bold;'>_____</span>"
            )

            st.markdown(f"""
            <div style="background-color:#e6f4ea;padding:20px 20px 10px 20px;border-radius:12px;margin-bottom:10px; text-align: center;">
                <audio controls style="width:100%; margin-bottom: 15px;">
                    <source src="{audio}" type="audio/wav">
                    오디오를 지원하지 않는 브라우저입니다.
                </audio>
                <p style="margin-bottom: 5px;">다음 문장을 듣고, 빈칸에 들어갈 단어를 고르세요.</p>
                <p style="font-size:17px;">{quiz_highlighted}</p>
            </div>
            """, unsafe_allow_html=True)

            if not choices or not isinstance(choices, list):
                st.error("선택지가 없습니다. 다시 문제를 생성하세요.")
                continue

            user_choice = st.radio(
                "보기 중 하나를 선택하세요👇",
                choices,
                key=key_choice
            )

            submitted = st.form_submit_button("정답 제출 ✅", use_container_width=True)

            if submitted:
                with st.spinner("채점 중입니다..."):
                    is_correct = user_choice == answ  # ✅ 정답 여부 판단

                    if is_correct:
                        st.session_state[key_feedback] = "✅ 정답입니다! 🎉"
                    else:
                        feedback = generate_feedback(user_choice, answ)
                        st.session_state[key_feedback] = f"❌ 오답입니다.\n\n{feedback}"

                    # ✅ quiz_data 누적 저장
                    if "quiz_data" not in st.session_state:
                        st.session_state["quiz_data"] = []

                    st.session_state["quiz_data"].append({
                        "question": quiz,
                        "topic": "지문화",       # 지금은 고정값
                        "correct": is_correct,
                        "difficulty": difficulty  # 💡 외부에서 전달된 값 사용!
                    })

        # 피드백 출력
        feedback = st.session_state.get(key_feedback, "")
        if feedback:
            with st.expander("📚 해설 보기", expanded=True):
                st.markdown(f"**정답:** {answ}")
                st.markdown(feedback)
# 퀴즈 리셋
def reset_quiz():
    if st.session_state["quiz"]:
        if st.button("🔄 새로운 문제", type="primary"):
            clear_session()
            st.rerun()

# 실행
if __name__ == "__main__":
    init_page()
    if img := uploaded_image(on_change=clear_session):
        set_quiz(img)
        show_quiz()
        reset_quiz()
