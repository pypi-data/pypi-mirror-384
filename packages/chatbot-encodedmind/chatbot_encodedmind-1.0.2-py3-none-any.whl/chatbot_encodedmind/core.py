import time
from chatbot_encodedmind.audio_io import record_audio, play_audio_from_text
from chatbot_encodedmind.ai_client import OpenAIClient, get_chatgpt_response

client = OpenAIClient(api_key="YOUR_OPENAI_API_KEY")


def main():
    conversation_history = [
        {
            "role": "system",
            "content": (
                "You are an empathetic assistant. The user might repeat information. "
                "Acknowledge any repetition if necessary, but focus on providing new insights "
                "or addressing the user's evolving needs. Respond primarily to new information, "
                "while taking repeated information into consideration."
            ),
        }
    ]

    # Initial greeting
    play_audio_from_text(client, "Hello! How can I assist you today?")

    while True:
        print("You: ")
        fs, audio = record_audio(duration=5)

        # Transcribe
        user_message = client.transcribe_audio(audio, fs)
        print(user_message)

        conversation_history.append({"role": "user", "content": user_message})
        response = get_chatgpt_response(client, conversation_history)

        play_audio_from_text(client, response)
        print("Bot:", response)
        conversation_history.append({"role": "assistant", "content": response})

        if user_message.lower() in ("goodbye.", "goodbye!", "goodbye"):
            break

        time.sleep(2)
