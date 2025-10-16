"""schemas/git_ssh.py"""

from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import datetime


class SSHBase(BaseModel):
    """Base SSH key model with common fields."""
    key_name: str
    description: Optional[str] = None

    @field_validator("key_name")
    def validate_key_name(cls, v) -> str:
        import re
        if not isinstance(v, str):
            raise ValueError("SSH key name must be a string.")
        if len(v) > 20:
            raise ValueError("SSH key name must be at most 20 characters long.")
        # Must start with letter, end with letter or digit
        # Can contain letters, numbers, and underscores
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*[A-Za-z0-9]|[A-Za-z]", v):
            raise ValueError(
                "SSH key name must start with a letter, end with a letter or digit, "
                "and contain only letters, numbers, and underscores (_)!"
            )
        return v


class SSHSave(SSHBase):
    """Model for creating a new SSH key."""
    public_key: str
    private_key: str


class SSHUpdate(BaseModel):
    """Model for updating an existing SSH key."""
    description: Optional[str] = None
    public_key: Optional[str] = None
    private_key: Optional[str] = None


class SSHRead(SSHBase):
    """Model for reading/displaying SSH key data."""
    public_key: str
    private_key: str
    created_date: Optional[datetime] = None

    class Config:
        from_attributes = True
