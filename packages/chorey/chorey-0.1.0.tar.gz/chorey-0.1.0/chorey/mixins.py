from typing import TYPE_CHECKING, Any, Callable, TypeVar, overload

from chorey._types import Feeder, FirstInput, Input, Output
from chorey.utils import get_step_func_name

if TYPE_CHECKING:
    from chorey._types import StepFunc
    from chorey.branch import Branch
    from chorey.route import Route
    from chorey.step import Step

_A = TypeVar("_A")
_B = TypeVar("_B")
_C = TypeVar("_C")
_D = TypeVar("_D")
_E = TypeVar("_E")
_T = TypeVar("_T")
_R = TypeVar("_R")


class BranchableMixin(Feeder[FirstInput, Input, Output]):
    @overload
    def branch(
        self,
        a: "Step[Output, Any, _A]",
    ) -> "Branch[FirstInput, Output, _A]": ...

    @overload
    def branch(
        self,
        a: "Step[Output, Any, _A]",
        b: "Step[Output, Any, _B]",
    ) -> "Branch[FirstInput, Output, _A, _B]": ...

    @overload
    def branch(
        self,
        a: "Step[Output, Any, _A]",
        b: "Step[Output, Any, _B]",
        c: "Step[Output, Any, _C]",
    ) -> "Branch[FirstInput, Output, _A, _B, _C]": ...

    @overload
    def branch(
        self,
        a: "Step[Output, Any, _A]",
        b: "Step[Output, Any, _B]",
        c: "Step[Output, Any, _C]",
        d: "Step[Output, Any, _D]",
    ) -> "Branch[FirstInput, Output, _A, _B, _C, _D]": ...

    @overload
    def branch(
        self,
        a: "Step[Output, Any, _A]",
        b: "Step[Output, Any, _B]",
        c: "Step[Output, Any, _C]",
        d: "Step[Output, Any, _D]",
        e: "Step[Output, Any, _E]",
    ) -> "Branch[FirstInput, Output, _A, _B, _C, _D, _E]": ...

    def branch(self, *args: "Step"):  # type: ignore
        from chorey.branch import Branch

        return Branch(steps=list(args), previous=self)


class RoutableMixin(Feeder[FirstInput, Input, Output]):
    def route(
        self,
        *choices: "Step[Output, Any, _T]",
        selector: Callable[[Output], int],
        decision_label: str | None = None,
    ) -> "Route[FirstInput, Output, _T]":
        from chorey.route import Route

        return Route(
            choices=list(choices),
            selector=selector,
            decision_label=decision_label,
            previous=self,  # type: ignore
        )


class NextableMixin(Feeder[FirstInput, Input, Output]):
    def next(
        self,
        func: "StepFunc[Output, _R]",
        /,
        *,
        description: str | None = None,
        name: str | None = None,
    ) -> "Step[FirstInput, Output, _R]":
        from chorey.step import Step

        return Step[FirstInput, Output, _R](
            func=func,
            name=name or get_step_func_name(func),
            description=description,
            previous=self,
        )


class GetFirstInputMixin:
    @property
    def first_input_type(self) -> type:
        if (previous := getattr(self, "previous", None)) is not None:
            if (first_input_type := getattr(previous, "first_input_type", None)) is not None:
                return first_input_type
            else:
                raise TypeError(
                    f"Cannot determine first input type because previous {type(previous)} does not have it",
                )  # pragma: no cover
        else:
            from chorey.step import Step
            from chorey.utils import get_input_output_type_from_step

            if isinstance(self, Step):
                input_type, _ = get_input_output_type_from_step(self)
                return input_type
            else:
                raise TypeError(
                    f"Cannot determine first input type for {type(self)} without previous step",
                )  # pragma: no cover
