# schemas/afas_response.py
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field

class AFASResponseSchema(BaseModel):
    ok: bool = Field(...)
    status_code: int = Field(..., ge=100, le=599)
    reason: str = Field(default="")
    request_url: str = Field(...)
    headers: Dict[str, str] = Field(default_factory=dict)
    request_id: Optional[str] = None
    location: Optional[str] = None

    # Body as returned by AFAS
    body_json: Optional[Any] = None
    body_text: Optional[str] = None

    # AFAS success metadata (decoded from headers when present)
    # Many AFAS update calls return important info here.
    result_json: Optional[Any] = None
    result_text: Optional[str] = None

    # Request payload for debugging successful requests with unexpected results
    request_payload: Optional[Dict[str, Any]] = None
