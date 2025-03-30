from PIL import Image, ImageFile
import random
from step_1_1 import IMG_DIR, IN_DIR
from step_1_2 import get_model
from step_2_3 import tokenize_sent


def generate_quiz(img: ImageFile.ImageFile) -> tuple[list, list]:
    """
    이미지를 받아서 퀴즈 문장과 빈칸 리스트(정답 + 객관식 보기)를 반환합니다.
    반환 형식: (quiz_sentence, list of blanks with choices and answers)
    """
    # 🔹 1. 이미지 설명 생성
    prompt_desc = IN_DIR / "p1_desc.txt"
    model_desc = get_model(sys_prompt=prompt_desc.read_text(encoding="utf8"))
    resp_desc = model_desc.generate_content([img, "Describe this image"])

    # 🔹 2. 설명을 기반으로 퀴즈 문장 생성
    prompt_quiz = IN_DIR / "p2_quiz.txt"
    model_quiz = get_model(sys_prompt=prompt_quiz.read_text(encoding="utf8"))
    resp_quiz = model_quiz.generate_content(resp_desc.text)

    # 🔹 3. 첫 문장만 퀴즈로 사용 (필요 시 여러 문장 처리 가능)
    quiz_sentence = tokenize_sent(resp_quiz.text)[0]
    answer_sentence = tokenize_sent(resp_desc.text)[0]

    # 🔹 4. 빈칸 정보 추출 (정답 + 객관식 보기)
    blanks = extract_blank_words(quiz_sentence, answer_sentence)

    return quiz_sentence, blanks

DISTRACTOR_POOL = [
    "goal", "strategy", "success", "achievement", "target",
    "vision", "effort", "result", "planning", "challenge",
    "growth", "performance", "mission", "teamwork", "drive"
]

# 🔽 객관식 정답+오답 보기 생성
def make_choices(correct_word: str) -> list[str]:
    distractors = [w for w in DISTRACTOR_POOL if w.lower() != correct_word.lower()]
    options = random.sample(distractors, 3) + [correct_word]
    random.shuffle(options)
    return options

# 🔽 빈칸에 들어갈 정답 단어 + 보기 옵션 리스트 반환
def extract_blank_words(quiz_sentence: str, answer_sentence: str) -> list[dict]:
    quiz_parts = quiz_sentence.split()
    answer_parts = answer_sentence.split()

    blanks = []
    for q, a in zip(quiz_parts, answer_parts):
        if q == "_____":
            blanks.append({
                "answer": a,
                "choices": make_choices(a)
            })
    return blanks

def display_quiz(quiz_sentence: str, blanks: list[dict]):
    st.subheader("📝 객관식 퀴즈를 풀어보세요")
    quiz_parts = quiz_sentence.split()
    blank_idx = 0
    quiz_display = ""

    for word in quiz_parts:
        if word == "_____":
            key = f"blank_{blank_idx}"
            selected = st.radio(
                f"빈칸 {blank_idx+1}",
                blanks[blank_idx]["choices"],
                key=key
            )
            quiz_display += f"**{selected}** "
            blank_idx += 1
        else:
            quiz_display += word + " "

    st.markdown("---")
    st.markdown(f"🔎 완성된 문장:\n\n{quiz_display.strip()}")
# 예시 퀴즈 세트
quiz_list = [
    "This image represents a team observing a leader who has achieved peak _____ or reached a significant business _____, possibly exceeding _____ _____.",
    "The mountain symbolizes the challenges and _____ _____ required to reach _____ _____, and demonstrates a commitment to strategic _____."
]

answer_list = [
    "This image represents a team observing a leader who has achieved peak performance or reached a significant business goal, possibly exceeding revenue targets.",
    "The mountain symbolizes the challenges and hard work required to reach ambitious goals, and demonstrates a commitment to strategic planning."
]

if __name__ == "__main__":
    img = Image.open(IMG_DIR / "billboard.jpg")
    quiz, answ = generate_quiz(img)

    # 퀴즈 문장 표시
    st.image(img, caption="분석할 이미지", use_column_width=True)
    st.markdown("### 🎯 생성된 퀴즈 문장")
    st.write(quiz[0])

    # 정답 단어 + 선택지 생성
    blanks = extract_blank_words(quiz[0], answ[0])

    # 객관식 퀴즈 표시
    display_quiz(quiz[0], blanks)

    # ✨ 선택된 정답 표시
    if st.button("정답 보기"):
        st.markdown("#### ✅ 정답 문장")
        st.write(answ[0])
