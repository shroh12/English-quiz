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

def generate_feedback(user_input: str, answ: list) -> str:
    # 빈칸마다 개별 피드백 제공
    feedback = ""
    for idx, correct_answer in enumerate(answ):
        feedback += f"**정답 {idx + 1}:** 학생 답변: {user_input[idx] if idx < len(user_input) else '빈칸'}\n"
        feedback += f"정답: {correct_answer}\n"
        feedback += f"피드백: "
        # 피드백 로직을 추가하여 학생의 답변과 정답을 비교
        if user_input[idx].strip().lower() == correct_answer.lower():
            feedback += "정확합니다! 좋은 접근입니다.\n"
        else:
            feedback += "정답을 다시 확인해 보세요.\n"
    return feedback



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
