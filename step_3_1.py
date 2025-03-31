from PIL import Image, ImageFile
import random
from step_1_1 import IMG_DIR, IN_DIR
from step_1_2 import get_model
from step_2_3 import tokenize_sent
import re

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


def parse_quiz_response(resp_text: str):
    quiz_match = re.search(r'Quiz: (.+?)\n', resp_text)
    quiz_sentence = quiz_match.group(1).strip()

    blanks = []
    options_matches = re.findall(r'Blank \d options:\n(.*?)\n\n', resp_text, re.DOTALL)
    correct_matches = re.findall(r'Blank \d: (\d)', resp_text)

    for options_text, correct_idx in zip(options_matches, correct_matches):
        choices = re.findall(r'\d+\.\s(.+)', options_text)
        correct_choice = choices[int(correct_idx) - 1]
        blanks.append({
            'choices': choices,
            'answer': correct_choice
        })

    return quiz_sentence, blanks

def display_quiz_radio(quiz_sentence: str, blanks: list[dict]):
    st.subheader("📝 객관식 퀴즈를 풀어보세요")

    quiz_parts = quiz_sentence.split('_____')
    user_answers = []

    # 각 빈칸마다 선택지 표시
    for idx, blank in enumerate(blanks):
        st.markdown(quiz_parts[idx])
        selected = st.radio(
            label=f'빈칸 {idx + 1}',
            options=blank['choices'],
            key=f'blank_{idx}'
        )
        user_answers.append(selected)

    st.markdown(quiz_parts[-1])  # 마지막 빈칸 뒤 문장

    if st.button("정답 확인"):
        correct_answers = [blank['answer'] for blank in blanks]
        result = all(user == correct for user, correct in zip(user_answers, correct_answers))
        if result:
            st.success("🎉 모든 정답이 맞았습니다!")
        else:
            st.error("❌ 오답이 포함되었습니다. 다시 시도해보세요!")
            for i, (user, correct) in enumerate(zip(user_answers, correct_answers)):
                if user == correct:
                    st.write(f"✅ 빈칸 {i+1}: 맞음")
                else:
                    st.write(f"❌ 빈칸 {i+1}: 틀림 (정답: **{correct}**)")

if __name__ == "__main__":
    img = Image.open(IMG_DIR / "billboard.jpg")
    
    # 이미지 → AI 퀴즈 생성
    prompt_desc = IN_DIR / "p1_desc.txt"
    model_desc = get_model(sys_prompt=prompt_desc.read_text(encoding="utf8"))
    resp_desc = model_desc.generate_content([img, "Describe this image"])

    prompt_quiz = IN_DIR / "p2_quiz.txt"
    model_quiz = get_model(sys_prompt=prompt_quiz.read_text(encoding="utf8"))
    resp_quiz = model_quiz.generate_content(resp_desc.text)

    # AI 응답 파싱
    quiz_sentence, blanks = parse_quiz_response(resp_quiz.text)

    # 화면 표시
    st.image(img, caption="분석 이미지", use_column_width=True)
    st.markdown("### 🎯 생성된 객관식 퀴즈")
    display_quiz_radio(quiz_sentence, blanks)
