import re
from typing import Any, Dict

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class SchemaEvent(BaseModel):
    url: str
    endpoint: str
    method: str
    status_code: int
    request_headers: Dict[str, str]
    request_body: Any
    response_headers: Dict[str, str]
    response_body: Any
    duration_ms: int


class SchemaUserConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_key: str
    secret_key: str = Field(..., min_length=43, max_length=43)
    endpoint: str = Field(default="https://main.aikocorp.ai/api/monitor/ingest")
    enabled: bool = True

    @field_validator("project_key", mode="before")
    @classmethod
    def check_project_key(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise TypeError("project_key must be a string")
        pattern = re.compile(r"^pk_[A-Za-z0-9_-]{22}$")
        if not pattern.match(v):
            raise ValueError("project_key must start with 'pk_' followed by 22 base64url characters")
        return v

    @model_validator(mode="before")
    @classmethod
    def validate_endpoint(cls, data: Any) -> Any:
        ep = data.get("endpoint")
        if ep is None:
            return data
        if not isinstance(ep, str):
            raise TypeError("endpoint must be a string")
        if not (
            (ep.startswith("http://localhost:") and ep.endswith("/api/monitor/ingest"))
            or ep == "https://main.aikocorp.ai/api/monitor/ingest"
        ):
            raise ValueError(
                "endpoint must match http://localhost:PORT/monitor/batch "
                "or be 'https://main.aikocorp.ai/api/monitor/ingest'"
            )
        return data
