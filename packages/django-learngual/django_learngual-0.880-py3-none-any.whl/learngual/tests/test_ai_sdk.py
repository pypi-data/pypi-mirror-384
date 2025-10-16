import math
import os
import wave
from unittest.mock import patch

from iam_service.utilities.utils import TestHelper

from ..ai_sdk import AIProcessing


def generate_sine_wav(
    filename: str = "sine_wave.wav",
    duration: float = 3.0,  # seconds
    sample_rate: int = 44100,  # Hz
    frequency: float = 440.0,  # Hz (A4 note)
    amplitude: float = 0.5,  # 0 to 1
    overwrite: bool = False,
):
    """Generates a sine wave audio file without numpy."""

    if not overwrite and os.path.exists(filename):
        print(f"File already exists: {filename} (Skipping generation)")
        return filename

    # Open a WAV file for writing
    with wave.open(filename, "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes (16-bit PCM)
        wav_file.setframerate(sample_rate)

        # Generate sine wave samples
        num_frames = int(duration * sample_rate)
        for i in range(num_frames):
            # Calculate sample value
            value = amplitude * math.sin(2 * math.pi * frequency * i / sample_rate)
            # Convert to 16-bit PCM (-32768 to 32767)
            sample = int(value * 32767)
            # Write the sample (as bytes)
            wav_file.writeframes(sample.to_bytes(2, "little", signed=True))


class TestAIProcessing(TestHelper):
    def test_relevance(self):
        mock_response = {
            "mock_ai_data": {
                "key": {"value": False},
            }
        }

        with patch("requests.post") as mock_dependency:
            mock_dependency.return_value.json.return_value = mock_response

            mock_dependency.return_value.ok = True
            mock_dependency.return_value.status_code = 200

            response_dict = AIProcessing.relevance(
                topic="this is the topic", essay="this is the essay"
            )
            assert response_dict.get("status")
            assert response_dict.get("response")
            assert response_dict["response"].json() == mock_response
            assert response_dict["response"].status_code == 200

    def test_logic_evaluation(self):
        mock_response = {
            "mock_ai_data": {
                "key": {"value": False},
            }
        }

        with patch("requests.post") as mock_dependency:
            mock_dependency.return_value.json.return_value = mock_response

            mock_dependency.return_value.ok = True
            mock_dependency.return_value.status_code = 200

            response_dict = AIProcessing.logic_evaluation(
                topic="this is the topic", essay="this is the essay"
            )
            assert response_dict.get("status")
            assert response_dict.get("response")
            assert response_dict["response"].json() == mock_response
            assert response_dict["response"].status_code == 200

    def test_grammar(self):
        mock_response = {
            "mock_ai_data": {
                "key": {"value": False},
            }
        }

        with patch("requests.post") as mock_dependency:
            mock_dependency.return_value.json.return_value = mock_response

            mock_dependency.return_value.ok = True
            mock_dependency.return_value.status_code = 200

            response_dict = AIProcessing.grammar(text_body="this is the topic")
            assert response_dict.get("status")
            assert response_dict.get("response")
            assert response_dict["response"].json() == mock_response
            assert response_dict["response"].status_code == 200

    def test_analyze_audio(self):
        mock_response = {
            "mock_ai_data": {
                "key": {"value": False},
            }
        }

        with patch("requests.post") as mock_dependency:
            mock_dependency.return_value.json.return_value = mock_response

            mock_dependency.return_value.ok = True
            mock_dependency.return_value.status_code = 200

            response_dict = AIProcessing.analyze_audio(
                audio=generate_sine_wav("output.wav"),
                reference_text="this is the topic",
                correct_reference=False,
            )
            assert response_dict.get("status")
            assert response_dict.get("response")
            assert response_dict["response"].json() == mock_response
            assert response_dict["response"].status_code == 200

    def test_check_audio(self):
        mock_response = {
            "mock_ai_data": {
                "key": {"value": False},
            }
        }

        with open("output.wav", "rb") as f:
            response_dict = AIProcessing.check_audio(audio=f, language="en")
            assert response_dict.get("status") is True
            assert response_dict.get("response")
            assert response_dict["response"].json()
            expected_keys = [
                "originalText",
                "correctedText",
                "issues",
                "metadata",
                "operations",
            ]

            assert self.has_fields(response_dict["response"].json(), expected_keys)

            assert response_dict["response"].status_code == 200

        with patch("iam_service.learngual.ai_sdk.requests.request") as mock_dependency:
            mock_dependency.return_value.json.return_value = mock_response

            mock_dependency.return_value.ok = False
            mock_dependency.return_value.status_code = 400

            with open("output.wav", "rb") as f:
                response_dict = AIProcessing.check_audio(audio=f, language="en")

                assert response_dict.get("status") is False
                assert response_dict.get("response")
                assert response_dict["response"].json() == mock_response
                assert response_dict["response"].status_code == 400
