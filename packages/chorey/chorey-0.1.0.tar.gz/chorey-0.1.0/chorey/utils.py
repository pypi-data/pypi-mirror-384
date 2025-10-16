from types import NoneType
from typing import TYPE_CHECKING, Any, TypeVar, get_args, get_origin

from pydantic import BaseModel

from chorey._types import StepFunc
from chorey.context import ChoreyContext

if TYPE_CHECKING:
    from chorey.step import Step

Input = TypeVar("Input")
Output = TypeVar("Output")


def get_step_func_name(func: "StepFunc") -> str:
    return getattr(func, "__name__", repr(func))


def get_input_output_type_from_step(
    step: "Step[Input, Output, Any]",
) -> tuple[type[Input], type[Output]]:
    from inspect import signature

    func_name = get_step_func_name(step.func)
    sig = signature(step.func)

    input_parameter = tuple(sig.parameters.values())[0] if sig.parameters else None
    if input_parameter is None or input_parameter.annotation is sig.empty:
        raise TypeError(f"Function {func_name} must have a type-annotated first parameter")

    output_type = sig.return_annotation
    if output_type is sig.empty:
        raise TypeError(f"Function {func_name} must have a return type annotation")

    return input_parameter.annotation, output_type


class MissingFeatureError(Exception):
    """
    Exception raised when a required feature is missing.
    """

    def __init__(self, feature: str) -> None:
        super().__init__(f"Missing required feature for pype: {feature}")  # pragma: no cover


def get_type_name_for_display(
    ty: type,
    *,
    unwrap_pypeline_context: bool = True,
) -> str:
    """
    Get a user-friendly name for a type, suitable for display in the pipeline visualization.
    """

    # unwrap ChoreyContext's data type for display purposes, as context does not matter
    # in the visualization
    if unwrap_pypeline_context and get_origin(ty) is ChoreyContext:
        ty, _ = get_args(ty)

    if args := get_args(ty):
        origin = get_origin(ty)
        if origin is not None:
            arg_names = ", ".join(get_type_name_for_display(arg) for arg in args)
            return f"{get_type_name_for_display(origin)}[{arg_names}]"
    elif ty is NoneType:
        return "None"

    if hasattr(ty, "__name__"):
        return ty.__name__

    return str(ty)  # pragma: no cover


class _NotExisting:
    pass


class ImportPipelineError(Exception):
    pass


class InvalidPipelinePathError(ImportPipelineError):
    def __init__(self, path: str) -> None:
        super().__init__(f"Invalid pipeline path: '{path}'. Must be in the format 'module.submodule:variable_name'")


class PipelineModuleDoesNotExistError(ImportPipelineError):
    def __init__(self, module: str) -> None:
        super().__init__(f"Could not find module to import pipeline from: '{module}'")


class PipelineDoesNotExistError(ImportPipelineError):
    def __init__(self, path: str) -> None:
        super().__init__(f"Could not find pipeline variable in module: '{path}'")


def import_pipeline(path: str) -> "Step":
    from chorey.step import Step

    if not path.count(":") == 1:
        raise InvalidPipelinePathError(path)

    module_path, var_name = path.rsplit(":", 1)

    try:
        module = __import__(module_path, fromlist=[var_name])
    except ModuleNotFoundError as e:
        raise PipelineModuleDoesNotExistError(module_path) from e

    var = getattr(module, var_name, _NotExisting)
    if var is _NotExisting:
        raise PipelineDoesNotExistError(var_name)

    if not isinstance(var, Step):
        raise TypeError(f"'{var_name}' is not a Step instance")

    return var


def parse_cli_input(value: str | None, to_type: type) -> Any:
    if value is None:
        if to_type is type(None):
            return None
        else:
            to_type_name = get_type_name_for_display(to_type, unwrap_pypeline_context=False)
            raise TypeError(f"Input of type '{to_type_name}' is required but none was provided")

    if isinstance(value, to_type):
        return value

    from json import JSONDecodeError, loads

    if BaseModel in to_type.__mro__:
        try:
            return to_type(**loads(value))
        except JSONDecodeError:
            raise TypeError(f"Cannot parse input into {to_type}: expected JSON object, got {type(value)}")

    if to_type not in {str, int, float, bool}:
        try:
            value = loads(value)
        except JSONDecodeError:
            value = value

    return to_type(value)
