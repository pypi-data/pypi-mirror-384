from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Dict, Any, Literal, Optional
from .auth_schema import LocaleEnum

class ExportRequest(BaseModel):
    format: Literal["csv", "xls"]            # File format selection
    destination: Literal["email", "local"]     # Destination: email or local download
    email: Optional[EmailStr] = None           # Required when destination is email
    table_data: List[Dict[str, Any]]           # Data to export
    locale: Optional[LocaleEnum] = LocaleEnum.en  # Default is 'en', but can be 'de'
    filename: Optional[str] = None           # Custom file name for the export

    # Ensure that an email is provided if the destination is email.
    @validator("email")
    @classmethod
    def email_required_if_email_destination(cls, v, values):
        if values.get("destination") == "email" and not v:
            raise ValueError("Email address must be provided when destination is email")
        return v

class ExportResponse(BaseModel):
    message: Optional[str] = Field(None, description="Message about the export process")
    filename: Optional[str] = Field(None, description="Name of the exported file (for local downloads)")
    mime_type: Optional[str] = Field(None, description="MIME type of the exported file (for local downloads)") 