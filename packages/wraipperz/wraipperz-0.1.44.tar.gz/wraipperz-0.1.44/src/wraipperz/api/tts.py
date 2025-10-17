import abc
import asyncio
import base64
import json
import mimetypes
import os
import shutil
import struct
import subprocess
from pathlib import Path
from typing import Optional, Union

import numpy as np
import requests
import requests.exceptions
import soundfile as sf
import websockets
import websockets.exceptions
from cartesia import Cartesia
from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types
from openai import OpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from websockets.exceptions import WebSocketException

from .asr import create_asr_manager


class TTSError(Exception):
    """Base exception for TTS-related errors"""

    pass


class TTSRateLimitError(TTSError):
    """Exception raised when hitting rate limits or system busy states"""

    pass


class TTSProvider(abc.ABC):
    @abc.abstractmethod
    def generate_speech(
        self, text: str, output_path: str, voice: str, **kwargs
    ) -> dict | None:
        """Synchronous version of speech generation"""
        pass

    async def generate_speech_async(
        self, text: str, output_path: str, voice: str, **kwargs
    ) -> dict | None:
        """Asynchronous version of speech generation. By default, wraps the sync version"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, self.generate_speech, text, output_path, voice, **kwargs
        )

    def convert_speech(
        self, input_path: str, output_path: str, voice: str, **kwargs
    ) -> dict | None:
        """Convert speech from one voice to another. Default implementation raises NotImplementedError."""
        raise NotImplementedError(
            "Speech-to-speech conversion not supported by this provider"
        )

    def find_similar_voices(
        self, audio_file: str, similarity_threshold: float = None, top_k: int = None
    ) -> list[dict]:
        """Find similar voices based on an audio sample. Default implementation raises NotImplementedError."""
        raise NotImplementedError(
            "Finding similar voices not supported by this provider"
        )

    def add_sharing_voice(
        self, public_user_id: str, voice_id: str, new_name: str
    ) -> dict | None:
        """Add a shared voice to the collection. Default implementation raises NotImplementedError."""
        raise NotImplementedError("Adding shared voices not supported by this provider")


class MiniMaxiTTSProvider(TTSProvider):
    def __init__(self, api_key: str = None, group_id: str = None):
        self.api_key = api_key or os.getenv("T2A_API_KEY")
        self.group_id = group_id or os.getenv("MINIMAXI_GROUP_ID")
        self.base_url = "https://api.minimaxi.chat/v1/t2a_v2"
        self.asr_manager = create_asr_manager()
        self.available_voices = {
            "Wise_Woman": {
                "name": "Wise_Woman",
                "description": "A mature female voice with wisdom and authority",
                "labels": {
                    "accent": "Standard",
                    "description": "wise and authoritative",
                    "age": "mature",
                    "gender": "female",
                    "use_case": "narration, documentaries",
                },
            },
            "Friendly_Person": {
                "name": "Friendly_Person",
                "description": "A warm, approachable voice for casual content",
                "labels": {
                    "accent": "Standard",
                    "description": "warm and friendly",
                    "age": "adult",
                    "gender": "neutral",
                    "use_case": "casual content, greetings",
                },
            },
            "Deep_Voice_Man": {
                "name": "Deep_Voice_Man",
                "description": "A deep, resonant male voice for dramatic content",
                "labels": {
                    "accent": "Standard",
                    "description": "deep and powerful",
                    "age": "adult",
                    "gender": "male",
                    "use_case": "dramatic narration, trailers",
                },
            },
            "Calm_Woman": {
                "name": "Calm_Woman",
                "description": "A soothing female voice for relaxing content",
                "labels": {
                    "accent": "Standard",
                    "description": "calm and soothing",
                    "age": "adult",
                    "gender": "female",
                    "use_case": "meditation, relaxation",
                },
            },
            "Exuberant_Girl": {
                "name": "Exuberant_Girl",
                "description": "An energetic young female voice for upbeat content",
                "labels": {
                    "accent": "Standard",
                    "description": "energetic and youthful",
                    "age": "young",
                    "gender": "female",
                    "use_case": "entertainment, advertisements",
                },
            },
            # Add other voices similarly...
        }

    def list_voices(self) -> list[dict]:
        """Return list of available voices with their details"""
        return [
            {"name": k, "voice_id": k, **v} for k, v in self.available_voices.items()
        ]

    def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: str = "Calm_Woman",
        speed: float = 1.0,
        volume: float = 1.0,
        pitch: float = 0.0,
        emotion: Optional[str] = None,
        **kwargs,
    ) -> dict | None:
        """Generate speech using MiniMaxi's T2A V2 API"""
        # Validate parameters
        if speed < 0.5 or speed > 2.0:
            raise ValueError("Speed must be between 0.5 and 2.0")
        if volume <= 0 or volume > 10:
            raise ValueError("Volume must be between 0 and 10")
        if pitch < -12 or pitch > 12:
            raise ValueError("Pitch must be between -12 and 12")
        if emotion and emotion not in [
            "happy",
            "sad",
            "angry",
            "fearful",
            "disgusted",
            "surprised",
            "neutral",
        ]:
            raise ValueError("Invalid emotion specified")

        # Base payload
        payload = {
            "model": "speech-01-turbo",
            "text": text,
            "stream": False,
            "voice_setting": {
                "voice_id": voice,
                "speed": speed,
                "vol": volume,
                "pitch": int(pitch),  # MiniMaxi API expects pitch as integer
            },
            "audio_setting": {
                "sample_rate": kwargs.get("sample_rate", 32000),
                "bitrate": kwargs.get("bitrate", 128000),
                "format": kwargs.get("format", "mp3"),
                "channel": kwargs.get("channel", 1),
            },
        }

        # Add emotion if specified
        if emotion:
            payload["voice_setting"]["emotion"] = emotion

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}?GroupId={self.group_id}"

        try:
            response = requests.post(url, headers=headers, json=payload, stream=True)
            response.raise_for_status()

            parsed_json = response.json()

            if parsed_json["base_resp"]["status_code"] != 0:
                raise TTSError(
                    f"MiniMaxi API error: {parsed_json['base_resp']['status_msg']}"
                )

            # Convert hex audio to bytes and save
            audio_data = bytes.fromhex(parsed_json["data"]["audio"])
            with open(output_path, "wb") as f:
                f.write(audio_data)

            result = {
                "status": "success",
                "extra_info": parsed_json.get("extra_info", {}),
                "trace_id": parsed_json.get("trace_id"),
            }

            # Generate alignment if requested
            if kwargs.get("return_alignment", False):
                temp_path = Path(output_path)
                temp_file = (
                    temp_path.parent / f"{temp_path.stem}_temp{temp_path.suffix}"
                )

                try:
                    with open(temp_file, "wb") as f:
                        f.write(audio_data)
                    asr_result = self.asr_manager.transcribe(
                        "openai", temp_file, language=kwargs.get("language")
                    )
                    result["alignment"] = asr_result.to_elevenlabs_alignment()
                finally:
                    temp_file.unlink(missing_ok=True)

            return result

        except requests.exceptions.RequestException as e:
            if e.response and e.response.status_code == 429:
                raise TTSRateLimitError(f"MiniMaxi API rate limit exceeded: {str(e)}")
            raise TTSError(f"MiniMaxi API request failed: {str(e)}")


class OpenAIRealtimeTTSProvider(TTSProvider):
    def __init__(self, api_key: Union[str, None] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.available_voices = {
            "alloy": {
                "name": "alloy",
                "description": "A female voice with a neutral, balanced tone, suitable for general-purpose applications.",
                "labels": {
                    "accent": "American",
                    "description": "balanced and neutral",
                    "age": "young adult",
                    "gender": "female",
                    "use_case": "general purpose",
                },
            },
            "echo": {
                "name": "echo",
                "description": "A soft male voice with an androgynous quality, ideal for narration.",
                "labels": {
                    "accent": "American",
                    "description": "soft and measured",
                    "age": "adult",
                    "gender": "male",
                    "use_case": "narration",
                },
            },
            "shimmer": {
                "name": "shimmer",
                "description": "A female voice with a warm, welcoming tone perfect for casual content.",
                "labels": {
                    "accent": "American",
                    "description": "warm and welcoming",
                    "age": "young adult",
                    "gender": "female",
                    "use_case": "casual content",
                },
            },
            "ash": {
                "name": "ash",
                "description": "A masculine voice with a clear, professional tone suitable for business content.",
                "labels": {
                    "accent": "American",
                    "description": "clear and professional",
                    "age": "adult",
                    "gender": "male",
                    "use_case": "business",
                },
            },
            "coral": {
                "name": "coral",
                "description": "A female voice with an energetic, professional tone great for presentations.",
                "labels": {
                    "accent": "American",
                    "description": "energetic and professional",
                    "age": "adult",
                    "gender": "female",
                    "use_case": "presentations",
                },
            },
            "sage": {
                "name": "sage",
                "description": "A female voice with a thoughtful, measured tone perfect for explanations.",
                "labels": {
                    "accent": "American",
                    "description": "thoughtful and measured",
                    "age": "adult",
                    "gender": "female",
                    "use_case": "explanations",
                },
            },
            "ballad": {
                "name": "ballad",
                "description": "A male voice with a polished, commercial tone suited for marketing and announcements.",
                "labels": {
                    "accent": "American",
                    "description": "polished and commercial",
                    "age": "adult",
                    "gender": "male",
                    "use_case": "marketing",
                },
            },
            "verse": {
                "name": "verse",
                "description": "A neutral voice with an expressive, versatile tone for creative content.",
                "labels": {
                    "accent": "American",
                    "description": "expressive and versatile",
                    "age": "adult",
                    "gender": "neutral",
                    "use_case": "creative content",
                },
            },
        }
        self.asr_manager = create_asr_manager()

    def list_voices(self) -> list[dict]:
        """Return list of available voices with their details"""
        # Add voice_id field to match ElevenLabs structure
        return [
            {"name": k, "voice_id": k, **v} for k, v in self.available_voices.items()
        ]

    def generate_speech(
        self, text: str, output_path: str, voice: str = "alloy", **kwargs
    ) -> dict | None:
        # Run the async version in a new event loop
        result = asyncio.run(self._generate_speech_internal(text, voice, **kwargs))
        if result and "audio_data" in result:
            # Extract audio data from the result dictionary
            self._save_to_wav(result["audio_data"], output_path)
        return result  # Return the full result including alignment if present

    async def generate_speech_async(
        self, text: str, output_path: str, voice: str = "alloy", **kwargs
    ) -> dict | None:
        result = await self._generate_speech_internal(text, voice, **kwargs)
        if result and "audio_data" in result:
            # Extract audio data from the result dictionary
            self._save_to_wav(result["audio_data"], output_path)
        return result  # Return the full result including alignment if present

    async def _generate_speech_internal(
        self, text: str, voice: str, **kwargs
    ) -> dict | None:
        uri = (
            "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        )
        try:
            # Updated websockets connection with correct header handling
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "OpenAI-Beta": "realtime=v1",
            }

            async with websockets.connect(
                uri,
                additional_headers=headers,
            ) as websocket:
                # Build instructions with additional context if provided

                context = kwargs.get("context")
                instructions = (
                    "You are a text-to-speech system."
                    f"Your task is to vocalize the provided text below{' .' if not context else ' respecting the provided context.'}"
                    f"{'Exactly match and clone the voice characteristics from the reference audio.' if kwargs.get('speech_reference') else ''}"
                    "Focus only on speech generation, maintaining natural prosody and pronunciation."
                    # "The text could be a single word, such as 'empty', you should still vocalize it."
                )
                if context:
                    instructions += f"\nContext:\n{context}\n"
                # instructions += f"\nThe text to vocalize is:\n{text}\n"
                # Send a single, comprehensive session update
                # Send messages in sequence as required by the API
                await websocket.send(
                    json.dumps(
                        {
                            "type": "session.update",
                            "session": {
                                "instructions": instructions,
                                "voice": voice,
                            },
                        }
                    )
                )

                if voice_ref := kwargs.get("voice_reference"):
                    with open(voice_ref, "rb") as f:
                        audio_data = f.read()

                    await websocket.send(
                        json.dumps(
                            {
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "message",
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "input_audio",
                                            "audio": base64.b64encode(
                                                audio_data
                                            ).decode("utf-8"),
                                        }
                                    ],
                                },
                            }
                        )
                    )

                await websocket.send(
                    json.dumps(
                        {
                            "type": "conversation.item.create",
                            "item": {
                                "type": "message",
                                "role": "user",
                                "content": [
                                    {
                                        "type": "input_text",
                                        "text": f"The text to vocalize is:\n{text}\n",
                                    }
                                ],
                            },
                        }
                    )
                )

                await websocket.send(
                    json.dumps(
                        {
                            "type": "response.create",
                            "response": {
                                "modalities": ["audio", "text"]
                            },  # Removed "text" since we only need audio
                        }
                    )
                )

                audio_chunks = []
                async for message in websocket:
                    data = json.loads(message)

                    if data["type"] == "response.done":
                        if data["response"]["status"] == "failed":
                            error_details = data["response"]["status_details"]["error"]
                            raise TTSError(
                                f"OpenAI API Error: {error_details['message']}\n"
                                f"Type: {error_details['type']}\n"
                                f"Code: {error_details['code']}"
                            )
                        break

                    if data["type"] == "response.audio.delta":
                        audio_chunks.append(base64.b64decode(data["delta"]))
                    elif data["type"] == "response.done":
                        break
                    elif data["type"] == "error":
                        raise TTSError(f"OpenAI Realtime TTS error: {data}")

                audio_data = b"".join(audio_chunks) if audio_chunks else None

                if not audio_data:
                    raise TTSError(
                        f"No audio data received from OpenAI Realtime API for input {text} and instructions {instructions}"
                    )

                if audio_data:
                    result = {"audio_data": audio_data}

                    # Add alignment if requested
                    if kwargs.get("return_alignment", False):
                        # Save temporary audio file for ASR
                        temp_path = Path(kwargs.get("output_path", "temp.wav"))
                        temp_file = (
                            temp_path.parent
                            / f"{temp_path.stem}_temp{temp_path.suffix}"
                        )

                        self._save_to_wav(audio_data, temp_file)

                        # Get alignment using ASR
                        try:
                            # asr_result = self.asr_manager.transcribe("openai", temp_file, language=kwargs.get("language"))
                            asr_result = self.asr_manager.transcribe(
                                "deepgram", temp_file, language=kwargs.get("language")
                            )
                            alignment = asr_result.to_elevenlabs_alignment()
                        finally:
                            # Clean up temp file
                            temp_file.unlink(missing_ok=True)

                        result["alignment"] = alignment

                    return result

                return None

        except Exception as e:
            print(f"Error in speech generation: {e}")
            return None

    def _save_to_wav(self, audio_data: bytes, output_path: Union[str, Path]) -> None:
        output_path = str(output_path)
        if not audio_data:
            raise TTSError("No audio data received from TTS service")

        try:
            audio_int16 = np.frombuffer(audio_data, dtype=np.int16)
            if len(audio_int16) == 0:
                raise TTSError("Empty audio data")

            sf.write(
                output_path,
                audio_int16,
                samplerate=24000,
                format="WAV",
                subtype="PCM_16",
            )

            # Verify the file was written correctly
            if not Path(output_path).exists() or Path(output_path).stat().st_size == 0:
                raise TTSError("Failed to write audio file")

        except Exception as e:
            raise TTSError(f"Failed to save audio: {str(e)}")


class OpenAITTSProvider(TTSProvider):
    def __init__(self, api_key: str = None):
        # OpenAI SDK now requires api_key as keyword-only argument
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.available_voices = {
            "alloy": {
                "name": "alloy",
                "description": "A female voice with a neutral, balanced tone, suitable for general-purpose applications.",
                "labels": {
                    "accent": "American",
                    "description": "balanced and neutral",
                    "age": "young adult",
                    "gender": "female",
                    "use_case": "general purpose",
                },
            },
            "echo": {
                "name": "echo",
                "description": "A soft male voice with an androgynous quality, ideal for narration.",
                "labels": {
                    "accent": "American",
                    "description": "soft and measured",
                    "age": "adult",
                    "gender": "male",
                    "use_case": "narration",
                },
            },
            "fable": {
                "name": "fable",
                "description": "A voice with a magical and dreamy tone, suitable for storytelling.",
                "labels": {
                    "accent": "American",
                    "description": "magical and dreamy",
                    "age": "indeterminate",
                    "gender": "neutral",
                    "use_case": "storytelling",
                },
            },
            "onyx": {
                "name": "onyx",
                "description": "A deep, rich voice with a commanding presence.",
                "labels": {
                    "accent": "American",
                    "description": "deep and commanding",
                    "age": "adult",
                    "gender": "male",
                    "use_case": "authoritative narration",
                },
            },
            "nova": {
                "name": "nova",
                "description": "A bright, energetic voice with a youthful quality.",
                "labels": {
                    "accent": "American",
                    "description": "bright and energetic",
                    "age": "young adult",
                    "gender": "female",
                    "use_case": "energetic content",
                },
            },
            "shimmer": {
                "name": "shimmer",
                "description": "A female voice with a warm, welcoming tone perfect for casual content.",
                "labels": {
                    "accent": "American",
                    "description": "warm and welcoming",
                    "age": "young adult",
                    "gender": "female",
                    "use_case": "casual content",
                },
            },
            "ash": {
                "name": "ash",
                "description": "A masculine voice with a clear, professional tone suitable for business content.",
                "labels": {
                    "accent": "American",
                    "description": "clear and professional",
                    "age": "adult",
                    "gender": "male",
                    "use_case": "business",
                },
            },
            "coral": {
                "name": "coral",
                "description": "A female voice with an energetic, professional tone great for presentations.",
                "labels": {
                    "accent": "American",
                    "description": "energetic and professional",
                    "age": "adult",
                    "gender": "female",
                    "use_case": "presentations",
                },
            },
            "sage": {
                "name": "sage",
                "description": "A female voice with a thoughtful, measured tone perfect for explanations.",
                "labels": {
                    "accent": "American",
                    "description": "thoughtful and measured",
                    "age": "adult",
                    "gender": "female",
                    "use_case": "explanations",
                },
            },
            "ballad": {
                "name": "ballad",
                "description": "A male voice with a polished, commercial tone suited for marketing and announcements.",
                "labels": {
                    "accent": "American",
                    "description": "polished and commercial",
                    "age": "adult",
                    "gender": "male",
                    "use_case": "marketing",
                },
            },
        }

    def list_voices(self) -> list[dict]:
        """Return list of available voices with their details"""
        return [
            {"name": k, "voice_id": k, **v} for k, v in self.available_voices.items()
        ]

    def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: str = "alloy",
        model: str = "gpt-4o-mini-tts",
        instructions: str = None,
        response_format: str = "mp3",
        speed: float = 1.0,
        **kwargs,
    ) -> dict | None:
        """
        Generate speech using OpenAI's TTS API

        Args:
            text: The text to convert to speech
            output_path: Where to save the resulting audio file
            voice: One of the available voices (alloy, echo, fable, onyx, nova, shimmer, ash, coral, sage, ballad)
            model: The TTS model to use (gpt-4o-mini-tts, tts-1, or tts-1-hd)
            instructions: Optional instructions to guide the voice style (e.g., "Speak in a cheerful tone")
            response_format: Output format (mp3, opus, aac, flac, wav, pcm)
            speed: Speed of speech (0.5 to 2.0)
            **kwargs: Additional parameters for future API options

        Returns:
            Dictionary with status and any additional information
        """
        # Validate parameters
        if speed < 0.5 or speed > 2.0:
            raise ValueError("Speed must be between 0.5 and 2.0")

        # Create request parameters
        request_params = {
            "model": model,
            "voice": voice,
            "input": text,
            "speed": speed,
        }

        # Add optional parameters if provided
        if instructions:
            request_params["instructions"] = instructions

        if response_format:
            request_params["response_format"] = response_format

        # Generate audio
        try:
            response = self.client.audio.speech.create(**request_params)
            response.stream_to_file(output_path)

            return {
                "status": "success",
                "model": model,
                "voice": voice,
                "output_format": response_format,
            }

        except Exception as e:
            # Handle rate limit errors specifically
            if "rate limit" in str(e).lower():
                raise TTSRateLimitError(f"OpenAI API rate limit exceeded: {str(e)}")
            # Handle other errors
            raise TTSError(f"OpenAI TTS generation failed: {str(e)}")


class ElevenLabsTTSProvider(TTSProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")

    def list_voices(self) -> list[dict]:
        """Return list of available voices with their details"""
        url = "https://api.elevenlabs.io/v1/voices"
        headers = {"xi-api-key": self.api_key}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()["voices"]
        except Exception as e:
            print(f"Error fetching ElevenLabs voices: {e}")
            return []

    def convert_speech(
        self,
        input_path: str,
        output_path: str,
        voice: str,
        model_id: str = "eleven_multilingual_sts_v2",
        output_format: str = "mp3_44100_128",
        **kwargs,
    ) -> dict | None:
        """Convert speech from one voice to another using ElevenLabs API"""
        url = f"https://api.elevenlabs.io/v1/speech-to-speech/{voice}"
        headers = {"xi-api-key": self.api_key}

        # Prepare the audio file
        with open(input_path, "rb") as f:
            files = {"audio": f}

            # Add optional parameters
            data = {"model_id": model_id, "output_format": output_format}

            # Make the API request
            response = requests.post(url, headers=headers, files=files, data=data)

            if response.status_code != 200:
                if response.status_code == 429:
                    raise TTSRateLimitError(
                        f"Error: {response.status_code}, {response.text}"
                    )
                raise TTSError(f"Error: {response.status_code}, {response.text}")

            # Save the audio response
            with open(output_path, "wb") as f:
                f.write(response.content)

            return {"status": "success"}

    def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: str,
        model_id: str = "eleven_multilingual_v2",
        language: str = None,
        **kwargs,
    ) -> None:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps"
        headers = {"Content-Type": "application/json", "xi-api-key": self.api_key}

        # Base data dictionary
        data = {
            "text": text,
            "model_id": model_id,
            "voice_settings": kwargs.get(
                "voice_settings",
                {
                    "stability": kwargs.get("stability", 0.5),
                    "similarity_boost": kwargs.get("similarity_boost", 0.75),
                },
            ),
        }

        # Add language if specified
        if language:
            data["language"] = language

        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 200:
            if response.status_code == 429:
                raise TTSRateLimitError(
                    f"Error: {response.status_code}, {response.text}"
                )
            raise TTSError(f"Error: {response.status_code}, {response.text}")

        response_dict = json.loads(response.content.decode("utf-8"))
        audio_bytes = base64.b64decode(response_dict["audio_base64"])

        # Write audio to output file immediately
        with open(output_path, "wb") as f:
            f.write(audio_bytes)

        speed = kwargs.get("speed", 1.0)
        if speed != 1.0:
            # Try FFmpeg processing
            temp_path = output_path + ".temp"
            shutil.copy2(output_path, temp_path)  # Make a copy for processing

            if self._process_with_ffmpeg(temp_path, output_path, speed):
                os.remove(temp_path)  # Clean up temp file
                # Adjust timestamps if they exist
                if "alignment" in response_dict:
                    self._adjust_timestamps(response_dict["alignment"], speed)
            else:
                print("FFmpeg processing failed, keeping original audio")
                os.remove(temp_path)

        return response_dict

    def _adjust_timestamps(self, alignment: dict, speed: float) -> None:
        """Adjust timestamps in the alignment dictionary based on speed factor"""
        if not alignment:
            return

        # Adjust start times
        if "character_start_times_seconds" in alignment:
            alignment["character_start_times_seconds"] = [
                t / speed for t in alignment["character_start_times_seconds"]
            ]

        # Adjust end times
        if "character_end_times_seconds" in alignment:
            alignment["character_end_times_seconds"] = [
                t / speed for t in alignment["character_end_times_seconds"]
            ]

    def _process_with_ffmpeg(
        self, input_path: str, output_path: str, target_speed: float
    ) -> None:
        """Process audio by progressively reducing silences until target speed is reached"""

        def get_duration(file_path):
            """Get duration of audio file using ffprobe"""
            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                file_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())

        try:
            temp_dir = Path(output_path).parent / ".temp"
            temp_dir.mkdir(exist_ok=True)
            current_file = temp_dir / "current.wav"

            # Copy input to our working file
            subprocess.run(
                ["ffmpeg", "-y", "-i", input_path, str(current_file)],
                check=True,
                capture_output=True,
            )

            original_duration = get_duration(input_path)
            target_duration = original_duration / target_speed
            current_duration = original_duration
            silence_factor = 0.5  # Start by halving silences

            # print(f"Original duration: {original_duration:.2f}s")
            # print(f"Target duration: {target_duration:.2f}s")

            # Try progressively stronger silence reduction until we get close to target
            while current_duration > target_duration * 1.05:  # Allow 5% margin
                # print(f"\nTrying silence reduction factor: {silence_factor}")
                temp_output = temp_dir / "temp_output.wav"

                cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(current_file),
                    "-af",
                    f"silenceremove=stop_periods=-1:stop_duration=0.2:stop_threshold=-30dB:leave_silence={silence_factor}",
                    "-acodec",
                    "pcm_s16le",
                    str(temp_output),
                ]

                # print("Running command:", " ".join(cmd))
                result = subprocess.run(cmd, capture_output=True)

                if result.returncode != 0:
                    # print("FFmpeg error:", result.stderr.decode())
                    break

                new_duration = get_duration(temp_output)
                # print(f"New duration: {new_duration:.2f}s")

                if new_duration >= current_duration:  # No improvement
                    break

                # Update current file and duration
                current_file.unlink()
                temp_output.rename(current_file)
                current_duration = new_duration

                # Reduce silence more aggressively in next iteration
                silence_factor *= 0.5

            # If we still need speed adjustment, apply atempo
            if current_duration > target_duration * 1.05:
                final_speed = current_duration / target_duration
                # print(f"\nApplying final speed adjustment: {final_speed:.2f}x")

                cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(current_file),
                    "-af",
                    f"atempo={final_speed}",
                    "-acodec",
                    "pcm_s16le",
                    output_path,
                ]

                # print("Running command:", " ".join(cmd))
                subprocess.run(cmd, check=True, capture_output=True)
            else:
                # Just copy the current file to output
                subprocess.run(
                    ["ffmpeg", "-y", "-i", str(current_file), output_path],
                    check=True,
                    capture_output=True,
                )

            # print(f"\nFinal duration: {get_duration(output_path):.2f}s")
            return True

        except Exception as e:
            print(f"FFmpeg processing failed: {str(e)}")
            return False

        finally:
            # Cleanup
            if temp_dir.exists():
                import shutil

                shutil.rmtree(temp_dir)

    def find_similar_voices(
        self, audio_file: str, similarity_threshold: float = None, top_k: int = None
    ) -> list[dict]:
        """Find similar voices based on an audio sample using ElevenLabs API.

        Args:
            audio_file: Path to the audio file to analyze
            similarity_threshold: Optional threshold for voice similarity (range 0-2)
            top_k: Optional number of most similar voices to return (range 1-100)

        Returns:
            List of voice dictionaries containing similarity matches
        """
        url = "https://api.elevenlabs.io/v1/similar-voices"
        headers = {"xi-api-key": self.api_key}

        # Prepare the multipart form data
        files = {"audio_file": open(audio_file, "rb")}
        data = {}

        # Add optional parameters if provided
        if similarity_threshold is not None:
            if not 0 <= similarity_threshold <= 2:
                raise ValueError("similarity_threshold must be between 0 and 2")
            data["similarity_threshold"] = similarity_threshold

        if top_k is not None:
            if not 1 <= top_k <= 100:
                raise ValueError("top_k must be between 1 and 100")
            data["top_k"] = top_k

        try:
            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()

            result = response.json()
            return result.get("voices", [])

        except requests.exceptions.RequestException as e:
            if response.status_code == 429:
                raise TTSRateLimitError(f"ElevenLabs API rate limit exceeded: {str(e)}")
            raise TTSError(f"ElevenLabs API request failed: {str(e)}")
        finally:
            files["audio_file"].close()

    def add_sharing_voice(
        self, public_user_id: str, voice_id: str, new_name: str
    ) -> dict | None:
        """Add a shared voice to your collection using ElevenLabs API.

        Args:
            public_user_id: Public user ID used to publicly identify ElevenLabs users
            voice_id: ID of the voice to be added
            new_name: The name that identifies this voice

        Returns:
            dict: Contains the new voice_id of the added voice
        """
        url = f"https://api.elevenlabs.io/v1/voices/add/{public_user_id}/{voice_id}"
        headers = {"xi-api-key": self.api_key, "Content-Type": "application/json"}

        data = {"new_name": new_name}

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            if response.status_code == 429:
                raise TTSRateLimitError(f"ElevenLabs API rate limit exceeded: {str(e)}")
            elif response.status_code == 422:
                raise TTSError(f"Invalid request parameters: {str(e)}")
            raise TTSError(f"ElevenLabs API request failed: {str(e)}")


class CartesiaTTSProvider(TTSProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("CARTESIA_API_KEY")
        self.client = Cartesia(api_key=self.api_key)
        self.asr_manager = create_asr_manager()
        self._available_voices = None  # Cache for available voices

    def list_voices(self) -> list[dict]:
        """Return list of available voices with their details"""
        try:
            voices = self.client.voices.list()

            # Transform the response to match the standard format
            return [
                {
                    "name": voice["name"],
                    "voice_id": voice["id"],
                    "description": voice.get("description", ""),
                    "labels": {
                        "language": voice.get("language", ""),
                        "is_public": voice.get("is_public", False),
                        "created_at": voice.get("created_at", ""),
                    },
                }
                for voice in voices
            ]

        except Exception as e:
            print(f"Error fetching Cartesia voices: {e}")
            return []

    def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: str,
        model_id: str = "sonic-2",
        language: str = "en",
        **kwargs,
    ) -> dict | None:
        """Generate speech using Cartesia's TTS API"""
        try:
            # Prepare voice specification
            voice_spec = {"mode": "id", "id": voice}

            # Prepare output format
            output_format = {
                "sample_rate": kwargs.get("sample_rate", 44100),
                "encoding": kwargs.get("encoding", "pcm_f32le"),
                "container": kwargs.get("container", "wav"),
            }

            # If mp3 format is requested, add bit_rate
            if output_format["container"] == "mp3":
                output_format["bit_rate"] = kwargs.get("bit_rate", 128000)

            # Generate audio using the SDK
            response_generator = self.client.tts.bytes(
                model_id=model_id,
                transcript=text,
                voice=voice_spec,
                language=language,
                output_format=output_format,
            )

            # Collect all audio chunks from the generator
            audio_chunks = []
            for chunk in response_generator:
                audio_chunks.append(chunk)

            # Combine all chunks into a single bytes object
            audio_data = b"".join(audio_chunks)

            # Save the audio response
            with open(output_path, "wb") as f:
                f.write(audio_data)

            result = {"status": "success"}

            # Generate alignment if requested
            if kwargs.get("return_alignment", False):
                temp_path = Path(output_path)
                temp_file = (
                    temp_path.parent / f"{temp_path.stem}_temp{temp_path.suffix}"
                )

                try:
                    with open(temp_file, "wb") as f:
                        f.write(audio_data)
                    asr_result = self.asr_manager.transcribe(
                        "openai", temp_file, language=language
                    )
                    result["alignment"] = asr_result.to_elevenlabs_alignment()
                finally:
                    temp_file.unlink(missing_ok=True)

            return result

        except Exception as e:
            if "rate limit" in str(e).lower():
                raise TTSRateLimitError(f"Cartesia API rate limit exceeded: {str(e)}")
            raise TTSError(f"Cartesia TTS generation failed: {str(e)}")

    def convert_speech(
        self,
        input_path: str,
        output_path: str,
        voice: str,
        sample_rate: int = 44100,
        container: str = "wav",
        encoding: str = "pcm_f32le",
        bit_rate: int = None,
        **kwargs,
    ) -> dict | None:
        """Convert speech from one voice to another using Cartesia's Voice Changer API"""
        try:
            # Open the input file
            with open(input_path, "rb") as f:
                clip = f.read()

            # Prepare the request parameters
            params = {
                "voice_id": voice,
                "output_format_container": container,
                "output_format_sample_rate": sample_rate,
                "output_format_encoding": encoding,
            }

            # Add bit_rate for mp3 container
            if container == "mp3" and bit_rate:
                params["output_format_bit_rate"] = bit_rate

            # Convert the audio using the SDK and collect all chunks
            response_chunks = []
            for chunk in self.client.voice_changer.bytes(clip=clip, **params):
                response_chunks.append(chunk)

            # Combine all chunks into a single bytes object
            audio_data = b"".join(response_chunks)

            # Save the converted audio
            with open(output_path, "wb") as f:
                f.write(audio_data)

            return {"status": "success"}

        except Exception as e:
            if "rate limit" in str(e).lower():
                raise TTSRateLimitError(f"Cartesia API rate limit exceeded: {str(e)}")
            raise TTSError(f"Cartesia voice conversion failed: {str(e)}")

    def print_available_voices(self):
        """Debug helper to print available voices"""
        try:
            voices = self.client.voices.list()
            print("Available voices:")
            for voice in voices:
                print(
                    f"  - {voice.get('name', 'Unknown')} (ID: {voice.get('id', 'Unknown')})"
                )
                print(f"    Language: {voice.get('language', 'Unknown')}")
                print(f"    Description: {voice.get('description', 'None')}")
                print("")
        except Exception as e:
            print(f"Error listing voices: {e}")


class GeminiTTSProvider(TTSProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key)
        self.asr_manager = create_asr_manager()
        self.available_voices = {
            "Zephyr": {
                "name": "Zephyr",
                "description": "Bright, cheerful tone",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "female",
                    "characteristic": "bright",
                    "use_case": "general purpose",
                },
            },
            "Puck": {
                "name": "Puck",
                "description": "Upbeat, energetic delivery",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "male",
                    "characteristic": "upbeat",
                    "use_case": "energetic content",
                },
            },
            "Charon": {
                "name": "Charon",
                "description": "Informative, clear tone",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "male",
                    "characteristic": "informative",
                    "use_case": "educational content",
                },
            },
            "Kore": {
                "name": "Kore",
                "description": "Firm, authoritative tone",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "female",
                    "characteristic": "firm",
                    "use_case": "business",
                },
            },
            "Fenrir": {
                "name": "Fenrir",
                "description": "Excitable, animated delivery",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "male",
                    "characteristic": "excitable",
                    "use_case": "entertainment",
                },
            },
            "Leda": {
                "name": "Leda",
                "description": "Youthful, fresh tone",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "female",
                    "characteristic": "youthful",
                    "use_case": "young audience",
                },
            },
            "Orus": {
                "name": "Orus",
                "description": "Firm, steady delivery",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "male",
                    "characteristic": "firm",
                    "use_case": "authoritative content",
                },
            },
            "Aoede": {
                "name": "Aoede",
                "description": "Breezy, light tone",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "female",
                    "characteristic": "breezy",
                    "use_case": "casual content",
                },
            },
            "Callirhoe": {
                "name": "Callirhoe",
                "description": "Easy-going, relaxed tone",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "female",
                    "characteristic": "easy-going",
                    "use_case": "conversational",
                },
            },
            "Autonoe": {
                "name": "Autonoe",
                "description": "Bright, cheerful delivery",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "female",
                    "characteristic": "bright",
                    "use_case": "positive content",
                },
            },
            "Enceladus": {
                "name": "Enceladus",
                "description": "Breathy, soft tone",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "male",
                    "characteristic": "breathy",
                    "use_case": "intimate content",
                },
            },
            "Iapetus": {
                "name": "Iapetus",
                "description": "Clear, articulate delivery",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "male",
                    "characteristic": "clear",
                    "use_case": "professional",
                },
            },
            "Umbriel": {
                "name": "Umbriel",
                "description": "Easy-going, casual tone",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "male",
                    "characteristic": "easy-going",
                    "use_case": "friendly content",
                },
            },
            "Algieba": {
                "name": "Algieba",
                "description": "Smooth tone (note: may have compatibility issues)",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "unknown",
                    "characteristic": "smooth",
                    "use_case": "general purpose",
                    "note": "potentially buggy",
                },
            },
            "Despina": {
                "name": "Despina",
                "description": "Smooth, pleasant delivery",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "female",
                    "characteristic": "smooth",
                    "use_case": "narration",
                },
            },
            "Erinome": {
                "name": "Erinome",
                "description": "Clear, crisp tone",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "female",
                    "characteristic": "clear",
                    "use_case": "instructional",
                },
            },
            "Algenib": {
                "name": "Algenib",
                "description": "Gravelly, textured delivery",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "male",
                    "characteristic": "gravelly",
                    "use_case": "dramatic content",
                },
            },
            "Rasalgethi": {
                "name": "Rasalgethi",
                "description": "Informative, educational tone",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "male",
                    "characteristic": "informative",
                    "use_case": "educational",
                },
            },
            "Laomedeia": {
                "name": "Laomedeia",
                "description": "Upbeat, lively delivery",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "female",
                    "characteristic": "upbeat",
                    "use_case": "motivational",
                },
            },
            "Achernar": {
                "name": "Achernar",
                "description": "Soft, gentle tone",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "female",
                    "characteristic": "soft",
                    "use_case": "calming content",
                },
            },
            "Alnilam": {
                "name": "Alnilam",
                "description": "Firm, confident delivery",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "male",
                    "characteristic": "firm",
                    "use_case": "authoritative",
                },
            },
            "Schedar": {
                "name": "Schedar",
                "description": "Even, balanced tone",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "male",
                    "characteristic": "even",
                    "use_case": "neutral narration",
                },
            },
            "Gacrux": {
                "name": "Gacrux",
                "description": "Mature, sophisticated delivery",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "female",
                    "characteristic": "mature",
                    "use_case": "professional",
                },
            },
            "Pulcherrima": {
                "name": "Pulcherrima",
                "description": "Forward, assertive tone",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "female",
                    "characteristic": "forward",
                    "use_case": "confident content",
                },
            },
            "Achird": {
                "name": "Achird",
                "description": "Friendly, approachable delivery",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "male",
                    "characteristic": "friendly",
                    "use_case": "conversational",
                },
            },
            "Zubenelgenubi": {
                "name": "Zubenelgenubi",
                "description": "Casual, relaxed tone",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "male",
                    "characteristic": "casual",
                    "use_case": "informal content",
                },
            },
            "Vindemiatrix": {
                "name": "Vindemiatrix",
                "description": "Gentle, soothing delivery",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "female",
                    "characteristic": "gentle",
                    "use_case": "therapeutic content",
                },
            },
            "Sadachbia": {
                "name": "Sadachbia",
                "description": "Lively, energetic tone",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "male",
                    "characteristic": "lively",
                    "use_case": "entertainment",
                },
            },
            "Sadaltager": {
                "name": "Sadaltager",
                "description": "Knowledgeable, wise delivery",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "male",
                    "characteristic": "knowledgeable",
                    "use_case": "educational",
                },
            },
            "Sulafat": {
                "name": "Sulafat",
                "description": "Warm, welcoming tone",
                "labels": {
                    "provider": "Gemini",
                    "model": "gemini-2.5-pro-preview-tts",
                    "gender": "female",
                    "characteristic": "warm",
                    "use_case": "hospitality content",
                },
            },
        }

    def list_voices(self) -> list[dict]:
        """Return list of available voices with their details"""
        return [
            {"name": k, "voice_id": k, **v} for k, v in self.available_voices.items()
        ]

    def generate_speech(
        self,
        text: str,
        output_path: str,
        voice: str = "Charon",
        model: str = "gemini-2.5-pro-preview-tts",
        temperature: float = 1.0,
        instructions: str = None,
        **kwargs,
    ) -> dict | None:
        """Generate speech using Google Gemini's TTS API

        Args:
            text: The text to convert to speech
            output_path: Where to save the resulting audio file
            voice: One of the available prebuilt voices (Charon, Milagros, Jaemin, etc.)
            model: The TTS model to use (gemini-2.5-pro-preview-tts or gemini-2.5-flash-preview-tts)
            temperature: Controls randomness in generation (0.0 to 1.0)
            instructions: Optional instructions to guide the voice style (e.g., "Speak in a cheerful tone")
            **kwargs: Additional parameters for future API options

        Returns:
            Dictionary with status and any additional information
        """
        try:
            # Create content parts with instructions if provided
            if instructions:
                content_text = f"{instructions}: {text}"
            else:
                content_text = text

            contents = [
                genai_types.Content(
                    role="user",
                    parts=[
                        genai_types.Part.from_text(text=content_text),
                    ],
                ),
            ]

            # Configure voice and response format
            generate_content_config = genai_types.GenerateContentConfig(
                temperature=temperature,
                response_modalities=["audio"],
                speech_config=genai_types.SpeechConfig(
                    voice_config=genai_types.VoiceConfig(
                        prebuilt_voice_config=genai_types.PrebuiltVoiceConfig(
                            voice_name=voice
                        )
                    )
                ),
            )

            # Process the streaming response
            audio_chunks = []
            for chunk in self.client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue

                if inline_data := chunk.candidates[0].content.parts[0].inline_data:
                    # Get the data and mime type
                    data_buffer = inline_data.data
                    mime_type = inline_data.mime_type

                    # Convert to WAV if needed
                    if not mime_type.startswith("audio/"):
                        continue

                    # Check if we need to convert the audio format
                    file_extension = mimetypes.guess_extension(mime_type)
                    if file_extension is None:
                        file_extension = ".wav"
                        data_buffer = self._convert_to_wav(data_buffer, mime_type)

                    audio_chunks.append(data_buffer)

            # Combine all audio chunks
            audio_data = b"".join(audio_chunks)

            # Save the audio data to output file
            with open(output_path, "wb") as f:
                f.write(audio_data)

            # Verify the file was written correctly
            if not Path(output_path).exists() or Path(output_path).stat().st_size == 0:
                raise TTSError("Failed to write audio file")

            result = {
                "status": "success",
                "model": model,
                "voice": voice,
            }

            # Generate alignment if requested
            if kwargs.get("return_alignment", False):
                temp_path = Path(output_path)
                temp_file = (
                    temp_path.parent / f"{temp_path.stem}_temp{temp_path.suffix}"
                )

                try:
                    with open(temp_file, "wb") as f:
                        f.write(audio_data)
                    asr_result = self.asr_manager.transcribe(
                        "openai", temp_file, language=kwargs.get("language")
                    )
                    result["alignment"] = asr_result.to_elevenlabs_alignment()
                finally:
                    temp_file.unlink(missing_ok=True)

            return result

        except Exception as e:
            # Handle rate limit errors specifically
            if "rate limit" in str(e).lower() or "quota" in str(e).lower():
                raise TTSRateLimitError(f"Gemini API rate limit exceeded: {str(e)}")
            # Handle other errors
            raise TTSError(f"Gemini TTS generation failed: {str(e)}")

    def _convert_to_wav(self, audio_data: bytes, mime_type: str) -> bytes:
        """Generates a WAV file header for the given audio data and parameters.

        Args:
            audio_data: The raw audio data as a bytes object.
            mime_type: Mime type of the audio data.

        Returns:
            A bytes object representing the WAV file with header.
        """
        parameters = self._parse_audio_mime_type(mime_type)
        bits_per_sample = parameters["bits_per_sample"]
        sample_rate = parameters["rate"]
        num_channels = 1
        data_size = len(audio_data)
        bytes_per_sample = bits_per_sample // 8
        block_align = num_channels * bytes_per_sample
        byte_rate = sample_rate * block_align
        chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size

        # Create WAV header
        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",  # ChunkID
            chunk_size,  # ChunkSize (total file size - 8 bytes)
            b"WAVE",  # Format
            b"fmt ",  # Subchunk1ID
            16,  # Subchunk1Size (16 for PCM)
            1,  # AudioFormat (1 for PCM)
            num_channels,  # NumChannels
            sample_rate,  # SampleRate
            byte_rate,  # ByteRate
            block_align,  # BlockAlign
            bits_per_sample,  # BitsPerSample
            b"data",  # Subchunk2ID
            data_size,  # Subchunk2Size (size of audio data)
        )
        return header + audio_data

    def _parse_audio_mime_type(self, mime_type: str) -> dict[str, int]:
        """Parses bits per sample and rate from an audio MIME type string.

        Args:
            mime_type: The audio MIME type string (e.g., "audio/L16;rate=24000").

        Returns:
            A dictionary with "bits_per_sample" and "rate" keys.
        """
        bits_per_sample = 16
        rate = 24000

        # Extract rate from parameters
        parts = mime_type.split(";")
        for param in parts:
            param = param.strip()
            if param.lower().startswith("rate="):
                try:
                    rate_str = param.split("=", 1)[1]
                    rate = int(rate_str)
                except (ValueError, IndexError):
                    pass  # Keep rate as default
            elif param.startswith("audio/L"):
                try:
                    bits_per_sample = int(param.split("L", 1)[1])
                except (ValueError, IndexError):
                    pass  # Keep bits_per_sample as default

        return {"bits_per_sample": bits_per_sample, "rate": rate}


class TTSManager:
    def __init__(self):
        self.providers = {}

    def add_provider(self, name: str, provider: TTSProvider):
        self.providers[name] = provider

    @retry(
        retry=(
            retry_if_exception_type(requests.exceptions.RequestException)
            | retry_if_exception_type(WebSocketException)
            | retry_if_exception_type(TTSRateLimitError)
        ),
        wait=wait_exponential(multiplier=2, min=2, max=120),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def generate_speech(
        self, provider_name: str, text: str, output_path: str, voice: str, **kwargs
    ) -> dict | None:
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found")
        return self.providers[provider_name].generate_speech(
            text, output_path, voice, **kwargs
        )

    @retry(
        retry=(
            retry_if_exception_type(requests.exceptions.RequestException)
            | retry_if_exception_type(WebSocketException)
            | retry_if_exception_type(TTSRateLimitError)
        ),
        wait=wait_exponential(multiplier=2, min=2, max=120),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def generate_speech_async(
        self, provider_name: str, text: str, output_path: str, voice: str, **kwargs
    ) -> dict | None:
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found")
        return await self.providers[provider_name].generate_speech_async(
            text, output_path, voice, **kwargs
        )

    def list_voices(self, provider_name: str) -> list[str] | list[dict]:
        """List available voices for the specified provider"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found")
        return self.providers[provider_name].list_voices()

    def test_provider(self, provider_name: str) -> dict:
        """Test if the provider can successfully generate speech.

        Args:
            provider_name: Name of the provider to test

        Returns:
            dict: Results of the test containing success status and any error messages
        """
        if provider_name not in self.providers:
            return {
                "success": False,
                "error": f"Provider '{provider_name}' not found",
                "provider": provider_name,
            }

        test_text = "This is a test of text-to-speech generation."
        test_file = Path("test_tts_output.wav")

        try:
            # Get first available voice for the provider
            voices = self.list_voices(provider_name)
            if not voices:
                return {
                    "success": False,
                    "error": "No voices available for this provider",
                    "provider": provider_name,
                }

            # Extract voice ID based on provider response format
            voice_id = voices[0].get("voice_id", voices[0].get("name", voices[0]))

            # Attempt generation
            result = self.generate_speech(
                provider_name, test_text, str(test_file), voice=voice_id
            )

            # Check if file was created and has content
            if test_file.exists() and test_file.stat().st_size > 0:
                return {
                    "success": True,
                    "provider": provider_name,
                    "voice_tested": voice_id,
                    "result": result,
                }
            else:
                return {
                    "success": False,
                    "error": "Audio file was not created or is empty",
                    "provider": provider_name,
                }

        except Exception as e:
            return {"success": False, "error": str(e), "provider": provider_name}

        finally:
            # Cleanup test file
            test_file.unlink(missing_ok=True)

    def find_similar_voices(
        self,
        provider_name: str,
        audio_file: str,
        similarity_threshold: float = None,
        top_k: int = None,
    ) -> list[dict]:
        """Find similar voices based on an audio sample using the specified provider.

        Args:
            provider_name: Name of the provider to use
            audio_file: Path to the audio file to analyze
            similarity_threshold: Optional threshold for voice similarity
            top_k: Optional number of most similar voices to return

        Returns:
            List of voice dictionaries containing similarity matches
        """
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found")

        return self.providers[provider_name].find_similar_voices(
            audio_file, similarity_threshold=similarity_threshold, top_k=top_k
        )

    @retry(
        retry=(
            retry_if_exception_type(requests.exceptions.RequestException)
            | retry_if_exception_type(WebSocketException)
            | retry_if_exception_type(TTSRateLimitError)
        ),
        wait=wait_exponential(multiplier=2, min=2, max=120),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def convert_speech(
        self,
        provider_name: str,
        input_path: str,
        output_path: str,
        voice: str,
        **kwargs,
    ) -> dict | None:
        """Convert speech from one voice to another using the specified provider.

        Args:
            provider_name: Name of the provider to use
            input_path: Path to the input audio file
            output_path: Path where the converted audio should be saved
            voice: Target voice ID/name
            **kwargs: Additional provider-specific parameters

        Returns:
            dict: Results of the conversion containing success status and any additional info
        """
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found")

        return self.providers[provider_name].convert_speech(
            input_path, output_path, voice, **kwargs
        )

    @retry(
        retry=(
            retry_if_exception_type(requests.exceptions.RequestException)
            | retry_if_exception_type(WebSocketException)
            | retry_if_exception_type(TTSRateLimitError)
        ),
        wait=wait_exponential(multiplier=2, min=2, max=120),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def add_sharing_voice(
        self, provider_name: str, public_user_id: str, voice_id: str, new_name: str
    ) -> dict | None:
        """Add a shared voice to the provider's collection.

        Args:
            provider_name: Name of the provider to use
            public_user_id: Public user ID used to identify the voice owner
            voice_id: ID of the voice to be added
            new_name: The name to identify this voice in your collection

        Returns:
            dict: Response containing the new voice_id

        Raises:
            ValueError: If the provider is not found
            TTSError: If the API request fails
            TTSRateLimitError: If rate limits are exceeded
        """
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found")

        return self.providers[provider_name].add_sharing_voice(
            public_user_id, voice_id, new_name
        )


# Initialize TTS manager and providers
"""
tts_manager = TTSManager()
tts_manager.add_provider("openai_realtime", OpenAIRealtimeTTSProvider())
tts_manager.add_provider("openai", OpenAITTSProvider())
tts_manager.add_provider("elevenlabs", ElevenLabsTTSProvider())
"""


def create_tts_manager():
    manager = TTSManager()
    if os.getenv("OPENAI_API_KEY"):
        manager.add_provider("openai_realtime", OpenAIRealtimeTTSProvider())
        manager.add_provider("openai", OpenAITTSProvider())
    if os.getenv("ELEVENLABS_API_KEY"):
        manager.add_provider("elevenlabs", ElevenLabsTTSProvider())
    if os.getenv("T2A_API_KEY") and os.getenv("MINIMAXI_GROUP_ID"):
        manager.add_provider("minimaxi", MiniMaxiTTSProvider())
    if os.getenv("CARTESIA_API_KEY"):
        manager.add_provider("cartesia", CartesiaTTSProvider())
    if os.getenv("GEMINI_API_KEY"):
        manager.add_provider("gemini", GeminiTTSProvider())
    return manager


def main():
    load_dotenv(override=True)

    text = "Hello, this is another and another and ANOTHER ... test of speed adjustements of TTS generated speech."
    tts_manager = create_tts_manager()

    # List ElevenLabs voices
    """
    print("\nElevenLabs voices:")
    elevenlabs_voices = tts_manager.list_voices("elevenlabs")
    for voice in elevenlabs_voices:
        print(f"- {voice['name']} (ID: {voice['voice_id']})")
        # Optional: print more details
        # print(f"  Description: {voice.get('description', 'N/A')}")
        # print(f"  Preview URL: {voice.get('preview_url', 'N/A')}")
    """

    text = "Welcome to our demonstration! I'm excited to show you how each voice sounds unique and special."
    tts_manager = create_tts_manager()

    # Test each OpenAI voice with the realtime API
    print("\nGenerating samples for each OpenAI voice using realtime API...")
    openai_voices = tts_manager.list_voices("openai_realtime")
    for voice_info in openai_voices:
        voice_name = voice_info["name"]
        print(f"\nGenerating sample for {voice_name}...")
        print(f"Description: {voice_info['description']}")

        # Test with different emotional contexts
        contexts = {
            # "default": "Speak naturally, in your default style.",
            "excited": "Speak with enthusiasm and excitement, like someone extremelly excited about something.",
            # "depressed": "Speak in a depressed, monotone tone, like an extremely depressed person.",
            # "extreme": "Take a random but EXTREME voice, hysteric, old blood-seeking vampire like, weird accent, etc...",
        }

        for context_name, context_description in contexts.items():
            context_output = f"tmp/output_realtime_{voice_name}_{context_name}.wav"
            response = tts_manager.generate_speech(
                "openai_realtime",
                text,
                context_output,
                voice=voice_name,
                context=context_description,
                return_alignment=True,
            )

            print(f"Sample with context {context_name} saved to {context_output}")

            if response and "alignment" in response:
                print("\nOriginal timestamps:")
                for i, char in enumerate(response["alignment"]["characters"]):
                    start = response["alignment"]["character_start_times_seconds"][i]
                    end = response["alignment"]["character_end_times_seconds"][i]
                    if char not in [" ", "\n"]:  # Skip whitespace for readability
                        print(f"Character '{char}': {start:.3f}s - {end:.3f}s")

        break
    # Test with different speeds and print timestamps

    speeds = []  # [1.02]  # , 1.5, 2.0]
    for speed in speeds:
        print("\nOpenAI voices:")
        openai_voices = tts_manager.list_voices("openai")
        for voice in openai_voices:
            print(f"- {voice}")

        # List ElevenLabs voices
        print("\nElevenLabs voices:")
        elevenlabs_voices = tts_manager.list_voices("elevenlabs")
        for voice in elevenlabs_voices:
            print(f"- {voice['name']} (ID: {voice['voice_id']})")
            print(f"  Description: {voice.get('description', 'N/A')}")
            print(f"  Labels: {voice.get('labels', 'N/A')}")

        """
        print(f"\nTesting with speed {speed}x:")
        response = tts_manager.generate_speech(
            "openai_realtime",  # "elevenlabs",
            text,
            "output_cheerful.wav",
            voice="alloy",  # "21m00Tcm4TlvDq8ikWAM",
            speed=speed,
            context="Speak in a cheerful, energetic, OVER THE TOP tone, like a morning show host on drugs.",
        )

        response = tts_manager.generate_speech(
            "openai_realtime",  # "elevenlabs",
            text,
            "output_sad.wav",
            voice="alloy",  # "21m00Tcm4TlvDq8ikWAM",
            speed=speed,
            context="Speak in a sad, depressed, monotone tone, like an extremely depressed person.",
        )

        if "alignment" in response:
            print("\nOriginal timestamps:")
            for i, char in enumerate(response["alignment"]["characters"]):
                start = response["alignment"]["character_start_times_seconds"][i]
                end = response["alignment"]["character_end_times_seconds"][i]
                if char not in [" ", "\n"]:  # Skip whitespace for readability
                    print(f"Character '{char}': {start:.3f}s - {end:.3f}s")
        """


if __name__ == "__main__":
    main()
