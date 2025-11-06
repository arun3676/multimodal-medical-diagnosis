"""
Whisper Voice Transcription Service
Lightweight audio transcription for symptom extraction
"""
import os
import logging
import io
import mimetypes
from typing import Dict, Any, Optional
import httpx
from openai import OpenAI

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """OpenAI Whisper-1 transcription service for medical symptoms."""
    
    def __init__(self, http_client: httpx.Client):
        self.http_client = http_client
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_whisper_model = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3")

        order_env = os.getenv("AUDIO_PROVIDER_ORDER", "groq,openai")
        self.provider_order = [provider.strip().lower() for provider in order_env.split(",") if provider.strip()]
        if not self.provider_order:
            self.provider_order = ["groq", "openai"]

        if not self.openai_api_key:
            logger.warning("OpenAI API key not configured for Whisper fallback")
        if not self.groq_api_key:
            logger.warning("Groq API key not configured for Whisper")
        logger.info("Audio provider order: %s", " -> ".join(self.provider_order))
    
    def transcribe_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file using Whisper-1 and extract symptoms.
        
        Args:
            audio_file_path: Path to audio file (WAV/MP3/M4A)
            
        Returns:
            Dictionary with transcription and extracted symptoms
        """
        try:
            # Load audio bytes once
            with open(audio_file_path, 'rb') as audio_file:
                audio_bytes = audio_file.read()

            if not audio_bytes:
                return {
                    "error": "Audio file is empty",
                    "symptoms": "",
                    "duration": 0.0,
                    "transcription": ""
                }

            # Get audio duration
            import wave
            try:
                with wave.open(audio_file_path, 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    rate = wav_file.getframerate()
                    duration = frames / float(rate)
            except:
                # Fallback duration estimation
                duration = 0.0
            
            mime_type = mimetypes.guess_type(audio_file_path)[0] or 'application/octet-stream'
            file_name = os.path.basename(audio_file_path)

            provider_map = {
                "groq": lambda: self._transcribe_with_groq(audio_bytes, file_name, mime_type),
                "openai": lambda: self._transcribe_with_openai(audio_bytes),
            }

            last_error: Optional[str] = None

            for provider in self.provider_order:
                call_fn = provider_map.get(provider)
                if call_fn is None:
                    logger.warning("Unknown audio provider '%s' in AUDIO_PROVIDER_ORDER", provider)
                    continue

                try:
                    logger.debug("Attempting audio transcription via %s", provider)
                    transcription_text = call_fn()
                    if transcription_text:
                        symptoms = self._extract_symptoms(transcription_text)
                        logger.info("✅ Audio transcribed successfully via %s (%.1fs)", provider, duration)
                        return {
                            "symptoms": symptoms,
                            "duration": duration,
                            "transcription": transcription_text,
                            "provider": f"{provider}-whisper"
                        }
                except Exception as provider_error:
                    last_error = str(provider_error)
                    logger.info("Audio transcription via %s failed, trying next provider", provider)
                    continue

            # All providers failed
            return {
                "error": f"Transcription failed: {last_error or 'no providers available'}",
                "symptoms": "",
                "duration": 0.0,
                "transcription": ""
            }
            
        except Exception as e:
            logger.info(f"Audio transcription error: {e}")
            return {
                "error": f"Transcription failed: {str(e)}",
                "symptoms": "",
                "duration": 0.0,
                "transcription": ""
            }

    def _transcribe_with_groq(self, audio_bytes: bytes, file_name: str, mime_type: str) -> str:
        if not self.groq_api_key:
            raise ValueError("Groq API key not configured")

        try:
            files = {
                "file": (file_name, audio_bytes, mime_type)
            }
            data = {
                "model": self.groq_whisper_model,
                "response_format": "text",
                "language": "en"
            }
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}"
            }

            response = self.http_client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                data=data,
                files=files,
                headers=headers,
                timeout=60.0
            )
            if response.status_code != 200:
                raise RuntimeError(f"Groq Whisper error: {response.status_code}")

            return response.text.strip()
        except Exception as e:
            logger.info(f"Groq transcription attempt failed")
            raise

    def _transcribe_with_openai(self, audio_bytes: bytes) -> str:
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not configured")

        client = OpenAI(api_key=self.openai_api_key)
        with io.BytesIO(audio_bytes) as audio_buffer:
            audio_buffer.name = "audio_input.wav"
            transcription_response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_buffer,
                language="en",
                response_format="text"
            )

        return transcription_response.strip()
    
    def _extract_symptoms(self, transcription: str) -> str:
        """
        Extract relevant medical symptoms from transcription.
        
        Args:
            transcription: Raw audio transcription text
            
        Returns:
            Cleaned symptom description
        """
        if not transcription:
            return ""
        
        # Common medical symptom keywords to look for
        symptom_keywords = [
            "pain", "ache", "hurt", "sore", "discomfort",
            "cough", "breathing", "shortness of breath", "difficulty breathing",
            "chest", "heart", "lung", "stomach", "abdomen", "head",
            "fever", "temperature", "chills", "sweating",
            "fatigue", "tired", "weakness", "dizzy", "nausea",
            "vomiting", "diarrhea", "constipation",
            "headache", "migraine", "dizziness",
            "swelling", "inflammation", "redness", "rash",
            "injury", "fracture", "broken", "sprain", "strain"
        ]
        
        # Extract sentences containing symptom keywords
        sentences = transcription.split('.')
        symptom_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and any(keyword.lower() in sentence.lower() for keyword in symptom_keywords):
                symptom_sentences.append(sentence)
        
        # If no symptom sentences found, return full transcription (limited)
        if not symptom_sentences:
            return transcription[:200] + "..." if len(transcription) > 200 else transcription
        
        # Combine symptom sentences
        symptoms = ". ".join(symptom_sentences)
        
        # Clean up and limit length
        symptoms = symptoms.replace("I am experiencing", "").replace("I have", "").replace("I feel", "")
        symptoms = symptoms.strip()
        
        return symptoms[:300] + "..." if len(symptoms) > 300 else symptoms
    
    def validate_audio_file(self, file_path: str) -> bool:
        """
        Validate if file is a supported audio format.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            True if valid audio format, False otherwise
        """
        supported_formats = ['.wav', '.mp3', '.m4a', '.ogg', '.flac']
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in supported_formats
