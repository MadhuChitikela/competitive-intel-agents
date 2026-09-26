"""Shared LangGraph state + structured output models."""
from typing import TypedDict, Annotated
import operator
import os
from pydantic import BaseModel, Field
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
    from langchain_groq import ChatGroq

    gemini_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
    groq_key = settings.groq_api_key or os.getenv("GROQ_API_KEY", "")
    groq_model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    # If a valid Groq key is present, use it as primary with Gemini as fallback
    if groq_key and not groq_key.startswith("mock_"):
        primary = ChatGroq(
            model=groq_model,
            api_key=groq_key,
            temperature=0,
        )
        if gemini_key:
            from langchain_google_genai import ChatGoogleGenerativeAI
            fallback = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=gemini_key,
                temperature=0,
            )
            return primary.with_fallbacks([fallback])
        return primary

    # If only Gemini is provided or Groq is a mock key
    if gemini_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=gemini_key,
            temperature=0,
        )

    return ChatGroq(
        model=groq_model,
        api_key=groq_key,
        temperature=0,
    )
