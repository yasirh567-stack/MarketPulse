from __future__ import annotations

from pydantic import BaseModel, field_validator


class AssistantQueryRequest(BaseModel):
    ticker: str
    question: str

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question must not be empty")
        if len(v) > 500:
            raise ValueError("Question is too long (max 500 characters)")
        return v


class CitationResponse(BaseModel):
    title: str
    url: str | None
    published_at: str
    kind: str


class AssistantQueryResponse(BaseModel):
    ticker: str
    question: str
    answer: str
    citations: list[CitationResponse]
    disclaimer: str
    data_sufficient: bool
