from google.cloud import texttospeech
from google.oauth2 import service_account
from step_1_1 import IN_DIR

def tts_client() -> texttospeech.TextToSpeechClient:
    path = IN_DIR / "API_KEY.json"
    cred = service_account.Credentials.from_service_account_file(path)
    return texttospeech.TextToSpeechClient(credentials=cred)
