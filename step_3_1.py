from PIL import Image, ImageFile
import random
from step_1_1 import IMG_DIR, IN_DIR
from step_1_2 import get_model
from step_2_3 import tokenize_sent


def generate_quiz(img: ImageFile.ImageFile) -> tuple[list, list]:
    # 1. 이미지 설명 생성
    prompt_desc = IN_DIR / "p1_desc.txt"
    model_desc = get_model(sys_prompt=prompt_desc.read_text(encoding="utf8"))
    resp_desc = model_desc.generate_content([img, "Describe this image"])

    # 2. 설명을 바탕으로 객관식 퀴즈 문장 생성 (프롬프트 내용은 위와 같이 수정됨)
    prompt_quiz = IN_DIR / "p2_quiz.txt"
    model_quiz = get_model(sys_prompt=prompt_quiz.read_text(encoding="utf8"))
    resp_quiz = model_quiz.generate_content(resp_desc.text)

    # tokenize_sent() 함수는 문장을 리스트로 분리한다고 가정
    return tokenize_sent(resp_quiz.text), tokenize_sent(resp_desc.text)

def generate_feedback(user_input: str, answ: str) -> str:
    prompt_feedback = IN_DIR / "p3_feedback.txt"
    text = prompt_feedback.read_text(encoding="utf8")
    prompt = text.format(user_input, answ)
    model = get_model()
    resp = model.generate_content(prompt)
    return resp.text

# 객관식 오답 선택지용 단어 목록
DISTRACTOR_POOL = [
    "goal", "strategy", "success", "achievement", "target",
    "vision", "effort", "result", "planning", "challenge",
    "growth", "performance", "mission", "teamwork", "drive"
]
# AI가 동적으로 생성한 정답 단어에 맞춰 3개의 오답 선택지를 동적 생성하는 함수 예시
def generate_distractors(correct_word: str) -> list[str]:
    prompt = (
        f"비즈니스 관련 맥락에서 '{correct_word}'와 의미가 비슷하지만 정답이 아닌 "
        "3개의 오답 단어를 쉼표로 구분해서 제공해 주세요. "
        "예시: word1, word2, word3"
    )
    model = get_model()
    resp = model.generate_content(prompt)
    distractors = [word.strip() for word in resp.text.split(",") if word.strip()]
    # 생성된 단어 수가 부족하면 기본 목록에서 보완
    if len(distractors) < 3:
        fallback = [
            "goal", "strategy", "success", "achievement", "target",
            "vision", "effort", "result", "planning", "challenge",
            "growth", "performance", "mission", "teamwork", "drive"
        ]
        additional = random.sample(
            [w for w in fallback if w.lower() != correct_word.lower()],
            3 - len(distractors)
        )
        distractors.extend(additional)
    return distractors[:3]


def make_choices(correct_word: str) -> list[str]:
    distractors = generate_distractors(correct_word)
    options = distractors + [correct_word]
    random.shuffle(options)
    return options


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

def display_quiz_radio(quiz_sentence: str, blanks: list[dict]):
    st.subheader("📝 객관식 퀴즈를 풀어보세요")

    quiz_parts = quiz_sentence.split()
    blank_idx = 0
    displayed_sentence = ""

    for word in quiz_parts:
        if word == "_____":
            options = blanks[blank_idx]["choices"]
            selected = st.radio(
                label=f"빈칸 {blank_idx + 1}",
                options=options,
                key=f"radio_{blank_idx}"
            )
            displayed_sentence += f" **{selected}** "
            blank_idx += 1
        else:
            displayed_sentence += f"{word} "

    st.markdown("---")
    st.markdown(f"🔎 **선택한 문장:**\n\n{displayed_sentence.strip()}")

if __name__ == "__main__":
    img = Image.open(IMG_DIR / "billboard.jpg")
    quiz_sentences, answer_sentences = generate_quiz(img)

    # 화면에 이미지와 퀴즈 문장 표시
    st.image(img, caption="분석할 이미지", use_column_width=True)
    st.markdown("### 🎯 생성된 퀴즈 문장")
    st.write(quiz_sentences[0])

    # 정답 단어 및 객관식 선택지 생성
    blanks = extract_blank_words(quiz_sentences[0], answer_sentences[0])

    # 🔥 radio 버튼으로 객관식 퀴즈 표시
    display_quiz_radio(quiz_sentences[0], blanks)

    # 정답 확인 버튼 추가
    if st.button("정답 보기"):
        st.markdown("#### ✅ 정답 문장")
        st.write(answer_sentences[0])
