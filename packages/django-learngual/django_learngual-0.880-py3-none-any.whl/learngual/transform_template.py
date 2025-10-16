import json
import os
import re
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.html import strip_tags

from .logger import logger
from .translator import Translator
from .utils import get_frontend_base_url

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@learngual.com")


class TransformTemplateContext:
    def __init__(
        self,
        template_dir: str | Path,
        user_or_account: Any | None = None,
        kwargs_map: dict[str, dict[str, Any]] = {},
        make_public: bool = False,
    ):
        """
        Initialize the TransformContext.

        :param json_file_path: Path to the JSON file.
        :param translate: Function to translate text.
        :param user_or_account: User or account object containing language preferences.
        :param kwargs_map: Dictionary containing key-value pairs for formatting.
        """
        self.kwargs_map = kwargs_map
        translator: Translator = Translator(
            target_language=user_or_account.language if user_or_account else None
        )

        self.translate = translator.get_translation
        self.target_language = translator.target_language
        self.template_dir = template_dir.strip("/")
        self.template_root = Path(settings.ROOT_DIR) / "templates"
        self.data = self.read_json(self.template_info_path)
        self.make_public = make_public

    @property
    def default_context(self) -> dict[str, Any]:
        context = {
            **self.default_enviroment_context,
            **self.default_settings_context,
            "main_url": get_frontend_base_url(),
            "demo_url": get_frontend_base_url("demo"),
        }
        return context

    @property
    def default_enviroment_context(self):
        context = os.getenv("LEARNGUAL_TEMPLATE_CONTEXT", "{}")

        if isinstance(context, str):
            try:
                context = json.loads(context)
            except json.JSONDecodeError:
                context = {}
        elif isinstance(context, dict):
            context = dict
        else:
            context = {}
        return context

    @property
    def default_settings_context(self) -> dict[str, Any]:
        return getattr(settings, "LEARNGUAL_TEMPLATE_CONTEXT", {}) or {}

    @property
    def template_file_path(self) -> Path:
        return self.template_root / self.template_dir / "index.html"

    @property
    def template(self) -> str:
        """template name

        Returns:
            str: _description_
        """
        return self.template_dir + "/index.html"

    @property
    def subject(self) -> str:
        """Extract and translate subject.

        Returns:
            str: _description_
        """
        return self.get_context().get("header", "")

    @property
    def template_info_path(self) -> Path:
        return self.template_root / self.template_dir / "info.json"

    def read_json(self, file_path: str) -> dict[str, Any]:
        """
        Read JSON data from a file.

        :param file_path: Path to the JSON file.
        :return: Parsed JSON data as a dictionary.
        """
        with open(file_path) as file:
            return json.load(file)

    def extract_patterns(self, input_string: str) -> dict[str, str]:
        """
        Extract key-value patterns from the input string.

        :param input_string: String containing the patterns in the format {key: value}.
        :return: Dictionary containing extracted key-value pairs.
        """
        # Define the regex pattern to match {<key>:<value>}
        pattern = r"\{([^{}:]+):([^{}]+)\}"

        # Find all matches in the input string
        matches = re.findall(pattern, input_string)

        # Create a dictionary from the matches
        result = {key.strip(): value.strip() for key, value in matches}
        return result

    @staticmethod
    def replace_placeholders(input_string: str, replacements: dict[str, str]) -> str:
        """
        Replace placeholders in the input string with values from the replacements dictionary.

        :param input_string: String containing placeholders in the format {variable_key: value}.
        :param replacements: Dictionary containing replacement values for each variable_key.
        :return: String with placeholders replaced by corresponding values.
        """
        # Define the pattern to match the placeholders {variable_key: value} and ignore those without a colon
        pattern = r"\{([^{}:]+):([^{}]+)\}"

        # Function to replace each match with the corresponding value from the replacements dictionary
        def replacer(match):
            variable_key = match.group(1).strip()  # Extract and strip the variable_key
            # Get the replacement value from the dictionary or use the original value if key not found
            return replacements.get(variable_key, match.group(0))

        # Use re.sub with the replacer function to replace all valid placeholders
        return re.sub(pattern, replacer, input_string)

    def process_string(self, value: str, key: str) -> str:
        """
        Process a string by translating and formatting it.

        :param value: String to be processed.
        :param key: Key associated with the string in the JSON data.
        :return: Translated and formatted string.
        """
        # Translate the value
        translated_value = self.translate(value)
        # Format the string using the corresponding kwargs_map
        try:
            formatted_value = translated_value.format_map(self.kwargs_map.get(key, {}))
        except ValueError:
            formatted_value = "Issue with email contact admin"
            logger.exception(f"Email template has incomplete keys {self.template_dir}")
        return formatted_value

    def process_dict(self, value: dict[str, Any], key: str) -> str:
        """
        Process a dictionary containing plainText and meta keys.

        :param value: Dictionary to be processed.
        :param key: Key associated with the dictionary in the JSON data.
        :return: Processed string with translated and formatted content.
        """
        plain_text = value["plainText"]
        # Translate the value
        translated_value: str = self.translate(plain_text)
        meta = value.get("meta", {})
        final_text: str = self.process_meta(translated_value, meta, key)

        try:
            # Format the string using the corresponding kwargs_map
            formatted_value = final_text.format_map(self.kwargs_map.get(key, {}))
        except KeyError as err:
            raise KeyError(
                f"no data for {str(err)} in kwargs_map['{key}']: meta: {meta}, final_text: {final_text}"
            ) from err
        return formatted_value

    @staticmethod
    def custom_format_map(template: str, replacements: dict[str, str]) -> str:
        """
        Custom format function that replaces placeholders in the format
        [key] with values from the replacements dictionary.

        :param template: The template string containing placeholders in the format [key].
        :param replacements: A dictionary containing replacement values for each key.
        :return: The formatted string with placeholders replaced by corresponding values.
        """
        # Define the pattern to match placeholders in the format [key]
        pattern = r"\[([^\[\]]+)\]"

        # Function to replace each match with the corresponding value from the replacements dictionary
        def replacer(match):
            key = match.group(1)  # Extract the key from the match
            return replacements.get(
                key, match.group(0)
            )  # Return the replacement value or the original placeholder

        # Use re.sub with the replacer function to replace all placeholders
        return re.sub(pattern, replacer, template)

    def process_meta(
        self, plain_text: str, meta: dict[str, dict[str, dict[str, str]]], key: str
    ) -> str:
        """
        Process meta information to replace placeholders with HTML tags.

        :param plain_text: Translated plain text string.
        :param meta: Meta information containing HTML tag and attributes.
        :param key: Key associated with the meta data.
        :return: String with placeholders replaced by HTML tags.
        """
        mapping = {
            _key: self.custom_format_map(
                value, replacements=self.kwargs_map.get(key, {})
            )
            for _key, value in self.extract_patterns(plain_text).items()
        }
        html_mapping = dict()
        for tag_variable, attributes in meta.items():
            tag, variable = tag_variable.split(":")
            # Format each attribute in the meta dictionary
            for attr, val in attributes["attr"].items():
                try:
                    attributes["attr"][attr] = val.format_map(
                        {
                            **(self.default_context or {}),
                            **self.kwargs_map.get(key, {}),
                        }
                    )
                except KeyError as e:
                    raise KeyError(f"No {str(e)} in kwargs_map['{key}']") from e
            variable = variable.strip()
            attributes_str = " ".join(
                [f'{k}="{v}"' for k, v in attributes["attr"].items()]
            )
            if variable in mapping:
                data_str = (
                    f"<{tag} {attributes_str}>" + "{" + variable + "}" + f"</{tag}>"
                )
                try:
                    html_mapping[variable] = data_str.format_map(
                        {variable: mapping[variable]}
                    )
                except KeyError:
                    raise KeyError(
                        f"{data_str = }"
                        f"{variable = }"
                        "{variable: mapping[variable]} = "
                        + str({variable: mapping[variable]})
                    )
        return self.replace_placeholders(
            input_string=plain_text, replacements=html_mapping
        )

    def get_context(self, **kwargs) -> dict[str, Any]:
        """
        Transform the JSON data by processing strings and dictionaries.

        :return: Dictionary containing transformed JSON data.
        """
        # Process the json_data
        result = {}
        for key, value in self.data.items():
            if isinstance(value, str):
                # Process the string value
                result[key] = self.process_string(value, key)
            elif isinstance(value, dict):
                # Handle plainText and meta structure
                result[key] = self.process_dict(value, key)
            else:
                raise ValueError(f"Value must either be a string or a dict: {value}")

        context = {**self.default_context, **result, **kwargs}

        return context

    def _send_email(
        self,
        emails: list[str],
        context: dict[str, Any],
        subject: str,
        template: str,
        fail_silently: bool = True,
        from_email: str = DEFAULT_FROM_EMAIL,
    ) -> None:
        """
        Internal method to send an email using Django's EmailMultiAlternatives.

        Args:
            emails (list[str]): List of recipient email addresses.
            context (dict[str, Any]): Context data for rendering the template.
            subject (str): Email subject.
            template (str): Path to the email template.
            fail_silently (bool, optional): Whether to suppress send errors. Defaults to True.
            from_email (str, optional): Sender email address. Defaults to DEFAULT_FROM_EMAIL.

        Returns:
            None
        """
        logger.info(
            f"Rendering email template '{template}' for recipients: {emails} with subject: '{subject}'"
        )
        to: list[str] = emails if isinstance(emails, list) else [emails]
        try:
            html_content: str = render_to_string(template, context)
            text_content: str = strip_tags(html_content)
            msg = EmailMultiAlternatives(subject, text_content, from_email, to)
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=fail_silently)
            logger.info(
                f"Email sent to {to} from {from_email} with subject '{subject}'"
            )
        except OSError as e:
            logger.error(f"OS error while sending email to {to}: {e}", exc_info=True)
            if not fail_silently:
                raise
        except ValueError as e:
            logger.error(f"Value error while sending email to {to}: {e}", exc_info=True)
            if not fail_silently:
                raise
        except TypeError as e:
            logger.error(f"Type error while sending email to {to}: {e}", exc_info=True)
            if not fail_silently:
                raise
        except Exception as e:
            # Log unexpected exceptions, but do not raise unless fail_silently is False
            logger.error(
                f"Unexpected error while sending email to {to}: {e}", exc_info=True
            )
            if not fail_silently:
                raise

    def send_email(
        self,
        emails: list[str] | str,
        context: dict[str, Any] = {},
        from_email: str = DEFAULT_FROM_EMAIL,
    ) -> None:
        """
        Send an email using the provided template and context.

        Args:
            emails (list[str] | str): Recipient email address(es).
            context (dict, optional): Additional context to merge with the template context. Defaults to {}.
            from_email (str, optional): Sender email address. Defaults to DEFAULT_FROM_EMAIL.

        Returns:
            None
        """
        if isinstance(emails, str):
            emails = [emails]
        logger.info(
            f"Preparing to send email to: {emails} using template: {self.template} from: {from_email}"
        )
        try:
            merged_context = self.get_context() | context
            self._send_email(
                from_email=from_email,
                emails=emails,
                context=merged_context,
                fail_silently=True,
                template=self.template,
                subject=self.subject,
            )
            logger.info(f"Email sent successfully to: {emails}")
        except (ValueError, KeyError, TypeError, OSError) as e:
            logger.error(
                f"Failed to send email to: {emails}. Error: {e}", exc_info=True
            )


class TransformContext:
    def __init__(
        self,
        data: dict[str, Any],
        language: str | None = None,
        kwargs_map: dict[str, dict[str, Any]] = {},
    ):
        """
        Initialize the TransformContext.

        :param json_file_path: Path to the JSON file.
        :param translate: Function to translate text.
        :param user_or_account: User or account object containing language preferences.
        :param kwargs_map: Dictionary containing key-value pairs for formatting.
        """
        self.kwargs_map = kwargs_map
        self.language = language or translation.get_language()
        self.translate = Translator(target_language=self.language).get_translation
        self.data = data

    def extract_patterns(self, input_string: str) -> dict[str, str]:
        """
        Extract key-value patterns from the input string.

        :param input_string: String containing the patterns in the format {key: value}.
        :return: Dictionary containing extracted key-value pairs.
        """
        # Define the regex pattern to match {<key>:<value>}
        pattern = r"\{([^{}:]+):([^{}]+)\}"

        # Find all matches in the input string
        matches = re.findall(pattern, input_string)

        # Create a dictionary from the matches
        result = {key.strip(): value.strip() for key, value in matches}
        return result

    @staticmethod
    def replace_placeholders(input_string: str, replacements: dict[str, str]) -> str:
        """
        Replace placeholders in the input string with values from the replacements dictionary.

        :param input_string: String containing placeholders in the format {variable_key: value}.
        :param replacements: Dictionary containing replacement values for each variable_key.
        :return: String with placeholders replaced by corresponding values.
        """
        # Define the pattern to match the placeholders {variable_key: value} and ignore those without a colon
        pattern = r"\{([^{}:]+):([^{}]+)\}"

        # Function to replace each match with the corresponding value from the replacements dictionary
        def replacer(match):
            variable_key = match.group(1).strip()  # Extract and strip the variable_key
            # Get the replacement value from the dictionary or use the original value if key not found
            return replacements.get(variable_key, match.group(0))

        # Use re.sub with the replacer function to replace all valid placeholders
        return re.sub(pattern, replacer, input_string)

    def process_string(self, value: str, key: str) -> str:
        """
        Process a string by translating and formatting it.

        :param value: String to be processed.
        :param key: Key associated with the string in the JSON data.
        :return: Translated and formatted string.
        """
        # Translate the value
        translated_value = self.translate(value)
        # Format the string using the corresponding kwargs_map
        formatted_value = translated_value.format_map(self.kwargs_map.get(key, {}))
        return formatted_value

    def process_dict(self, value: dict[str, Any], key: str) -> str:
        """
        Process a dictionary containing plainText and meta keys.

        :param value: Dictionary to be processed.
        :param key: Key associated with the dictionary in the JSON data.
        :return: Processed string with translated and formatted content.
        """
        plain_text = value["plainText"]
        # Translate the value
        translated_value: str = self.translate(plain_text)
        meta = value.get("meta", {})
        final_text: str = self.process_meta(translated_value, meta, key)

        try:
            # Format the string using the corresponding kwargs_map
            formatted_value = final_text.format_map(self.kwargs_map.get(key, {}))
        except KeyError as err:
            raise KeyError(
                f"no data for {str(err)} in kwargs_map['{key}']: meta: {meta}, final_text: {final_text}"
            ) from err
        return formatted_value

    @staticmethod
    def custom_format_map(template: str, replacements: dict[str, str]) -> str:
        """
        Custom format function that replaces placeholders in the format
        [key] with values from the replacements dictionary.

        :param template: The template string containing placeholders in the format [key].
        :param replacements: A dictionary containing replacement values for each key.
        :return: The formatted string with placeholders replaced by corresponding values.
        """
        # Define the pattern to match placeholders in the format [key]
        pattern = r"\[([^\[\]]+)\]"

        # Function to replace each match with the corresponding value from the replacements dictionary
        def replacer(match):
            key = match.group(1)  # Extract the key from the match
            return replacements.get(
                key, match.group(0)
            )  # Return the replacement value or the original placeholder

        # Use re.sub with the replacer function to replace all placeholders
        return re.sub(pattern, replacer, template)

    def process_meta(
        self, plain_text: str, meta: dict[str, dict[str, dict[str, str]]], key: str
    ) -> str:
        """
        Process meta information to replace placeholders with HTML tags.

        :param plain_text: Translated plain text string.
        :param meta: Meta information containing HTML tag and attributes.
        :param key: Key associated with the meta data.
        :return: String with placeholders replaced by HTML tags.
        """
        mapping = {
            _key: self.custom_format_map(
                value, replacements=self.kwargs_map.get(key, {})
            )
            for _key, value in self.extract_patterns(plain_text).items()
        }
        html_mapping = dict()
        for tag_variable, attributes in meta.items():
            tag, variable = tag_variable.split(":")
            # Format each attribute in the meta dictionary
            for attr, val in attributes["attr"].items():
                try:
                    attributes["attr"][attr] = val.format_map(
                        self.kwargs_map.get(key, {})
                    )
                except KeyError as e:
                    raise KeyError(f"No {str(e)} in kwargs_map['{key}']") from e
            variable = variable.strip()
            attributes_str = " ".join(
                [f'{k}="{v}"' for k, v in attributes["attr"].items()]
            )
            if variable in mapping:
                html_mapping[variable] = (
                    f"<{tag} {attributes_str}>" + "{" + variable + "}" + f"</{tag}>"
                ).format_map({variable: mapping[variable]})
        return self.replace_placeholders(
            input_string=plain_text, replacements=html_mapping
        )

    def get_context(self, **kwargs) -> dict[str, Any]:
        """
        Transform the JSON data by processing strings and dictionaries.

        :return: Dictionary containing transformed JSON data.
        """
        # Process the json_data
        result = {}
        for key, value in self.data.items():
            if isinstance(value, str):
                # Process the string value
                result[key] = self.process_string(value, key)
            elif isinstance(value, dict):
                # Handle plainText and meta structure
                result[key] = self.process_dict(value, key)
            else:
                raise ValueError(f"Value must either be a string or a dict: {value}")
        return {**result, **kwargs}
