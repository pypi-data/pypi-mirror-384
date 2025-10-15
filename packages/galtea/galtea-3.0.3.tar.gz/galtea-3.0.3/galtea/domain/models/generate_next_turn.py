from typing import Optional

from pydantic import field_validator

from galtea.utils.from_camel_case_base_model import FromCamelCaseBaseModel


class GenerateNextTurnRequest(FromCamelCaseBaseModel):
    session_id: str
    max_turns: Optional[int]


class GenerateNextTurnResponse(FromCamelCaseBaseModel):
    next_message: str
    finished: bool
    stopping_reason: Optional[str] = None
    simulator_version: Optional[str] = None

    @field_validator("simulator_version", mode="before")
    @classmethod
    def convert_simulator_version_to_string(cls, v):
        """Convert simulator_version to string if it's an integer."""
        if v is not None and not isinstance(v, str):
            return str(v)
        return v
