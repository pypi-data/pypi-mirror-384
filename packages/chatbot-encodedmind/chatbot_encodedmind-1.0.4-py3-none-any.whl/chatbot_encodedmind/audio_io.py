import sounddevice as sd
import io
from pydub import AudioSegment
import pydub.playback


def record_audio(duration=5, fs=44100, device=None):
    print("Recording...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=2, device=device)
    sd.wait()
    print("Recording finished")
    return fs, audio


def play_audio_from_text(client, text):
    tts_response = client.create_tts(text)
    audio_content = io.BytesIO(tts_response)
    audio_segment = AudioSegment.from_file(audio_content, format="mp3")
    pydub.playback.play(audio_segment)
