from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from typing_extensions import Annotated
from fastapi import Query
from uuid import UUID
from enum import Enum


class RequestsAndJobsViewResponse(BaseModel):
    """Schema for the response of the requests and jobs view."""
    # Mandatory fields
    id: str #TODO rename "key"?
    request_id: str
    request_status: str
    request_type: str
    
    # Optional fields
    job_id: Optional[str] = None
    job_type: Optional[str] = None
    job_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    level_id: Optional[int] = None
    sku_id: Optional[str] = None
    sku_name: Optional[str] = None
    carrier_id: Optional[str] = None
    created_by: Optional[str] = None
    triggered_by: Optional[str] = None
    
    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=str(obj.id),
            request_id=str(obj.request_id),
            request_status=obj.request_status,
            request_type=obj.request_type,
            job_id=None if obj.job_id is None else str(obj.job_id),
            job_type=obj.job_type,
            job_status=obj.job_status,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            level_id=obj.level_id,
            sku_id=obj.sku_id,
            sku_name=obj.sku_name,
            carrier_id=obj.carrier_id,
            created_by=getattr(obj, 'created_by', None),
            triggered_by=getattr(obj, 'triggered_by', None),
        )
    

class RequestAndJobsViewSearch(str, Enum):
    """Valid search options for requests and jobs view."""
    SKU_ID = 'sku_id'
    SKU_NAME = 'sku_name'
    CARRIER_ID = 'carrier_id'

class RequestsAndJobsViewSort(str, Enum):
    """Valid sort options for requests and jobs view."""
    ID = 'id' #TODO rename "key"?
    REQUEST_ID = 'request_id'
    REQUEST_STATUS = 'request_status'
    REQUEST_TYPE = 'request_type'
    JOB_ID = 'job_id'
    JOB_TYPE = 'job_type'
    JOB_STATUS = 'job_status'
    CREATED_AT = 'created_at'
    UPDATED_AT = 'updated_at'
    LEVEL_ID = 'level_id'
    SKU_ID = 'sku_id'
    SKU_NAME = 'sku_name'
    CARRIER_ID = 'carrier_id'
    CREATED_BY = 'created_by'
    TRIGGERED_BY = 'triggered_by'

class RequestsAndJobsViewFilter(BaseModel):
    """Schema for filtering requests and jobs view."""
    request_status__eq: Optional[str] = Field(None, description="Filter by request status (exact match)")
    request_status__in: Optional[Annotated[List[str], Query(None, description="Filter by multiple request statuses")]] = None
    request_id__ilike: Optional[str] = Field(None, description="Filter by request ID (ilike match)")
    request_type__eq: Optional[str] = Field(None, description="Filter by request type (exact match)")
    request_type__in: Optional[Annotated[List[str], Query(None, description="Filter by multiple request types")]] = None
    job_id__ilike: Optional[str] = Field(None, description="Filter by job ID (ilike match)")
    job_status__eq: Optional[str] = Field(None, description="Filter by job status (exact match)")
    job_status__in: Optional[Annotated[List[str], Query(None, description="Filter by multiple job statuses")]] = None
    job_type__eq: Optional[str] = Field(None, description="Filter by job type (exact match)")
    job_type__in: Optional[Annotated[List[str], Query(None, description="Filter by multiple job types")]] = None
    level_id__eq: Optional[int] = Field(None, description="Filter by level ID (exact match)")
    level_id__in: Optional[Annotated[List[int], Query(None, description="Filter by multiple level IDs")]] = None
    sku_id__eq: Optional[str] = Field(None, description="Filter by SKU ID (exact match)")
    sku_id__ilike: Optional[str] = Field(None, description="Filter by SKU ID (ilike match)")
    sku_name__ilike: Optional[str] = Field(None, description="Filter by SKU name (ilike match)")
    carrier_id__ilike: Optional[str] = Field(None, description="Filter by carrier id (ilike match)")
    created_at__lte: Optional[datetime] = Field(None, description="Filter by created_at end date")
    created_at__gte: Optional[datetime] = Field(None, description="Filter by created_at start date")
    updated_at__lte: Optional[datetime] = Field(None, description="Filter by updated_at end date")
    updated_at__gte: Optional[datetime] = Field(None, description="Filter by updated_at start date")
    created_by__ilike: Optional[str] = Field(None, description="Filter by creator username (ilike match)")
    triggered_by__ilike: Optional[str] = Field(None, description="Filter by trigger username (ilike match)")

    class Config:
        extra = "forbid"  # This makes the model reject unexpected fields
