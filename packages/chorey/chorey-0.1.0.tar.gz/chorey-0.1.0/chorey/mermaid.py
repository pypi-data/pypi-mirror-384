from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generator, Iterator, Protocol, TypeGuard

from chorey.utils import MissingFeatureError, get_input_output_type_from_step, get_type_name_for_display

try:
    from uuid import uuid4
except ImportError as e:
    raise MissingFeatureError("mermaid") from e

if TYPE_CHECKING:
    from chorey import Step


class _UnexpectedTypeError(TypeError):
    def __init__(self, ty: type | object) -> None:
        type_ = ty if isinstance(ty, type) else type(ty)

        super().__init__(f"Unexpected type: {type_}")


def _new_id() -> str:
    """
    Generates a new unique identifier for nodes in the mermaid diagram.
    They will always start with "id-" to ensure they do not start with a digit,
    as mermaid does not support node IDs that start with them.
    """

    return f"id-{uuid4().hex}"


@dataclass
class _Edge:
    """
    Represents an edge in the mermaid diagram, connecting nodes.
    """

    id: str
    type: str


class _MermaidGenerator(Protocol):
    def generate(self, *edges: _Edge) -> Iterator[str]:
        """Generate mermaid edge definitions from given from-edges."""
        ...

    @property
    def out_edges(self) -> Iterator[_Edge]:
        """Get the outgoing edges from this node."""
        ...


class _HasIdNameDescription(Protocol):
    id: str
    name: str
    description: str | None


class _MermaidNode(_HasIdNameDescription, _MermaidGenerator, Protocol):
    """
    Represents a node datastructure in the mermaid diagram.
    """

    pass


@dataclass
class _Input(_MermaidNode):
    """
    Input node for the mermaid diagram. Only one is used per diagram as the starting point.
    """

    out_type: str
    id: str = field(default="input", init=False)
    name: str = field(default="Input", init=False)
    description: str | None = field(default=None, init=False)

    def generate(self, *edges: _Edge) -> Generator[str, None, None]:
        yield f'    {self.id}["{self.name}"]'

    @property
    def out_edges(self) -> Iterator[_Edge]:
        yield _Edge(id=self.id, type=self.out_type)


@dataclass
class _Output(_MermaidNode):
    """
    Output node for the mermaid diagram. Only one is used per diagram as the ending point.
    """

    id: str = field(default="output", init=False)
    name: str = field(default="Output", init=False)
    description: str | None = field(default=None, init=False)

    def generate(self, *edges: _Edge) -> Iterator[str]:
        for edge in edges:
            yield f'    {edge.id} -->|"{edge.type}"| {self.id}["{self.name}"]'

    @property
    def out_edges(self) -> Iterator[_Edge]:
        yield from ()


@dataclass
class _Step(_MermaidNode):
    """
    `Step`'s representation for the mermaid diagram.
    """

    name: str
    description: str | None
    input_type: str
    output_type: str
    id: str = field(default_factory=_new_id)

    def generate(self, *edges: _Edge) -> Iterator[str]:
        label = f"<b>{self.name}</>"
        if self.description is not None:
            label += f"</br><sub>{self.description}</sub>"

        for edge in edges:
            yield f'    {edge.id} -->|"{edge.type}"| {self.id}["{label}"]'

    @property
    def out_edges(self) -> Iterator[_Edge]:
        yield _Edge(id=self.id, type=self.output_type)


@dataclass
class _Branch(_MermaidNode):
    """
    `Branch`'s representation for the mermaid diagram.
    """

    branches: list[list[_MermaidNode]]
    """
    A list of branches, where each branch is a list of `_MermaidNode` instances.
    """

    # these fields are not used for branches, probably should be refactored later
    id: str = field(default_factory=_new_id, init=False)
    name: str = field(default="<BRANCH>", init=False)
    description: str | None = field(default=None, init=False)

    def generate(self, *edges: _Edge) -> Generator[str, None, None]:
        for branch in self.branches:
            if not branch:
                continue

            # the branch will be from start-to-end at first, but we actually
            # need it to be from end-to-start to generate the edges correctly
            branch = list(reversed(branch))

            # generate the edges up until the last (actually first) step in the branch
            for current, next in zip(branch, branch[1:]):
                yield from current.generate(*next.out_edges)

            # finally, the last step in the branch (actually the first)
            # will connect the previous edges to the start of this branch
            yield from branch[-1].generate(*edges)

    @property
    def out_edges(self) -> Iterator[_Edge]:
        # we only need to yield the out_edges of the last step in each branch
        # because those are the ones that will connect to the next step after the branch
        for branch in self.branches:
            if not branch:
                continue
            yield from branch[-1].out_edges

    @property
    def input_type(self) -> str:
        # will never happen, hopefully
        if not self.branches:
            return "None"

        # since all paths in a branch must have the same input type at first,
        # we can just take the first branch and the first generator in it
        # and return its input type
        first_generator = self.branches[0][0]

        if _ensure_generator_type(first_generator):
            return first_generator.input_type

        raise _UnexpectedTypeError(first_generator)


@dataclass
class _Route(_MermaidNode):
    """
    `Branch`'s representation for the mermaid diagram.
    """

    branches: list[list[_MermaidNode]]
    """
    A list of branches the router chooses rom, where each branch is a list of `_MermaidNode` instances.
    """

    decision_label: str | None

    # just like _Branch, these fields are also not used
    id: str = field(default_factory=_new_id, init=False)
    name: str = field(default="<ROUTE>", init=False)
    description: str | None = field(default=None, init=False)

    def generate(self, *edges: _Edge) -> Generator[str, None, None]:
        label = self.decision_label or ""
        yield f'    {self.id}{{"{label}"}}'

        for edge in edges:
            yield f'    {edge.id} -->|"{edge.type}"| {self.id}'

        for i, branch in enumerate(self.branches):
            if not branch:
                continue

            branch = list(reversed(branch))

            for current, next in zip(branch, branch[1:]):
                yield from current.generate(*next.out_edges)

            start_of_choice = branch[-1]

            if _ensure_generator_type(start_of_choice):
                condition_label = f"Choice {i}"
                yield from start_of_choice.generate(
                    _Edge(
                        id=self.id,
                        type=f"{condition_label} ({start_of_choice.input_type})",
                    )
                )
            else:
                raise _UnexpectedTypeError(start_of_choice)

    @property
    def out_edges(self) -> Iterator[_Edge]:
        for branch in self.branches:
            if not branch:
                continue
            yield from branch[-1].out_edges

    @property
    def input_type(self) -> str:
        if not self.branches:
            return "None"

        first_generator = self.branches[0][0]

        if _ensure_generator_type(first_generator):
            return first_generator.input_type

        raise _UnexpectedTypeError(first_generator)


def _ensure_generator_type(g: _MermaidGenerator) -> TypeGuard[_Step | _Branch | _Route]:
    """
    Currently only `_Step` and `_Branch` are valid types for generators in the mermaid diagram.
    But maybe in the future there will be more types, that is why I generalized almost everything
    in this file.
    """

    return isinstance(g, (_Step, _Branch, _Route))


def mermaid(step: "Step") -> str:
    """
    Generate a mermaid diagram from a given pipeline.
    The generated string can be used in mermaid live editor:
    https://mermaid.live/
    """

    from chorey import Branch, Route, Step

    # the lines of the mermaid diagram
    lines: list[str] = []
    lines.append("flowchart TD")

    def visit(n: Step | Branch | Route) -> Iterator[_MermaidNode]:
        """
        Recursively turns a `Step` or `Branch` into their mermaid representation.
        """

        if isinstance(n, Step):
            input_type, output_type = get_input_output_type_from_step(n)

            yield _Step(
                name=n.name,
                description=n.description,
                input_type=get_type_name_for_display(input_type),
                output_type=get_type_name_for_display(output_type),
            )
        elif isinstance(n, Branch):
            branches: list[list[_MermaidNode]] = []
            for branch in n.steps:
                items: list[_MermaidNode] = []
                items.extend(collect(branch))
                branches.append(items)
            yield _Branch(branches=branches)
        elif isinstance(n, Route):
            branches: list[list[_MermaidNode]] = []
            for branch in n.choices:
                items: list[_MermaidNode] = []
                items.extend(collect(branch))
                branches.append(items)
            yield _Route(branches=branches, decision_label=n.decision_label)
        else:
            raise _UnexpectedTypeError(n)

    def collect(n: Step | Branch | Route) -> Iterator[_MermaidNode]:
        """
        Flattens the pipeline into a series of mermaid nodes.
        """

        if n.previous is None:
            yield from visit(n)
        elif isinstance(n.previous, (Step, Branch, Route)):
            yield from collect(n.previous)
            yield from visit(n)
        else:
            raise _UnexpectedTypeError(n.previous)

    items: list[_MermaidNode] = []

    pipeline_items = list(collect(step))

    if (item := pipeline_items[0]) and _ensure_generator_type(item):
        items.append(_Input(out_type=item.input_type))
    else:
        raise _UnexpectedTypeError(item)

    items.extend(pipeline_items)
    items.append(_Output())

    # we need to generate the edges from the end to the start
    items.reverse()

    # generate the edges between all nodes
    for current, next in zip(items, items[1:]):
        lines.extend(current.generate(*next.out_edges))

    # finally, the input node
    lines.extend(items[-1].generate(*items[-2].out_edges))

    return "\n".join(lines)
