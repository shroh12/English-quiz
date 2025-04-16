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

    quiz_prompt_filename = get_prompt_by_group_and_difficulty(group, difficulty)
    quiz_prompt_path = IN_DIR / quiz_prompt_filename
    
    model_quiz = get_model(sys_prompt=quiz_prompt_path.read_text(encoding="utf8"))
    resp_quiz = model_quiz.generate_content(description)

    # Quiz, Answer, Choices만이라도 파싱하도록 유연화
    quiz_match = re.search(r'Quiz:\s*["“”]?(.*?)["“”]?\s*$', resp_quiz.text, re.MULTILINE)
    answer_match = re.search(r'Answer:\s*["“”]?(.*?)["“”]?\s*$', resp_quiz.text, re.MULTILINE)
    choices_match = re.search(r'Choices:\s*(\[[^\]]+\](?:,\s*\[[^\]]+\])*)', resp_quiz.text, re.MULTILINE | re.DOTALL)

    if quiz_match and answer_match and choices_match:
        quiz_sentence = quiz_match.group(1).strip()
        answer_word = [w.strip().strip('"') for w in answer_match.group(1).split(",")]
        choices = ast.literal_eval(f"[{choices_match.group(1)}]")

        # Original 문장이 없다면 quiz 문장으로 대신함
        original_sentence = quiz_sentence.replace("_____", answer_word[0])

        return quiz_sentence, answer_word, choices, original_sentence

    # 에러 발생 시 실제 AI 응답 추가 제공 (디버깅용)
    raise ValueError(f"AI 응답 파싱 실패! AI 응답 내용:\n{resp_quiz.text}")



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
    img = Image.open(IMG_DIR / "billboard.jpg")

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
