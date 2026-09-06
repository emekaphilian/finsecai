from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.db.models import TenantProvenance, TenantStatus, TenantType, UserStatus


def _contains_secret_key(value: object) -> bool:
    secret_terms = ("secret", "password", "token", "api_key", "credential")
    if isinstance(value, dict):
        return any(
            any(term in str(key).lower() for term in secret_terms)
            or _contains_secret_key(nested)
            for key, nested in value.items()
        )
    if isinstance(value, list):
        return any(_contains_secret_key(item) for item in value)
    return False


class InitialTenantUser(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)
    role: str = "admin"

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("email must be valid")
        return value

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        value = value.strip().lower()
        if value == "owner":
            raise ValueError("owner cannot be assigned to a tenant user")
        if value not in {"admin", "compliance_officer", "analyst", "viewer"}:
            raise ValueError("invalid tenant user role")
        return value


class CreateTenantRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=2000)
    industry: str = Field(default="", max_length=255)
    website: str = Field(default="", max_length=500)
    contact_email: str = Field(default="", max_length=320)
    contact_phone: str = Field(default="", max_length=100)
    country: str = Field(default="", max_length=100)
    timezone: str = Field(default="UTC", max_length=100)
    configuration: dict = Field(default_factory=dict)
    initial_administrator: InitialTenantUser

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("company_name cannot be blank")
        return value

    @field_validator("configuration")
    @classmethod
    def reject_secrets(cls, value: dict) -> dict:
        if _contains_secret_key(value):
            raise ValueError("secret configuration values are not accepted")
        return value


class TenantOut(BaseModel):
    id: str
    name: str
    description: str
    tenant_type: TenantType | None
    provenance: TenantProvenance
    status: TenantStatus
    industry: str
    website: str
    contact_email: str
    contact_phone: str
    country: str
    timezone: str
    created_at: datetime
    updated_at: datetime
    user_count: int = 0
    incident_count: int = 0
    evidence_count: int = 0
    report_count: int = 0
    configured: bool = False

    model_config = {"from_attributes": True}


class TenantUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    industry: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=500)
    contact_email: str | None = Field(default=None, max_length=320)
    contact_phone: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    timezone: str | None = Field(default=None, max_length=100)
    status: TenantStatus | None = None


class TenantConfigurationOut(BaseModel):
    tenant_id: str
    configuration: dict
    updated_at: datetime

    model_config = {"from_attributes": True}


class TenantConfigurationUpdate(BaseModel):
    configuration: dict

    @field_validator("configuration")
    @classmethod
    def reject_secrets(cls, value: dict) -> dict:
        if _contains_secret_key(value):
            raise ValueError("secret configuration values are not accepted")
        return value


class TenantUserCreateRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)
    role: str = "analyst"

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("email must be valid")
        return value

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        value = value.strip().lower()
        if value == "owner" or value not in {"admin", "compliance_officer", "analyst", "viewer"}:
            raise ValueError("invalid tenant user role")
        return value


class TenantUserUpdateRequest(BaseModel):
    role: str | None = None
    status: UserStatus | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip().lower()
        if value == "owner" or value not in {"admin", "compliance_officer", "analyst", "viewer"}:
            raise ValueError("invalid tenant user role")
        return value


class TenantUserOut(BaseModel):
    id: str
    email: str
    role: str
    tenant_id: str | None
    status: UserStatus
    must_change_password: bool = False

    model_config = {"from_attributes": True}
