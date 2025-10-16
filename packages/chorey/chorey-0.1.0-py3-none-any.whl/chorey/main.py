from dataclasses import dataclass
from typing import TypeVar

from pype import PypelineContext, step
from pype.mermaid import mermaid


@dataclass(frozen=True)
class Context:
    force_full_analysis: bool
    db_session: str  # Placeholder for an actual DB session object


@dataclass
class Document:
    id: int
    content: str


@dataclass
class Summary:
    document_id: int
    summary_text: str


@dataclass
class FullAnalysis:
    document_id: int
    word_count: int
    sentiment: str


# helper types to make the signatures cleaner
T = TypeVar("T")
Input = PypelineContext[T, Context]
Output = Input


async def fetch_document(input: Input[int]) -> Output[Document]:
    # unpack the PypelineContext to work with its parts
    doc_id, ctx = input.parts

    # simulate fetching a document from a database or API

    # use .with_data() to keep the context while changing the data
    return input.with_data(Document(id=doc_id, content="This is a sample document content."))


async def summarize_document(input: Input[Document]) -> Output[Summary]:
    # unpack the PypelineContext to work with its parts
    doc, ctx = input.parts

    # simulate summarizing the document

    return input.with_data(Summary(document_id=doc.id, summary_text="This is a summary."))


async def analyze_document(input: Input[Document]) -> Output[FullAnalysis]:
    doc, ctx = input.parts

    # simulate performing a full analysis of the document

    return input.with_data(FullAnalysis(document_id=doc.id, word_count=len(doc.content.split()), sentiment="Positive"))


async def store_processing_result(input: Input[Summary] | Input[FullAnalysis]) -> None:
    result, ctx = input.parts

    # simulate storing the result
    print(f"Storing result: {result}")
    print(f"Type of result: {type(result)}")


def selector(input: Input[Document]) -> int:
    doc, ctx = input.parts

    if ctx.force_full_analysis:
        return 1  # force full analysis if the context says so

    # same as before
    return 0 if len(doc.content) < 50 else 1


pipeline = (
    step(fetch_document)
    .route(step(summarize_document), step(analyze_document), selector=selector, decision_label="Document Length Check")
    .next(store_processing_result)
)

if __name__ == "__main__":
    print(mermaid(pipeline))
