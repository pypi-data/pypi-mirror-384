from typing import Any

from askui.locators.locators import Locator


class AutomationError(Exception):
    """Exception raised when the automation step cannot complete.

    Args:
        message (str): The error message.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class QueryNoResponseError(AutomationError):
    """Exception raised when a query does not return a response.

    Args:
        message (str): The error message.
        query (str): The query that was made.
    """

    def __init__(self, message: str, query: str):
        self.message = message
        self.query = query
        super().__init__(self.message)


class ElementNotFoundError(AutomationError):
    """Exception raised when an element cannot be located.

    Args:
        locator (str | Locator): The locator that was used.
        locator_serialized (Any): The locator serialized for the specific model
    """

    def __init__(self, locator: str | Locator, locator_serialized: Any) -> None:
        self.locator = locator
        self.locator_serialized = locator_serialized
        super().__init__(f"Element not found: {self.locator}")


class QueryUnexpectedResponseError(AutomationError):
    """Exception raised when a query returns an unexpected response.

    Args:
        message (str): The error message.
        query (str): The query that was made.
        response (Any): The response that was received.
    """

    def __init__(self, message: str, query: str, response: Any):
        self.message = message
        self.query = query
        self.response = response
        super().__init__(self.message)


class ModelNotFoundError(AutomationError):
    """Exception raised when a model could not be found within available models.

    Args:
        model_choice (str): The model choice.
    """

    def __init__(
        self,
        model_choice: str,
        message: str | None = None,
    ):
        self.model_choice = model_choice
        super().__init__(
            f"Model not found: {model_choice}" if message is None else message
        )


class ModelTypeMismatchError(ModelNotFoundError):
    """Exception raised when a model is not of the expected type.

    Args:
        model_choice (str): The model choice.
        expected_type (type): The expected type.
        actual_type (type): The actual type.
    """

    def __init__(
        self,
        model_choice: str,
        expected_type: type,
        actual_type: type,
    ):
        self.expected_type = expected_type
        self.actual_type = actual_type
        super().__init__(
            model_choice=model_choice,
            message=f'Model "{model_choice}" is an instance of {actual_type.mro()}, '
            f"expected it to be an instance of {expected_type.mro()}",
        )


class MaxTokensExceededError(AutomationError):
    """Exception raised when the model stops due to reaching the maximum token limit.

    Args:
        max_tokens (int): The maximum token limit that was exceeded.
        message (str, optional): Custom error message. If not provided, a default
            message will be generated.
    """

    def __init__(self, max_tokens: int, message: str | None = None):
        self.max_tokens = max_tokens
        error_msg = (
            f"Model stopped due to reaching maximum token limit of {max_tokens} tokens"
            if message is None
            else message
        )
        super().__init__(error_msg)


class ModelRefusalError(AutomationError):
    """Exception raised when the model refuses to process the request.

    Args:
        message (str, optional): Custom error message. If not provided, a default
            message will be generated.
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            "Model refused to process the request" if message is None else message
        )
