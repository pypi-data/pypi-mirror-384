from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
R = TypeVar("R")
Context = TypeVar("Context")


@dataclass
class ChoreyContext(Generic[T, Context]):
    """
    Wraps data with additional context information.
    Recommended for use as input and output types for nodes in a pype pipeline,
    as when visualizing the pipeline, the data type is shown instead of this wrapper or
    the context.

    Example:
    ```python
    from dataclasses import dataclass
    from typing import TypeVar
    from chorey.context import ChoreyContext
    from chorey.node import node
    from chorey.display import print_table_from_node

    @dataclass
    class Context:
        id: str

    T = TypeVar("T")
    Input = ChoreyContext[T, Context]
    Output = Input

    async def first(input: Input[int]) -> Output[str]:
        # access context information
        print(input.context.id)
        return input.with_data("example" * input.data)

    async def second(input: Input[str]) -> Output[float]:
        ...

    pipeline = node(first).next(second)

    pipeline.feed(Input(data=42, context=Context(id="example")))

    # displays input and output types without the ChoreyContext wrapper
    # e.g. int -> str -> float
    print(print_table_from_node(pipeline))
    ```
    """

    data: T
    context: Context

    def with_data(self, new_data: R) -> "ChoreyContext[R, Context]":
        """
        Creates a new `ChoreyContext` with the same context but different data.
        """

        return ChoreyContext(data=new_data, context=self.context)

    @property
    def parts(self) -> tuple[T, Context]:
        return (self.data, self.context)
