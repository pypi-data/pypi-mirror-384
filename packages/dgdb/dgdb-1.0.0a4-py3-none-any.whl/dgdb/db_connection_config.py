from pydantic import BaseModel, field_validator
from pydantic_core.core_schema import ValidationInfo


class DBConnectionConfig(BaseModel):
    """Pydantic model for validating database connection configuration."""

    dialect: str
    db_user: str
    db_pass: str
    db_name: str
    db_host: str | None = None
    db_port: int | None = None

    @classmethod
    @field_validator('dialect')
    def validate_dialect(cls, v):
        supported = ["postgresql", "mysql", "oracle", "mssql", "sqlite"]
        if not any(d in v.lower() for d in supported):
            raise ValueError(f"Unsupported dialect. Must be one of: {supported}")
        return v

    @classmethod
    @field_validator('db_port')
    def validate_port(cls, v: int | None, info: ValidationInfo) -> int | None:
        """Validate port range if provided."""
        if v is not None and not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v

    @classmethod
    @field_validator('db_host')
    def validate_host(cls, v: str | None, info: ValidationInfo) -> str | None:
        """Validate host format if provided."""
        if v is not None and '..' in v:
            raise ValueError("Invalid host format")
        return v