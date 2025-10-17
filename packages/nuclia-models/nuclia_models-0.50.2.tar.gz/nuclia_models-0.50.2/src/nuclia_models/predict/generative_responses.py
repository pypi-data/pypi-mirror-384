from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field

from nuclia_models.common.consumption import Consumption, ConsumptionGenerative

GenerativeResponseType = Literal["text", "object", "meta", "citations", "status", "footnote_citations"]


class TextGenerativeResponse(BaseModel):
    type: Literal["text"] = "text"
    text: str


class JSONGenerativeResponse(BaseModel):
    type: Literal["object"] = "object"
    object: dict[str, Any]


class MetaGenerativeResponse(BaseModel):
    type: Literal["meta"] = "meta"
    input_tokens: int
    output_tokens: int
    timings: dict[str, float]
    input_nuclia_tokens: Optional[float] = None
    output_nuclia_tokens: Optional[float] = None


class CitationsGenerativeResponse(BaseModel):
    type: Literal["citations"] = "citations"
    citations: dict[str, Any]


class FootnoteCitationsGenerativeResponse(BaseModel):
    """Maps ids in the footnote citations to query_context keys (normally paragraph ids)
    e.g.,
    { "block-AA": "f44f4e8acbfb1d48de3fd3c2fb04a885/f/f44f4e8acbfb1d48de3fd3c2fb04a885/73758-73972", ... }
    If the query_context is a list, it will map to 1-based indices as strings
    e.g., { "block-AA": "1", "block-AB": "2", ... }
    """

    type: Literal["footnote_citations"] = "footnote_citations"
    footnote_to_context: dict[str, str]


class RerankGenerativeResponse(BaseModel):
    type: Literal["rerank"] = "rerank"
    context_scores: dict[str, float]


class StatusGenerativeResponse(BaseModel):
    type: Literal["status"] = "status"
    code: str
    details: Optional[str] = None


class CallArguments(BaseModel):
    name: Optional[str]
    arguments: dict[str, Any]


class ToolCall(BaseModel):
    function: CallArguments
    id: Optional[str] = None


class ToolsGenerativeResponse(BaseModel):
    type: Literal["tools"] = "tools"
    tools: dict[str, list[ToolCall]]


class ReasoningGenerativeResponse(BaseModel):
    type: Literal["reasoning"] = "reasoning"
    text: str


GenerativeResponse = Union[
    TextGenerativeResponse,
    ReasoningGenerativeResponse,
    JSONGenerativeResponse,
    MetaGenerativeResponse,
    CitationsGenerativeResponse,
    FootnoteCitationsGenerativeResponse,
    StatusGenerativeResponse,
    RerankGenerativeResponse,
    ToolsGenerativeResponse,
    ConsumptionGenerative,
]


class GenerativeChunk(BaseModel):
    chunk: GenerativeResponse = Field(..., discriminator="type")


class GenerativeFullResponse(BaseModel):
    input_tokens: Optional[int] = None  # TODO: deprecate
    output_tokens: Optional[int] = None  # TODO: deprecate
    timings: Optional[dict[str, float]] = None
    citations: Optional[dict[str, Any]] = None
    citation_footnote_to_context: Optional[dict[str, str]] = Field(
        default=None,
        description="For the LLM footnote citations feature, "
        "maps footnote ids to context keys (normally paragraph ids)",
    )
    code: Optional[str] = None
    details: Optional[str] = None
    answer: str
    reasoning: Optional[str] = None
    object: Optional[dict[str, Any]] = None
    input_nuclia_tokens: Optional[float] = None  # TODO: deprecate
    output_nuclia_tokens: Optional[float] = None  # TODO: deprecate
    tools: Optional[dict[str, list[ToolCall]]] = None
    consumption: Optional[Consumption] = None
