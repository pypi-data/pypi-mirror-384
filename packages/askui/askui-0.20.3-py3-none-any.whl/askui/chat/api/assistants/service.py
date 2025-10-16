from pathlib import Path

from askui.chat.api.assistants.models import (
    Assistant,
    AssistantCreateParams,
    AssistantModifyParams,
)
from askui.chat.api.assistants.seeds import SEEDS
from askui.chat.api.models import AssistantId, WorkspaceId
from askui.chat.api.utils import build_workspace_filter_fn
from askui.utils.api_utils import (
    LIST_LIMIT_MAX,
    ConflictError,
    ForbiddenError,
    ListQuery,
    ListResponse,
    NotFoundError,
    list_resources,
)


class AssistantService:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._assistants_dir = base_dir / "assistants"

    def _get_assistant_path(self, assistant_id: AssistantId, new: bool = False) -> Path:
        assistant_path = self._assistants_dir / f"{assistant_id}.json"
        exists = assistant_path.exists()
        if new and exists:
            error_msg = f"Assistant {assistant_id} already exists"
            raise ConflictError(error_msg)
        if not new and not exists:
            error_msg = f"Assistant {assistant_id} not found"
            raise NotFoundError(error_msg)
        return assistant_path

    def list_(
        self, workspace_id: WorkspaceId | None, query: ListQuery
    ) -> ListResponse[Assistant]:
        return list_resources(
            self._assistants_dir,
            query,
            Assistant,
            filter_fn=build_workspace_filter_fn(workspace_id, Assistant),
        )

    def retrieve(
        self, workspace_id: WorkspaceId | None, assistant_id: AssistantId
    ) -> Assistant:
        try:
            assistant_path = self._get_assistant_path(assistant_id)
            content = assistant_path.read_text()
            if not content.strip():
                error_msg = f"Assistant {assistant_id} not found"
                raise NotFoundError(error_msg)
            assistant = Assistant.model_validate_json(content)
            if not (
                assistant.workspace_id is None or assistant.workspace_id == workspace_id
            ):
                error_msg = f"Assistant {assistant_id} not found"
                raise NotFoundError(error_msg)
        except FileNotFoundError as e:
            error_msg = f"Assistant {assistant_id} not found"
            raise NotFoundError(error_msg) from e
        except (ValueError, TypeError) as e:
            # Handle JSON parsing errors
            error_msg = f"Assistant {assistant_id} not found"
            raise NotFoundError(error_msg) from e
        else:
            return assistant

    def create(
        self, workspace_id: WorkspaceId, params: AssistantCreateParams
    ) -> Assistant:
        assistant = Assistant.create(workspace_id, params)
        self._save(assistant, new=True)
        return assistant

    def modify(
        self,
        workspace_id: WorkspaceId,
        assistant_id: AssistantId,
        params: AssistantModifyParams,
    ) -> Assistant:
        assistant = self.retrieve(workspace_id, assistant_id)
        if assistant.workspace_id is None:
            error_msg = f"Default assistant {assistant_id} cannot be modified"
            raise ForbiddenError(error_msg)
        modified = assistant.modify(params)
        self._save(modified)
        return modified

    def delete(
        self,
        workspace_id: WorkspaceId | None,
        assistant_id: AssistantId,
        force: bool = False,
    ) -> None:
        try:
            assistant = self.retrieve(workspace_id, assistant_id)
            if assistant.workspace_id is None and not force:
                error_msg = f"Default assistant {assistant_id} cannot be deleted"
                raise ForbiddenError(error_msg)
            try:
                self._get_assistant_path(assistant_id).unlink()
            except FileNotFoundError:
                # File already deleted, that's fine
                pass
        except FileNotFoundError as e:
            error_msg = f"Assistant {assistant_id} not found"
            raise NotFoundError(error_msg) from e
        except NotFoundError:
            # If force=True and assistant doesn't exist, just ignore
            if not force:
                raise
            # For force=True, we can ignore the NotFoundError

    def _save(self, assistant: Assistant, new: bool = False) -> None:
        self._assistants_dir.mkdir(parents=True, exist_ok=True)
        assistant_file = self._get_assistant_path(assistant.id, new=new)
        assistant_file.write_text(assistant.model_dump_json(), encoding="utf-8")

    def seed(self) -> None:
        """Seed the assistant service with default assistants."""
        for seed in SEEDS:
            self.delete(None, seed.id, force=True)
            try:
                self._save(seed, new=True)
            except ConflictError:  # noqa: PERF203
                self._save(seed)
