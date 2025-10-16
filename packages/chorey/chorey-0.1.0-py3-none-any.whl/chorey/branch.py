import asyncio
from dataclasses import dataclass, field
from types import EllipsisType
from typing import TYPE_CHECKING, Any, Generic, TypeVar, TypeVarTuple

from chorey._types import Feeder, FirstInput, Input, StepFunc
from chorey.mixins import GetFirstInputMixin
from chorey.utils import get_step_func_name

if TYPE_CHECKING:
    from chorey.step import Step

OrderedOutcomes = TypeVarTuple("OrderedOutcomes")
R = TypeVar("R")


@dataclass(frozen=True)
class Branch(
    Generic[FirstInput, Input, *OrderedOutcomes],
    GetFirstInputMixin,
    Feeder[FirstInput, Input, tuple[*OrderedOutcomes]],
):
    steps: list["Step[Input, Any, Any]"] = field(default_factory=list)

    previous: Feeder[FirstInput, Input, Any] | None = field(default=None)

    async def __call__(self, input: Input) -> tuple[*OrderedOutcomes]:
        results = await asyncio.gather(*(step.feed(input) for step in self.steps))
        return tuple(results)  # type: ignore

    async def feed(
        self,
        input: FirstInput,
    ) -> tuple[*OrderedOutcomes]:
        if self.previous is not None:
            intermediate = await self.previous.feed(input)
            return await self(intermediate)
        else:
            return await self(input)  # type: ignore

    def copy_with(
        self,
        *,
        steps: list["Step[Input, Any, Any]"] | None = None,
        previous: Feeder[FirstInput, Input, Any] | None | EllipsisType = ...,
    ) -> "Branch[FirstInput, Input, *OrderedOutcomes]":
        return Branch(
            steps=self.steps if steps is None else steps,
            previous=self.previous if previous is ... else previous,
        )

    def merge(
        self,
        func: StepFunc[tuple[*OrderedOutcomes], R],
        /,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> "Step[FirstInput, tuple[*OrderedOutcomes], R]":
        from chorey.step import Step

        return Step(
            func=func,
            name=name or get_step_func_name(func),
            description=description,
            previous=self,  # type: ignore
        )
