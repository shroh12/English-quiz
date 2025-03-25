from pathlib import Path
from google.cloud import texttospeech
from step_1_1 import IN_DIR, OUT_DIR
from step_2_1 import tts_client

def synth_speech(text: str, voice: str, audio_encoding: str = None) -> bytes:
    lang_code = "-".join(voice.split("-")[:2])
    MP3 = texttospeech.AudioEncoding.MP3
    WAV = texttospeech.AudioEncoding.LINEAR16
    audio_type = MP3 if audio_encoding == "mp3" else WAV
    
    client = tts_client()
    resp = client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=texttospeech.VoiceSelectionParams(language_code=lang_code,
                                                name=voice),
        audio_config=texttospeech.AudioConfig(audio_encoding=audio_type),
    )
    return resp.audio_content

if __name__ == "__main__":
    text_path = IN_DIR / "billboard.txt"
    text = text_path.read_text(encoding="utf-8")
    audio = synth_speech(text, "en-GB-Studio-C", "mp3")
    with open(OUT_DIR / f"{Path(__file__).stem}.mp3", "wb") as fp:
        fp.write(audio)