import sys
from typing import Any, Dict

from examiner.actions import ExaminerAction

try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


if PYDANTIC_AVAILABLE:
    class ExaminerResponse(BaseModel):
        """
        Pydantic Schema enforcing structured LLM outputs from Qwen.
        Level 2 Validation: Ensures output contains a non-empty response string
        and an action matching the ExaminerAction Enum.
        """
        response: str = Field(..., description="The natural spoken response of the IELTS examiner.")
        action: ExaminerAction = Field(..., description="The action performed by the examiner (must be a valid ExaminerAction enum member).")
else:
    class ExaminerResponse:
        """
        Lightweight fallback ExaminerResponse class when Pydantic is not installed.
        Enforces ExaminerAction Enum validation identically to Pydantic schema.
        """
        def __init__(self, response: str, action: Any):
            if not response or not isinstance(response, str):
                raise ValueError("ExaminerResponse response must be a non-empty string.")
            
            if isinstance(action, ExaminerAction):
                self.action = action
            else:
                enum_act = ExaminerAction._missing_(str(action))
                if enum_act is None:
                    raise ValueError(f"Invalid ExaminerAction: '{action}'. Must be one of {[e.value for e in ExaminerAction]}.")
                self.action = enum_act
            
            self.response = response.strip()

        def dict(self) -> Dict[str, Any]:
            return {"response": self.response, "action": self.action.value}

        def model_dump(self) -> Dict[str, Any]:
            return self.dict()

        def __repr__(self):
            return f"ExaminerResponse(response='{self.response}', action={self.action})"


__all__ = ["ExaminerResponse", "ExaminerAction"]
