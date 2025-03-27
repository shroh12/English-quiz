from PIL import Image, ImageFile

from step_1_1 import IMG_DIR, IN_DIR  # 이전에 작성한 모듈을 불러옵니다.
from step_1_2 import get_model
from step_2_3 import tokenize_sent


def generate_quiz(img: ImageFile.ImageFile) -> tuple[list, list]:
    prompt_desc = IN_DIR / "p1_desc.txt"  # 이미지 묘사 시스템 프롬프트
    model_desc = get_model(sys_prompt=prompt_desc.read_text(encoding="utf8"))
    resp_desc = model_desc.generate_content([img, "Describe this image"])  # 문장 생성

    prompt_quiz = IN_DIR / "p2_quiz.txt"  # 퀴즈 생성 시스템 프롬프트
    model_quiz = get_model(sys_prompt=prompt_quiz.read_text(encoding="utf8"))
    resp_quiz = model_quiz.generate_content(resp_desc.text)  # 퀴즈 생성
    return tokenize_sent(resp_quiz.text), tokenize_sent(resp_desc.text)

def generate_feedback(user_input: str, answ: str) -> str:
     prompt_feedback = IN_DIR / "p3_feedback.txt"  # 피드백 생성 프롬프트 템플릿
     text = prompt_feedback.read_text(encoding="utf8")  # 템플릿 불러오기
     prompt = text.format(user_input, answ)  # 중괄호 {}를 사용자 입력과 정답으로 대체
     model = get_model()  # 시스템 프롬프트를 사용하지 않는 모델 객체 생성
     resp = model.generate_content(prompt)  # 피드백 생성
     return resp.text

# 🔽 빈칸에 들어갈 단어 추출 로직
def extract_blank_word(quiz_sentence, answer_sentence):
    quiz_parts = quiz_sentence.split()
    answer_parts = answer_sentence.split()
    for q_word, a_word in zip(quiz_parts, answer_parts):
        if q_word == "_____":
            return a_word
    return None

if __name__ == "__main__":
    img = Image.open(IMG_DIR / "billboard.jpg")
    quiz, answ = generate_quiz(img)
    print(f"quiz: {quiz[0]}")  # quiz: This _____ advertises...
    print(f"answ: {answ[0]}")  # answ: This billboard advertises...
    resp = generate_feedback(
        "this image showcase a bilboard advertise",  # 사용자 입력 예시
        "This image showcases a billboard advertising",  # 올바른 정답 예시
    )
    print(resp)
