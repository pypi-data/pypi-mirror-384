import base64
import json as json_lib
import logging
from functools import cached_property
from typing import Any, Type, cast

import httpx
from anthropic import (
    NOT_GIVEN,
    Anthropic,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    NotGiven,
)
from anthropic.types import AnthropicBetaParam
from anthropic.types.beta import (
    BetaMessageParam,
    BetaTextBlockParam,
    BetaThinkingConfigParam,
    BetaToolChoiceParam,
)
from pydantic import UUID4, Field, HttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
from typing_extensions import Self, override

from askui.locators.locators import Locator
from askui.locators.serializers import AskUiLocatorSerializer, AskUiSerializedLocator
from askui.models.askui.retry_utils import (
    RETRYABLE_HTTP_STATUS_CODES,
    wait_for_retry_after_header,
)
from askui.models.exceptions import ElementNotFoundError
from askui.models.models import GetModel, LocateModel, ModelComposition, PointList
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.messages_api import MessagesApi
from askui.models.shared.settings import MessageSettings
from askui.models.shared.tools import ToolCollection
from askui.models.types.response_schemas import ResponseSchema
from askui.utils.excel_utils import OfficeDocumentSource
from askui.utils.image_utils import ImageSource
from askui.utils.pdf_utils import PdfSource
from askui.utils.source_utils import Source

from ..types.response_schemas import to_response_schema

logger = logging.getLogger(__name__)


class AskUiInferenceApiSettings(BaseSettings):
    model_config = SettingsConfigDict(
        validate_by_name=True,
        env_prefix="ASKUI__",
        env_nested_delimiter="__",
        arbitrary_types_allowed=True,
    )

    inference_endpoint: HttpUrl = Field(
        default_factory=lambda: HttpUrl("https://inference.askui.com"),  # noqa: F821
        validation_alias="ASKUI_INFERENCE_ENDPOINT",
    )
    messages: MessageSettings = Field(default_factory=MessageSettings)
    authorization: SecretStr | NotGiven = Field(
        default=NOT_GIVEN,
        description=(
            "The authorization header to use for the AskUI Inference API. "
            "If not provided, the token will be used to generate the header."
        ),
    )
    token: SecretStr | NotGiven = Field(
        default=NOT_GIVEN,
        validation_alias="ASKUI_TOKEN",
    )
    workspace_id: UUID4 = Field(
        default=...,
        validation_alias="ASKUI_WORKSPACE_ID",
    )

    @model_validator(mode="after")
    def check_authorization(self) -> "Self":
        if self.authorization == NOT_GIVEN and self.token == NOT_GIVEN:
            error_message = (
                'Either authorization ("ASKUI__AUTHORIZATION" environment variable) '
                'or token ("ASKUI_TOKEN" environment variable) must be provided'
            )
            raise ValueError(error_message)
        return self

    @property
    def authorization_header(self) -> str:
        if self.authorization:
            return self.authorization.get_secret_value()
        assert not isinstance(self.token, NotGiven), "Token is not set"
        token_str = self.token.get_secret_value()
        token_base64 = base64.b64encode(token_str.encode()).decode()
        return f"Basic {token_base64}"

    @property
    def base_url(self) -> str:
        # NOTE(OS): Pydantic parses urls with trailing slashes
        # meaning "https://inference.askui.com" turns into -> "https://inference.askui.com/"
        # https://github.com/pydantic/pydantic/issues/7186
        return f"{self.inference_endpoint}api/v1/workspaces/{self.workspace_id}"


def _is_retryable_error(exception: BaseException) -> bool:
    """Check if the exception is a retryable error."""
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code in RETRYABLE_HTTP_STATUS_CODES
    if isinstance(exception, APIStatusError):
        return exception.status_code in RETRYABLE_HTTP_STATUS_CODES
    return isinstance(exception, (APIConnectionError, APITimeoutError))


class AskUiInferenceApi(GetModel, LocateModel, MessagesApi):
    def __init__(
        self,
        locator_serializer: AskUiLocatorSerializer,
        settings: AskUiInferenceApiSettings | None = None,
    ) -> None:
        self._settings_default = settings
        self._locator_serializer = locator_serializer

    @cached_property
    def _settings(self) -> AskUiInferenceApiSettings:
        if self._settings_default is None:
            return AskUiInferenceApiSettings()
        return self._settings_default

    @cached_property
    def _http_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=f"{self._settings.base_url}",
            headers={
                "Content-Type": "application/json",
                "Authorization": self._settings.authorization_header,
            },
        )

    @cached_property
    def _anthropic_client(self) -> Anthropic:
        return Anthropic(
            api_key="DummyValueRequiredByAnthropicClient",
            base_url=f"{self._settings.base_url}/proxy/anthropic",
            default_headers={
                "Authorization": self._settings.authorization_header,
            },
        )

    @retry(
        stop=stop_after_attempt(4),  # 3 retries
        wait=wait_for_retry_after_header(
            wait_exponential(multiplier=30, min=30, max=120)
        ),  # retry after or as a fallback 30s, 60s, 120s
        retry=retry_if_exception(_is_retryable_error),
        reraise=True,
    )
    def _post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> httpx.Response:
        try:
            response = self._http_client.post(
                path,
                json=json,
                timeout=timeout,
            )
            response.raise_for_status()
        except Exception as e:  # noqa: BLE001
            if (
                isinstance(e, httpx.HTTPStatusError)
                and 400 <= e.response.status_code < 500
            ):
                raise ValueError(e.response.text) from e
            if _is_retryable_error(e):
                logger.debug("Retryable error", extra={"error": str(e)})
            raise
        else:
            return response

    @override
    def locate(
        self,
        locator: str | Locator,
        image: ImageSource,
        model_choice: ModelComposition | str,
    ) -> PointList:
        serialized_locator = (
            self._locator_serializer.serialize(locator=locator)
            if isinstance(locator, Locator)
            else AskUiSerializedLocator(customElements=[], instruction=locator)
        )
        logger.debug(
            "Locator serialized",
            extra={"serialized_locator": json_lib.dumps(serialized_locator)},
        )
        json: dict[str, Any] = {
            "image": image.to_data_url(),
            "instruction": f"get element {serialized_locator['instruction']}",
        }
        if "customElements" in serialized_locator:
            json["customElements"] = serialized_locator["customElements"]
        if isinstance(model_choice, ModelComposition):
            json["modelComposition"] = model_choice.model_dump(by_alias=True)
            logger.debug(
                "Model composition",
                extra={"modelComposition": json_lib.dumps(json["modelComposition"])},
            )
        response = self._post(path="/inference", json=json)
        content = response.json()
        assert content["type"] == "DETECTED_ELEMENTS", (
            f"Received unknown content type {content['type']}"
        )
        detected_elements = content["data"]["detected_elements"]
        if len(detected_elements) == 0:
            raise ElementNotFoundError(locator, serialized_locator)

        return [
            (
                int((element["bndbox"]["xmax"] + element["bndbox"]["xmin"]) / 2),
                int((element["bndbox"]["ymax"] + element["bndbox"]["ymin"]) / 2),
            )
            for element in detected_elements
        ]

    @override
    def get(
        self,
        query: str,
        source: Source,
        response_schema: Type[ResponseSchema] | None,
        model_choice: str,
    ) -> ResponseSchema | str:
        if isinstance(source, (PdfSource, OfficeDocumentSource)):
            err_msg = (
                f"PDF or Office Document processing is not supported for the model: "
                f"{model_choice}"
            )
            raise NotImplementedError(err_msg)
        json: dict[str, Any] = {
            "image": source.to_data_url(),
            "prompt": query,
        }
        _response_schema = to_response_schema(response_schema)
        json_schema = _response_schema.model_json_schema()
        json["config"] = {"json_schema": json_schema}
        logger.debug(
            "Json schema used for response",
            extra={"json_schema": json_lib.dumps(json["config"]["json_schema"])},
        )
        response = self._post(path="/vqa/inference", json=json)
        content = response.json()
        data = content["data"]["response"]
        validated_response = _response_schema.model_validate(data)
        return validated_response.root

    @override
    @retry(
        stop=stop_after_attempt(4),  # 3 retries
        wait=wait_for_retry_after_header(
            wait_exponential(multiplier=30, min=30, max=120)
        ),  # retry after or as a fallback 30s, 60s, 120s
        retry=retry_if_exception(_is_retryable_error),
        reraise=True,
    )
    def create_message(
        self,
        messages: list[MessageParam],
        model: str,
        tools: ToolCollection | NotGiven = NOT_GIVEN,
        max_tokens: int | NotGiven = NOT_GIVEN,
        betas: list[AnthropicBetaParam] | NotGiven = NOT_GIVEN,
        system: str | list[BetaTextBlockParam] | NotGiven = NOT_GIVEN,
        thinking: BetaThinkingConfigParam | NotGiven = NOT_GIVEN,
        tool_choice: BetaToolChoiceParam | NotGiven = NOT_GIVEN,
    ) -> MessageParam:
        response = self._anthropic_client.beta.messages.create(
            messages=[
                cast("BetaMessageParam", message.model_dump(exclude={"stop_reason"}))
                for message in messages
            ],
            tools=tools.to_params() if tools else NOT_GIVEN,
            max_tokens=max_tokens or self._settings.messages.max_tokens,
            model=model,
            betas=betas
            if not isinstance(betas, NotGiven)
            else self._settings.messages.betas,
            system=system or self._settings.messages.system,
            thinking=thinking or self._settings.messages.thinking,
            tool_choice=tool_choice or self._settings.messages.tool_choice,
            timeout=300.0,
        )
        return MessageParam.model_validate(response.model_dump())
