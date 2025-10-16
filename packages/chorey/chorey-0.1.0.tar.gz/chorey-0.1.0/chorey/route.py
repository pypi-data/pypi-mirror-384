from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from chorey._types import Feeder, FirstInput, Input, Output
from chorey.mixins import BranchableMixin, GetFirstInputMixin, NextableMixin, RoutableMixin

if TYPE_CHECKING:
    from chorey.step import Step

T = TypeVar("T")


@dataclass(frozen=True, kw_only=True)
class Route(
    NextableMixin[FirstInput, Input, Output],
    BranchableMixin[FirstInput, Input, Output],
    RoutableMixin[FirstInput, Input, Output],
    GetFirstInputMixin,
    Feeder[FirstInput, Input, Output],
):
    choices: list["Step[Input, Any, Output]"] = field(default_factory=list)
    selector: Callable[[Input], int] = field(default=lambda _: 0)

    decision_label: str | None = field(default=None)
    """
    The label to use for the decision point in the mermaid diagram.
    If None, empty diamond will be used.
    """

    previous: Feeder[FirstInput, Input, Any] | None = field(default=None)

    async def __call__(self, input: Input) -> Output:
        index = self.selector(input)
        if index < 0 or index >= len(self.choices):
            raise IndexError(f"Selector returned out-of-bounds index {index} for choices of length {len(self.choices)}")

        step = self.choices[index]
        return await step.feed(input)

    async def feed(
        self,
        input: FirstInput,
    ) -> Output:
        if self.previous is not None:
            intermediate = await self.previous.feed(input)
            return await self(intermediate)
        else:
            return await self(input)  # type: ignore
