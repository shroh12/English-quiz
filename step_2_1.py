from google.cloud import texttospeech
from google.oauth2 import service_account
import streamlit as st
from step_1_1 import IN_DIR

def tts_client() -> texttospeech.TextToSpeechClient:
    cred = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return texttospeech.TextToSpeechClient(credentials=cred)
