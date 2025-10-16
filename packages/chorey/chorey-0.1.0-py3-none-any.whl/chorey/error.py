from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from chorey.step import Step


class PipelineError(Exception):
    step_name: str
    input: Any
    original_exception: Exception

    def __init__(self, *, step: "Step", input: Any, original_exception: Exception) -> None:
        self.step_name = step.name
        self.input = input
        self.original_exception = original_exception

        message = (
            f"Pipeline execution failed at step '{self.step_name}'",
            f"Input that caused the error: {input!r}",
            f"Original error: {type(original_exception).__name__}: {original_exception}",
        )

        super().__init__("\n".join(message))


class UnreachableCodeReachedError(Exception):
    """
    Exception raised when the code reaches a point that should be logically unreachable.
    """

    def __init__(self) -> None:
        super().__init__("Unreachable code reached.")
