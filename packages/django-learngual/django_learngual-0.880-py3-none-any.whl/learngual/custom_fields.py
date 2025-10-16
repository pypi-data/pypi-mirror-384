"""
Custom Django model fields and DRF serializer fields for Pydantic model integration.

This module provides Django model fields and Django REST Framework serializer fields
that seamlessly integrate Pydantic models with Django's ORM and API serialization.
The fields support automatic validation, type conversion, and JSON serialization
while maintaining type safety and comprehensive error handling.

Classes:
    PydanticModelFieldEncoder: JSON encoder for Pydantic models
    PydanticModelField: Django model field for storing Pydantic models as JSON
    PydanticModelSerializerField: DRF serializer field for Pydantic models

Features:
    - Single model support: Store individual Pydantic model instances
    - List model support: Store lists of Pydantic model instances
    - Polymorphic model support: Store different model types with type discrimination
    - Automatic validation using Pydantic schemas
    - Graceful error handling with detailed error messages
    - Type-safe serialization and deserialization
    - Integration with Django's validation system

Example Usage:
    >>> from django.db import models
    >>> from .custom_fields import PydanticModelField
    >>>
    >>> class MyModel(models.Model):
    ...     # Single model
    ...     data = PydanticModelField(pydantic_model=AnswerModel)
    ...     # List of models
    ...     answers = PydanticModelField(pydantic_model=[AnswerModel])
    ...     # Polymorphic models
    ...     content = PydanticModelField(pydantic_model={
    ...         "word_play": WordPlayAnswer,
    ...         "essay": EssayAnswer
    ...     })
"""

import json

from django.db import models
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from rest_framework import serializers

from . import custom_exceptions
from .interface import BaseTypeModel
from .logger import logger


def transform_data(value: str) -> str:
    """
    Transform and clean the input data by removing newline characters.

    This method cleans JSON string data by removing all newline characters (\n)
    that might interfere with JSON parsing or storage.

    Args:
        value (str): The input string to clean, typically a JSON string.

    Returns:
        str: The cleaned string with all newline characters removed.

    Examples:
        >>> field = PydanticModelField()
        >>> field.transform_data('{"key": "value\\nwith\\nnewlines"}')
        '{"key": "valuewithwenlines"}'
    """
    if isinstance(value, str):
        try:
            json.loads(value)
        except json.JSONDecodeError:
            return value.replace("\n", "")
    return value


class PydanticModelFieldEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for Pydantic models.

    This encoder extends the standard JSONEncoder to handle serialization of Pydantic BaseModel
    instances and lists of BaseModel instances by converting them to JSON-compatible dictionaries
    using their model_dump() method.

    Examples:
        >>> encoder = PydanticModelFieldEncoder()
        >>> json.dumps(pydantic_model, cls=PydanticModelFieldEncoder)
        >>> json.dumps([model1, model2], cls=PydanticModelFieldEncoder)
    """

    def default(self, obj):
        """
        Convert a Python object to a JSON-serializable format.

        This method is called by the JSON encoder when it encounters an object that is not
        natively JSON-serializable. It handles Pydantic BaseModel instances and lists of
        BaseModel instances by converting them to dictionaries using the model_dump() method.

        Args:
            obj: The object to be serialized. Can be a BaseModel instance, a list of BaseModel
                instances, or any other object.

        Returns:
            dict | list[dict] | Any: A JSON-serializable representation of the object. For BaseModel
                instances, returns a dictionary. For lists of BaseModel instances, returns a list
                of dictionaries. For other objects, delegates to the parent encoder.

        Raises:
            TypeError: If the object cannot be serialized (raised by parent encoder).

        Examples:
            >>> encoder = PydanticModelFieldEncoder()
            >>> model = SomeModel(field="value")
            >>> encoder.default(model)  # Returns {'field': 'value'}
            >>> encoder.default([model1, model2])  # Returns [{'field': 'value1'}, {'field': 'value2'}]
        """
        if isinstance(obj, BaseModel):
            return obj.model_dump(mode="json", by_alias=True)
        elif isinstance(obj, list) and isinstance(obj[0], BaseModel):
            data: list[BaseModel] = obj
            return [model.model_dump(mode="json", by_alias=True) for model in data]
        else:
            return super().default(obj)


class PydanticModelField(models.JSONField):
    retry_count = 2
    """
    A Django model field that stores and validates Pydantic models as JSON data.

    This field extends Django's JSONField to provide seamless integration with Pydantic models,
    supporting single models, lists of models, and polymorphic models with type discrimination.
    It automatically handles serialization/deserialization, validation, and type conversion
    between Python objects and database JSON storage.

    Features:
        - Automatic validation using Pydantic model schemas
        - Support for single models, lists/tuples of models, and polymorphic models
        - Graceful error handling with detailed error messages
        - Optional fallback to default values on validation errors
        - Type-safe serialization and deserialization

    Supported Configurations:
        1. Single model: PydanticModelField(pydantic_model=AnswerModel)
        2. List of models: PydanticModelField(pydantic_model=[AnswerModel])
        3. Polymorphic models: PydanticModelField(pydantic_model={"word_play": AnswerModel, "essay": EssayAnswer})

    Args:
        pydantic_model: The Pydantic model(s) to use for validation. Can be:
            - A single Pydantic model class
            - A tuple/list containing a single model class (for lists of instances)
            - A dict mapping type names to model classes (for polymorphic models)
        null: Whether the field allows NULL values in the database (default: True)
        blank: Whether the field allows blank values in forms (default: True)
        validate_default: Whether to validate the default value against the model (default: False)
        use_default_on_invalid_data: Whether to use default value when data is invalid (default: False)
        base_type_model: Base class for polymorphic models (default: BaseTypeModel)

    Examples:
        >>> # Single model
        >>> class MyModel(models.Model):
        ...     data = PydanticModelField(pydantic_model=AnswerModel)

        >>> # List of models
        >>> class MyModel(models.Model):
        ...     answers = PydanticModelField(pydantic_model=[AnswerModel])

        >>> # Polymorphic models
        >>> class MyModel(models.Model):
        ...     content = PydanticModelField(pydantic_model={
        ...         "word_play": WordPlayAnswer,
        ...         "essay": EssayAnswer
        ...     })

    Raises:
        ValidationError: If the pydantic_model configuration is invalid or if validation fails
            during field operations.
    """

    def __init__(
        self,
        pydantic_model: BaseModel
        | tuple[type[BaseModel]]
        | dict[str, type[BaseModel]] = None,
        null: bool = True,
        blank: bool = True,
        validate_default: bool = False,
        use_default_on_invalid_data: bool = False,
        base_type_model: type[BaseTypeModel] | None = BaseTypeModel,
        *args,
        **kwargs,
    ):
        """
        Initialize a PydanticModelField for Django models.

        Args:
            pydantic_model (BaseModel | tuple[type[BaseModel]] | dict[str, type[BaseModel]], optional):
                The Pydantic model(s) to use for validation and serialization.
                Can be a single model, a tuple/list of models, or a dict mapping type names to models.
            null (bool, optional): Whether the field allows NULL values. Defaults to True.
            blank (bool, optional): Whether the field allows blank values. Defaults to True.
            validate_default (bool, optional): Whether to validate the default value against the model.
                Defaults to False.
            base_type_model (type[BaseTypeModel] | None, optional): The base type for
                polymorphic models. Defaults to BaseTypeModel.
            *args: Additional positional arguments for the parent class.
            **kwargs: Additional keyword arguments for the parent class.

        Raises:
            ValueError: If the provided pydantic_model or default value is invalid.
        """
        self.base_type_model = base_type_model or BaseTypeModel
        self.default_value = None
        self.use_default_on_invalid_data = use_default_on_invalid_data

        # Validate and set the default value if provided
        if default_value := kwargs.get("default"):
            if validate_default:
                if isinstance(default_value, type):
                    if not (
                        default_value
                        and isinstance(pydantic_model, (list, tuple))
                        and issubclass(default_value, (list, tuple))
                    ) and not issubclass(
                        default_value, (BaseModel, self.base_type_model)
                    ):
                        # Detailed internal logging for debugging
                        logger.exception(
                            f"Invalid default value configuration for field '{getattr(self, 'name', 'unknown')}': "
                            f"default_value={default_value!r}, pydantic_model={pydantic_model!r}. "
                            f"Expected a subclass of BaseModel or BaseTypeModel, or a tuple/list of such classes. "
                            f"Field definition location: {self.__class__.__module__}.{self.__class__.__qualname__}"
                        )
                        # User-friendly error message for developers
                        raise custom_exceptions.ServiceUnavailable(
                            f"Invalid default value: {default_value}. "
                            f"Expected a subclass of BaseModel or BaseTypeModel, "
                            f"or a tuple/list of such classes matching the pydantic_model. "
                            f"Check that your default value matches the type and structure of "
                            f"your pydantic_model."
                        )
                else:
                    if not (
                        default_value
                        and isinstance(pydantic_model, (list, tuple))
                        and isinstance(default_value, (list, tuple))
                    ) and not isinstance(
                        default_value, (BaseModel, self.base_type_model)
                    ):
                        # Detailed internal logging for debugging
                        logger.exception(
                            f"Invalid default value instance for field '{getattr(self, 'name', 'unknown')}': "
                            f"default_value={default_value!r}, type={type(default_value)}, "
                            f"pydantic_model={pydantic_model!r}. "
                            f"Expected an instance of BaseModel or BaseTypeModel, or a tuple/list of such instances. "
                            f"Field definition location: {self.__class__.__module__}.{self.__class__.__qualname__}"
                        )
                        # User-friendly error message for developers
                        raise custom_exceptions.ServiceUnavailable(
                            "Invalid field configuration: default value instance does not match "
                            "the pydantic model structure. "
                            "Please ensure the default value instance is compatible with the "
                            "specified pydantic model."
                        )
            self.default_value = default_value

        # Validate the pydantic_model argument
        if pydantic_model:
            if isinstance(pydantic_model, (list, tuple)):
                if not pydantic_model:
                    # Detailed internal logging for debugging
                    logger.exception(
                        f"Empty pydantic_model list/tuple for field '{getattr(self, 'name', 'unknown')}': "
                        f"{pydantic_model!r}. "
                        f"Field definition location: {self.__class__.__module__}.{self.__class__.__qualname__}"
                    )
                    # User-friendly error message for developers
                    raise custom_exceptions.ServiceUnavailable(
                        "Invalid field configuration: pydantic_model list cannot be empty. "
                        "Please provide at least one Pydantic model class."
                    )
                for model_class in pydantic_model:
                    if not issubclass(model_class, (BaseModel, self.base_type_model)):
                        # Detailed internal logging for debugging
                        logger.exception(
                            "Invalid model class in pydantic_model list/tuple for field "
                            f"'{getattr(self, 'name', 'unknown')}': "
                            f"model_class={model_class!r}, pydantic_model={pydantic_model!r}. "
                            "Expected subclass of BaseModel or BaseTypeModel. "
                            f"Field definition location: {self.__class__.__module__}.{self.__class__.__qualname__}"
                        )
                        # User-friendly error message for developers
                        raise custom_exceptions.ServiceUnavailable(
                            "Invalid field configuration: all elements in pydantic_model list "
                            "must be valid Pydantic model classes. "
                            "Please ensure all model classes inherit from BaseModel or BaseTypeModel."
                        )
            elif isinstance(pydantic_model, dict):
                for key, model_class in pydantic_model.items():
                    if not issubclass(model_class, self.base_type_model):
                        # Detailed internal logging for debugging
                        logger.exception(
                            f"Invalid model class for key '{key}' in pydantic_model dict for field "
                            f"'{getattr(self, 'name', 'unknown')}': "
                            f"model_class={model_class!r}, key='{key}', pydantic_model={pydantic_model!r}. "
                            "Expected subclass of BaseTypeModel. "
                            f"Field definition location: {self.__class__.__module__}.{self.__class__.__qualname__}"
                        )
                        # User-friendly error message for developers
                        raise custom_exceptions.ServiceUnavailable(
                            f"Invalid field configuration: model class for type '{key}' must "
                            f"inherit from BaseTypeModel. "
                            "Please ensure all values in the pydantic_model dictionary are "
                            "valid BaseTypeModel subclasses."
                        )
            elif not issubclass(pydantic_model, (BaseModel, self.base_type_model)):
                # Detailed internal logging for debugging
                logger.exception(
                    f"Invalid pydantic_model type for field '{getattr(self, 'name', 'unknown')}': "
                    f"pydantic_model={pydantic_model!r}, type={type(pydantic_model)}. "
                    f"Expected BaseModel/BaseTypeModel subclass, tuple/list of such classes, "
                    f"or dict mapping to such classes. "
                    f"Field definition location: {self.__class__.__module__}.{self.__class__.__qualname__}"
                )
                # User-friendly error message for developers
                raise custom_exceptions.ServiceUnavailable(
                    "Invalid field configuration: pydantic_model must be a Pydantic model class, "
                    "a list containing a model class, or a dictionary mapping type names to model classes."
                )

        self.pydantic_model: (
            type[BaseModel]
            | type[BaseTypeModel]
            | None
            | tuple[type[BaseModel] | type[BaseTypeModel]]
            | dict[str, type[BaseModel] | type[BaseTypeModel]]
        ) = pydantic_model

        # Use the custom encoder for JSON serialization
        kwargs["encoder"] = kwargs.get("encoder", PydanticModelFieldEncoder)
        super().__init__(null=null, blank=blank, *args, **kwargs)

    def __to_python(
        self, value
    ) -> BaseModel | BaseTypeModel | list[BaseModel] | dict | None:
        """
        Convert the input value from the database or deserialization into a Pydantic model instance,
        a list of model instances, or a dictionary, depending on the configuration of the field.

        Args:
            value (str | dict | list | None): The value to convert, typically from the database.

        Returns:
            BaseModel | BaseTypeModel | list[BaseModel] | dict | None:
                The deserialized Pydantic model(s) or default value.

        Raises:
            ValueError: If the value cannot be deserialized into the expected Pydantic model(s).
        """

        # If the value is a JSON string, attempt to parse it
        if isinstance(value, str):
            try:
                value = json.loads(transform_data(value))
                if isinstance(value, str):
                    value = json.loads(transform_data(value))
            except (TypeError, ValueError, json.JSONDecodeError) as e:
                # Detailed internal logging for debugging
                logger.exception(
                    f"JSON decode error for field '{getattr(self, 'name', 'unknown')}': "
                    f"value={value!r}, error={e!r}. "
                    f"Field type: {self.__class__.__name__}, "
                    f"pydantic_model={getattr(self, 'pydantic_model', None)!r}"
                )
                # User-friendly error message for API response
                raise custom_exceptions.ServiceUnavailable(
                    "Invalid data format: the provided value is not valid JSON. "
                    "Please ensure the data is properly formatted."
                ) from e

        # If a pydantic_model is set and value is not empty, attempt to instantiate the model(s)
        if value and self.pydantic_model:
            try:
                if isinstance(self.pydantic_model, (list, tuple)):
                    # Expecting a list of model instances
                    if not isinstance(value, (list, tuple)):
                        # Detailed internal logging for debugging
                        logger.exception(
                            f"Type mismatch for field '{getattr(self, 'name', 'unknown')}': "
                            f"expected=list/tuple, got={type(value).__name__}, value={value!r}, "
                            f"pydantic_model={getattr(self, 'pydantic_model', None)!r}"
                        )
                        # User-friendly error message for API response
                        raise custom_exceptions.ServiceUnavailable(
                            "Invalid data format: expected a list of items but received a "
                            "different data type. Please provide data as an array."
                        )
                    data = []
                    ModelClass = self.pydantic_model[0]
                    for idx, x in enumerate(value):
                        try:
                            data.append(ModelClass(**x))
                        except Exception as e:
                            # Detailed internal logging for debugging
                            logger.exception(
                                f"Model instantiation failed for field '{getattr(self, 'name', 'unknown')}' "
                                f"at index {idx}: "
                                f"ModelClass={ModelClass.__name__}, item_data={x!r}, error={e!r}, "
                                f"pydantic_model={getattr(self, 'pydantic_model', None)!r}"
                            )
                            # User-friendly error message for API response
                            raise custom_exceptions.ServiceUnavailable(
                                f"Invalid data at position {idx + 1}: the provided data does not "
                                f"match the expected format. Please check the data structure and "
                                f"required fields."
                            ) from e
                    return data
                elif isinstance(self.pydantic_model, dict):
                    # Expecting a dict with a "type" key and "data" payload
                    if not isinstance(value, dict):
                        try:
                            value = dict(value)
                        except (TypeError, ValueError) as e:
                            # Detailed internal logging for debugging
                            logger.exception(
                                f"Dict conversion failed for field '{getattr(self, 'name', 'unknown')}': "
                                f"value={value!r}, error={e!r}, "
                                f"pydantic_model={getattr(self, 'pydantic_model', None)!r}"
                            )
                            # User-friendly error message for API response
                            raise custom_exceptions.ServiceUnavailable(
                                "Invalid data format: expected an object with key-value pairs but "
                                "received a different data type. Please provide data as a JSON object."
                            )
                    model_type = value.get("type")
                    ModelClass = self.pydantic_model.get(model_type)
                    if not ModelClass:
                        # Detailed internal logging for debugging
                        logger.exception(
                            f"Invalid or missing type key for field '{getattr(self, 'name', 'unknown')}': "
                            f"model_type={model_type!r}, value={value!r}, "
                            f"valid_types={list(getattr(self, 'pydantic_model', {}).keys())}, "
                            f"pydantic_model={getattr(self, 'pydantic_model', None)!r}"
                        )
                        # User-friendly error message for API response
                        valid_types = list(getattr(self, "pydantic_model", {}).keys())
                        raise custom_exceptions.ServiceUnavailable(
                            f"Invalid data type: expected one of {valid_types} but received '{model_type}'. "
                            "Please specify a valid data type."
                        )
                    data_payload = value.get("data", {})
                    try:
                        return ModelClass(**data_payload)
                    except Exception as e:
                        # Detailed internal logging for debugging
                        logger.exception(
                            f"Model instantiation failed for polymorphic field '{getattr(self, 'name', 'unknown')}': "
                            f"ModelClass={ModelClass.__name__}, model_type='{model_type}', "
                            f"data_payload={data_payload!r}, error={e!r}, "
                            f"pydantic_model={getattr(self, 'pydantic_model', None)!r}"
                        )
                        # User-friendly error message for API response
                        raise custom_exceptions.ServiceUnavailable(
                            f"Invalid data for type '{model_type}': the provided data does not "
                            f"match the expected format. Please check the data structure and "
                            f"required fields."
                        ) from e
                elif issubclass(self.pydantic_model, (BaseModel, self.base_type_model)):
                    # Expecting a single model instance
                    if not isinstance(value, dict):
                        try:
                            value = dict(value)
                        except (TypeError, ValueError):
                            # Detailed internal logging for debugging
                            logger.exception(
                                f"Dict conversion failed for single model field '{getattr(self, 'name', 'unknown')}': "
                                f"value={value!r}, type={type(value).__name__}, "
                                f"pydantic_model={getattr(self, 'pydantic_model', None)!r}"
                            )
                            # User-friendly error message for API response
                            raise custom_exceptions.ServiceUnavailable(
                                "Invalid data format: expected an object with key-value pairs but "
                                "received a different data type. Please provide data as a JSON object."
                            )

                    try:
                        return self.pydantic_model(**value)
                    except Exception as e:
                        # Detailed internal logging for debugging
                        logger.exception(
                            f"Model instantiation failed for single model field '{getattr(self, 'name', 'unknown')}': "
                            f"ModelClass={getattr(self, 'pydantic_model', None).__name__ if getattr(self, 'pydantic_model', None) else 'Unknown'}, "  # noqa: E501
                            f"value={value!r}, error={e!r}, "
                            f"pydantic_model={getattr(self, 'pydantic_model', None)!r}"
                        )
                        # User-friendly error message for API response
                        raise custom_exceptions.ServiceUnavailable(
                            "Invalid data: the provided data does not match the expected format. "
                            "Please check the data structure and required fields."
                        ) from e
                else:
                    # Detailed internal logging for debugging
                    logger.exception(
                        f"Invalid pydantic_model configuration for field '{getattr(self, 'name', 'unknown')}': "
                        f"pydantic_model={getattr(self, 'pydantic_model', None)!r}, "
                        f"Field type: {self.__class__.__name__}, "
                        f"Field definition location: {self.__class__.__module__}.{self.__class__.__qualname__}"
                    )
                    # User-friendly error message for API response (this is likely an internal configuration error)
                    raise custom_exceptions.ServiceUnavailable(
                        "Data processing error: invalid field configuration detected. "
                        "Please contact support if this issue persists."
                    )
            except Exception as exc:
                if self.use_default_on_invalid_data:
                    logger.warning(
                        f"Invalid data for field '{self.name}': {exc}. "
                        "Using default value instead."
                    )
                    return self.__get_default_instance()
                else:
                    logger.exception(
                        f"Failed to convert value for field '{self.name}'. "
                        f"Value: {value!r}. "
                        f"Expected pydantic_model: {self.pydantic_model!r}. "
                        f"Error: {exc}"
                    )

                    raise custom_exceptions.ServiceUnavailable(
                        f"Failed to convert value for field '{self.name}': {exc}. "
                        f"Value: {value!r}. "
                        f"Expected pydantic_model: {self.pydantic_model!r}. "
                        "Ensure the value matches the expected structure and type."
                    ) from exc
        elif self.default_value:
            return self.__get_default_instance()

        # Return the value as-is if no model is set or value is empty
        return value

    def to_python(
        self, value
    ) -> BaseModel | BaseTypeModel | list[BaseModel] | dict | None:

        for i in range(1, self.retry_count + 1):
            try:
                return self.__to_python(value)
            except Exception as e:
                if i < self.retry_count:
                    logger.warning(
                        f"Retrying to convert value for field (attempt {i}/{self.retry_count}) due to: {e}. "
                        "This is an internal error, please contact support if this issue persists."
                    )
                else:
                    raise e

    def __get_default_value(self) -> str:
        """
        Returns the default value for the field, serialized as a JSON string.

        Returns:
            str: The JSON-encoded default value, which matches the structure expected by the field's pydantic_model.

        Raises:
            ValueError: If the default value cannot be serialized due to a type mismatch or invalid structure.
        """
        # Determine the base value structure based on the pydantic_model type
        value: list | dict = (
            [] if isinstance(self.pydantic_model, (list, tuple)) else {}
        )

        if self.default_value:
            # If the default value is callable (e.g., a function or lambda), call it to get the value
            if callable(self.default_value):
                default_value: BaseModel | BaseTypeModel | list | tuple = (
                    self.default_value()
                )
            else:
                default_value: BaseModel | BaseTypeModel | list | tuple = (
                    self.default_value
                )

            try:
                # For list/tuple pydantic_model, wrap the default value in a list if it's not already a list/tuple
                if isinstance(self.pydantic_model, (list, tuple)):
                    if isinstance(default_value, (list, tuple)):
                        value = [
                            item.model_dump(mode="json", by_alias=True)
                            for item in default_value
                        ]
                    else:
                        value = [default_value.model_dump(mode="json", by_alias=True)]
                else:
                    # For single model, just dump the default value
                    value = default_value.model_dump(mode="json", by_alias=True)
            except AttributeError as e:
                # Detailed internal logging for debugging
                logger.exception(
                    f"Default value serialization failed for field '{getattr(self, 'name', 'unknown')}': "
                    f"default_value={getattr(self, 'default_value', None)!r}, error={e!r}, "
                    f"pydantic_model={getattr(self, 'pydantic_model', None)!r}, "
                    f"Field type: {self.__class__.__name__}"
                )
                # User-friendly error message (this is likely an internal configuration error)
                raise custom_exceptions.ServiceUnavailable(
                    "Data processing error: failed to serialize default value. "
                    "Please contact support if this issue persists."
                ) from e
            except Exception as e:
                # Detailed internal logging for debugging
                logger.exception(
                    f"Unexpected serialization error for field '{getattr(self, 'name', 'unknown')}': "
                    f"default_value={getattr(self, 'default_value', None)!r}, error={e!r}, "
                    f"pydantic_model={getattr(self, 'pydantic_model', None)!r}, "
                    f"Field type: {self.__class__.__name__}"
                )
                # User-friendly error message (this is likely an internal configuration error)
                raise custom_exceptions.ServiceUnavailable(
                    "Data processing error: unexpected error during serialization. "
                    "Please contact support if this issue persists."
                ) from e

        try:
            return json.dumps(
                value,
            )
        except Exception as e:
            # Detailed internal logging for debugging
            logger.exception(
                f"JSON encoding failed for field '{getattr(self, 'name', 'unknown')}': "
                f"value={value!r}, error={e!r}, "
                f"pydantic_model={getattr(self, 'pydantic_model', None)!r}, "
                f"Field type: {self.__class__.__name__}"
            )
            # User-friendly error message (this is likely an internal processing error)
            raise custom_exceptions.ServiceUnavailable(
                "Data processing error: failed to encode data for storage. "
                "Please contact support if this issue persists."
            ) from e

    def __get_default_instance(
        self,
    ) -> BaseModel | BaseTypeModel | list[BaseModel] | dict | None:
        """
        Returns the default instance for the field, matching the structure expected by the field's pydantic_model.

        Returns:
            BaseModel | BaseTypeModel | list[BaseModel] | dict | None: The default instance(s) for the field.

        Raises:
            ValueError: If the default value is not compatible with the pydantic_model configuration.
        """
        if self.default_value:
            # If the default value is callable (e.g., a function or lambda), call it to get the value
            if callable(self.default_value):
                default_value: BaseModel | BaseTypeModel | list | tuple = (
                    self.default_value()
                )
            else:
                default_value: BaseModel | BaseTypeModel | list | tuple = (
                    self.default_value
                )

            # For list/tuple pydantic_model, wrap the default value in a list if it's not already a list/tuple
            if isinstance(self.pydantic_model, (list, tuple)):
                if not isinstance(default_value, (list, tuple)):
                    return [default_value]
                return default_value
            else:
                return default_value

        # If no default value is set, return an empty list or dict based on the pydantic_model type
        if isinstance(self.pydantic_model, (list, tuple)):
            return []
        elif isinstance(self.pydantic_model, dict):
            return {}
        elif self.pydantic_model is None:
            return None
        else:
            # Detailed internal logging for debugging
            logger.exception(
                f"Invalid default instance configuration for field '{getattr(self, 'name', 'unknown')}': "
                f"default_value={getattr(self, 'default_value', None)!r}, "
                f"pydantic_model={getattr(self, 'pydantic_model', None)!r}, "
                f"Field type: {self.__class__.__name__}"
            )
            # User-friendly error message (this is an internal configuration error)
            raise custom_exceptions.ServiceUnavailable(
                "Data processing error: unable to determine default value for field. "
                "Please contact support if this issue persists."
            )

    def from_db_value(
        self, value: str | dict | list | None, expression, connection
    ) -> BaseModel | BaseTypeModel | list[BaseModel] | dict | None:
        """
        Converts a value as returned by the database to a Python object.

        Args:
            value (str | dict | list | None): The value from the database.
            expression: The expression used in the query (unused).
            connection: The database connection (unused).

        Returns:
            BaseModel | BaseTypeModel | list[BaseModel] | dict | None:
                The deserialized Pydantic model(s) or default value.

        Raises:
            ValueError: If the value cannot be deserialized into the expected Pydantic model(s).
        """
        try:
            return self.to_python(value)
        except Exception as exc:
            if self.use_default_on_invalid_data:
                logger.warning(f"Invalid data for field '{self.name}': {exc}")
                return self.__get_default_instance()
            else:
                # Detailed internal logging for debugging
                logger.exception(
                    f"Database value conversion error for field '{getattr(self, 'name', 'unknown')}': "
                    f"db_value={value!r}, error={exc!r}, "
                    f"pydantic_model={getattr(self, 'pydantic_model', None)!r}, "
                    f"Field type: {self.__class__.__name__}"
                )
                # User-friendly error message (this could be a data corruption issue)
                raise custom_exceptions.ServiceUnavailable(
                    "Data processing error: failed to load data from database. "
                    "The stored data may be corrupted. Please contact support if this issue persists."
                ) from exc

    def get_prep_value(
        self, value: BaseModel | BaseTypeModel | list[BaseModel] | None
    ) -> str:
        """
        Prepare the value for storage in the database by serializing it to a JSON string.
        Handles single Pydantic models, lists/tuples of models, and polymorphic dict-based models.

        Args:
            value (BaseModel | BaseTypeModel | list[BaseModel] | None): The value to serialize.

        Returns:
            str: The JSON-encoded value suitable for database storage.

        Raises:
            ValueError: If the value does not match the expected structure or type for the configured pydantic_model.
        """
        if value is None or not self.pydantic_model:
            return self.__get_default_value()

        data = {}

        if isinstance(self.pydantic_model, (list, tuple)):
            # Expecting a list/tuple of model instances
            if not isinstance(value, (list, tuple)):
                # Detailed internal logging for debugging
                logger.exception(
                    f"Type mismatch for list field '{getattr(self, 'name', 'unknown')}': "
                    f"expected=list/tuple, got={type(value).__name__}, value={value!r}, "
                    f"pydantic_model={getattr(self, 'pydantic_model', None)!r}"
                )
                # User-friendly error message for API response
                raise custom_exceptions.ServiceUnavailable(
                    "Invalid data format: expected a list of items but received a different data type. "
                    "Please provide data as an array."
                )
            data = []
            ModelClass = self.pydantic_model[0]
            for idx, model_instance in enumerate(value):
                if not isinstance(model_instance, ModelClass):
                    # Detailed internal logging for debugging
                    logger.exception(
                        f"Invalid item type at index {idx} for field '{getattr(self, 'name', 'unknown')}': "
                        f"expected={ModelClass.__name__}, got={type(model_instance).__name__}, "
                        f"item_value={model_instance!r}, pydantic_model={getattr(self, 'pydantic_model', None)!r}"
                    )
                    # User-friendly error message for API response
                    raise custom_exceptions.ServiceUnavailable(
                        f"Invalid data at position {idx + 1}: expected a valid data "
                        "object but received incompatible data type. "
                        "Please ensure all items in the array are properly formatted."
                    )
                data.append(model_instance.model_dump(mode="json", by_alias=True))
        elif isinstance(self.pydantic_model, dict):
            # Expecting a polymorphic model (dict with "type" and "data")
            if not isinstance(value, self.base_type_model):
                # Detailed internal logging for debugging
                logger.exception(
                    f"Type mismatch for polymorphic field '{getattr(self, 'name', 'unknown')}': "
                    f"expected={getattr(self, 'base_type_model', 'BaseTypeModel').__name__}, "
                    f"got={type(value).__name__}, value={value!r}, "
                    f"pydantic_model={getattr(self, 'pydantic_model', None)!r}"
                )
                # User-friendly error message for API response
                raise custom_exceptions.ServiceUnavailable(
                    "Invalid data format: expected a properly typed data object. "
                    "Please ensure the data includes the correct type information."
                )
            _type = getattr(value, "object_type", getattr(value, "type", None))
            if not _type:
                # Detailed internal logging for debugging
                logger.exception(
                    f"Missing object_type attribute for polymorphic field '{getattr(self, 'name', 'unknown')}': "
                    f"value={value!r}, pydantic_model={getattr(self, 'pydantic_model', None)!r}"
                )
                # User-friendly error message for API response
                raise custom_exceptions.ServiceUnavailable(
                    "Invalid data format: missing required 'type' field. "
                    "Please specify the data type in your request."
                )
            model_type = _type
            ModelClass = self.pydantic_model.get(model_type)
            if ModelClass is None:
                # Detailed internal logging for debugging
                logger.exception(
                    f"Invalid model type for polymorphic field '{getattr(self, 'name', 'unknown')}': "
                    f"model_type='{model_type}', valid_types={list(getattr(self, 'pydantic_model', {}).keys())}, "
                    f"value={value!r}, pydantic_model={getattr(self, 'pydantic_model', None)!r}"
                )
                # User-friendly error message for API response
                valid_types = list(getattr(self, "pydantic_model", {}).keys())
                raise custom_exceptions.ServiceUnavailable(
                    f"Invalid data type: '{model_type}' is not supported. "
                    f"Please use one of the following types: {', '.join(valid_types)}."
                )
            if not isinstance(value, ModelClass):
                # Detailed internal logging for debugging
                logger.exception(
                    f"Type mismatch for polymorphic field '{getattr(self, 'name', 'unknown')}': "
                    f"model_type='{model_type}', expected={ModelClass.__name__}, "
                    f"got={type(value).__name__}, value={value!r}, "
                    f"pydantic_model={getattr(self, 'pydantic_model', None)!r}"
                )
                # User-friendly error message for API response
                raise custom_exceptions.ServiceUnavailable(
                    f"Invalid data for type '{model_type}': the provided data does not match the expected structure. "
                    "Please verify the data format and try again."
                )
            data = {
                "type": model_type,
                "data": value.model_dump(mode="json", by_alias=True),
            }
        elif issubclass(self.pydantic_model, (BaseModel, self.base_type_model)):
            # Expecting a single Pydantic model instance
            if not isinstance(value, BaseModel):
                if not value:
                    return value
                # Detailed internal logging for debugging
                logger.exception(
                    f"Invalid value type for single model field '{getattr(self, 'name', 'unknown')}': "
                    f"expected=BaseModel instance, got={type(value).__name__}, value={value!r}, "
                    f"pydantic_model={getattr(self, 'pydantic_model', None)!r}"
                )
                # User-friendly error message for API response
                raise custom_exceptions.ServiceUnavailable(
                    "Invalid data format: expected a valid data object. "
                    "Please ensure the data is properly formatted."
                )
            return value.model_dump_json(by_alias=True)
        else:
            # Detailed internal logging for debugging
            logger.exception(
                f"Invalid pydantic_model configuration for field '{getattr(self, 'name', 'unknown')}': "
                f"pydantic_model={getattr(self, 'pydantic_model', None)!r}, "
                f"Field type: {self.__class__.__name__}"
            )
            # User-friendly error message (this is an internal configuration error)
            raise custom_exceptions.ServiceUnavailable(
                "Data processing error: invalid field configuration detected. "
                "Please contact support if this issue persists."
            )
        try:
            return json.dumps(
                data,
            )
        except Exception as e:
            # Detailed internal logging for debugging
            logger.exception(
                f"JSON encoding error for field '{getattr(self, 'name', 'unknown')}': "
                f"data={data!r}, error={e!r}, "
                f"pydantic_model={getattr(self, 'pydantic_model', None)!r}"
            )
            # User-friendly error message (this is likely an internal processing error)
            raise custom_exceptions.ServiceUnavailable(
                "Data processing error: failed to encode data for storage. "
                "Please contact support if this issue persists."
            ) from e

    def value_to_string(self, obj) -> str:
        """
        Serializes the field's value from the given model instance to a JSON
        string for use in fixtures or serialization.

        Args:
            obj: The model instance from which to retrieve the field value.

        Returns:
            str: The JSON-encoded string representation of the field's value.

        Raises:
            ValueError: If the value cannot be serialized due to a type mismatch or invalid structure.
        """
        try:
            value = self.value_from_object(obj)
            return self.get_prep_value(value)
        except Exception as exc:
            # Detailed internal logging for debugging
            logger.exception(
                f"Value serialization error in value_to_string for field '{getattr(self, 'name', 'unknown')}': "
                f"object={obj!r}, error={exc!r}, "
                f"pydantic_model={getattr(self, 'pydantic_model', None)!r}, "
                f"Field type: {self.__class__.__name__}"
            )
            # User-friendly error message (this is likely an internal processing error)
            raise custom_exceptions.ServiceUnavailable(
                "Data processing error: failed to serialize field value. "
                "Please contact support if this issue persists."
            ) from exc


class PydanticModelSerializerField(serializers.JSONField):
    """
    A Django REST Framework serializer field for Pydantic models.

    This field extends DRF's JSONField to provide seamless serialization and deserialization
    of Pydantic models in API endpoints. It handles conversion between JSON data and Pydantic
    model instances, supporting the same configurations as PydanticModelField.

    Features:
        - Automatic validation using Pydantic model schemas
        - Support for single models, lists of models, and polymorphic models
        - Integration with DRF's validation system
        - Clean JSON output for API responses
        - Automatic type discrimination for polymorphic models

    Args:
        pydantic_model: The Pydantic model(s) to use for validation. Can be:
            - A single Pydantic model class
            - A tuple/list containing a single model class (for lists of instances)
            - A dict mapping type names to model classes (for polymorphic models)

    Examples:
        >>> class TestModelRetrieve(serializers.ModelSerializer):
        ...     data = PydanticModelSerializerField(
        ...         pydantic_model=TestModel.data.field.pydantic_model
        ...     )
        ...     list_data = PydanticModelSerializerField(
        ...         pydantic_model=TestModel.list_data.field.pydantic_model
        ...     )
        ...     type_data = PydanticModelSerializerField(
        ...         pydantic_model=TestModel.type_data.field.pydantic_model
        ...     )
        ...
        ...     class Meta:
        ...         model = TestModel
        ...         fields = ["data", "list_data", "type_data"]

    Polymorphic Model Output:
        For polymorphic models, the output structure is:
        {
            "type": "WORD_PLAY",
            "data": {
                "key1": "value1",
            }
        }

    Raises:
        serializers.ValidationError: If validation fails during serialization or deserialization.
    """

    def __init__(
        self,
        pydantic_model: type[BaseModel]
        | tuple[type[BaseModel]]
        | dict[str, type[BaseModel]]
        | None = None,
        *args,
        **kwargs,
    ):
        """
        Initialize a PydanticModelSerializerField for DRF serializers.

        Args:
            pydantic_model (type[BaseModel] | tuple[type[BaseModel]] | dict[str, type[BaseModel]] | None, optional):
                The Pydantic model(s) to use for validation and serialization.
                Can be a single model, a tuple/list of models, or a dict mapping type names to models.
            *args: Additional positional arguments for the parent class.
            **kwargs: Additional keyword arguments for the parent class.

        Raises:
            ValueError: If the provided pydantic_model is invalid.
        """
        self.pydantic_model = pydantic_model
        try:
            super().__init__(*args, **kwargs)
        except Exception as exc:
            # Detailed internal logging for debugging
            logger.exception(
                f"PydanticModelSerializerField initialization failed: "
                f"pydantic_model={pydantic_model!r}, error={exc!r}, "
                f"args={args!r}, kwargs={kwargs!r}, "
                f"Field type: {self.__class__.__name__}"
            )
            # User-friendly error message (this is an internal configuration error)
            raise custom_exceptions.ServiceUnavailable(
                "Field configuration error: failed to initialize serializer field. "
                "Please contact support if this issue persists."
            ) from exc

    def to_internal_value(self, data: dict):
        """
        Convert incoming JSON data to Pydantic model instances for internal use.

        This method deserializes JSON data received from API requests into the appropriate
        Pydantic model instances based on the field's configuration. It handles single models,
        lists of models, and polymorphic models with type discrimination.

        Args:
            data (dict): The incoming JSON data to be deserialized. The structure depends
                on the pydantic_model configuration:
                - For single models: dict with model fields
                - For list models: list of dicts with model fields
                - For polymorphic models: dict with "type" field and model fields

        Returns:
            BaseModel | list[BaseModel] | dict: The deserialized Pydantic model instance(s)
                or the original data if no pydantic_model is configured.

        Raises:
            serializers.ValidationError: If the data cannot be validated against the Pydantic
                model schema, or if an invalid type is provided for polymorphic models.

        Examples:
            >>> # Single model
            >>> field.to_internal_value({"name": "John", "age": 30})
            >>> # Returns: UserModel(name="John", age=30)

            >>> # List of models
            >>> field.to_internal_value([{"name": "John"}, {"name": "Jane"}])
            >>> # Returns: [UserModel(name="John"), UserModel(name="Jane")]

            >>> # Polymorphic model
            >>> field.to_internal_value({"type": "user", "name": "John", "age": 30})
            >>> # Returns: UserModel(name="John", age=30)
        """
        try:
            if self.pydantic_model:
                if isinstance(self.pydantic_model, (list, tuple)):
                    deserialized_data = []
                    ModelClass = self.pydantic_model[0]
                    for item in data:
                        deserialized_data.append(ModelClass(**item))
                    return deserialized_data
                elif isinstance(self.pydantic_model, dict):
                    ModelClass = self.pydantic_model.get(data.get("type"))
                    if not ModelClass:
                        # User-friendly error message for API response
                        raise serializers.ValidationError(
                            f"Invalid data type: '{data.get('type')}' is not supported. "
                            "Please specify a valid data type."
                        )
                    return ModelClass(**data)
                elif issubclass(self.pydantic_model, (BaseModel, BaseTypeModel)):

                    return self.pydantic_model(**data)
                else:
                    # User-friendly error message for API response
                    raise serializers.ValidationError(
                        "Invalid data format: the provided data structure is not supported. "
                        "Please check the API documentation for the correct format."
                    )
            return data
        except (PydanticValidationError, custom_exceptions.ServiceUnavailable):
            # User-friendly error message for API response - convert Pydantic errors to readable format
            raise serializers.ValidationError(
                "Invalid data: the provided data does not match the required format. "
                "Please check the required fields and data types."
            )

    def to_representation(self, value) -> str | dict | list | None:
        """
        Serializes the internal value (Pydantic model instance(s)) to a JSON-compatible Python object
        for use in API responses.

        Args:
            value: The internal value to serialize, which may be a Pydantic model instance, a list of instances,
                   or a dict, depending on the field configuration.

        Returns:
            str | dict | list | None: The serialized representation suitable for JSON encoding.

        Raises:
            serializers.ValidationError: If serialization fails due to a type mismatch or invalid structure,
                with a comprehensive error message indicating the root cause.
        """
        try:
            # Use the PydanticModelField logic to serialize the value to a JSON string
            data = PydanticModelField(self.pydantic_model).get_prep_value(value)
            if isinstance(data, str):
                data = json.loads(transform_data(data))
            # If the data is a dict with "type" and "data" keys, and the type matches the nested data's type,
            # flatten the structure for cleaner API output
            if (
                data
                and isinstance(data, dict)
                and sorted(list(data.keys())) == sorted(["data", "type"])
                and data.get("type")
                and data.get("type") == data.get("data", {}).get("type")
            ):
                data = data.get("data")
            return data
        except Exception as exc:
            # Detailed internal logging for debugging
            logger.exception(
                f"Serialization error in to_representation for field '{getattr(self, 'field_name', 'unknown')}': "
                f"value={value!r}, error={exc!r}, "
                f"pydantic_model={getattr(self, 'pydantic_model', None)!r}, "
                f"Field type: {self.__class__.__name__}"
            )
            # User-friendly error message for API response
            raise custom_exceptions.ServiceUnavailable(
                "Data processing error: failed to serialize data for response. "
                "Please contact support if this issue persists."
            ) from exc

    def _format_validation_error(self, error: Exception) -> list[dict[str, str]] | str:
        """
        Formats a PydanticValidationError or any other exception into a comprehensive error message
        that helps developers understand the root cause of the error.

        Args:
            error (Exception): The exception to format, typically a PydanticValidationError.

        Returns:
            list[dict[str, str]] | str: A list of error details (field and message) if available,
            or a string with the error message.
        """
        if isinstance(error, PydanticValidationError):
            error_messages = []
            for err in error.errors():
                # Each err is a dict with keys like 'loc', 'msg', 'type'
                field_path = ".".join(str(loc) for loc in err.get("loc", []))
                message = (
                    f"{err.get('msg', '')} (type: {err.get('type', '')})"
                    if "type" in err
                    else err.get("msg", "")
                )
                error_messages.append(
                    {
                        "field": field_path,
                        "message": (
                            f"Validation error on field '{field_path}': {message}. "
                            f"Input value: {err.get('input', 'N/A')}. "
                            "Check that the value matches the expected type and constraints."
                        ),
                    }
                )
            return error_messages
        # For non-Pydantic errors, return a detailed string
        return (
            f"Unexpected error: {str(error)}. "
            "Check the stack trace and ensure the input data and model configuration are correct."
        )
