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
        page_title="앵무새 스쿨",
        layout="wide",
        page_icon="🦜"
    )

    # 타이틀
    st.markdown(
        """
        <h1 style='text-align: center; font-size:48px; color: #4B89DC;'>🔊앵무새 스쿨</h1>
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
def set_quiz(img: ImageFile.ImageFile, group: str, difficulty: str):
    if img and not st.session_state["quiz"]:
        with st.spinner("이미지 퀴즈를 준비 중입니다...🦜"):
            quiz_sentence, answer_word, choices, full_desc = generate_quiz(img, group, difficulty)

            # 🔥 이 부분 수정 (이중리스트 문제 해결)
            if isinstance(choices[0], list):
                choices = choices[0]

            answer_words = [answer_word]

            wav_file = synth_speech(full_desc, st.session_state["voice"], "wav")
            path = OUT_DIR / f"{Path(__file__).stem}.wav"
            with open(path, "wb") as fp:
                fp.write(wav_file)

            quiz_display = f"""
            이미지를 보고 설명을 잘 들은 후, 빈칸에 들어갈 알맞은 단어를 선택하세요.  

            **{quiz_sentence}**
            """

        st.session_state["img"] = img
        st.session_state["quiz"] = [quiz_display]
        st.session_state["answ"] = answer_words
        st.session_state["audio"] = [path.as_posix()]
        st.session_state["choices"] = [choices]  # 여기는 리스트로 감싸줘야 함 (이전 구조 유지)
        st.session_state["quiz_data"] = [{
            "question": quiz_display,
            "topic": "지문화",
            "difficulty": global_difficulty,
            "correct": is_correct
        }]

def show_quiz(difficulty="medium"):
    zipped = zip(
        range(len(st.session_state["quiz"])),
        st.session_state["quiz"],
        st.session_state["answ"],
        st.session_state["audio"],
        st.session_state["choices"],
    )

    for idx, quiz, answ, audio, choices in zipped:
        key_feedback = f"feedback_{idx}"
        init_session({key_feedback: "", submitted_flag_key: False})

        with st.form(f"form_question_{idx}", border=True):
            st.markdown("""
            <div style="background-color:#e6f4ea; padding:10px; border-radius:10px; text-align: center;">
                <h4 style="color:#006d2c; margin: 0;">문제</h4>
            </div>
            """, unsafe_allow_html=True)

            st.audio(audio)

            quiz_display = quiz.replace("**", "").replace(
                "_____", "<span style='color:red; font-weight:bold;'>_____</span>"
            )
            st.markdown(f"<p style='font-size:17px;'>{quiz_display}</p>", unsafe_allow_html=True)

            is_multi_blank = all(isinstance(c, list) for c in choices)
            user_choices = []

            if not choices:
                st.error("선택지가 없습니다. 다시 문제를 생성하세요.")
                continue

            if is_multi_blank:
                for i, choice_set in enumerate(choices):
                    key_choice = f"choice_{idx}_{i}"
                    init_session({key_choice: ""})
                    user_choice = st.radio(
                        f"빈칸 {i + 1} 보기 👇",
                        choice_set,
                        key=key_choice
                    )
                    user_choices.append(user_choice)
            else:
                key_choice = f"choice_{idx}_0"
                init_session({key_choice: ""})
                if st.session_state[key_choice] not in choices:
                    st.session_state[key_choice] = choices[0]
                user_choice = st.radio(
                    "보기 중 하나를 선택하세요👇",
                    choices,
                    key=key_choice
                )
                user_choices.append(user_choice)

            submitted = st.form_submit_button("정답 제출 ✅", use_container_width=True)

            if submitted and not st.session_state.get(submitted_flag_key):
                st.session_state[submitted_flag_key] = True  # ✅ 중복 제출 방지 플래그
                
                with st.spinner("채점 중입니다..."):
                    is_correct = user_choices == answ
                    update_score(is_correct)  # ✅ 점수 누적

                    if "quiz_data" not in st.session_state:
                        st.session_state["quiz_data"] = []

                    st.session_state["quiz_data"].append({
                        "question": quiz_display,
                        "correct": is_correct,
                        "difficulty": difficulty
                    })
                    
                    if is_correct:
                        feedback = "✅ 정답입니다! 🎉"
                    else:
                        feedback_parts = [
                            generate_feedback(u, a) for u, a in zip(user_choices, answ)
                        ]
                        feedback = f"❌ 오답입니다.\n\n" + "\n\n".join(feedback_parts)

                    if "quiz_data" not in st.session_state:
                        st.session_state["quiz_data"] = []

                    st.session_state["quiz_data"].append({
                        "question": quiz_display,
                        "correct": is_correct,
                        "difficulty": difficulty
                    })

                    st.session_state[key_feedback] = feedback

        feedback = st.session_state.get(key_feedback, "")
        if feedback:
            with st.expander("📚 해설 보기", expanded=True):
                st.markdown(f"**정답:** {', '.join(answ)}")
                st.markdown(feedback, unsafe_allow_html=True)
                
def init_score():
    if "total_score" not in st.session_state:
        st.session_state["total_score"] = 0
    if "quiz_data" not in st.session_state:
        st.session_state["quiz_data"] = []

def update_score(is_correct: bool):
    if "total_score" not in st.session_state:
        st.session_state["total_score"] = 0
    if is_correct:
        st.session_state["total_score"] += 10
        
# 퀴즈 리셋 (점수는 유지)
def reset_quiz():
    if st.session_state.get("quiz"):
        if st.button("🔄 새로운 문제", type="primary"):
            st.session_state["keep_score"] = True           # ✅ 점수는 유지
            st.session_state["new_problem"] = True          # ✅ 문제 리셋 트리거

            # 문제 관련 세션 키 초기화
            for key in ["quiz", "answ", "audio", "choices", "quiz_data"]:
                if key in st.session_state:
                    del st.session_state[key]

            # ❗ 문제별 상태 키도 초기화
            for key in list(st.session_state.keys()):
                if key.startswith("submitted_") or key.startswith("feedback_") or key.startswith("choice_") or key.startswith("form_question_"):
                    del st.session_state[key]

            st.rerun()
# 실행
if __name__ == "__main__":
    init_page()  # 페이지 초기화

    # ✅ 1. 학습자 그룹 선택
    group_display = st.selectbox("연령대를 선택하세요", ["초등학생", "중학생", "고등학생", "성인"])
    group_mapping = {
        "초등학생": "elementary",
        "중학생": "middle",
        "고등학생": "high",
        "성인": "adult"
    }
    group_code = group_mapping.get(group_display, "default")

    # ✅ 2. 난이도 선택
    difficulty_display = st.selectbox("문제 난이도를 선택하세요", ["쉬움", "중간", "어려움"])
    difficulty_mapping = {
        "쉬움": "easy",
        "중간": "normal",
        "어려움": "hard"
    }
    global_difficulty = difficulty_mapping.get(difficulty_display, "normal")

    # ✅ 3. 이미지 업로드 → 퀴즈 세팅
    if st.session_state.get("new_problem"):
        img = st.session_state.get("img")  # 이전 이미지 재활용
        st.session_state["new_problem"] = False
    else:
        img = uploaded_image()

    if img:
        st.session_state["img"] = img  # 이미지 저장 (재사용을 위해)
        
        if not st.session_state.get("keep_score") and "total_score" not in st.session_state:
            init_score()
        st.session_state["keep_score"] = False

        set_quiz(img, group_code, global_difficulty)
        show_quiz(global_difficulty)

        if st.session_state.get("quiz_data"):
            show_score_summary()
            
        reset_quiz()
