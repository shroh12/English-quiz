from PIL import Image, ImageFile
import re
import ast
from pathlib import Path
import streamlit as st
from step_1_1 import IMG_DIR, IN_DIR
from step_1_2 import get_model
from step_2_3 import tokenize_sent
from io import BytesIO

def get_prompt_by_group(group: str) -> Path:
    path = IN_DIR / f"quiz_{group}.txt"
    if not path.exists():
        st.warning(f"⚠️ '{group}' 그룹의 프롬프트가 존재하지 않아 기본값을 사용합니다.")
        path = IN_DIR / "prompt_default.txt"
    return path
        
def generate_quiz(img: ImageFile.ImageFile, group: str, difficulty: str):
    prompt_desc = IN_DIR / "p1_desc.txt"
    model_desc = get_model(sys_prompt=prompt_desc.read_text(encoding="utf8"))
    resp_desc = model_desc.generate_content([img, "Describe this image"])
    description = resp_desc.text.strip()

    quiz_prompt_filename = get_prompt_by_group_and_difficulty(group, difficulty)
    quiz_prompt_path = IN_DIR / quiz_prompt_filename
    model_quiz = get_model(sys_prompt=quiz_prompt_path.read_text(encoding="utf8"))
    resp_quiz = model_quiz.generate_content(description)

    quiz_match = re.search(r'Quiz:\s*["“”]?(.*?)["“”]?\s*$', resp_quiz.text, re.MULTILINE)
    answer_match = re.search(r'Answer:\s*["“”]?(.*?)["“”]?\s*$', resp_quiz.text, re.MULTILINE)
    choices_match = re.search(r'Choices:\s*(\[[^\]]+\](?:,\s*\[[^\]]+\])*)', resp_quiz.text, re.MULTILINE | re.DOTALL)

    if not (quiz_match and answer_match and choices_match):
        raise ValueError(f"AI 응답 파싱 실패! 필드 누락\n응답 원문:\n{resp_quiz.text}")

    quiz_sentence = quiz_match.group(1).strip()
    answer_raw = answer_match.group(1).strip().strip('"')
    answer_word = [answer_raw] if isinstance(answer_raw, str) else answer_raw

    try:
        choices = ast.literal_eval(f"[{choices_match.group(1)}]")
    except Exception as e:
        raise ValueError(f"Choices 파싱 실패: {e}\nAI 응답:\n{resp_quiz.text}")

    original_sentence = quiz_sentence.replace("_____", answer_word[0])
    return quiz_sentence, answer_word, choices, original_sentence




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


if __name__ == "__main__":

    IMG_DIR = Path("images")  # 이미지 경로 설정 (수정 필요)
    img = Image.open(BytesIO(st.session_state["img_bytes"]))

    quiz_sentence, answer_word, choices, full_desc = generate_quiz(img)

    print(f"Quiz: {quiz_sentence}")
    print(f"Answer: {answer_word}")
    print(f"Choices: {choices}")

    # 안전하게 오답 선택 (정답이 아닌 첫 번째 보기)
    user_wrong_input = next((c for c in choices if c != answer_word), None)

    if user_wrong_input:
        feedback = generate_feedback(user_wrong_input, answer_word)
        print(f"\nFeedback for wrong input ({user_wrong_input}): {feedback}")
    else:
        print("⚠️ 오답 피드백 테스트용 보기를 찾을 수 없습니다.")
