import json as json_lib
import logging
from typing import Type

import google.genai as genai
from google.genai import types as genai_types
from google.genai.errors import APIError
from pydantic import ValidationError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
from typing_extensions import override

from askui.models.askui.inference_api import AskUiInferenceApiSettings
from askui.models.askui.retry_utils import (
    RETRYABLE_HTTP_STATUS_CODES,
    wait_for_retry_after_header,
)
from askui.models.exceptions import QueryNoResponseError, QueryUnexpectedResponseError
from askui.models.models import GetModel, ModelName
from askui.models.shared.prompts import SYSTEM_PROMPT_GET
from askui.models.types.response_schemas import ResponseSchema, to_response_schema
from askui.utils.excel_utils import OfficeDocumentSource
from askui.utils.image_utils import ImageSource
from askui.utils.source_utils import Source

logger = logging.getLogger(__name__)

ASKUI_MODEL_CHOICE_PREFIX = "askui/"
ASKUI_MODEL_CHOICE_PREFIX_LEN = len(ASKUI_MODEL_CHOICE_PREFIX)
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024


def _is_retryable_error(exception: BaseException) -> bool:
    """Check if the exception is a retryable error."""
    if isinstance(exception, APIError):
        return exception.code in RETRYABLE_HTTP_STATUS_CODES
    return False


def _extract_model_id(model_choice: str) -> str:
    if model_choice == ModelName.ASKUI:
        return ModelName.GEMINI__2_5__FLASH
    if model_choice.startswith(ASKUI_MODEL_CHOICE_PREFIX):
        return model_choice[ASKUI_MODEL_CHOICE_PREFIX_LEN:]
    return model_choice


class AskUiGoogleGenAiApi(GetModel):
    def __init__(self, settings: AskUiInferenceApiSettings | None = None) -> None:
        self._settings = settings or AskUiInferenceApiSettings()
        self._client = genai.Client(
            vertexai=True,
            api_key="DummyValueRequiredByGenaiClient",
            http_options=genai_types.HttpOptions(
                base_url=f"{self._settings.base_url}/proxy/vertexai",
                headers={
                    "Authorization": self._settings.authorization_header,
                },
            ),
        )

    @retry(
        stop=stop_after_attempt(4),  # 3 retries
        wait=wait_for_retry_after_header(
            wait_exponential(multiplier=30, min=30, max=120)
        ),  # retry after or as a fallback 30s, 60s, 120s
        retry=retry_if_exception(_is_retryable_error),
        reraise=True,
    )
    @override
    def get(
        self,
        query: str,
        source: Source,
        response_schema: Type[ResponseSchema] | None,
        model_choice: str,
    ) -> ResponseSchema | str:
        try:
            _response_schema = to_response_schema(response_schema)
            json_schema = _response_schema.model_json_schema()
            logger.debug(
                "Json schema used for response",
                extra={"json_schema": json_lib.dumps(json_schema)},
            )
            part = self._create_genai_part_from_source(source)
            content = genai_types.Content(
                parts=[
                    part,
                    genai_types.Part.from_text(text=query),
                ],
                role="user",
            )
            generate_content_response = self._client.models.generate_content(
                model=f"models/{_extract_model_id(model_choice)}",
                contents=content,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": _response_schema,
                    "system_instruction": SYSTEM_PROMPT_GET,
                },
            )
            json_str = generate_content_response.text
            if json_str is None:
                raise QueryNoResponseError(
                    message="No response from the model", query=query
                )
            try:
                return _response_schema.model_validate_json(json_str).root
            except ValidationError as e:
                error_message = str(e.errors())
                raise QueryUnexpectedResponseError(
                    message=f"Unexpected response from the model: {error_message}",
                    query=query,
                    response=json_str,
                ) from e
        except RecursionError as e:
            error_message = (
                "Recursive response schemas are not supported by AskUiGoogleGenAiApi"
            )
            raise NotImplementedError(error_message) from e

    def _create_genai_part_from_source(self, source: Source) -> genai_types.Part:
        """Create a genai Part from a Source object.

        Only ImageSource and PdfSource are currently supported.

        Args:
            source (Source): The source object to convert.

        Returns:
            genai_types.Part: The genai Part object.

        Raises:
            NotImplementedError: If source type is not ImageSource or PdfSource.
            ValueError: If the source data exceeds the size limit.
        """
        if isinstance(source, ImageSource):
            data = source.to_bytes()
            if len(data) > MAX_FILE_SIZE_BYTES:
                _err_msg = (
                    f"Image file size exceeds the limit of {MAX_FILE_SIZE_BYTES} bytes."
                )
                raise ValueError(_err_msg)
            return genai_types.Part.from_bytes(
                data=data,
                mime_type="image/png",
            )
        if isinstance(source, OfficeDocumentSource):
            with source.reader as r:
                data = r.read()
                return genai_types.Part.from_text(text=data.decode())
        with source.reader as r:
            data = r.read()
            if len(data) > MAX_FILE_SIZE_BYTES:
                _err_msg = (
                    f"PDF file size exceeds the limit of {MAX_FILE_SIZE_BYTES} bytes."
                )
                raise ValueError(_err_msg)
            return genai_types.Part.from_bytes(
                data=data,
                mime_type="application/pdf",
            )
