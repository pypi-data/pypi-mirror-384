from typing import Awaitable, Callable, Protocol, TypeVar

FirstInput = TypeVar("FirstInput", contravariant=True)
Input = TypeVar("Input", contravariant=True)
Output = TypeVar("Output", covariant=True)


StepFunc = Callable[[Input], Awaitable[Output]]


class Feeder(Protocol[FirstInput, Input, Output]):
    async def __call__(self, input: Input) -> Output:
        """
        Processes an input of type `Input` and produces an output of type `Output`.
        """

        ...

    async def feed(self, input: FirstInput) -> Output:
        """
        Feeds a chain of Feeders starting from an initial input of type `FirstInput`
        and produces an output of type `Output`.
        """

        ...
