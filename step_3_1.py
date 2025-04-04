from PIL import Image, ImageFile
import re
import ast
from pathlib import Path
import streamlit as st
from step_1_1 import IMG_DIR, IN_DIR
from step_1_2 import get_model
from step_2_3 import tokenize_sent

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

    # 🔥 난이도 및 연령대별 프롬프트 동적 선택
    quiz_prompt_filename = get_prompt_by_group_and_difficulty(group, difficulty)
    quiz_prompt_path = Path(quiz_prompt_filename)
    model_quiz = get_model(sys_prompt=quiz_prompt_path.read_text(encoding="utf8"))
    resp_quiz = model_quiz.generate_content(description)

    original_match = re.search(r'Original:\s*["“”]?(.*?)["“”]?\s*$', resp_quiz.text, re.MULTILINE)
    quiz_match = re.search(r'Quiz:\s*["“”]?(.*?)["“”]?\s*$', resp_quiz.text, re.MULTILINE)
    answer_match = re.search(r'Answer:\s*["“”]?(.*?)["“”]?\s*$', resp_quiz.text, re.MULTILINE)
    choices_match = re.search(r'Choices:\s*(\[[^\]]+\])', resp_quiz.text)

    if quiz_match and answer_match and choices_match and original_match:
        quiz_sentence = quiz_match.group(1).strip()
        answer_word = answer_match.group(1).strip()
        choices = ast.literal_eval(choices_match.group(1))
        original_sentence = original_match.group(1).strip()
        return quiz_sentence, answer_word, choices, original_sentence

    raise ValueError("AI 응답 파싱 실패!")

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
    # 사용자의 오답과 정답을 기반으로 피드백을 위한 프롬프트 생성
    # AI 모델을 통해 맞춤형 피드백을 생성하여 반환
    prompt_feedback = IN_DIR / "p3_feedback.txt"
    text = prompt_feedback.read_text(encoding="utf8")
    prompt = text.format(user_input, answ)
    model = get_model()
    resp = model.generate_content(prompt)
    return resp.text

if __name__ == "__main__":
    img = Image.open(IMG_DIR / "billboard.jpg")
    quiz_sentence, answer_word, choices, full_desc = generate_quiz(img)

    print(f"Quiz: {quiz_sentence}")
    print(f"Answer: {answer_word}")
    print(f"Choices: {choices}")

    # 예시 오답에 대한 피드백
    user_wrong_input = choices[0] if choices[0] != answer_word else choices[1]
    feedback = generate_feedback(user_wrong_input, answer_word)
    print(f"\nFeedback: {feedback}")
