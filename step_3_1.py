from PIL import Image, ImageFile
import random
from step_1_1 import IMG_DIR, IN_DIR
from step_1_2 import get_model
from step_2_3 import tokenize_sent


def generate_quiz(img: ImageFile.ImageFile) -> tuple[list, list]:
    prompt_desc = IN_DIR / "p1_desc.txt"
    model_desc = get_model(sys_prompt=prompt_desc.read_text(encoding="utf8"))
    resp_desc = model_desc.generate_content([img, "Describe this image"])

    prompt_quiz = IN_DIR / "p2_quiz.txt"
    model_quiz = get_model(sys_prompt=prompt_quiz.read_text(encoding="utf8"))
    resp_quiz = model_quiz.generate_content(resp_desc.text)
    return tokenize_sent(resp_quiz.text), tokenize_sent(resp_desc.text)

def generate_feedback(user_input: str, answ: str) -> str:
    prompt_feedback = IN_DIR / "p3_feedback.txt"
    text = prompt_feedback.read_text(encoding="utf8")
    prompt = text.format(user_input, answ)
    model = get_model()
    resp = model.generate_content(prompt)
    return resp.text
    
DISTRACTOR_POOL = [
    "goal", "strategy", "success", "achievement", "target",
    "vision", "effort", "result", "planning", "challenge",
    "growth", "performance", "mission", "teamwork", "drive"
]

def generate_choices_with_answer(correct_answer: str, distractor_pool: list[str], n_choices: int = 4):
    distractors = [d for d in distractor_pool if d.lower() != correct_answer.lower()]
    sampled_distractors = random.sample(distractors, n_choices - 1)
    choices = sampled_distractors + [correct_answer]
    random.shuffle(choices)
    correct_index = choices.index(correct_answer)
    return choices, correct_index
    
# 🔽 객관식 정답+오답 보기 생성
def make_choices(correct_word: str) -> list[str]:
    distractors = [w for w in DISTRACTOR_POOL if w.lower() != correct_word.lower()]
    options = random.sample(distractors, 3) + [correct_word]
    random.shuffle(options)
    return options

def extract_blank_words(quiz_sentence: str, answer_sentence: str) -> list[dict]:
    quiz_parts = quiz_sentence.split()
    answer_parts = answer_sentence.split()

    blanks = []
    for q, a in zip(quiz_parts, answer_parts):
        if q == "_____":
            choices, _ = generate_choices_with_answer(a, DISTRACTOR_POOL)
            blanks.append({
                "answer": a,
                "choices": choices
            })
    return blanks

if __name__ == "__main__":
    img = Image.open(IMG_DIR / "billboard.jpg")
    quiz, answ = generate_quiz(img)

    print(f"quiz: {quiz[0]}")
    print(f"answ: {answ[0]}")

    # ✨ 정답 단어만 추출해서 표시
    blanks = extract_blank_words(quiz[0], answ[0])
    print(f"# correct answer(s): {', '.join(blanks)}")

    # 사용자의 오답 예시 → 정답 문장 전체 비교로 피드백 생성
    resp = generate_feedback(
        "this image showcase a bilboard advertise",
        "This image showcases a billboard advertising",
    )
    print(resp)
