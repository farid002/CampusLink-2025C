from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()


def test_all_apis():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ API açarı tapılmadı!")
        return False

    client = OpenAI(api_key=api_key)

    # Test Chat API
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Salam!"}]
        )
        print("✅ Chat API işləyir!")
    except Exception as e:
        print(f"❌ Chat API xətası: {str(e)}")
        return False

    # Test Whisper API (əgər audio faylı varsa)
    # try:
    #     with open("test.mp3", "rb") as audio_file:
    #         transcript = client.audio.transcriptions.create(
    #             model="whisper-1",
    #             file=audio_file
    #         )
    #     print("✅ Whisper API işləyir!")
    # except Exception as e:
    #     print(f"⚠️ Whisper API test edilmədi: {str(e)}")

    # Test TTS API
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input="Test"
        )
        print("✅ TTS API işləyir!")
    except Exception as e:
        print(f"❌ TTS API xətası: {str(e)}")
        return False

    return True


if __name__ == "__main__":
    test_all_apis()