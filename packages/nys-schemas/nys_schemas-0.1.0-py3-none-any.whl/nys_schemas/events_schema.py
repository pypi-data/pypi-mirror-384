from typing import Optional, Union, List, Literal, Annotated, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from fastapi import Query
from nys_constants.nys_constants import LogLevel
from enum import Enum

class EventsResponse(BaseModel):
    hex_value: str
    description: str
    component: str
    severity: int
    created_at: datetime
    level_id: Optional[int] = None
    bot_id: Optional[str] = None
    request_id: Optional[str] = None

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj):
        """Create EventsResponse from ORM object, populating optional fields from details"""
        event_data = {
            'hex_value': obj.hex_value,
            'description': obj.description,
            'component': obj.component,
            'severity': obj.severity,
            'created_at': obj.created_at,
            'level_id': None,
            'bot_id': None,
            'request_id': None
        }
        
        # Populate optional fields from details if they exist
        if obj.details:
            event_data['level_id'] = obj.details.get('level_id')
            event_data['bot_id'] = obj.details.get('bot_id')
            event_data['request_id'] = obj.details.get('request_id')
        
        return cls(**event_data)

class EventsSort(str, Enum):
    """Valid sort options for Event endpoints."""
    HEX_VALUE = 'hex_value'
    CREATED_AT = 'created_at'
    COMPONENT = 'component'
    SEVERITY = 'severity'

class EventsFilter(BaseModel):
    hex_value__eq: Optional[str] = Field(None, description="Filter by hex value (exact match)")
    hex_value__ilike: Optional[str] = Field(None, description="Filter by hex value (partial match)")
    component__eq: Optional[str] = Field(None, description="Filter by component (exact match)")
    component__ilike: Optional[str] = Field(None, description="Filter by component (partial match)")
    component__in: Optional[Annotated[List[str], Query(None, description="Filter by component (in list)")]] = None
    severity__eq: Optional[int] = Field(None, description="Filter by severity (exact match)")
    severity__in: Optional[Annotated[List[int], Query(None, description="Filter by severity (in list)")]] = None
    severity__gte: Optional[int] = Field(None, description="Filter by severity (greater than or equal)")
    severity__lte: Optional[int] = Field(None, description="Filter by severity (less than or equal)")
    created_at__gte: Optional[datetime] = Field(None, description="Filter by created_at (greater than or equal)")
    created_at__lte: Optional[datetime] = Field(None, description="Filter by created_at (less than or equal)")
    level_id__eq: Optional[Union[int, str]] = Field(None, description="Filter by level_id (exact match, pass 'null' for undefined)")
    bot_id__eq: Optional[str] = Field(None, description="Filter by bot_id (exact match)")
    request_id__eq: Optional[str] = Field(None, description="Filter by request_id (exact match)")
    request_id__ilike: Optional[str] = Field(None, description="Filter by request_id (partial match)")

    class Config:
        extra = 'forbid'

# ------------------------------
# Search options for events endpoint
# ------------------------------

class EventsSearch(str, Enum):
    """Fields allowed for search query in /events endpoint."""
    DESCRIPTION = 'description'
    COMPONENT = 'component'