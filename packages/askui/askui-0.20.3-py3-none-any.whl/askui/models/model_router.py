import functools
import logging
from typing import Type, overload

from typing_extensions import Literal

from askui.locators.locators import Locator
from askui.locators.serializers import AskUiLocatorSerializer, VlmLocatorSerializer
from askui.models.anthropic.messages_api import AnthropicMessagesApi
from askui.models.askui.ai_element_utils import AiElementCollection
from askui.models.askui.get_model import AskUiGetModel
from askui.models.askui.google_genai_api import AskUiGoogleGenAiApi
from askui.models.askui.model_router import AskUiModelRouter
from askui.models.exceptions import ModelNotFoundError, ModelTypeMismatchError
from askui.models.huggingface.spaces_api import HFSpacesHandler
from askui.models.models import (
    MODEL_TYPES,
    ActModel,
    GetModel,
    LocateModel,
    Model,
    ModelComposition,
    ModelName,
    ModelRegistry,
    PointList,
)
from askui.models.shared.agent import Agent
from askui.models.shared.agent_message_param import MessageParam
from askui.models.shared.agent_on_message_cb import OnMessageCb
from askui.models.shared.facade import ModelFacade
from askui.models.shared.settings import ActSettings
from askui.models.shared.tools import ToolCollection
from askui.models.types.response_schemas import ResponseSchema
from askui.reporting import NULL_REPORTER, CompositeReporter, Reporter
from askui.utils.image_utils import ImageSource
from askui.utils.source_utils import Source

from .askui.inference_api import AskUiInferenceApi
from .ui_tars_ep.ui_tars_api import UiTarsApiHandler, UiTarsApiHandlerSettings

logger = logging.getLogger(__name__)


def initialize_default_model_registry(  # noqa: C901
    reporter: Reporter = NULL_REPORTER,
) -> ModelRegistry:
    @functools.cache
    def vlm_locator_serializer() -> VlmLocatorSerializer:
        return VlmLocatorSerializer()

    @functools.cache
    def anthropic_facade() -> ModelFacade:
        messages_api = AnthropicMessagesApi(
            locator_serializer=vlm_locator_serializer(),
        )
        computer_agent = Agent(
            messages_api=messages_api,
            reporter=reporter,
        )
        return ModelFacade(
            act_model=computer_agent,
            get_model=messages_api,
            locate_model=messages_api,
        )

    @functools.cache
    def askui_google_genai_api() -> AskUiGoogleGenAiApi:
        return AskUiGoogleGenAiApi()

    @functools.cache
    def askui_inference_api() -> AskUiInferenceApi:
        return AskUiInferenceApi(
            locator_serializer=AskUiLocatorSerializer(
                ai_element_collection=AiElementCollection(),
                reporter=reporter,
            ),
        )

    @functools.cache
    def askui_model_router() -> AskUiModelRouter:
        return AskUiModelRouter(
            inference_api=askui_inference_api(),
        )

    @functools.cache
    def askui_get_model() -> AskUiGetModel:
        return AskUiGetModel(
            google_genai_api=askui_google_genai_api(),
            inference_api=askui_inference_api(),
        )

    @functools.cache
    def askui_facade() -> ModelFacade:
        computer_agent = Agent(
            messages_api=askui_inference_api(),
            reporter=reporter,
        )
        return ModelFacade(
            act_model=computer_agent,
            get_model=askui_get_model(),
            locate_model=askui_model_router(),
        )

    @functools.cache
    def hf_spaces_handler() -> HFSpacesHandler:
        return HFSpacesHandler(
            locator_serializer=vlm_locator_serializer(),
        )

    @functools.cache
    def tars_handler() -> UiTarsApiHandler:
        try:
            settings = UiTarsApiHandlerSettings()
            locator_serializer = VlmLocatorSerializer()
            return UiTarsApiHandler(
                reporter=reporter,
                settings=settings,
                locator_serializer=locator_serializer,
            )
        except Exception as e:  # noqa: BLE001
            error_msg = f"Failed to initialize TARS model: {e}"
            raise ValueError(error_msg)  # noqa: B904

    return {
        ModelName.CLAUDE__SONNET__4__20250514: anthropic_facade,
        ModelName.ASKUI: askui_facade,
        ModelName.ASKUI__GEMINI__2_5__FLASH: askui_google_genai_api,
        ModelName.ASKUI__GEMINI__2_5__PRO: askui_google_genai_api,
        ModelName.ASKUI__AI_ELEMENT: askui_model_router,
        ModelName.ASKUI__COMBO: askui_model_router,
        ModelName.ASKUI__OCR: askui_model_router,
        ModelName.ASKUI__PTA: askui_model_router,
        ModelName.CLAUDE__SONNET__4__20250514: anthropic_facade,
        ModelName.HF__SPACES__ASKUI__PTA_1: hf_spaces_handler,
        ModelName.HF__SPACES__QWEN__QWEN2_VL_2B_INSTRUCT: hf_spaces_handler,
        ModelName.HF__SPACES__QWEN__QWEN2_VL_7B_INSTRUCT: hf_spaces_handler,
        ModelName.HF__SPACES__OS_COPILOT__OS_ATLAS_BASE_7B: hf_spaces_handler,
        ModelName.HF__SPACES__SHOWUI__2B: hf_spaces_handler,
        ModelName.TARS: tars_handler,
    }


class ModelRouter:
    def __init__(
        self,
        reporter: Reporter | None = None,
        models: ModelRegistry | None = None,
    ):
        self._reporter = reporter or CompositeReporter()
        self._models = models or {}

    @overload
    def _get_model(self, model_choice: str, model_type: Literal["act"]) -> ActModel: ...

    @overload
    def _get_model(self, model_choice: str, model_type: Literal["get"]) -> GetModel: ...

    @overload
    def _get_model(
        self, model_choice: str, model_type: Literal["locate"]
    ) -> LocateModel: ...

    def _get_model(
        self, model_choice: str, model_type: Literal["act", "get", "locate"]
    ) -> Model:
        if model_choice not in self._models:
            raise ModelNotFoundError(model_choice)

        model_or_model_factory = self._models[model_choice]
        if not isinstance(model_or_model_factory, (ActModel, GetModel, LocateModel)):
            model = model_or_model_factory()
        else:
            model = model_or_model_factory

        if not isinstance(model, MODEL_TYPES[model_type]):
            raise ModelTypeMismatchError(
                model_choice,
                MODEL_TYPES[model_type],
                type(model),
            )

        return model

    def act(
        self,
        messages: list[MessageParam],
        model_choice: str,
        on_message: OnMessageCb | None = None,
        tools: ToolCollection | None = None,
        settings: ActSettings | None = None,
    ) -> None:
        m = self._get_model(model_choice, "act")
        logger.debug(
            'Routing "act" to model',
            extra={"model_choice": model_choice},
        )
        return m.act(
            messages=messages,
            model_choice=model_choice,
            on_message=on_message,
            settings=settings,
            tools=tools,
        )

    def get(
        self,
        query: str,
        source: Source,
        model_choice: str,
        response_schema: Type[ResponseSchema] | None = None,
    ) -> ResponseSchema | str:
        m = self._get_model(model_choice, "get")
        logger.debug(
            'Routing "get" to model',
            extra={"model_choice": model_choice},
        )
        return m.get(query, source, response_schema, model_choice)

    def locate(
        self,
        screenshot: ImageSource,
        locator: str | Locator,
        model_choice: ModelComposition | str,
    ) -> PointList:
        _model_choice = (
            ModelName.ASKUI
            if isinstance(model_choice, ModelComposition)
            else model_choice
        )
        _model_composition = (
            model_choice if isinstance(model_choice, ModelComposition) else None
        )
        m = self._get_model(_model_choice, "locate")
        logger.debug(
            "Routing locate prediction to",
            extra={"model_choice": _model_choice},
        )
        return m.locate(locator, screenshot, _model_composition or _model_choice)
