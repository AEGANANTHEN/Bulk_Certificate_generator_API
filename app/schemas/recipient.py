import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+$")

class RecipientInput(BaseModel):
    name: str = Field(..., description="Full name of the certificate recipient")
    email: Optional[str] = Field(None, description="Optional recipient email address")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Recipient name cannot be empty or only whitespace")
        if len(trimmed) > 200:
            raise ValueError("Recipient name exceeds 200 characters limit")
        return trimmed

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        trimmed = v.strip()
        if not trimmed:
            return None
        if not EMAIL_REGEX.match(trimmed):
            raise ValueError(f"Invalid email address format: '{trimmed}'")
        return trimmed.lower()


class RecipientRawInput(BaseModel):
    """
    Lenient schema for bulk input allowing tracking of individual validation failures
    without aborting the whole job request.
    """
    name: Optional[str] = None
    email: Optional[str] = None
