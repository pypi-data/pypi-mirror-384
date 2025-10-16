from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Callable, Generic, Literal, Sequence, Type

from fastapi import Query
from pydantic import BaseModel, ValidationError
from typing_extensions import TypeVar

ListOrder = Literal["asc", "desc"]
LIST_LIMIT_MAX = 100
LIST_LIMIT_DEFAULT = 20


Id = TypeVar("Id", bound=str, default=str)


@dataclass(kw_only=True)
class ListQuery(Generic[Id]):
    limit: Annotated[int, Query(ge=1, le=LIST_LIMIT_MAX)] = LIST_LIMIT_DEFAULT
    after: Annotated[Id | None, Query()] = None
    before: Annotated[Id | None, Query()] = None
    order: Annotated[ListOrder, Query()] = "desc"


ObjectType = TypeVar("ObjectType", bound=BaseModel)


class ListResponse(BaseModel, Generic[ObjectType]):
    object: Literal["list"] = "list"
    data: Sequence[ObjectType]
    first_id: str | None = None
    last_id: str | None = None
    has_more: bool = False


class ApiError(Exception):
    pass


class ConflictError(ApiError):
    pass


class LimitReachedError(ApiError):
    pass


class NotFoundError(ApiError):
    pass


class ForbiddenError(ApiError):
    pass


class FileTooLargeError(ApiError):
    def __init__(self, max_size: int):
        self.max_size = max_size
        super().__init__(f"File too large. Maximum size is {max_size} bytes.")


def _build_after_fn(after: str, order: ListOrder) -> Callable[[Path], bool]:
    after_name = f"{after}.json"
    if order == "asc":
        return lambda f: f.name > after_name
    # desc - "after" means files that come before in the sorted list
    return lambda f: f.name < after_name


def _build_before_fn(before: str, order: ListOrder) -> Callable[[Path], bool]:
    before_name = f"{before}.json"
    if order == "asc":
        return lambda f: f.name < before_name
    return lambda f: f.name > before_name


def _build_list_filter_fn(list_query: ListQuery) -> Callable[[Path], bool]:
    after_fn = (
        _build_after_fn(list_query.after, list_query.order)
        if list_query.after
        else None
    )
    before_fn = (
        _build_before_fn(list_query.before, list_query.order)
        if list_query.before
        else None
    )
    if after_fn and before_fn:
        return lambda f: after_fn(f) and before_fn(f)
    if after_fn:
        return after_fn
    if before_fn:
        return before_fn
    return lambda _: True


def list_resource_paths(
    base_dir: Path, list_query: ListQuery, pattern: str = "*.json"
) -> list[Path]:
    paths: list[Path] = []
    filter_fn = _build_list_filter_fn(list_query)
    for f in base_dir.glob(pattern):
        try:
            if filter_fn(f):
                paths.append(f)
        except ValidationError:  # noqa: PERF203
            continue
    return sorted(paths, key=lambda f: f.name, reverse=(list_query.order == "desc"))


class Resource(BaseModel):
    id: str


ResourceT = TypeVar("ResourceT", bound=Resource)


def list_resources(
    base_dir: Path,
    query: ListQuery,
    resource_type: Type[ResourceT],
    filter_fn: Callable[[ResourceT], bool] | None = None,
    pattern: str = "*.json",
) -> ListResponse[ResourceT]:
    """
    List resources from a directory.

    Args:
        base_dir: The base directory to list resources from.
        query: The query to filter resources.
        resource_type: The type of resource to list.
        filter_fn: A function to filter resources. If it returns `False`,
            the resource is not included in the list.

    Returns:
        A list of resources.
    """
    resource_paths = list_resource_paths(base_dir, query, pattern)
    resources: list[ResourceT] = []
    for resource_file in resource_paths:
        try:
            resource = resource_type.model_validate_json(
                resource_file.read_text(encoding="utf-8")
            )
            if filter_fn and not filter_fn(resource):
                continue
            resources.append(resource)
        except (ValidationError, FileNotFoundError):  # noqa: PERF203
            continue
    has_more = len(resources) > query.limit
    resources = resources[: query.limit]
    return ListResponse(
        data=resources,
        first_id=resources[0].id if resources else None,
        last_id=resources[-1].id if resources else None,
        has_more=has_more,
    )
