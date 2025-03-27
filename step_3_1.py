from PIL import Image, ImageFile

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

# 🔽 빈칸에 들어갈 단어만 추출
# 빈칸 단어 추출
def extract_blank_words(quiz_sentence, answer_sentence):
    quiz_parts = quiz_sentence.split()
    answer_parts = answer_sentence.split()
    return [a for q, a in zip(quiz_parts, answer_parts) if q == "_____"]


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
