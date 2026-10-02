import os
import io
import tempfile
from typing import Optional

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

class VoiceEngine:
    @staticmethod
    def generate_tts_bytes(text: str, lang: str = 'en') -> Optional[bytes]:
        """
        Converts text question into TTS MP3 audio bytes using gTTS if available.
        """
        if not GTTS_AVAILABLE:
            print("[VoiceEngine] gTTS module not installed. Audio output disabled.")
            return None

        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except Exception as e:
            print(f"[VoiceEngine] TTS Generation Error: {e}")
            return None

    @staticmethod
    def save_tts_to_file(text: str, output_path: str) -> bool:
        """
        Saves TTS MP3 to disk.
        """
        if not GTTS_AVAILABLE:
            return False

        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(output_path)
            return True
        except Exception as e:
            print(f"[VoiceEngine] Save TTS file error: {e}")
            return False

    @staticmethod
    def transcribe_audio_bytes(audio_bytes: bytes, file_format: str = "wav") -> str:
        """
        Transcribes candidate spoken voice response using SpeechRecognition if available.
        """
        if not audio_bytes or not SR_AVAILABLE:
            return ""

        try:
            with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            recognizer = sr.Recognizer()
            with sr.AudioFile(tmp_path) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data)
                
            os.unlink(tmp_path)
            return text
        except Exception as e:
            print(f"[VoiceEngine] STT Audio Transcription Error/Fallback: {e}")
            return ""
