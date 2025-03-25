from pathlib import Path
import streamlit as st 
from PIL import ImageFile
from step_1_1 import OUT_DIR
from step_1_2 import uploaded_image
from step_1_3 import clear_session, init_session
from step_2_2 import synth_speech
from step_3_1 import generate_quiz

def init_page():
    st.set_page_config(layout="wide")
    st.title("🔊 만들면서 배우는 영어 받아쓰기 웹 앱")
    init_session(dict(quiz=[], answ=[], voice="en-US-Journey-F"))
    
def set_quiz(img: ImageFile.ImageFile):
    if img and not st.session_state["quiz"]:
        with st.spinner("문제를 출제중입니다...🤯"):
            quiz, answ = generate_quiz(img)
            
            audio = []
            for idx, sent in enumerate(answ):
                wav_file = synth_speech(sent, st.session_state["voice"], "wav")
                path = OUT_DIR / f"{Path(__file__).stem}_{idx}.wav"
                with open(path, "wb") as fp: 
                    fp.write(wav_file)
                    audio.append(path.as_posix())
                    
            st.session_state["quiz"] = quiz
            st.session_state["answ"] = answ
            st.session_state["audio"] = audio
            
def reset_quiz():
    if st.session_state["quiz"]:
        with st.form("form_reset", border=False):
            if st.form_submit_button(label="새로운 문제 풀어보기",
                                     use_container_width=True, type="primary"):
                clear_session()
                st.rerun()
                
if __name__ == "__main__":
    init_page()
    if img := uploaded_image(on_change=clear_session):
        set_quiz(img)
        st.write(st.session_state["quiz"])
        reset_quiz()