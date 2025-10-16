import datetime
import logging
from os import PathLike
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    Literal,
    Optional,
    get_args,
)

import git
from aind_behavior_curriculum.task import SEMVER_REGEX
from pydantic import (
    AwareDatetime,
    BaseModel,
    Field,
    GetJsonSchemaHandler,
    ValidatorFunctionWrapHandler,
    WrapValidator,
    field_validator,
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from semver import Version

from aind_behavior_services import __semver__

logger = logging.getLogger(__name__)


class SchemaVersionedModel(BaseModel):
    aind_behavior_services_pkg_version: Literal[__semver__] = Field(
        default=__semver__, pattern=SEMVER_REGEX, title="aind_behavior_services package version", frozen=True
    )
    version: str = Field(..., pattern=SEMVER_REGEX, description="schema version", title="Version", frozen=True)

    @field_validator("aind_behavior_services_pkg_version", "version", mode="before", check_fields=False)
    @classmethod
    def coerce_version(cls, v: str, ctx) -> str:
        return coerce_schema_version(cls, v, ctx.field_name)


class SemVerAnnotation:
    """A class representing semantic version annotations."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Callable[[Any], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        def validate_from_str(value: str) -> Version:
            return Version.parse(value)

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(validate_from_str),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(Version),
                    from_str_schema,
                ]
            ),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return handler(core_schema.str_schema())


def coerce_schema_version(
    cls: type[SchemaVersionedModel], v: str, version_string: str = "version", check_compatibility: bool = True
) -> str:
    try:  # Get the default schema version from the model literal field
        _default_schema_version = Version.parse(get_args(cls.model_fields[version_string].annotation)[0])
    except IndexError:  # This handles the case where the base class does not define a literal schema_version value
        return v

    semver = Version.parse(v)
    if semver != _default_schema_version:
        logger.warning(
            "Deserialized versioned field %s, expected %s. Will attempt to coerce. "
            "This will be considered a best-effort operation.",
            semver,
            _default_schema_version,
        )
    return str(_default_schema_version)


def get_commit_hash(repository: Optional[PathLike] = None) -> str:
    """Get the commit hash of the repository."""
    try:
        if repository is None:
            repo = git.Repo(search_parent_directories=True)
        else:
            repo = git.Repo(repository)
        return repo.head.commit.hexsha
    except git.InvalidGitRepositoryError as e:
        raise e("Not a git repository. Please run from the root of the repository.") from e


if TYPE_CHECKING:
    DefaultAwareDatetime = Annotated[AwareDatetime, ...]
else:

    def _add_default_tz(dt: Any, handler: ValidatorFunctionWrapHandler) -> datetime.datetime:
        if isinstance(dt, str):
            dt = datetime.datetime.fromisoformat(dt)
        if isinstance(dt, datetime.datetime):
            if dt.tzinfo is None:
                dt = dt.astimezone()
        return dt

    DefaultAwareDatetime = Annotated[AwareDatetime, WrapValidator(_add_default_tz), Field(validate_default=True)]
