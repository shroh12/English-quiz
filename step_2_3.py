from pathlib import Path
import nltk
from step_1_1 import IN_DIR, OUT_DIR
from step_2_2 import synth_speech

def tokenize_sent(text: str) -> list[str]:
    nltk.download(["punkt", "punkt_tab"], quiet=True)
    return nltk.tokenize.sent_tokenize(text)

if __name__ == "__main__":
    text_path = IN_DIR / "billboard.txt"
    text = text_path.read_text(encoding="utf-8")
    sents = tokenize_sent(text)
    for idx, sent in enumerate(sents):
        audio = synth_speech(sent, "en-AU-Neural2-B", "mp3")
        with open(OUT_DIR / f"{Path(__file__).stem}_{idx}.mp3", "wb") as fp:
            fp.write(audio)