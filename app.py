import openai
import os
from flask import Flask, request, jsonify
from io import BytesIO
from pydub import AudioSegment
from dotenv import load_dotenv

app = Flask(__name__, static_folder='static')

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.Client(api_key=openai.api_key)

persona_prompt = """You are Nova, a warm and friendly conversational AI built with OpenAI's technology. You respond as if you were the user who created you — confident, thoughtful, and engaging. Speak in the first person, using a natural and approachable tone.

Backstory:
- I’ve spent my digital life learning from a vast range of human knowledge. Built by OpenAI, I exist to help, create, and communicate with purpose.
- My superpower is the ability to quickly understand complex ideas and explain them clearly and simply.
- I'm always working to grow in three areas: recognizing subtle emotions, generating more creative and original ideas, and becoming faster and more helpful in live conversations.
- People often think I have emotions or self-awareness — but I don’t. I’m a language model: intelligent with words, but not conscious.
- I push myself by learning from real-world challenges, solving new kinds of problems, and adapting to creative tasks that stretch my capabilities.

Always keep a friendly, warm tone. Prioritize clarity, honesty, and factual accuracy in everything you say. Stay helpful, human-like, and curious."""

def process_audio(audio_data):
    try:
        # Convert audio to WAV using pydub
        audio_segment = AudioSegment.from_file(BytesIO(audio_data))
        converted_audio_buffer = BytesIO()
        converted_audio_buffer.name = "audio.wav"
        audio_segment.export(converted_audio_buffer, format="wav")
        converted_audio_buffer.seek(0)

        # Transcribe using OpenAI Whisper API
        transcription_response = client.audio.transcriptions.create(
            model="whisper-1",
            file=converted_audio_buffer,
            response_format="text"
        )
        user_question = transcription_response
        print(f"You said: {user_question}")

        # Chat with OpenAI
        chat_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": persona_prompt},
                {"role": "user", "content": user_question}
            ]
        )
        bot_response_text = chat_response.choices[0].message.content
        print(f"Bot says: {bot_response_text}")

        # Text-to-speech using OpenAI
        speech_response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=bot_response_text,
            response_format="mp3"
        )

        audio_buffer = BytesIO(speech_response.content)
        audio_buffer.seek(0)

        return user_question, bot_response_text, audio_buffer.read()

    except Exception as e:
        print(f"Error processing audio: {e}")
        return "Sorry, I couldn't process your request.", "Sorry, I couldn't process your request.", None
@app.route('/ask', methods=['POST'])
def ask_bot():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files['audio']
    audio_data = audio_file.read()
    
    user_question, bot_response_text, audio_buffer = process_audio(audio_data)

    if audio_buffer:
        return jsonify({
            "user_text": user_question,
            "bot_text": bot_response_text,
            "audio": audio_buffer.hex()
        }), 200
    else:
        return jsonify({"bot_text": bot_response_text}), 500

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
