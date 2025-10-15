from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel


class DynamicStructuredOutputRequest(BaseModel):
    """Request model for dynamic structured output.

    Matches existing services' request payload for compatibility.
    """

    text: str
    json_schema: Dict[str, Any]
    schema_name: str = "DynamicSchema"
    session_id: Optional[str] = None
    prompt: Optional[str] = None
    prompt_id: Optional[str] = None

