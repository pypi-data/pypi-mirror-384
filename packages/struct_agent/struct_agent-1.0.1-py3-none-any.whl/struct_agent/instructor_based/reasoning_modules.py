from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class NextAction(str, Enum):
    """Allowed directives emitted by the agent."""

    CONTINUE = "continue"
    VALIDATE = "validate"
    FINAL_ANSWER = "final_answer"
    RESET = "reset"

class ReasoningStep(BaseModel):
    """Single reasoning step returned by the agent."""

    title: Optional[str] = Field(None, description="Short step title.")
    action: Optional[str] = Field(None, description="Planned action written in first person.")
    result: Optional[str] = Field(None, description="Outcome summary for the step.")
    reasoning: Optional[str] = Field(None, description="Why this step matters.")
    next_action: Optional[NextAction] = Field(None, description="continue, validate, final_answer, or reset.")
    confidence: Optional[float] = Field(None, description="Confidence score between 0.0 and 1.0.")

class ReasoningSteps(BaseModel):
    """Ordered reasoning steps returned by the agent."""

    reasoning_steps: List[ReasoningStep] = Field(..., description="Ordered reasoning steps.")

__all__ = ["NextAction", "ReasoningStep", "ReasoningSteps"]