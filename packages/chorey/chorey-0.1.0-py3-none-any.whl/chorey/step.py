import asyncio
from dataclasses import dataclass, field
from types import EllipsisType
from typing import Any, Awaitable, Callable, Final, Generic, TypeVar

from pydantic import BaseModel
from pydantic import ConfigDict as ModelConfig
from pydantic import Field

from chorey._types import Feeder, FirstInput, Input, Output, StepFunc
from chorey.error import PipelineError, UnreachableCodeReachedError
from chorey.mixins import BranchableMixin, GetFirstInputMixin, NextableMixin, RoutableMixin
from chorey.utils import get_step_func_name

R = TypeVar("R")

OnFailureFunc = Callable[[Input, Exception], None | Awaitable[None]]
"""
Callback function to be called when the step fails.
Takes the input that caused the failure and the exception as arguments.
Must return None as it is only for side effects (e.g., logging).
"""


class FailureConfig(BaseModel, Generic[Input]):
    max_attempts: int = Field(default=1, ge=1)
    delay_seconds: float = Field(default=0.0, ge=0.0)
    on_failure: OnFailureFunc[Input] | None = None

    model_config = ModelConfig(frozen=True)

    def copy_with(
        self,
        *,
        max_attempts: int | None = None,
        delay_seconds: float | None = None,
        on_failure: OnFailureFunc[Input] | None | EllipsisType = ...,
    ) -> "FailureConfig":
        return FailureConfig(
            max_attempts=max_attempts if max_attempts is not None else self.max_attempts,
            delay_seconds=delay_seconds if delay_seconds is not None else self.delay_seconds,
            on_failure=self.on_failure if on_failure is ... else on_failure,
        )


@dataclass(frozen=True)
class Step(
    RoutableMixin[FirstInput, Input, Output],
    BranchableMixin[FirstInput, Input, Output],
    NextableMixin[FirstInput, Input, Output],
    GetFirstInputMixin,
    Feeder[FirstInput, Input, Output],
):
    """
    Represents a step in a processing pipeline that mutates the data it receives.
    Each step is linked to its previous one to allow chaining of operations.

    Note:
        The reason why backward linkage is used is to ensure that the first input type is preserved
        throughout the chain of steps.
    """

    func: Final[StepFunc[Input, Output]]
    """ The function that the step will execute. """

    name: Final[str]
    """ The name of the step, either given or derived from the function name. """

    description: Final[str | None] = None
    """
    An optional description of what the step does. Will be displayed in the graph output.
    """

    failure_config: FailureConfig | None = field(default=None)
    """
    Configuration for handling failures in the step.
    """

    previous: "Feeder[FirstInput, Input, Any] | None" = field(default=None)
    """
    A reference to the previous step in the chain. None if this is the first step.
    """

    async def __call__(self, input: Input) -> Output:
        """
        Calls the step's function with the given input and returns the output.
        """

        failure_config = self.failure_config or FailureConfig()

        for attempt in range(1, failure_config.max_attempts + 1):
            try:
                return await self.func(input)
            except Exception as e:
                if attempt == failure_config.max_attempts:
                    if failure_config.on_failure is not None:
                        if asyncio.iscoroutinefunction(failure_config.on_failure):
                            await failure_config.on_failure(input, e)
                        else:
                            failure_config.on_failure(input, e)

                    raise PipelineError(step=self, original_exception=e, input=input) from e
                else:
                    if failure_config.delay_seconds > 0:
                        await asyncio.sleep(failure_config.delay_seconds)

        raise UnreachableCodeReachedError()

    async def feed(self, input: FirstInput) -> Output:
        """
        Feeds the input through the chain of steps, starting from the first step to the current one.
        """

        if self.previous is not None:
            intermediate = await self.previous.feed(input)
            return await self(intermediate)
        else:
            return await self(input)  # type: ignore

    def copy_with(
        self,
        *,
        previous: "Feeder[FirstInput, Input, Any] | None | EllipsisType" = ...,
        failure_config: FailureConfig | None | EllipsisType = ...,
    ) -> "Step[FirstInput, Input, Output]":
        return Step(
            func=self.func,
            name=self.name,
            description=self.description,
            failure_config=self.failure_config if failure_config is ... else failure_config,
            previous=self.previous if previous is ... else previous,
        )

    def retry(
        self,
        max_attempts: int = 3,
        delay_seconds: float = 1.0,
    ) -> "Step[FirstInput, Input, Output]":
        return self.copy_with(
            failure_config=(self.failure_config or FailureConfig()).copy_with(
                max_attempts=max_attempts,
                delay_seconds=delay_seconds,
            )
        )

    def on_failure_do(
        self,
        func: OnFailureFunc,
    ) -> "Step[FirstInput, Input, Output]":
        """
        Sets a callback function to be called if the step fails.
        The function takes the input that caused the failure and the exception as arguments.
        """

        return self.copy_with(
            failure_config=(self.failure_config or FailureConfig()).copy_with(
                on_failure=func,
            )
        )


def step(
    func: StepFunc[Input, Output],
    /,
    *,
    description: str | None = None,
    name: str | None = None,
) -> Step[Input, Input, Output]:
    """
    Sets up the initial step in the processing pipeline.
    """

    return Step(func, description=description, name=name or get_step_func_name(func))
