from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from nys_constants.nys_constants import StorageStatus

class StorageResponse(BaseModel):
    """Standard response model for maintenance operations like starting/stopping brain or tests"""
    status: str
    details: str
    # For backward compatibility
    brain_status: Optional[str] = Field(None, description="Deprecated: Use status instead")
    testing_script: Optional[str] = Field(None, description="Deprecated: Use status instead")

    def __init__(self, **data):
        super().__init__(**data)
        # Maintain backward compatibility
        if self.status in ["started", "stopped"]:
            self.brain_status = self.status
            self.testing_script = self.status

class ReportResponse(BaseModel):
    """Response model for report generation endpoint"""
    status: str = Field(..., description="Status of report generation")
    tar_filename: str = Field(..., description="Name of the generated tar file")
    report_path: str = Field(..., description="Path where the report is saved")
    # For backward compatibility
    report: str = Field("generated", description="Deprecated: Use status instead")

class EnvFileResponse(BaseModel):
    """Response model for environment file endpoint"""
    properties: Dict[str, Any] = Field(..., description="Environment variables and their values")
    definitions: Dict[str, str] = Field({}, description="JSON schema definitions")
    title: str = Field(..., description="Schema title")
    type: str = Field(..., description="Schema type")



class BalconyResponse(BaseModel):
    id: int

    class Config:
        orm_mode = True

class LevelResponse(BaseModel):
    id: int
    height: Optional[int]

    class Config:
        orm_mode = True

class StorageStatusResponse(BaseModel):
    storage_status: StorageStatus

    class Config:
        orm_mode = True
