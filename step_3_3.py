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
from database import register_user, verify_user, save_learning_history, get_learning_history, update_username

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
    # First try to get the specific group and difficulty prompt
    if difficulty:
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
        prompt_file = prompts.get((group, difficulty), None)
        if prompt_file:
            path = IN_DIR / prompt_file
            if path.exists():
                return path
    
    # If no specific prompt found or difficulty not provided, try group-specific prompt
    path = IN_DIR / f"quiz_{group}.txt"
    if path.exists():
        return path
    
    # If no group-specific prompt found, use default
    st.warning(f"⚠️ '{group}' 그룹의 프롬프트가 존재하지 않아 기본값을 사용합니다.")
    return IN_DIR / "prompt_default.txt"

def get_model(sys_prompt: str = None) -> genai.GenerativeModel:
    GEMINI_KEY = st.secrets['GEMINI_KEY']
    GEMINI_MODEL = "gemini-2.0-flash"
    genai.configure(api_key=GEMINI_KEY, transport="rest")
    return genai.GenerativeModel(GEMINI_MODEL, system_instruction=sys_prompt)

def generate_quiz(img: ImageFile.ImageFile, group: str, difficulty: str):
    if not can_generate_more_questions():
        return None, None, None, None

    prompt_desc = IN_DIR / "p1_desc.txt"
    model_desc = get_model(sys_prompt=prompt_desc.read_text(encoding="utf8"))
    resp_desc = model_desc.generate_content([img, "Describe this image"])
    description = resp_desc.text.strip()

    quiz_prompt_path = get_prompt(group, difficulty)
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
        st.session_state["question_count"] = st.session_state.get("question_count", 0) + 1
        return quiz_sentence, answer_word, choices, original_sentence

    raise ValueError(f"AI 응답 파싱 실패! AI 응답 내용:\n{resp_quiz.text}")

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
            quiz_sentence, answer_word, choices, full_desc = generate_quiz(img, group, difficulty)
            if not quiz_sentence:  # If we've reached the question limit
                st.warning("이미지에 대한 10개의 문제를 모두 생성했습니다. 새로운 이미지를 업로드해주세요.")
                return
                
            if isinstance(choices[0], list):
                choices = choices[0]
            answer_words = [answer_word]
            wav_file = synth_speech(full_desc, st.session_state["voice"], "wav")
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
            # Ensure score doesn't go below 0
            st.session_state["total_score"] = max(0, st.session_state["total_score"] - 10)
            
        # Add to current quiz data
        st.session_state["quiz_data"].append({
            "question": question,
            "correct": is_correct,
            "timestamp": pd.Timestamp.now()
        })
        
        # Save to database if user is authenticated
        if st.session_state.get("authenticated") and st.session_state.get("user_id"):
            save_learning_history(
                user_id=st.session_state["user_id"],
                group_code=st.session_state.get("current_group", "default"),
                score=st.session_state["total_score"],
                total_questions=st.session_state["total_questions"]
            )

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

def show_score_summary():
    if "quiz_data" not in st.session_state or not st.session_state["quiz_data"]:
        return

    # Get the latest counts from session state
    total = st.session_state["total_questions"]
    correct = st.session_state["correct_answers"]
    accuracy = round((correct / total) * 100, 1) if total else 0.0
    score = st.session_state["total_score"]

    # Only show score summary when all 10 questions are answered
    if total < 10:
        st.info(f"아직 {10 - total}문제가 남았어요! 계속 풀어보세요! 💪")
        return

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
    
    # Add clear all scores button at the bottom
    clear_all_scores()

def reset_quiz():
    if st.session_state.get("quiz"):
        # Add some vertical space before the button
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 새로운 문제", type="primary"):
            # Keep image state
            img_state = st.session_state.get("img_state", {
                "has_image": False,
                "img_bytes": None,
                "img": None
            })
            
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # Restore image state
            st.session_state["img_state"] = img_state
            
            # Initialize other necessary states
            init_score()
            init_question_count()
            
            st.rerun()
        # Add some vertical space after the button
        st.markdown("<br>", unsafe_allow_html=True)

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
        
    # Convert history to DataFrame for calculations
    history_df = pd.DataFrame(history, columns=['group_code', 'score', 'total_questions', 'timestamp'])
    if len(history_df) > 0:
        latest_score = history_df["score"].iloc[-1]
        accuracy = ((latest_score / ((len(history_df)) * 10)) * 100).round(1)
        
        # Create two columns for score and accuracy
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div style='background-color: #f0f8ff; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <h3 style='color: #4B89DC; margin-bottom: 15px; font-size: 24px;'>현재 점수</h3>
                <h1 style='font-size: 36px; color: #2E7D32; margin: 0;'>{latest_score}점</h1>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div style='background-color: #f0f8ff; padding: 20px; border-radius: 10px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <h3 style='color: #4B89DC; margin-bottom: 15px; font-size: 24px;'>정답률</h3>
                <h1 style='font-size: 36px; color: #2E7D32; margin: 0;'>{accuracy}%</h1>
            </div>
            """, unsafe_allow_html=True)
            
        # Show learning history table
        st.markdown("### 📊 상세 학습 기록")
        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
        history_df['date'] = history_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        history_df = history_df[['date', 'group_code', 'score', 'total_questions']]
        history_df.columns = ['날짜', '그룹', '점수', '문제 수']
        st.dataframe(history_df, use_container_width=True)

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
        init_page()
        
        # 로그인 상태 확인
        if not st.session_state.get("authenticated", False):
            show_auth_page()
        else:
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
                                    st.success("닉네임이 변경되었습니다!")
                                    st.rerun()
                                else:
                                    st.error("이미 사용 중인 닉네임입니다.")
                
                if st.button("로그아웃", use_container_width=True):
                    # Clear all session state including image state
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
            
            # 메인 컨텐츠
            init_score()
            init_question_count()
            
            # 1. 그룹 선택
            st.markdown("### 📚 학습 그룹 선택")
            group_display = st.selectbox(
                "연령대를 선택하세요.",
                ["초등학생", "중학생", "고등학생", "성인"],
                help="선택한 연령대에 맞는 난이도의 퀴즈가 출제됩니다."
            )
            group_mapping = {
                "초등학생": "elementary",
                "중학생": "middle",
                "고등학생": "high",
                "성인": "adult"
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
