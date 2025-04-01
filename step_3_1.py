from PIL import Image, ImageFile
import re
import ast
from step_1_1 import IMG_DIR, IN_DIR
from step_1_2 import get_model
from step_2_3 import tokenize_sent

def generate_quiz(img: ImageFile.ImageFile):
    prompt_desc = IN_DIR / "p1_desc.txt"
    model_desc = get_model(sys_prompt=prompt_desc.read_text(encoding="utf8"))
    resp_desc = model_desc.generate_content([img, "Describe this image"])
    prompt_quiz = IN_DIR / "p2_quiz.txt"
    model_quiz = get_model(sys_prompt=prompt_quiz.read_text(encoding="utf8"))
    resp_quiz = model_quiz.generate_content(resp_desc.text)
    # AI의 응답을 parsing하여 Original, Quiz, Answer, Choices 얻음
    original_match = re.search(r'Original:\s*"(.*?)"', resp_quiz.text)
    quiz_match = re.search(r'Quiz:\s*"(.*?)"', resp_quiz.text)
    answer_match = re.search(r'Answer:\s*"(.*?)"', resp_quiz.text)
    choices_match = re.search(r'Choices:\s*(\[[^\]]+\])', resp_quiz.text)
    if quiz_match and answer_match and choices_match and original_match:
        quiz_sentence = quiz_match.group(1)
        answer_word = answer_match.group(1)
        choices = ast.literal_eval(choices_match.group(1))
        original_sentence = original_match.group(1)  # match 객체 대신 문자열로 반환
        return quiz_sentence, answer_word, choices, original_sentence
    else:
        raise ValueError("AI 응답 파싱 실패!")

def generate_feedback(user_input: str, answ: str) -> str:
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
