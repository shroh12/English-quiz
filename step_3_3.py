import base64
import re
import ast
import nltk
import pandas as pd
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageFile
import streamlit as st
from streamlit_extras.stylable_container import stylable_container
import google.generativeai as genai
from google.cloud import texttospeech
from google.oauth2 import service_account

# Constants and directory setup
wORK_DIR = Path(__file__).parent
IMG_DIR, IN_DIR, OUT_DIR = wORK_DIR / "img", wORK_DIR / "input", wORK_DIR / "output"

# Create directories if they don't exist
IMG_DIR.mkdir(exist_ok=True)
IN_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)

# Utility functions
def img_to_base64(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def get_model(sys_prompt: str = None) -> genai.GenerativeModel:
    GEMINI_KEY = st.secrets['GEMINI_KEY']
    GEMINI_MODEL = "gemini-2.0-flash"
    genai.configure(api_key=GEMINI_KEY, transport="rest")
    return genai.GenerativeModel(GEMINI_MODEL, system_instruction=sys_prompt)

def tts_client() -> texttospeech.TextToSpeechClient:
    cred = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return texttospeech.TextToSpeechClient(credentials=cred)

def synth_speech(text: str, voice: str, audio_encoding: str = None) -> bytes:
    lang_code = "-".join(voice.split("-")[:2])
    MP3 = texttospeech.AudioEncoding.MP3
    WAV = texttospeech.AudioEncoding.LINEAR16
    audio_type = MP3 if audio_encoding == "mp3" else WAV
    
    client = tts_client()
    resp = client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=texttospeech.VoiceSelectionParams(language_code=lang_code, name=voice),
        audio_config=texttospeech.AudioConfig(audio_encoding=audio_type),
    )
    return resp.audio_content

def tokenize_sent(text: str) -> list[str]:
    nltk.download(["punkt", "punkt_tab"], quiet=True)
    return nltk.tokenize.sent_tokenize(text)

# Session management
def init_session(initial_state: dict = None):
    if initial_state:
        for key, value in initial_state.items():
            if key not in st.session_state:
                st.session_state[key] = value

def clear_session():
    keys_to_keep = ["total_score", "quiz_data", "keep_score"]
    keys_to_clear = [k for k in st.session_state.keys() if k not in keys_to_keep]
    for key in keys_to_clear:
        del st.session_state[key]

# Image upload component
def uploaded_image(on_change=None, args=None) -> Image.Image | None:
    with st.sidebar:
        st.markdown(
            "<div style='text-align: center; font-weight: bold; font-size: 25px;'>이미지 업로드</div>",
            unsafe_allow_html=True
        )

        img = Image.open('img/angmose.jpg').resize((300, 300))
        st.markdown(
            f"""
            <div style="text-align: center; padding-bottom: 10px;">
                <img src="data:image/png;base64,{img_to_base64(img)}"
                    width="200"
                    style="border-radius: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);" />
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
             <div style='text-align: left; font-size: 15px; color: #444; line-height: 1.6; padding-left: 5px;'>
                이미지를 업로드 하시면<br>
                AI가 문장을 생성해 퀴즈를 출제합니다.<br>
                문장을 잘 듣고 퀴즈를 풀어보세요.
            </div>
            """,
            unsafe_allow_html=True
        )

        uploaded = st.file_uploader(
            label="",
            label_visibility="collapsed",
            on_change=on_change,
            args=args
        )

        if uploaded is not None:
            with st.container(border=True):
                img = Image.open(uploaded).convert("RGB")
                st.image(img, use_container_width=True)
                st.session_state["img"] = img
                buf = BytesIO()
                img.save(buf, format="PNG")
                st.session_state["img_bytes"] = buf.getvalue()
                return img

        elif "img_bytes" in st.session_state:
            img = Image.open(BytesIO(st.session_state["img_bytes"]))
            st.image(img, use_container_width=True)
            return img

        return None

# Quiz generation and management
def get_prompt_by_group(group: str) -> Path:
    path = IN_DIR / f"quiz_{group}.txt"
    if not path.exists():
        st.warning(f"⚠️ '{group}' 그룹의 프롬프트가 존재하지 않아 기본값을 사용합니다.")
        path = IN_DIR / "prompt_default.txt"
    return path

def get_prompt_by_group_and_difficulty(group: str, difficulty: str) -> str:
    prompts = {
        ("elementary", "easy"): "prompt_elementary_easy.txt",
        ("elementary", "medium"): "prompt_elementary_medium.txt",
        ("elementary", "hard"): "prompt_elementary_hard.txt",
        ("middle", "easy"): "prompt_middle_easy.txt",
        ("middle", "medium"): "prompt_middle_medium.txt",
        ("middle", "hard"): "prompt_middle_hard.txt",
        ("high", "easy"): "prompt_high_easy.txt",
        ("high", "medium"): "prompt_high_medium.txt",
        ("high", "hard"): "prompt_high_hard.txt",
        ("adult", "easy"): "prompt_adult_easy.txt",
        ("adult", "medium"): "prompt_adult_medium.txt",
        ("adult", "hard"): "prompt_adult_hard.txt",
    }
    return prompts.get((group, difficulty), "prompt_default.txt")

def generate_quiz(img: ImageFile.ImageFile, group: str, difficulty: str):
    prompt_desc = IN_DIR / "p1_desc.txt"
    model_desc = get_model(sys_prompt=prompt_desc.read_text(encoding="utf8"))
    resp_desc = model_desc.generate_content([img, "Describe this image"])
    description = resp_desc.text.strip()

    quiz_prompt_filename = get_prompt_by_group_and_difficulty(group, difficulty)
    quiz_prompt_path = IN_DIR / quiz_prompt_filename
    model_quiz = get_model(sys_prompt=quiz_prompt_path.read_text(encoding="utf8"))
    resp_quiz = model_quiz.generate_content(description)

    quiz_match = re.search(r'Quiz:\s*[""](.*?)[""]\s*$', resp_quiz.text, re.MULTILINE)
    answer_match = re.search(r'Answer:\s*[""](.*?)[""]\s*$', resp_quiz.text, re.MULTILINE)
    choices_match = re.search(r'Choices:\s*(\[[^\]]+\](?:,\s*\[[^\]]+\])*)', resp_quiz.text, re.MULTILINE | re.DOTALL)

    if quiz_match and answer_match and choices_match:
        quiz_sentence = quiz_match.group(1).strip()
        answer_word = [answer_match.group(1).strip().strip('"')]
        choices = ast.literal_eval(f"[{choices_match.group(1)}]")
        original_sentence = quiz_sentence.replace("_____", answer_word[0])
        return quiz_sentence, answer_word, choices, original_sentence

    raise ValueError(f"AI 응답 파싱 실패! AI 응답 내용:\n{resp_quiz.text}")

def generate_feedback(user_input: str, answ: str) -> str:
    try:
        prompt_path = IN_DIR / "p3_feedback.txt"
        template = prompt_path.read_text(encoding="utf8")
        prompt = template.format(user=user_input, correct=answ)
        model = get_model()
        response = model.generate_content(prompt)
        return response.text.strip() if response and response.text else "(⚠️ 응답 없음)"
    except Exception as e:
        return f"(⚠️ 피드백 생성 중 오류: {e})"

# Score management
def init_score():
    if "total_score" not in st.session_state:
        st.session_state["total_score"] = 0
    if "quiz_data" not in st.session_state:
        st.session_state["quiz_data"] = []
    if "answered_questions" not in st.session_state:
        st.session_state["answered_questions"] = set()
    if "correct_answers" not in st.session_state:
        st.session_state["correct_answers"] = 0
    if "total_questions" not in st.session_state:
        st.session_state["total_questions"] = 0

def update_score(question: str, is_correct: bool):
    init_score()
    
    # Only update if this question hasn't been answered before
    if question not in st.session_state["answered_questions"]:
        st.session_state["answered_questions"].add(question)
        st.session_state["total_questions"] += 1
        
        if is_correct:
            st.session_state["correct_answers"] += 1
            st.session_state["total_score"] += 10
            
        st.session_state["quiz_data"].append({
            "question": question,
            "correct": is_correct,
            "timestamp": pd.Timestamp.now()
        })

def reset_quiz():
    if st.session_state.get("quiz"):
        if st.button("🔄 새로운 문제", type="primary"):
            # Keep all score-related data
            st.session_state["keep_score"] = True
            st.session_state["new_problem"] = True
            
            # Only clear the current quiz data, not the score data
            keys_to_clear = ["quiz", "answ", "audio", "choices"]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Clear form-related states
            for key in list(st.session_state.keys()):
                if key.startswith(("submitted_", "feedback_", "choice_", "form_question_")):
                    del st.session_state[key]
            
            st.rerun()

def clear_all_scores():
    if st.button("🗑️ 모든 점수 초기화", type="secondary"):
        st.session_state["total_score"] = 0
        st.session_state["quiz_data"] = []
        st.session_state["answered_questions"] = set()
        st.session_state["correct_answers"] = 0
        st.session_state["total_questions"] = 0
        st.success("모든 점수가 초기화되었습니다.")
        st.rerun()

def show_score_summary():
    if "quiz_data" not in st.session_state or not st.session_state["quiz_data"]:
        return

    # Get the latest counts from session state
    total = st.session_state["total_questions"]
    correct = st.session_state["correct_answers"]
    accuracy = round((correct / total) * 100, 1) if total else 0.0
    score = st.session_state["total_score"]

    # Create a more visually appealing and accessible score display
    st.markdown("---")
    
    # Score header with emoji
    st.markdown("""
    <div style='text-align: center; margin-bottom: 20px;'>
        <h2 style='color: #4B89DC;'>🏆 점수 현황</h2>
    </div>
    """, unsafe_allow_html=True)

    # Create two columns for better layout
    col1, col2 = st.columns(2)

    with col1:
        # Score card with large, clear numbers
        st.markdown(f"""
        <div style='background-color: #f0f8ff; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <h3 style='color: #4B89DC; margin-bottom: 10px;'>현재 점수</h3>
            <h1 style='font-size: 48px; color: #2E7D32; margin: 0;'>{score}점</h1>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Progress card with clear statistics
        st.markdown(f"""
        <div style='background-color: #f0f8ff; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <h3 style='color: #4B89DC; margin-bottom: 10px;'>정답률</h3>
            <h2 style='color: #2E7D32; margin: 0;'>{accuracy}%</h2>
            <p style='color: #666; margin-top: 10px;'>맞춘 문제: {correct} / {total}</p>
        </div>
        """, unsafe_allow_html=True)

    # Progress bar with better visibility
    st.markdown(f"""
    <div style='margin-top: 20px;'>
        <div style='background-color: #e0e0e0; height: 20px; border-radius: 10px; margin-bottom: 10px;'>
            <div style='background-color: #4B89DC; width: {accuracy}%; height: 20px; border-radius: 10px;'></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Add encouraging message based on performance
    if accuracy >= 80:
        st.success("🎉 훌륭해요! 계속 이렇게 잘 해봐요!")
    elif accuracy >= 60:
        st.info("👍 잘하고 있어요! 조금만 더 노력해봐요!")
    else:
        st.warning("💪 조금 더 연습하면 더 잘할 수 있을 거예요!")
    
    # Add clear all scores button at the bottom
    clear_all_scores()

# UI Components
def init_page():
    st.set_page_config(
        page_title="앵무새 스쿨",
        layout="wide",
        page_icon="🦜"
    )
    st.markdown(
        """
        <h1 style='text-align: center; font-size:48px; color: #4B89DC;'>🔊앵무새 스쿨</h1>
        """, unsafe_allow_html=True)
    st.markdown(
        """
        <p style='text-align: center; font-size: 20px; color: #555;'>
        <b>다 함께 퀴즈를 풀어봅시다!</b>
        </p>
        """, unsafe_allow_html=True)
    init_session(dict(quiz=[], answ=[], audio=[], choices=[], voice="en-US-Journey-F"))

def set_quiz(img: ImageFile.ImageFile, group: str, difficulty: str):
    if img and not st.session_state["quiz"]:
        with st.spinner("이미지 퀴즈를 준비 중입니다...🦜"):
            quiz_sentence, answer_word, choices, full_desc = generate_quiz(img, group, difficulty)
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
            st.session_state["choices"] = [choices]
            st.session_state["quiz_data"] = [{
                "question": quiz_display,
                "topic": "지문화",
                "difficulty": difficulty,
                "correct": False
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
        init_session({key_feedback: "", f"submitted_{idx}": False})

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

            if not choices:
                st.error("선택지가 없습니다. 다시 문제를 생성하세요.")
                continue

            key_choice = f"choice_{idx}_0"
            init_session({key_choice: ""})
            if st.session_state[key_choice] not in choices:
                st.session_state[key_choice] = choices[0]
            user_choice = st.radio(
                "보기 중 하나를 선택하세요👇",
                choices,
                key=key_choice
            )

            submitted = st.form_submit_button("정답 제출 ✅", use_container_width=True)

            if submitted and not st.session_state.get(f"submitted_{idx}"):
                st.session_state[f"submitted_{idx}"] = True
                
                with st.spinner("채점 중입니다..."):
                    is_correct = user_choice == answ[0]
                    update_score(quiz_display, is_correct)

                    if is_correct:
                        feedback = "✅ 정답입니다! 🎉"
                    else:
                        feedback = f"❌ 오답입니다.\n\n{generate_feedback(user_choice, answ[0])}"

                    st.session_state[key_feedback] = feedback

        feedback = st.session_state.get(key_feedback, "")
        if feedback:
            with st.expander("📚 해설 보기", expanded=True):
                st.markdown(f"**정답:** {answ[0]}")
                st.markdown(feedback, unsafe_allow_html=True)

# Main application
if __name__ == "__main__":
    init_page()
    init_score()  # Initialize score at the start of the app

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
        set_quiz(img, group_code, global_difficulty)
        show_quiz(global_difficulty)

        if st.session_state.get("quiz_data"):
            show_score_summary()

        reset_quiz() 
