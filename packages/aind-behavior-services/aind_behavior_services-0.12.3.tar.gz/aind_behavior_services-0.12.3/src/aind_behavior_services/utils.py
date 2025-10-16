import datetime
import inspect
import json
import logging
import os
import subprocess
from enum import Enum
from os import PathLike
from pathlib import Path
from string import capwords
from subprocess import CalledProcessError, CompletedProcess, run
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type, TypeVar, Union, cast, get_args

import pydantic
from pydantic import BaseModel, PydanticInvalidForJsonSchema
from pydantic.json_schema import (
    GenerateJsonSchema,
    JsonSchemaMode,
    JsonSchemaValue,
    _deduplicate_schemas,
)
from pydantic_core import PydanticOmit, core_schema, to_jsonable_python
from semver import Version

logger = logging.getLogger(__name__)


T = TypeVar("T")

TModel = TypeVar("TModel", bound=BaseModel)


class CustomGenerateJsonSchema(GenerateJsonSchema):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nullable_as_oneof = kwargs.get("nullable_as_oneof", True)
        self.unions_as_oneof = kwargs.get("unions_as_oneof", True)
        self.render_x_enum_names = kwargs.get("render_x_enum_names", True)

    def nullable_schema(self, schema: core_schema.NullableSchema) -> JsonSchemaValue:
        null_schema = {"type": "null"}
        inner_json_schema = self.generate_inner(schema["schema"])

        if inner_json_schema == null_schema:
            return null_schema
        else:
            if self.nullable_as_oneof:
                return self.get_flattened_oneof([inner_json_schema, null_schema])
            else:
                return super().get_flattened_anyof([inner_json_schema, null_schema])

    def get_flattened_oneof(self, schemas: list[JsonSchemaValue]) -> JsonSchemaValue:
        members = []
        for schema in schemas:
            if len(schema) == 1 and "oneOf" in schema:
                members.extend(schema["oneOf"])
            else:
                members.append(schema)
        members = _deduplicate_schemas(members)
        if len(members) == 1:
            return members[0]
        return {"oneOf": members}

    def enum_schema(self, schema: core_schema.EnumSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches an Enum value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        enum_type = schema["cls"]
        description = None if not enum_type.__doc__ else inspect.cleandoc(enum_type.__doc__)
        if (
            description == "An enumeration."
        ):  # This is the default value provided by enum.EnumMeta.__new__; don't use it
            description = None
        result: dict[str, Any] = {"title": enum_type.__name__, "description": description}
        result = {k: v for k, v in result.items() if v is not None}

        expected = [to_jsonable_python(v.value) for v in schema["members"]]

        result["enum"] = expected
        if len(expected) == 1:
            result["const"] = expected[0]

        types = {type(e) for e in expected}
        if isinstance(enum_type, str) or types == {str}:
            result["type"] = "string"
        elif isinstance(enum_type, int) or types == {int}:
            result["type"] = "integer"
        elif isinstance(enum_type, float) or types == {float}:
            result["type"] = "numeric"
        elif types == {bool}:
            result["type"] = "boolean"
        elif types == {list}:
            result["type"] = "array"

        _type = result.get("type", None)
        if (self.render_x_enum_names) and (_type != "string"):
            result["x-enumNames"] = [screaming_snake_case_to_pascal_case(v.name) for v in schema["members"]]

        return result

    def literal_schema(self, schema: core_schema.LiteralSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a literal value.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        expected = [v.value if isinstance(v, Enum) else v for v in schema["expected"]]
        # jsonify the expected values
        expected = [to_jsonable_python(v) for v in expected]

        types = {type(e) for e in expected}

        if len(expected) == 1:
            if isinstance(expected[0], str):
                return {"const": expected[0], "type": "string"}
            elif isinstance(expected[0], int):
                return {"const": expected[0], "type": "integer"}
            elif isinstance(expected[0], float):
                return {"const": expected[0], "type": "number"}
            elif isinstance(expected[0], bool):
                return {"const": expected[0], "type": "boolean"}
            elif isinstance(expected[0], list):
                return {"const": expected[0], "type": "array"}
            elif expected[0] is None:
                return {"const": expected[0], "type": "null"}
            else:
                return {"const": expected[0]}

        if types == {str}:
            return {"enum": expected, "type": "string"}
        elif types == {int}:
            return {"enum": expected, "type": "integer"}
        elif types == {float}:
            return {"enum": expected, "type": "number"}
        elif types == {bool}:
            return {"enum": expected, "type": "boolean"}
        elif types == {list}:
            return {"enum": expected, "type": "array"}
        # there is not None case because if it's mixed it hits the final `else`
        # if it's a single Literal[None] then it becomes a `const` schema above
        else:
            return {"enum": expected}

    def union_schema(self, schema: core_schema.UnionSchema) -> JsonSchemaValue:
        """Generates a JSON schema that matches a schema that allows values matching any of the given schemas.

        Args:
            schema: The core schema.

        Returns:
            The generated JSON schema.
        """
        generated: list[JsonSchemaValue] = []

        choices = schema["choices"]
        for choice in choices:
            # choice will be a tuple if an explicit label was provided
            choice_schema = choice[0] if isinstance(choice, tuple) else choice
            try:
                generated.append(self.generate_inner(choice_schema))
            except PydanticOmit:
                continue
            except PydanticInvalidForJsonSchema as exc:
                self.emit_warning("skipped-choice", exc.message)
        if len(generated) == 1:
            return generated[0]
        if self.unions_as_oneof is True:
            return self.get_flattened_oneof(generated)
        else:
            return self.get_flattened_anyof(generated)


TModel = TypeVar("TModel", bound=BaseModel)


def export_schema(
    model: BaseModel,
    schema_generator: Type[GenerateJsonSchema] = CustomGenerateJsonSchema,
    mode: JsonSchemaMode = "serialization",
    remove_root: bool = True,
):
    """Export the schema of a model to a json file"""
    _model = model.model_json_schema(schema_generator=schema_generator, mode=mode)
    if remove_root:
        for to_remove in ["title", "description", "properties", "required", "type", "oneOf"]:
            _model.pop(to_remove, None)
    return json.dumps(_model, indent=2)


class BonsaiSgenSerializers(Enum):
    NONE = "None"
    JSON = "json"
    YAML = "yaml"


def bonsai_sgen(
    schema_path: PathLike,
    output_path: PathLike,
    namespace: Optional[str] = None,
    root_element: Optional[str] = None,
    serializer: Optional[List[BonsaiSgenSerializers]] = None,
) -> CompletedProcess:
    """Runs Bonsai.SGen to generate a Bonsai-compatible schema from a json-schema model
    For more information run `bonsai.sgen --help` in the command line.

    Returns:
        CompletedProcess: The result of running the command.
    Args:
        schema_path (PathLike): Target Json Schema file
        output_path (PathLike): Specifies the name of the
          file containing the generated code.
        namespace (Optional[str], optional): Specifies the
          namespace to use for all generated serialization
          classes. Defaults to DataSchema.
        root_element (Optional[str], optional):  Specifies the
          name of the class used to represent the schema root element.
          If None, it will use the json schema root element. Defaults to None.
        serializer (Optional[List[BonsaiSgenSerializers]], optional):
          Specifies the serializer data annotations to include in the generated classes.
          Defaults to None.
    """

    if serializer is None:
        serializer = [BonsaiSgenSerializers.JSON]

    _restore_cmd = run("dotnet tool restore", shell=True, check=True, capture_output=True)
    try:
        _restore_cmd.check_returncode()
    except CalledProcessError as e:
        print(f"Error occurred while restoring tools: {e}")
        print(
            "Ensure you have the Bonsai.Sgen tool installed locally. See https://github.com/bonsai-rx/sgen?tab=readme-ov-file#getting-started for instructions."
        )
        raise

    version = _check_bonsai_sgen_version()
    if version < Version.parse("0.6.0"):
        raise RuntimeError("Version of Bonsai.Sgen must be at least 0.6.0, found: " + str(version))

    cmd_string = (
        f'dotnet tool run bonsai.sgen "{schema_path}" -o "{Path(output_path).parent}" -n {Path(output_path).name}'
    )
    cmd_string += f" --namespace {namespace}" if namespace is not None else ""
    cmd_string += f" --root {root_element}" if root_element is not None else ""

    if len(serializer) == 0 or BonsaiSgenSerializers.NONE in serializer:
        cmd_string += " --serializer none"
    else:
        cmd_string += " --serializer"
        cmd_string += " ".join([f" {sr.value}" for sr in serializer])
    return run(cmd_string, shell=True, check=True)


def _check_bonsai_sgen_version() -> Version:
    """Check the version of the Bonsai.SGen tool."""
    result = run("dotnet tool run bonsai.sgen --version", shell=True, check=True, capture_output=True)
    version_str = result.stdout.strip()
    return Version.parse(version_str)


def convert_pydantic_to_bonsai(
    model: BaseModel,
    *,
    model_name: Optional[str] = None,
    json_schema_output_dir: PathLike = Path("./src/DataSchemas/"),
    cs_output_dir: Optional[PathLike] = Path("./src/Extensions/"),
    cs_namespace: str = "DataSchema",
    cs_serializer: Optional[List[BonsaiSgenSerializers]] = None,
    json_schema_export_kwargs: Optional[Dict[str, Any]] = None,
    root_element: Optional[str] = None,
) -> Optional[CompletedProcess]:
    def _write_json(schema_path: PathLike, output_model_name: str, model: BaseModel, **extra_kwargs) -> None:
        with open(os.path.join(schema_path, f"{output_model_name}.json"), "w", encoding="utf-8") as f:
            json_model = export_schema(model, **extra_kwargs)
            f.write(json_model)

    _model_name = model_name or model.__class__.__name__
    _write_json(json_schema_output_dir, _model_name, model, **(json_schema_export_kwargs or {}))

    if cs_output_dir is not None:
        cmd_return = bonsai_sgen(
            schema_path=Path(os.path.join(json_schema_output_dir, f"{_model_name}.json")),
            output_path=Path(os.path.join(cs_output_dir, f"{snake_to_pascal_case(_model_name)}.Generated.cs")),
            namespace=cs_namespace,
            serializer=cs_serializer,
            root_element=root_element,
        )
        return cmd_return

    return None


def snake_to_pascal_case(s: str) -> str:
    """
    Converts a snake_case string to PascalCase.

    Args:
        s (str): The snake_case string to be converted.

    Returns:
        str: The PascalCase string.
    """
    return "".join(map(capwords, s.split("_")))


def pascal_to_snake_case(s: str) -> str:
    """
    Converts a PascalCase string to snake_case.

    Args:
        s (str): The PascalCase string to be converted.

    Returns:
        str: The snake_case string.
    """
    result = ""
    for i, char in enumerate(s):
        if char.isupper():
            if i != 0:
                result += "_"
            result += char.lower()
        else:
            result += char
    return result


def screaming_snake_case_to_pascal_case(s: str) -> str:
    """
    Converts a SCREAMING_SNAKE_CASE string to PascalCase.

    Args:
        s (str): The SCREAMING_SNAKE_CASE string to be converted.

    Returns:
        str: The PascalCase string.
    """
    words = s.split("_")
    return "".join(word.capitalize() for word in words)


def _build_bonsai_process_command(
    workflow_file: PathLike | str,
    bonsai_exe: PathLike | str = "bonsai/bonsai.exe",
    is_editor_mode: bool = True,
    is_start_flag: bool = True,
    layout: Optional[PathLike | str] = None,
    additional_properties: Optional[Dict[str, str]] = None,
) -> str:
    output_cmd: str = f'"{bonsai_exe}" "{workflow_file}"'
    if is_editor_mode:
        if is_start_flag:
            output_cmd += " --start"
    else:
        output_cmd += " --no-editor"
        if layout is not None:
            output_cmd += f' --visualizer-layout:"{layout}"'

    if additional_properties:
        for param, value in additional_properties.items():
            output_cmd += f' -p:"{param}"="{value}"'

    return output_cmd


def run_bonsai_process(
    workflow_file: PathLike | str,
    bonsai_exe: PathLike | str = "bonsai/bonsai.exe",
    is_editor_mode: bool = True,
    is_start_flag: bool = True,
    layout: Optional[PathLike | str] = None,
    additional_properties: Optional[Dict[str, str]] = None,
    cwd: Optional[PathLike | str] = None,
    timeout: Optional[float] = None,
    print_cmd: bool = False,
) -> CompletedProcess:
    if not Path(bonsai_exe).exists():
        has_setup = (Path(bonsai_exe).parent / "setup.ps1").exists()
        m = f"Bonsai executable not found at {bonsai_exe}." + (
            " A 'setup.ps1' file exists in the target directory, consider running it." if has_setup else ""
        )
        raise FileNotFoundError(m)

    output_cmd = _build_bonsai_process_command(
        workflow_file=workflow_file,
        bonsai_exe=bonsai_exe,
        is_editor_mode=is_editor_mode,
        is_start_flag=is_start_flag,
        layout=layout,
        additional_properties=additional_properties,
    )
    if cwd is None:
        cwd = os.getcwd()
    if print_cmd:
        logging.debug(output_cmd)
    return subprocess.run(output_cmd, cwd=cwd, check=True, timeout=timeout, capture_output=True)


def open_bonsai_process(
    workflow_file: PathLike | str,
    bonsai_exe: PathLike | str = "bonsai/bonsai.exe",
    is_editor_mode: bool = True,
    is_start_flag: bool = True,
    layout: Optional[PathLike | str] = None,
    additional_properties: Optional[Dict[str, str]] = None,
    log_file_name: Optional[str] = None,
    cwd: Optional[PathLike | str] = None,
    creation_flags: Optional[int] = None,
    print_cmd: bool = False,
) -> subprocess.Popen:
    output_cmd = _build_bonsai_process_command(
        workflow_file=workflow_file,
        bonsai_exe=bonsai_exe,
        is_editor_mode=is_editor_mode,
        is_start_flag=is_start_flag,
        layout=layout,
        additional_properties=additional_properties,
    )

    if cwd is None:
        cwd = os.getcwd()
    if creation_flags is None:
        creation_flags = subprocess.CREATE_NEW_CONSOLE

    if log_file_name is None:
        if print_cmd:
            logging.debug(output_cmd)
        return subprocess.Popen(output_cmd, cwd=cwd, creationflags=creation_flags)
    else:
        logging_cmd = f'powershell -ep Bypass -c "& {output_cmd} *>&1 | tee -a {log_file_name}"'
        if print_cmd:
            logging.debug(logging_cmd)
        return subprocess.Popen(logging_cmd, cwd=cwd, creationflags=creation_flags)


def format_datetime(value: datetime.datetime, is_tz_strict: bool = False) -> str:
    if value.tzinfo is None:
        if is_tz_strict:
            raise ValueError("Datetime object must be timezone-aware")
        return value.strftime("%Y-%m-%dT%H%M%S")
    elif value.tzinfo.utcoffset(value) == datetime.timedelta(0):
        return value.strftime("%Y-%m-%dT%H%M%SZ")
    else:
        return value.strftime("%Y-%m-%dT%H%M%S%z")


def now() -> datetime.datetime:
    """Returns the current time as a timezone unaware datetime."""
    return datetime.datetime.now()


def utcnow() -> datetime.datetime:
    """Returns the current time as a timezone aware datetime in UTC."""
    return datetime.datetime.now(datetime.timezone.utc)


def tznow() -> datetime.datetime:
    """Returns the current time as a timezone aware datetime in the local timezone."""
    return utcnow().astimezone()


def model_from_json_file(json_path: os.PathLike | str, model: type[TModel]) -> TModel:
    with open(Path(json_path), "r", encoding="utf-8") as file:
        return model.model_validate_json(file.read())


ISearchable = Union[pydantic.BaseModel, Dict, List]
_ISearchableTypeChecker = tuple(get_args(ISearchable))  # pre-compute for performance


def get_fields_of_type(
    searchable: ISearchable,
    target_type: Type[T],
    *,
    recursive: bool = True,
    stop_recursion_on_type: bool = True,
) -> List[Tuple[Optional[str], T]]:
    _iterable: Iterable
    _is_type: bool
    result: List[Tuple[Optional[str], T]] = []

    if isinstance(searchable, dict):
        _iterable = searchable.items()
    elif isinstance(searchable, list):
        _iterable = list(zip([None for _ in range(len(searchable))], searchable))
    elif isinstance(searchable, pydantic.BaseModel):
        _iterable = {k: getattr(searchable, k) for k in type(searchable).model_fields.keys()}.items()
    else:
        raise ValueError(f"Unsupported model type: {type(searchable)}")

    for name, field in _iterable:
        _is_type = False
        if isinstance(field, target_type):
            result.append((name, field))
            _is_type = True
        if recursive and isinstance(field, _ISearchableTypeChecker) and not (stop_recursion_on_type and _is_type):
            result.extend(
                get_fields_of_type(
                    cast(ISearchable, field),
                    target_type,
                    recursive=recursive,
                    stop_recursion_on_type=stop_recursion_on_type,
                )
            )
    return result
