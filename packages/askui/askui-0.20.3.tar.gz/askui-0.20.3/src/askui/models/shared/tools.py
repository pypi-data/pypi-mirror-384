import logging
import types
from abc import ABC, abstractmethod
from datetime import timedelta
from functools import wraps
from typing import Any, Literal, Protocol, Type

import jsonref
import mcp
from anthropic.types.beta import (
    BetaCacheControlEphemeralParam,
    BetaToolParam,
    BetaToolUnionParam,
)
from anthropic.types.beta.beta_tool_param import InputSchema
from asyncer import syncify
from fastmcp.client.client import CallToolResult, ProgressHandler
from fastmcp.tools import Tool as FastMcpTool
from fastmcp.utilities.types import Image as FastMcpImage
from mcp import Tool as McpTool
from PIL import Image
from pydantic import BaseModel, Field
from typing_extensions import Self

from askui.models.shared.agent_message_param import (
    Base64ImageSourceParam,
    ContentBlockParam,
    ImageBlockParam,
    TextBlockParam,
    ToolResultBlockParam,
    ToolUseBlockParam,
)
from askui.utils.image_utils import ImageSource

logger = logging.getLogger(__name__)

PrimitiveToolCallResult = Image.Image | None | str | BaseModel

ToolCallResult = (
    PrimitiveToolCallResult
    | list[PrimitiveToolCallResult]
    | tuple[PrimitiveToolCallResult, ...]
    | CallToolResult
)


IMAGE_MEDIA_TYPES_SUPPORTED: list[
    Literal["image/jpeg", "image/png", "image/gif", "image/webp"]
] = ["image/jpeg", "image/png", "image/gif", "image/webp"]


def _convert_to_content(
    result: ToolCallResult,
) -> list[TextBlockParam | ImageBlockParam]:
    if result is None:
        return []

    if isinstance(result, CallToolResult):
        _result: list[TextBlockParam | ImageBlockParam] = []
        for block in result.content:
            match block.type:
                case "text":
                    _result.append(TextBlockParam(text=block.text))
                case "image":
                    media_type = block.mimeType
                    if media_type not in IMAGE_MEDIA_TYPES_SUPPORTED:
                        logger.warning(
                            "Unsupported image media type",
                            extra={"media_type": media_type},
                        )
                        continue
                    _result.append(
                        ImageBlockParam(
                            source=Base64ImageSourceParam(
                                media_type=media_type,
                                data=block.data,
                            )
                        )
                    )
                case _:
                    logger.warning(
                        "Unsupported block type",
                        extra={"block_type": block.type},
                    )
        return _result

    if isinstance(result, str):
        return [TextBlockParam(text=result)]

    if isinstance(result, list | tuple):
        return [
            item
            for sublist in [_convert_to_content(item) for item in result]
            for item in sublist
        ]

    if isinstance(result, BaseModel):
        return [TextBlockParam(text=result.model_dump_json())]

    return [
        ImageBlockParam(
            source=Base64ImageSourceParam(
                media_type="image/png",
                data=ImageSource(result).to_base64(),
            )
        )
    ]


def _default_input_schema() -> InputSchema:
    return {"type": "object", "properties": {}, "required": []}


def _convert_to_mcp_content(
    result: Any,
) -> Any:
    if isinstance(result, tuple):
        return tuple(_convert_to_mcp_content(item) for item in result)

    if isinstance(result, list):
        return [_convert_to_mcp_content(item) for item in result]

    if isinstance(result, Image.Image):
        src = ImageSource(result)
        return FastMcpImage(data=src.to_bytes(), format="png").to_image_content()

    return result


PLAYWRIGHT_TOOL_PREFIX = "browser_"


def _is_playwright_error(
    param: ToolUseBlockParam,
    error: Exception,  # noqa: ARG001
) -> bool:
    if param.name.startswith(PLAYWRIGHT_TOOL_PREFIX):
        return True
    return False


def _create_tool_result_block_param_for_playwright_error(
    param: ToolUseBlockParam, error: Exception
) -> ToolResultBlockParam:
    lines = str(error).split("\n")
    line_idx: int | None = None
    for idx, line in enumerate(lines):
        if line.startswith('Run "npx playwright install '):
            line_idx = idx
            break

    if line_idx is not None:
        lines[line_idx] = "Download and install the browser to continue."
    return ToolResultBlockParam(
        content="\n\n".join(lines),
        is_error=True,
        tool_use_id=param.id,
    )


class Tool(BaseModel, ABC):
    name: str = Field(description="Name of the tool")
    description: str = Field(description="Description of what the tool does")
    input_schema: InputSchema = Field(
        default_factory=_default_input_schema,
        description="JSON schema for tool parameters",
    )

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> ToolCallResult:
        """Executes the tool with the given arguments."""
        error_msg = "Tool subclasses must implement __call__ method"
        raise NotImplementedError(error_msg)

    def to_params(
        self,
    ) -> BetaToolUnionParam:
        return BetaToolParam(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
        )

    def to_mcp_tool(
        self, tags: set[str], name_prefix: str | None = None
    ) -> FastMcpTool:
        """Convert the AskUI tool to an MCP tool."""
        tool_call = self.__call__

        @wraps(tool_call)
        def wrapped_tool_call(*args: Any, **kwargs: Any) -> Any:
            return _convert_to_mcp_content(tool_call(*args, **kwargs))

        tool_name = self.name
        if name_prefix is not None:
            tool_name = f"{name_prefix}{tool_name}"

        return FastMcpTool.from_function(
            wrapped_tool_call,
            name=tool_name,
            description=self.description,
            tags=tags,
        )


class AgentException(Exception):
    """
    Exception raised by the agent.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class McpClientProtocol(Protocol):
    async def list_tools(self) -> list[mcp.types.Tool]: ...

    async def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        timeout: timedelta | float | None = None,  # noqa: ASYNC109
        progress_handler: ProgressHandler | None = None,
        raise_on_error: bool = True,
    ) -> CallToolResult: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None: ...


def _replace_refs(tool_name: str, input_schema: InputSchema) -> InputSchema:
    try:
        return jsonref.replace_refs(  # type: ignore[no-any-return]
            input_schema,
            lazy_load=False,
            proxies=False,
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "Failed to replace refs for tool",
            extra={
                "tool_name": tool_name,
                "input_schema": input_schema,
            },
        )
        return input_schema


class ToolCollection:
    """A collection of tools.

    Use for dispatching tool calls

    **Important**: Tools must have unique names. A tool with the same name as a tool
    added before will override the tool added before.


    Vision:
    - Could be used for parallelizing tool calls configurable through init arg
    - Could be used for raising on an exception
      (instead of just returning `ContentBlockParam`)
      within tool call or doing tool call or if tool is not found

    Args:
        tools (list[Tool] | None, optional): The tools to add to the collection.
            Defaults to `None`.
        mcp_client (McpClientProtocol | None, optional): The client to use for
            the tools. Defaults to `None`.
    """

    def __init__(
        self,
        tools: list[Tool] | None = None,
        mcp_client: McpClientProtocol | None = None,
        include: set[str] | None = None,
    ) -> None:
        _tools = tools or []
        self._tool_map = {tool.to_params()["name"]: tool for tool in _tools}
        self._mcp_client = mcp_client
        self._include = include

    def retrieve_tool_beta_flags(self) -> list[str]:
        result: set[str] = set()
        for tool in self._get_mcp_tools().values():
            beta_flags = (tool.meta or {}).get("betas", [])
            if not isinstance(beta_flags, list):
                continue
            for beta_flag in beta_flags:
                if not isinstance(beta_flag, str):
                    continue
                result.add(beta_flag)
        return list(result)

    def to_params(self) -> list[BetaToolUnionParam]:
        tool_map = {
            **self._get_mcp_tool_params(),
            **{
                tool_name: tool.to_params()
                for tool_name, tool in self._tool_map.items()
            },
        }
        filtered_tool_map = {
            tool_name: tool
            for tool_name, tool in tool_map.items()
            if self._include is None or tool_name in self._include
        }
        result = list(filtered_tool_map.values())
        if result:
            result[-1]["cache_control"] = BetaCacheControlEphemeralParam(
                type="ephemeral",
            )
        return result

    def _get_mcp_tool_params(self) -> dict[str, BetaToolUnionParam]:
        if not self._mcp_client:
            return {}
        mcp_tools = self._get_mcp_tools()
        result: dict[str, BetaToolUnionParam] = {}
        for tool_name, tool in mcp_tools.items():
            if params := (tool.meta or {}).get("params"):
                # validation missing
                result[tool_name] = params
                continue
            result[tool_name] = BetaToolParam(
                name=tool_name,
                description=tool.description or "",
                input_schema=_replace_refs(tool_name, tool.inputSchema),
            )
        return result

    def append_tool(self, *tools: Tool) -> "Self":
        """Append a tool to the collection."""
        for tool in tools:
            self._tool_map[tool.to_params()["name"]] = tool
        return self

    def reset_tools(self, tools: list[Tool] | None = None) -> "Self":
        """Reset the tools in the collection with new tools."""
        _tools = tools or []
        self._tool_map = {tool.to_params()["name"]: tool for tool in _tools}
        return self

    def run(
        self, tool_use_block_params: list[ToolUseBlockParam]
    ) -> list[ContentBlockParam]:
        return [
            self._run_tool(tool_use_block_param)
            for tool_use_block_param in tool_use_block_params
        ]

    def _run_tool(
        self, tool_use_block_param: ToolUseBlockParam
    ) -> ToolResultBlockParam:
        tool = self._tool_map.get(tool_use_block_param.name)
        if tool:
            return self._run_regular_tool(tool_use_block_param, tool)
        mcp_tool = self._get_mcp_tools().get(tool_use_block_param.name)
        if mcp_tool:
            return self._run_mcp_tool(tool_use_block_param)
        return ToolResultBlockParam(
            content=f"Tool not found: {tool_use_block_param.name}",
            is_error=True,
            tool_use_id=tool_use_block_param.id,
        )

    async def _list_mcp_tools(self, mcp_client: McpClientProtocol) -> list[McpTool]:
        async with mcp_client:
            return await mcp_client.list_tools()

    def _get_mcp_tools(self) -> dict[str, McpTool]:
        """Get cached MCP tools or fetch them if not cached."""
        try:
            if not self._mcp_client:
                return {}
            list_mcp_tools_sync = syncify(self._list_mcp_tools, raise_sync_error=False)
            tools_list = list_mcp_tools_sync(self._mcp_client)
        except Exception:  # noqa: BLE001
            logger.exception(
                "Failed to list MCP tools",
            )
            return {}
        else:
            return {tool.name: tool for tool in tools_list}

    def _run_regular_tool(
        self,
        tool_use_block_param: ToolUseBlockParam,
        tool: Tool,
    ) -> ToolResultBlockParam:
        try:
            tool_result: ToolCallResult = tool(**tool_use_block_param.input)  # type: ignore
            return ToolResultBlockParam(
                content=_convert_to_content(tool_result),
                tool_use_id=tool_use_block_param.id,
            )
        except AgentException:
            raise
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "Tool failed",
                extra={"tool_name": tool_use_block_param.name, "error": str(e)},
            )
            return ToolResultBlockParam(
                content=str(e),
                is_error=True,
                tool_use_id=tool_use_block_param.id,
            )

    async def _call_mcp_tool(
        self,
        mcp_client: McpClientProtocol,
        tool_use_block_param: ToolUseBlockParam,
    ) -> ToolCallResult:
        async with mcp_client:
            return await mcp_client.call_tool(
                tool_use_block_param.name,
                tool_use_block_param.input,  # type: ignore[arg-type]
            )

    def _run_mcp_tool(
        self,
        tool_use_block_param: ToolUseBlockParam,
    ) -> ToolResultBlockParam:
        """Run an MCP tool using the client."""
        if not self._mcp_client:
            return ToolResultBlockParam(
                content="MCP client not available",
                is_error=True,
                tool_use_id=tool_use_block_param.id,
            )
        try:
            call_mcp_tool_sync = syncify(self._call_mcp_tool, raise_sync_error=False)
            result = call_mcp_tool_sync(self._mcp_client, tool_use_block_param)
            return ToolResultBlockParam(
                content=_convert_to_content(result),
                tool_use_id=tool_use_block_param.id,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "MCP tool failed",
                exc_info=True,
                extra={"tool_name": tool_use_block_param.name, "error": str(e)},
            )
            if _is_playwright_error(tool_use_block_param, e):
                return _create_tool_result_block_param_for_playwright_error(
                    tool_use_block_param,
                    e,
                )
            return ToolResultBlockParam(
                content=str(e),
                is_error=True,
                tool_use_id=tool_use_block_param.id,
            )

    def __add__(self, other: "ToolCollection") -> "ToolCollection":
        return ToolCollection(
            tools=list(self._tool_map.values()) + list(other._tool_map.values()),
            mcp_client=other._mcp_client or self._mcp_client,
        )
