from logging import getLogger
from uuid import uuid4

import requests
from django.conf import settings

logger = getLogger(__file__)

api_key = settings.AI_SERVICE_API_KEY
base_url = settings.AI_SERVICE_DEMO_URL
headers = {"api-key": api_key}


class AIProcessing:
    """
    This class handles the AI processing for submissions

    For this to work, you must specify the AI_SERVICE_DEMO_URL
    and LEARNGUAL_AI_API_KEY in your settings.py file.
    """

    @staticmethod
    def analyze_audio(
        audio,
        reference_text,
        scripted: bool = False,
        prompt: str = None,
        language: str = None,
        correct_reference: bool = True,
        query_string: str = None,
    ):
        """
        this communicates with the AI model and returns the analysis results
        for the given audio
        """
        base_url = settings.AI_SERVICE_DEMO_URL
        if not str(base_url).endswith("/"):
            base_url += "/"

        uid = uuid4().hex
        files = {"audio_data": (f"{uid}-audio.mp3", audio)}
        payload = {
            "reference_text": reference_text,
            "scripted": scripted,
            "correct_reference": correct_reference,
        }

        if prompt:
            payload["prompt"] = prompt

        if language:
            payload["language"] = language

        if query_string:
            base_url += "?" + query_string

        response = requests.post(
            url=base_url, headers=headers, files=files, data=payload
        )
        if response.status_code == 200:
            return {"status": True, "response": response}

        else:
            return {"status": False, "response": response}

    @staticmethod
    def relevance(topic: str, essay: str, query_string: str = None):
        base_url = settings.AI_SERVICE_DEMO_URL

        if not str(base_url).endswith("/"):
            base_url += "/"

        base_url = base_url.rstrip("process/") + "/relevance/"

        if query_string:
            base_url += "?" + query_string

        response = requests.post(
            url=base_url,
            headers=headers,
            data={"topic": topic, "essay": essay},
        )

        if response.status_code == 200:
            return {"status": True, "response": response}

        else:
            return {"status": False, "response": response}

    def logic_evaluation(
        topic: str,
        essay: str,
        criteria: list[str] = None,
        query_string: str = None,
    ):
        """Evaluates the logical structure and reasoning of an essay in relation to a topic.

        Assesses the essay's logical flow, argument validity, and reasoning quality by sending
        it to an AI evaluation service. The evaluation can be customized with specific criteria.

        Args:
            topic: The topic or subject the essay should address.
            essay: The text content of the essay to be evaluated.
            criteria: List of evaluation criteria to assess. Defaults to:
                ["evidence", "coherence", "relevance", "critical_thinking"] if not provided.
                For pure logic evaluation, consider ["argument_structure", "fallacies", "reasoning"].

        Returns:
            dict: A dictionary containing:
                - status (bool): True if request was successful (HTTP 200), False otherwise
                - response (Union[requests.Response, dict]):
                    The full response object if successful, or error details if failed

        Raises:
            ConnectionError: If the request to the evaluation service fails.
            ValueError: If topic or essay is empty or None.
        """
        if not criteria:
            criteria = [
                "evidence",
                "coherence",
                "relevance",
                "critical_thinking",
            ]

        base_url = settings.AI_SERVICE_DEMO_URL

        if not str(base_url).endswith("/"):
            base_url += "/"

        base_url = base_url.removesuffix("/process/") + "/essay-evaluation/"

        if query_string:
            base_url += "?" + query_string

        try:
            response = requests.post(
                url=base_url,
                headers=headers,
                json={
                    "topic": topic,
                    "essay": essay,
                    "criteria": criteria,
                },
            )
        except ConnectionError:
            return {"status": False, "response": {"message": "connection error"}}
        if response.status_code == 200:
            return {"status": True, "response": response}
        else:
            return {"status": False, "response": response}

    def grammar(text_body: str, query_string: str = None):
        """
        Analyze and correct grammar in the provided text using AI service.

        Args:
            text_body (str): The text content to be analyzed for grammar corrections.
            query_string (str, optional): Additional query parameters to append to the request URL.

        Returns:
            dict: A dictionary containing the analysis status and response data.
                - status (bool): True if request was successful (status code 200), False otherwise.
                - response (requests.Response): The raw response object from the AI service.

                On successful response, the response.json() contains:
                - Original Speech (str): The original input text
                - Grammatical Correct Version (str): The corrected version of the text
                - Feedback (list): List of corrections made to the text
                - Grammar Score (int): Numerical score representing grammar quality (0-100)
                - Correction Operations (list, optional): Detailed correction operations with:
                    - operation (str): Type of correction (e.g., "substituted")
                    - original_word (str): The original word that was corrected
                    - replacement_word (str): The word that replaced the original
                    - position (int): Character position where the correction was made
                    - length (int): Length of the original word

        Example:
            >>> result = grammar("A boy fell on the log and broke his leg")
            >>> if result["status"]:
            ...     data = result["response"].json()
            ...     print(data["Grammatical Correct Version"])
            ...     # Output: "A boy fell on a log and broke his leg"
        """
        base_url: str = settings.AI_SERVICE_DEMO_URL

        if not str(base_url).endswith("/"):
            base_url += "/"

        base_url = base_url.removesuffix("/process/") + "/gammar/"
        if query_string:
            base_url += "?" + query_string

        response = requests.post(
            url=base_url,
            headers=headers,
            data={"speech": text_body},
        )

        if response.status_code == 200:
            return {"status": True, "response": response}

        else:
            return {"status": False, "response": response}

    def grammarv2(text_body: str, query_string: str = None):
        """
        Check grammar of provided text using AI service v2 grammar endpoint.
        This function sends a POST request to the AI service's v2 grammar check endpoint
        to analyze and correct grammatical errors in the provided text.
        Args:
            text_body (str): The text content to be checked for grammar errors.
            query_string (str, optional): Additional query parameters to append to the URL.
                                         Defaults to None.
        Returns:
            dict: A dictionary containing the grammar check results with the following structure:
                - status (bool): True if the request was successful (status code 200), False otherwise.
                - response (requests.Response): The raw response object from the API call.
                On successful response (status=True), the response.json() will contain:
                - originalText (str): The original input text
                - correctedText (str): The grammatically corrected version of the text
                - issues (list): List of grammar issues found, each containing:
                    - type (str): Type of grammar issue (e.g., "PrepositionUsage")
                    - message (str): Detailed explanation of the issue
                    - suggestion (str): Suggested correction
                    - severity (str): Severity level of the issue
                    - targetWord (str): The problematic word or phrase
                - metadata (dict): Processing information including:
                    - processingTime (int): Time taken to process in seconds
                    - agentsUsed (list): List of grammar agents used for analysis
                    - totalIssuesFound (int): Total number of issues detected
                    - overallScore (int): Overall grammar score
                - operations (list): Detailed edit operations showing text changes
        Raises:
            requests.RequestException: If there's an issue with the HTTP request.
        Note:
            Requires the 'settings.AI_SERVICE_DEMO_URL' to be properly configured
            and 'headers' to be defined in the module scope.
        """

        base_url: str = settings.AI_SERVICE_DEMO_URL

        urls = str(base_url).split("/v1/")
        if len(urls) < 1:
            return

        base_url = urls[0] + "/v2/" + "grammar/check"

        if query_string:
            base_url += "?" + query_string

        response = requests.post(
            url=base_url,
            headers=headers,
            data={"speech": text_body, "content": text_body},
        )

        if response.status_code == 200:
            return {"status": True, "response": response}

        else:
            return {"status": False, "response": response}

    def check_audio(audio, language="en"):
        """
        Analyze audio using the AI service.

        Args:
            audio: Audio file content (bytes or file-like object) to be analyzed.
            language (str, optional): Language code of the audio (default: "en").

        Returns:
            dict: {
                "status": True/False,
                "response": requests.Response or error details
            }

        Raises:
            requests.RequestException: If the HTTP request fails.

        Note:
            The 'audio' parameter should be the actual audio data, not a file path.
            The AI service endpoint must be properly configured in settings.

        Example:
            >>> with open("sample.mp3", "rb") as f:
            ...     result = AIProcessing.check_audio(f.read(), language="en")
            ...     if result["status"]:
            ...         print(result["response"].json())
        """
        base_url: str = settings.AI_SERVICE_DEMO_URL

        urls = str(base_url).split("/v1/")
        if len(urls) < 1:
            return {"status": False, "response": {"error": "Invalid base URL"}}

        base_url = urls[0] + "/v2/" + "grammar/check-audio"
        payload = {"language": language}

        uid = uuid4().hex
        files = [("file", (f"{uid}-audio.mp3", audio, "application/octet-stream"))]

        try:
            response = requests.request(
                "POST", base_url, headers=headers, data=payload, files=files
            )
            if response.status_code == 200:
                return {"status": True, "response": response}
            else:
                logger.error(
                    f"AI audio grammar check failed: {response.status_code} {response.text}"
                )
                return {"status": False, "response": response}
        except requests.RequestException as e:
            logger.error(f"RequestException during AI audio grammar check: {e}")
            return {"status": False, "response": {"error": str(e)}}
