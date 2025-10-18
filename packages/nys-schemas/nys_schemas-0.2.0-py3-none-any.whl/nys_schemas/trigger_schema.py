from pydantic import BaseModel, Field
from typing import List
from uuid import UUID
from nys_constants.nys_constants import TriggerStatus, TriggerType

class TriggerRequest(BaseModel):
    """Schema for job trigger requests"""
    trigger_status: TriggerStatus = Field(default=TriggerStatus.SUCCEEDED_TRIGGER, alias="TriggerStatus")

    class Config:
        allow_population_by_field_name = True
        use_enum_values = True

class TriggerResponse(BaseModel):
    """Schema for job trigger responses"""
    pass  # Empty response as per existing implementation 