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
from database import register_user, verify_user, save_learning_history, get_learning_history, update_username, find_username, reset_password
import extra_streamlit_components as stx

# Constants and directory setup
wORK_DIR = Path(__file__).parent
IMG_DIR, IN_DIR, OUT_DIR = wORK_DIR / "img", wORK_DIR / "input", wORK_DIR / "output"

# Create directories if they don't exist
IMG_DIR.mkdir(exist_ok=True)
IN_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)

def init_page():
    st.set_page_config(
        page_title="앵무새 스쿨",
        layout="wide",
        page_icon="🦜"
    )
    # Initialize cookie manager after page config
    global cookie_manager
    cookie_manager = stx.CookieManager(key="auth_cookie_manager")

def get_auth_cookie():
    return cookie_manager.get("auth")

def set_auth_cookie(username, user_id):
    cookie_manager.set("auth", f"{username}:{user_id}", expires_at=pd.Timestamp.now() + pd.Timedelta(days=7))

def clear_auth_cookie():
    cookie_manager.delete("auth")

def show_auth_page():
    st.markdown(
        """
        <div style='text-align: center; margin-bottom: 30px;'>
            <h1 style='font-size:48px; color: #4B89DC;'>🔊앵무새 스쿨</h1>
            <p style='font-size: 20px; color: #555;'>
                <b>이미지로 배우는 즐거운 영어 학습!</b>
            </p>
        </div>
        """, unsafe_allow_html=True)

    # 탭 생성
    tab1, tab2, tab3 = st.tabs(["로그인", "회원가입", "아이디/비밀번호 찾기"])
    
    with tab1:
        with st.form("login_form", border=True):
            st.markdown("""
            <div style='text-align: center; margin-bottom: 20px;'>
                <h3 style='color: #4B89DC;'>로그인</h3>
            </div>
            """, unsafe_allow_html=True)
            
            username = st.text_input("아이디", placeholder="아이디를 입력하세요")
            password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
            submitted = st.form_submit_button("로그인", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("아이디와 비밀번호를 모두 입력해주세요.")
                else:
                    success, user_id = verify_user(username, password)
                    if success:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username
                        st.session_state["user_id"] = user_id
                        set_auth_cookie(username, user_id)  # Set auth cookie
                        st.success("로그인 성공!")
                        st.rerun()
                    else:
                        st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    with tab2:
        with st.form("register_form", border=True):
            st.markdown("""
            <div style='text-align: center; margin-bottom: 20px;'>
                <h3 style='color: #4B89DC;'>회원가입</h3>
            </div>
            """, unsafe_allow_html=True)
            
            name = st.text_input("이름", placeholder="이름을 입력하세요")
            new_username = st.text_input("사용할 아이디", placeholder="아이디를 입력하세요")
            new_password = st.text_input("사용할 비밀번호", type="password", placeholder="비밀번호를 입력하세요")
            confirm_password = st.text_input("비밀번호 확인", type="password", placeholder="비밀번호를 다시 입력하세요")
            email = st.text_input("이메일", placeholder="이메일을 입력하세요")
            submitted = st.form_submit_button("회원가입", use_container_width=True)
            
            if submitted:
                if not all([new_username, new_password, confirm_password, name, email]):
                    st.error("모든 항목을 입력해주세요.")
                elif new_password != confirm_password:
                    st.error("비밀번호가 일치하지 않습니다.")
                elif len(new_password) < 6:
                    st.error("비밀번호는 최소 6자 이상이어야 합니다.")
                elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                    st.error("올바른 이메일 형식이 아닙니다.")
                else:
                    if register_user(new_username, new_password, email, name):
                        st.success("회원가입이 완료되었습니다! 이제 로그인해주세요.")
                    else:
                        st.error("이미 존재하는 아이디 또는 이메일입니다.")

    with tab3:
        st.markdown("""
        <div style='text-align: center; margin-bottom: 20px;'>
            <h3 style='color: #4B89DC;'>아이디/비밀번호 찾기</h3>
        </div>
        """, unsafe_allow_html=True)

        find_option = st.radio(
            "찾으실 항목을 선택하세요",
            ["아이디 찾기", "비밀번호 재설정"],
            horizontal=True
        )

        if find_option == "아이디 찾기":
            with st.form("find_username_form", border=True):
                name = st.text_input("이름", placeholder="가입 시 등록한 이름을 입력하세요")
                email = st.text_input("이메일", placeholder="가입 시 등록한 이메일을 입력하세요")
                submitted = st.form_submit_button("아이디 찾기", use_container_width=True)

                if submitted:
                    if not name or not email:
                        st.error("이름과 이메일을 모두 입력해주세요.")
                    else:
                        username = find_username(name, email)
                        if username:
                            st.success(f"회원님의 아이디는 **{username}** 입니다.")
                        else:
                            st.error("입력하신 정보와 일치하는 계정이 없습니다.")

        else:  # 비밀번호 재설정
            with st.form("reset_password_form", border=True):
                username = st.text_input("아이디", placeholder="아이디를 입력하세요")
                email = st.text_input("이메일", placeholder="가입 시 등록한 이메일을 입력하세요")
                new_password = st.text_input("새 비밀번호", type="password", placeholder="새로운 비밀번호를 입력하세요")
                confirm_password = st.text_input("새 비밀번호 확인", type="password", placeholder="새로운 비밀번호를 다시 입력하세요")
                submitted = st.form_submit_button("비밀번호 재설정", use_container_width=True)

                if submitted:
                    if not all([username, email, new_password, confirm_password]):
                        st.error("모든 항목을 입력해주세요.")
                    elif new_password != confirm_password:
                        st.error("새 비밀번호가 일치하지 않습니다.")
                    elif len(new_password) < 6:
                        st.error("비밀번호는 최소 6자 이상이어야 합니다.")
                    else:
                        if reset_password(username, email, new_password):
                            st.success("비밀번호가 성공적으로 변경되었습니다. 새로운 비밀번호로 로그인해주세요.")
                        else:
                            st.error("입력하신 정보와 일치하는 계정이 없습니다.")

def init_session(initial_state: dict = None):
    if initial_state:
        for key, value in initial_state.items():
            if key not in st.session_state:
                st.session_state[key] = value

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
    if "learning_history" not in st.session_state:
        st.session_state["learning_history"] = []
    # Initialize quiz-related session state variables
    if "quiz" not in st.session_state:
        st.session_state["quiz"] = []
    if "answ" not in st.session_state:
        st.session_state["answ"] = []
    if "audio" not in st.session_state:
        st.session_state["audio"] = []
    if "choices" not in st.session_state:
        st.session_state["choices"] = []
    if "img" not in st.session_state:
        st.session_state["img"] = None
    if "has_image" not in st.session_state:
        st.session_state["has_image"] = False
    if "img_bytes" not in st.session_state:
        st.session_state["img_bytes"] = None
    if "current_group" not in st.session_state:
        st.session_state["current_group"] = "default"
    if "voice" not in st.session_state:
        st.session_state["voice"] = "ko-KR-Standard-A"  # 기본 음성 설정

def init_question_count():
    if "question_count" not in st.session_state:
        st.session_state["question_count"] = 0
    if "max_questions" not in st.session_state:
        st.session_state["max_questions"] = 10

def can_generate_more_questions() -> bool:
    return st.session_state.get("question_count", 0) < st.session_state.get("max_questions", 10)

def uploaded_image(on_change=None, args=None) -> Image.Image | None:
    with st.sidebar:
        st.markdown(
            "<div style='text-align: center; font-weight: bold; font-size: 25px;'>이미지 업로드</div>",
            unsafe_allow_html=True
        )

        # 안내 이미지 표시
        guide_img = Image.open('img/angmose.jpg').resize((300, 300))
        st.markdown(
            f"""
            <div style="text-align: center; padding-bottom: 10px;">
                <img src="data:image/png;base64,{img_to_base64(guide_img)}"
                    width="200"
                    style="border-radius: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />
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

        # 이미지 상태 초기화
        if "img_state" not in st.session_state:
            st.session_state["img_state"] = {
                "has_image": False,
                "img_bytes": None,
                "img": None
            }

        # 파일 업로더
        uploaded = st.file_uploader(
            label="",
            label_visibility="collapsed",
            on_change=on_change,
            args=args,
            type=["jpg", "jpeg", "png", "gif", "bmp", "webp"]
        )

        # 새로 업로드된 이미지가 있는 경우
        if uploaded is not None:
            try:
                img = Image.open(uploaded).convert("RGB")
                # 이미지를 세션 상태에 저장
                buf = BytesIO()
                img.save(buf, format="PNG")
                img_bytes = buf.getvalue()
                
                # 이미지 상태 업데이트
                st.session_state["img_state"] = {
                    "has_image": True,
                    "img_bytes": img_bytes,
                    "img": img
                }
                
                with st.container(border=True):
                    st.image(img, use_container_width=True)
                return img
            except Exception as e:
                st.error("이미지를 불러올 수 없습니다. 지원되는 형식: JPG, JPEG, PNG, GIF, BMP, WEBP")
                return None

        # 이전에 업로드된 이미지가 있는 경우
        elif st.session_state["img_state"]["has_image"]:
            try:
                img = st.session_state["img_state"]["img"]
                if img:
                    with st.container(border=True):
                        st.image(img, use_container_width=True)
                    return img
            except Exception as e:
                st.error("저장된 이미지를 불러올 수 없습니다. 새로운 이미지를 업로드해주세요.")
                st.session_state["img_state"] = {
                    "has_image": False,
                    "img_bytes": None,
                    "img": None
                }
                return None

        return None

# Utility functions
def img_to_base64(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def get_prompt(group: str, difficulty: str = None) -> Path:
    # Map group to exam type
    exam_mapping = {
        "yle": "YLE",
        "toefl_junior": "TOEFL_JUNIOR",
        "toeic": "TOEIC",
        "toefl": "TOEFL"
    }
    
    # Map difficulty to exam level
    difficulty_mapping = {
        "easy": "easy",
        "normal": "medium",
        "hard": "hard"
    }
    
    exam_type = exam_mapping.get(group, "default")
    exam_level = difficulty_mapping.get(difficulty, "medium")
    
    # First try to get the specific exam type and difficulty prompt
    if difficulty:
        prompt_file = f"prompt_{exam_type.lower()}_{exam_level}.txt"
        path = IN_DIR / prompt_file
        if path.exists():
            return path
    
    # If no specific prompt found or difficulty not provided, try exam-specific prompt
    path = IN_DIR / f"prompt_{exam_type.lower()}.txt"
    if path.exists():
        return path
    
    # If no exam-specific prompt found, use default
    st.warning(f"⚠️ '{exam_type}' 시험 유형의 프롬프트가 존재하지 않아 기본값을 사용합니다.")
    return IN_DIR / "prompt_default.txt"

def get_model() -> genai.GenerativeModel:
    GEMINI_KEY = st.secrets['GEMINI_KEY']
    GEMINI_MODEL = "gemini-2.0-flash"
    genai.configure(api_key=GEMINI_KEY, transport="rest")
    return genai.GenerativeModel(GEMINI_MODEL)

def generate_quiz(img: ImageFile.ImageFile, group: str, difficulty: str):
    if not can_generate_more_questions():
        return None, None, None, None

    prompt_desc = IN_DIR / "p1_desc.txt"
    sys_prompt_desc = prompt_desc.read_text(encoding="utf8")
    model_desc = get_model()
    resp_desc = model_desc.generate_content(
        [img, f"{sys_prompt_desc}\nDescribe this image"]
    )
    description = resp_desc.text.strip()

    quiz_prompt_path = get_prompt(group, difficulty)
    sys_prompt_quiz = quiz_prompt_path.read_text(encoding="utf8")
    model_quiz = get_model()
    
    # Add exam-specific context to the prompt
    exam_context = {
        "elementary": "YLE 시험 형식에 맞춰",
        "middle": "TOEFL Junior 시험 형식에 맞춰",
        "high": "TOEIC 시험 형식에 맞춰",
        "adult": "TOEFL 시험 형식에 맞춰"
    }
    
    exam_type = exam_context.get(group, "")
    difficulty_context = {
        "easy": "기초 수준의",
        "normal": "중급 수준의",
        "hard": "고급 수준의"
    }
    
    level = difficulty_context.get(difficulty, "중급 수준의")
    
    resp_quiz = model_quiz.generate_content(
        f"{sys_prompt_quiz}\n{exam_type} {level} 문제를 생성해주세요.\n{description}"
    )

    # Try different patterns to match the response
    quiz_text = resp_quiz.text.strip()
    
    # Pattern 1: Standard format with quotes
    quiz_match = re.search(r'Quiz:\s*["\'](.*?)["\']\s*$', quiz_text, re.MULTILINE)
    answer_match = re.search(r'Answer:\s*["\'](.*?)["\']\s*$', quiz_text, re.MULTILINE)
    choices_match = re.search(r'Choices:\s*(\[[^\]]+\](?:,\s*\[[^\]]+\])*)', quiz_text, re.MULTILINE | re.DOTALL)
    
    # Pattern 2: Format without quotes
    if not (quiz_match and answer_match and choices_match):
        quiz_match = re.search(r'Quiz:\s*(.*?)\s*$', quiz_text, re.MULTILINE)
        answer_match = re.search(r'Answer:\s*(.*?)\s*$', quiz_text, re.MULTILINE)
        choices_match = re.search(r'Choices:\s*\[(.*?)\]', quiz_text, re.MULTILINE | re.DOTALL)
        
        if choices_match:
            # Convert comma-separated choices to proper list format
            choices_str = choices_match.group(1)
            choices = [choice.strip().strip('"\'') for choice in choices_str.split(',')]
            choices = [f'"{choice}"' for choice in choices]
            choices_str = f"[{', '.join(choices)}]"
            choices_match = type('obj', (object,), {'group': lambda x: choices_str})

    if quiz_match and answer_match and choices_match:
        quiz_sentence = quiz_match.group(1).strip().strip('"\'')
        answer_word = [answer_match.group(1).strip().strip('"\'')]
        try:
            choices = ast.literal_eval(choices_match.group(1))
            if isinstance(choices, str):
                choices = [choice.strip().strip('"\'') for choice in choices.split(',')]
        except:
            # If parsing fails, try to extract choices manually
            choices_str = choices_match.group(1)
            choices = [choice.strip().strip('"\'') for choice in choices_str.split(',')]
        
        original_sentence = quiz_sentence.replace("_____", answer_word[0])
        st.session_state["question_count"] = st.session_state.get("question_count", 0) + 1
        return quiz_sentence, answer_word, choices, original_sentence

    # If all parsing attempts fail, raise error with the full response
    raise ValueError(f"AI 응답 파싱 실패! AI 응답 내용:\n{quiz_text}")

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

def tts_client() -> texttospeech.TextToSpeechClient:
    cred = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return texttospeech.TextToSpeechClient(credentials=cred)

def tokenize_sent(text: str) -> list[str]:
    nltk.download(["punkt", "punkt_tab"], quiet=True)
    return nltk.tokenize.sent_tokenize(text)

def set_quiz(img: ImageFile.ImageFile, group: str, difficulty: str):
    if img and not st.session_state["quiz"]:
        with st.spinner("이미지 퀴즈를 준비 중입니다...🦜"):
            # 이미지가 변경되었을 때 question_count 초기화
            if "last_image" not in st.session_state or st.session_state["last_image"] != img:
                st.session_state["question_count"] = 0
                st.session_state["last_image"] = img
            
            if not can_generate_more_questions():
                st.warning(f"현재 {st.session_state['question_count']}문제를 풀었어요! 새로운 이미지를 업로드하면 새로운 문제를 풀 수 있습니다.")
                return
                
            quiz_sentence, answer_word, choices, full_desc = generate_quiz(img, group, difficulty)
            if not quiz_sentence:  # If we've reached the question limit
                st.warning(f"현재 {st.session_state['question_count']}문제를 풀었어요! 새로운 이미지를 업로드하면 새로운 문제를 풀 수 있습니다.")
                return
                
            if isinstance(choices[0], list):
                choices = choices[0]
            answer_words = [answer_word]
            
            # Generate simple audio instruction
            question_audio = "Look at the image carefully."
            wav_file = synth_speech(question_audio, st.session_state["voice"], "wav")
            path = OUT_DIR / f"{Path(__file__).stem}.wav"
            with open(path, "wb") as fp:
                fp.write(wav_file)
                
            quiz_display = f"""이미지를 보고 설명을 잘 들은 후, 빈칸에 들어갈 알맞은 단어를 선택하세요.

**{quiz_sentence}**"""
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
                "_____", "<span style='color:black; font-weight:bold;'>_____</span>"
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
                    # 마지막 문제 정보 저장
                    st.session_state["last_question"] = quiz_display
                    st.session_state["last_user_choice"] = user_choice
                    st.session_state["last_correct_answer"] = answ[0]
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

def update_score(question: str, is_correct: bool):
    init_score()
    
    # Only update if this question hasn't been answered before
    if question not in st.session_state["answered_questions"]:
        st.session_state["answered_questions"].add(question)
        st.session_state["total_questions"] += 1
        
        if is_correct:
            st.session_state["correct_answers"] += 1
            st.session_state["total_score"] += 10
        else:
            # 오답인 경우 점수 차감 (0점 이하로는 내려가지 않음)
            st.session_state["total_score"] = max(0, st.session_state["total_score"] - 5)
            
        # 현재 문제의 피드백 생성
        feedback = generate_feedback(
            st.session_state.get("last_user_choice", ""),
            st.session_state.get("last_correct_answer", "")
        ) if not is_correct else "정답입니다! 🎉"
            
        # Add to current quiz data
        st.session_state["quiz_data"].append({
            "question": question,
            "correct": is_correct,
            "score": 10 if is_correct else -5,  # 정답은 10점, 오답은 -5점
            "timestamp": pd.Timestamp.now(),
            "feedback": feedback,
            "question_content": st.session_state.get("last_question", ""),
            "user_choice": st.session_state.get("last_user_choice", ""),
            "correct_answer": st.session_state.get("last_correct_answer", "")
        })
        
        # Save to database if user is authenticated
        if st.session_state.get("authenticated") and st.session_state.get("user_id"):
            save_learning_history(
                user_id=st.session_state["user_id"],
                group_code=st.session_state.get("current_group", "default"),
                score=10 if is_correct else -5,  # 정답은 10점, 오답은 -5점
                total_questions=1,  # 한 번에 한 문제씩 저장
                question_content=st.session_state.get("last_question", ""),
                feedback=feedback,
                user_choice=st.session_state.get("last_user_choice", ""),
                correct_answer=st.session_state.get("last_correct_answer", "")
            )

def generate_feedback(user_input: str, answ: str) -> str:
    try:
        prompt_path = IN_DIR / "p3_feedback.txt"
        template = prompt_path.read_text(encoding="utf8")
        prompt = template.format(user=user_input, correct=answ)
        model = get_model()
        response = model.generate_content(
            f"""다음과 같은 형식으로 피드백을 제공해주세요:
1. 정답과 오답의 관계 설명
2. 간단한 학습 조언
3. 다음에 도움이 될 팁

정답: {answ}
학생 답변: {user_input}

위 형식에 맞춰 한국어로만 답변해주세요. 번역은 하지 마세요."""
        )
        return response.text.strip() if response and response.text else "(⚠️ 응답 없음)"
    except Exception as e:
        return f"(⚠️ 피드백 생성 중 오류: {e})"

def show_score_summary():
    if "quiz_data" not in st.session_state or not st.session_state["quiz_data"]:
        return

    # Get the latest counts from session state
    total = st.session_state["total_questions"]
    correct = st.session_state["correct_answers"]
    accuracy = round((correct / total) * 100, 1) if total else 0.0
    score = st.session_state["total_score"]

    # Show current progress
    st.info(f"현재 {total}문제를 풀었어요! (정답률: {accuracy}%, 현재 점수: {score}점)")
    
    # Only show detailed summary when all 10 questions are answered
    if total < 10:
        return

    # Create a more visually appealing and accessible score display
    st.markdown("---")
    
    # Score header with emoji
    st.markdown("""
    <div style='text-align: center; margin-bottom: 20px;'>
        <h2 style='color: #4B89DC;'>🏆 최종 점수</h2>
    </div>
    """, unsafe_allow_html=True)

    # Create two columns for better layout
    col1, col2 = st.columns(2)

    with col1:
        # Score card with large, clear numbers
        st.markdown(f"""
        <div style='background-color: #f0f8ff; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <h3 style='color: #4B89DC; margin-bottom: 10px;'>최종 점수</h3>
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
    if total == 10 and correct == 10:
        st.success("🎉 축하합니다! 100점입니다! 완벽한 성적이에요!")
    elif accuracy >= 80:
        st.success("🎉 훌륭해요! 계속 이렇게 잘 해봐요!")
    elif accuracy >= 60:
        st.info("👍 잘하고 있어요! 조금만 더 노력해봐요!")
    else:
        st.warning("💪 조금 더 연습하면 더 잘할 수 있을 거예요!")
    
    clear_all_scores()

def reset_quiz():
    if st.session_state.get("quiz"):
        # Add some vertical space before the button
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 새로운 문제", type="primary"):
            # Keep authentication state
            auth_state = {
                "authenticated": st.session_state.get("authenticated", False),
                "username": st.session_state.get("username", ""),
                "user_id": st.session_state.get("user_id", None)
            }
            
            # Keep image state
            img_state = st.session_state.get("img_state", {
                "has_image": False,
                "img_bytes": None,
                "img": None
            })
            
            # Keep score-related states
            score_state = {
                "total_score": st.session_state.get("total_score", 0),
                "quiz_data": st.session_state.get("quiz_data", []),
                "answered_questions": st.session_state.get("answered_questions", set()),
                "correct_answers": st.session_state.get("correct_answers", 0),
                "total_questions": st.session_state.get("total_questions", 0),
                "question_count": st.session_state.get("question_count", 0),
                "last_image": st.session_state.get("last_image", None)
            }
            
            # Clear only current quiz states
            keys_to_clear = ["quiz", "answ", "audio", "choices"]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            # Clear form-related states
            for key in list(st.session_state.keys()):
                if key.startswith(("submitted_", "feedback_", "choice_", "form_question_")):
                    del st.session_state[key]
            
            # Restore important states
            st.session_state.update(auth_state)
            st.session_state["img_state"] = img_state
            st.session_state.update(score_state)
            
            st.rerun()

def show_learning_history():
    if not st.session_state.get("authenticated") or not st.session_state.get("user_id"):
        return
        
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; margin-bottom: 20px;'>
        <h2 style='color: #4B89DC;'>📚 학습 기록</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Get learning history from database
    history = get_learning_history(st.session_state["user_id"])
    if not history:
        st.info("아직 학습 기록이 없습니다. 퀴즈를 풀어보세요!")
        return

    # 데이터프레임 생성 (모든 컬럼 포함)
    history_df = pd.DataFrame(history, columns=['group_code', 'score', 'total_questions', 'timestamp', 'question_content', 'feedback', 'user_choice', 'correct_answer'])
    
    # 날짜/시간 포맷 변경
    history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
    history_df['date'] = history_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
    
    # 시험 유형 이름 매핑
    group_name_mapping = {
        "yle": "YLE",
        "toefl_junior": "TOEFL JUNIOR",
        "toeic": "TOEIC",
        "toefl": "TOEFL"
    }
    history_df['group_code'] = history_df['group_code'].map(group_name_mapping)
    
    # 정답 여부 표시를 위한 함수
    def get_result_icon(row):
        return "✅" if row['score'] > 0 else "❌"
    
    # 컬럼 이름 변경 및 표시
    history_df['result'] = history_df.apply(get_result_icon, axis=1)
    
    # 음수 점수를 0으로 변경
    history_df['score'] = history_df['score'].clip(lower=0)
    
    # 표시할 컬럼만 선택
    display_df = history_df[['date', 'group_code', 'result', 'score', 'total_questions']]
    display_df.columns = ['날짜', '시험 유형', '결과', '점수', '문제 수']
    
    # 필터링된 데이터가 있는 경우에만 표시
    if not display_df.empty:
        # 데이터프레임을 표시
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("학습 기록이 없습니다.")

def clear_all_scores():
    if st.button("🗑️ 현재 점수 초기화", type="secondary"):
        # Only clear current score-related data, not learning history
        st.session_state["total_score"] = 0
        st.session_state["quiz_data"] = []
        st.session_state["answered_questions"] = set()
        st.session_state["correct_answers"] = 0
        st.session_state["total_questions"] = 0
        st.session_state["question_count"] = 0  # Reset question count
        st.success("현재 점수가 초기화되었습니다.")
        st.rerun()

# Main application
if __name__ == "__main__":
    try:
        # Initialize page configuration first
        init_page()
        
        # Initialize session state
        init_score()
        init_question_count()
        
        # Check authentication from cookie
        auth_cookie = get_auth_cookie()
        if auth_cookie and not st.session_state.get("authenticated"):
            username, user_id = auth_cookie.split(":")
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.session_state["user_id"] = user_id
        
        # 로그인 상태 확인
        if not st.session_state.get("authenticated", False):
            show_auth_page()
        else:
            # 메인 페이지 타이틀
            st.markdown(
                """
                <div style='text-align: center; margin-bottom: 30px;'>
                    <h1 style='font-size:48px; color: #4B89DC;'>🔊앵무새 스쿨</h1>
                    <p style='font-size: 20px; color: #555;'>
                        <b>이미지로 배우는 즐거운 영어 학습!</b>
                    </p>
                </div>
                """, unsafe_allow_html=True
            )
            
            # 사이드바에 사용자 정보 표시
            with st.sidebar:
                st.markdown(f"""
                <div style='text-align: center; padding: 10px; background-color: #f0f8ff; border-radius: 10px; margin-bottom: 20px;'>
                    <h3 style='color: #4B89DC;'>👤 {st.session_state.get('username', '')}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # 닉네임 변경 폼
                with st.expander("✏️ 닉네임 변경", expanded=False):
                    with st.form("change_username_form"):
                        new_username = st.text_input(
                            "새로운 닉네임",
                            placeholder="변경할 닉네임을 입력하세요",
                            value=st.session_state.get('username', '')
                        )
                        submitted = st.form_submit_button("변경하기", use_container_width=True)
                        
                        if submitted:
                            if not new_username:
                                st.error("닉네임을 입력해주세요.")
                            elif new_username == st.session_state.get('username'):
                                st.info("현재 사용 중인 닉네임과 동일합니다.")
                            else:
                                if update_username(st.session_state.get('user_id'), new_username):
                                    st.session_state["username"] = new_username
                                    set_auth_cookie(new_username, st.session_state.get('user_id'))  # Update cookie
                                    st.success("닉네임이 변경되었습니다!")
                                    st.rerun()
                                else:
                                    st.error("이미 사용 중인 닉네임입니다.")
                
                if st.button("로그아웃", use_container_width=True):
                    # Clear all session state including image state
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    clear_auth_cookie()  # Clear auth cookie
                    st.rerun()
            
            # 메인 컨텐츠
            init_score()
            init_question_count()
            
            # 1. 시험 종류 선택
            st.markdown("### 📚 시험 종류 선택")
            group_display = st.selectbox(
                "시험 종류를 선택하세요.",
                ["YLE", "TOEFL JUNIOR", "TOEIC", "TOEFL"],
                help="선택한 시험 유형에 맞는 퀴즈가 출제됩니다."
            )
            group_mapping = {
                "YLE": "yle",
                "TOEFL JUNIOR": "toefl_junior",
                "TOEIC": "toeic",
                "TOEFL": "toefl"
            }
            group_code = group_mapping.get(group_display, "default")
            st.session_state["current_group"] = group_code

            # 2. 난이도 선택
            st.markdown("### 🎯 난이도 선택")
            difficulty_display = st.selectbox(
                "문제 난이도를 선택하세요.",
                ["쉬움", "중간", "어려움"],
                help="선택한 난이도에 따라 문제의 복잡도가 달라집니다."
            )
            difficulty_mapping = {
                "쉬움": "easy",
                "중간": "normal",
                "어려움": "hard"
            }
            global_difficulty = difficulty_mapping.get(difficulty_display, "normal")

            # 3. 이미지 업로드 or 복원
            st.markdown("### 🖼️ 이미지 업로드")
            img = uploaded_image()

            if img:
                # 새로운 퀴즈 생성이 필요한 경우
                if not st.session_state.get("quiz"):
                    set_quiz(img, group_code, global_difficulty)
                
                show_quiz(global_difficulty)

                if st.session_state.get("quiz_data"):
                    show_score_summary()
                    show_learning_history()

                reset_quiz()
            else:
                st.info("이미지를 업로드하면 퀴즈가 시작됩니다!")
                
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
        st.info("페이지를 새로고침하거나 다시 시도해주세요.") 
