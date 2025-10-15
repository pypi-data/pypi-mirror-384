from datetime import datetime
from uuid import UUID
from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field
from typing_extensions import Annotated
from enum import Enum
from fastapi import Query

class JobResponse(BaseModel):
    # Mandatory fields
    id: str
    type: str
    status: str
    request_id: str
    created_at: datetime
    updated_at: datetime

    # Optional fields
    box_id: Optional[int]
    carrier_id: Optional[str]
    sku_id: Optional[str]
    balcony_id: Optional[int]
    quantity: Optional[int]
    level_id: Optional[int]
    sku_name: Optional[str]
    bot_id: Optional[int]
    measurement_unit: Optional[str]

    class Config:
        orm_mode = True
    
    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=str(obj.id),
            type=obj.type,
            status=obj.status,
            request_id=str(obj.request.id),
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            box_id=obj.details['box_id'] if obj.details and 'box_id' in obj.details else None,
            carrier_id=obj.details['carrier_id'] if obj.details and 'carrier_id' in obj.details else None,
            sku_id=obj.details['sku_id'] if obj.details and 'sku_id' in obj.details else None,
            sku_name=obj.details['sku_name'] if obj.details and 'sku_name' in obj.details else None,
            bot_id=obj.details['bot_id'] if obj.details and 'bot_id' in obj.details else None,
            measurement_unit=obj.details['measurement_unit'] if obj.details and 'measurement_unit' in obj.details else None,
            balcony_id=obj.balcony_id,
            quantity=obj.quantity,
            level_id=obj.level_id,
        )

class JobSort(str, Enum):
    TYPE = 'type'
    STATUS = 'status'
    CREATED_AT = 'created_at'
    UPDATED_AT = 'updated_at'
    BALCONY_ID = 'balcony_id'
    LEVEL_ID = 'level_id'


class JobFilter(BaseModel):
    id__eq: Optional[Union[str, UUID]] = Field(None, description="Filter by job ID (exact match)")
    status__eq: Optional[str] = Field(None, description="Filter by job status (exact match)")
    type__eq: Optional[str] = Field(None, description="Filter by job type (exact match)")
    balcony_id__eq: Optional[int] = Field(None, description="Filter by balcony ID (exact match)")
    request_id__eq: Optional[Union[str, UUID]] = Field(None, description="Filter by request ID (exact match)")
    request_id__in: Optional[Annotated[List[Union[str, UUID]], Query(None, description="Filter by multiple request IDs")]] = None
    created_at__lte: Optional[datetime] = Field(None, description="Filter by created_at end date")
    created_at__gte: Optional[datetime] = Field(None, description="Filter by created_at start date")
    updated_at__lte: Optional[datetime] = Field(None, description="Filter by updated_at end date")
    updated_at__gte: Optional[datetime] = Field(None, description="Filter by updated_at start date")
    status__in: Optional[Annotated[List[str], Query(None, description="Filter by multiple job statuses")]] = None
    type__in: Optional[Annotated[List[str], Query(None, description="Filter by multiple job types")]] = None
    level_id__eq: Optional[int] = Field(None, description="Filter by level ID (exact match)") 

    class Config:
        extra = "forbid"  # This makes the model reject unexpected fields