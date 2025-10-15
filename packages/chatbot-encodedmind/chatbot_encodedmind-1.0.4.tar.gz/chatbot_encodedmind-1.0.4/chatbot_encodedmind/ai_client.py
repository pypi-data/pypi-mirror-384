import requests
import numpy as np
import scipy.io.wavfile as wav
from openai import OpenAI


class OpenAIClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.api_key = api_key

    def transcribe_audio(self, audio, fs):
        wav.write("Recording.wav", fs, np.int16(audio * 32767))
        with open("Recording.wav", "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1", file=audio_file
            )
            return transcript.text

    def create_tts(self, text: str):
        response = self.client.audio.speech.create(
            model="tts-1", voice="nova", input=text
        )
        return response.content


def get_chatgpt_response(client: OpenAIClient, conversation_history):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {client.api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": conversation_history,
        "max_tokens": 1000,
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        chatgpt_response = response.json()
        return chatgpt_response["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code} - {response.text}"
