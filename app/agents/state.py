"""Shared LangGraph state + structured output models."""
from typing import TypedDict, Annotated
import operator
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from app.config import settings


# ------------------------- Graph state -------------------------
class AgentState(TypedDict, total=False):
    company: str
    signals: list[dict]
    analyses: list[dict]
    brief: str
    audit: dict
    retries: int
    messages: Annotated[list[str], operator.add]
    trace_ids: Annotated[list[str], operator.add]


# -------------------- Structured LLM outputs --------------------
class SignalAnalysis(BaseModel):
    signal_id: str = Field(description="ID of the signal being analyzed")
    category: str = Field(description="One of: product, funding, hiring, partnership, other")
    threat_score: int = Field(ge=0, le=100, description="0-100 threat score")
    reasoning: str = Field(description="One sentence explaining the score")


class AnalysisResult(BaseModel):
    analyses: list[SignalAnalysis]


class BriefOutput(BaseModel):
    brief_markdown: str = Field(
        description="Full brief in markdown with sections: "
                    "Executive Summary, Threats, Opportunities, Recommendations"
    )


def get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.groq_api_key,
        temperature=0,
    )
