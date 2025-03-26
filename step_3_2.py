import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from PIL import ImageFile, Image
from pathlib import Path
from step_1_1 import OUT_DIR
from step_1_2 import uploaded_image
from step_1_3 import clear_session, init_session
from step_2_2 import synth_speech
from step_3_1 import generate_quiz, get_model

IN_DIR = Path("input")


def init_page():
    st.set_page_config(layout="wide", page_icon="🦜")
    st.markdown("""
        <h1 style='text-align: center; font-size:48px; color: #4B89DC;'>🔊 영어 받아쓰기 연습</h1>
    """, unsafe_allow_html=True)

    img = Image.open('img/angmose.jpg').resize((500, 500))
    st.image(img)

    st.markdown("""
        <p style='text-align: center; font-size: 20px; color: #555;'>
        이미지를 올려주시면, AI가 문장을 생성해 문제를 출제합니다. 문장을 잘 듣고 빈칸을 채워보세요!<br>
        왼쪽의 <b>이미지 붙여넣기 📷</b> 에서 시작할 수 있습니다.
        </p>
    """, unsafe_allow_html=True)

    init_session(dict(quiz=[], answ=[], audio=[], voice="en-US-Journey-F"))


def preprocess_answers(quiz: str, answ) -> list[str]:
    num_blanks = quiz.count("_____")

    if isinstance(answ, list):
        answ_list = answ
    elif isinstance(answ, str):
        if "," in answ:
            answ_list = [s.strip() for s in answ.split(",")]
        elif " and " in answ:
            answ_list = [s.strip() for s in answ.split(" and ")]
        else:
            answ_list = [answ.strip()]
    else:
        raise ValueError("정답은 문자열이나 리스트여야 합니다.")

    if len(answ_list) < num_blanks:
        answ_list += [""] * (num_blanks - len(answ_list))
    elif len(answ_list) > num_blanks:
        answ_list = answ_list[:num_blanks]

    return answ_list


def generate_feedback(user_inputs: list[str], answers: list[str]) -> str:
    input_table = ""
    for i, (inp, ans) in enumerate(zip(user_inputs, answers), start=1):
        input_table += f"Blank {i}:\n- Student's Input: {inp}\n- Correct Answer: {ans}\n\n"

    prompt_template = (IN_DIR / "p3_feedback_multi.txt").read_text(encoding="utf-8")
    prompt = prompt_template.format(input_table=input_table)

    model = get_model()
    resp = model.generate_content(prompt)
    return resp.text

def set_quiz(img: ImageFile.ImageFile):
    if img and not st.session_state["quiz"]:
        with st.spinner("문제를 준비 중입니다...🤔"):
            quiz_text, answer_text = generate_quiz(img)  # quiz_text는 str
            answer_list = preprocess_answers(quiz_text, answer_text)

            audio = []

            # 🔥 수정된 부분: quiz_text는 str이므로 그대로 음성 생성
            wav_file = synth_speech(quiz_text, st.session_state["voice"], "wav")
            path = OUT_DIR / f"quiz_0.wav"
            with open(path, "wb") as fp:
                fp.write(wav_file)
                audio.append(path.as_posix())

            # 문제와 정답은 리스트 형태로 감싸 저장
            st.session_state["quiz"] = [quiz_text]
            st.session_state["answ"] = [answer_list]
            st.session_state["audio"] = audio



def show_quiz():
    st.divider()
    st.markdown("### 📌 문장을 듣고 빈칸을 채워주세요!")

    for idx, (quiz, answ_list, audio) in enumerate(zip(
        st.session_state["quiz"],
        st.session_state["answ"],
        st.session_state["audio"]
    )):
        key_feedback = f"feedback_{idx}"
        init_session({key_feedback: ""})

        with stylable_container(key=f"form_question_{idx}", css_styles="""
            {
                background-color: #F0F8FF;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0px 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
        """):
            st.audio(audio)

            quiz_display = quiz.replace("_____", "🔲")
            st.markdown(f"<p style='font-size:20px; color:#333;'><b>문제:</b> {quiz_display}</p>", unsafe_allow_html=True)

            user_inputs = []
            for i in range(len(answ_list)):
                key_input = f"input_{idx}_{i}"
                init_session({key_input: ""})
                user_input = st.text_input(f"정답 입력 {i + 1}", value=st.session_state[key_input], key=key_input)
                user_inputs.append(user_input)

            submitted = st.button("정답 제출 ✅", key=f"submit_{idx}")

            if submitted:
                with st.spinner("정답 확인 중입니다...🔍"):
                    feedback = generate_feedback(user_inputs, answ_list)
                    st.session_state[key_feedback] = feedback

            if st.session_state[key_feedback]:
                with st.expander("📚 해설 및 정답 보기", expanded=True):
                    st.markdown(f"**정답:** {answ_list}")
                    st.markdown(st.session_state[key_feedback])


def reset_quiz():
    if st.session_state["quiz"]:
        if st.button("🔄 새로운 문제로 연습하기", type="primary"):
            clear_session()
            st.rerun()


if __name__ == "__main__":
    init_page()
    if img := uploaded_image(on_change=clear_session):
        set_quiz(img)
        show_quiz()
        reset_quiz()
