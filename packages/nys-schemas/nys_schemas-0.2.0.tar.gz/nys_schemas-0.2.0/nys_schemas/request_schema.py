from datetime import datetime
import os
from typing import Optional, List, Literal, TypeAlias, get_args, Union, Any, Tuple, List
from uuid import UUID
from pydantic import BaseModel, Field, validator, root_validator
from pydantic.error_wrappers import ValidationError
from nys_constants.nys_constants import RequestType, RequestStatus, EntityType
from typing_extensions import Annotated
from fastapi import Query
from enum import Enum


# Sku entity for fulfillment and replenishment requests --------------------------
class SkuEntityInput(BaseModel):
    sku_id: str
    quantity: int

    class Config:
        orm_mode = True
        extra = "forbid"

class CarrierEntityInput(BaseModel):
    carrier_id: str

    class Config:
        orm_mode = True
        extra = "forbid"

class EntityResponse(BaseModel):
    id: str
    entity_type: EntityType
    completed_quantity: int
    total_quantity: int

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.entity_id,
            entity_type=obj.entity_type,
            completed_quantity=obj.completed_quantity,
            total_quantity=obj.total_quantity
        )



class RequestResponseComposite(BaseModel):
    id: str
    type: RequestType
    status: RequestStatus
    priority: int
    created_at: datetime
    updated_at: datetime

    # Optional fields
    """Response model for requests"""
    entities: Optional[List[EntityResponse]] = None
    counter: Optional[int] = None
    placing_pos: Optional[int] = None
    bot_id: Optional[int] = None
    level_id: Optional[int] = None

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            type=obj.type,
            status=obj.status,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            priority=obj.priority,
            entities=[EntityResponse.from_orm(e) for e in obj.entities] if obj.type in [RequestType.FULFILLMENT, RequestType.REPLENISHMENT, RequestType.FETCH] else [], #TODO else return None is better but UI doesn't like it rn
            counter=obj.counter if hasattr(obj, 'counter') else None,
            placing_pos=obj.placing_position if hasattr(obj, 'placing_position') else None,
            bot_id=obj.bot_id if hasattr(obj, 'bot_id') else None,
            level_id=obj.level_id if hasattr(obj, 'level_id') else None,
        )


class RequestSort(str, Enum):
    """Valid sort options for requests."""
    TYPE = 'type'
    STATUS = 'status'
    PRIORITY = 'priority'
    CREATED_AT = 'created_at'
    UPDATED_AT = 'updated_at'
    COUNTER = 'counter'
    PLACING_POS = 'placing_pos'

class RequestFilter(BaseModel):
    """Filter model for Request queries"""
    type__eq: Optional[str] = Field(None, description="Filter by request type (exact match)")
    status__eq: Optional[str] = Field(None, description="Filter by request status (exact match)")
    id__eq: Optional[Union[str, UUID]] = Field(None, description="Filter by id (exact match)")
    id__in: Optional[Annotated[List[Union[str, UUID]], Query(None, description="Filter for multiple ids")]] = None
    priority__eq: Optional[int] = Field(None, description="Filter by priority (exact match)")
    counter__eq: Optional[int] = Field(None, description="Filter by counter (exact match)")
    created_at__lte: Optional[datetime] = Field(None, description="Filter by created_at end date")
    created_at__gte: Optional[datetime] = Field(None, description="Filter by created_at start date")
    updated_at__lte: Optional[datetime] = Field(None, description="Filter by updated_at end date")
    updated_at__gte: Optional[datetime] = Field(None, description="Filter by updated_at start date")
    status__in: Optional[Annotated[List[str], Query(None, description="Filter by multiple statuses")]] = None
    type__in: Optional[Annotated[List[str], Query(None, description="Filter by multiple types")]] = None
    class Config:
        extra = "forbid"  # This makes the model reject unexpected fields


class RequestCreateInputGeneric(BaseModel):
    """Input model for creating a request"""
    id: Optional[str] = None
    

# Fetch request ------------------------------------------------------------
class FetchRequestCreateInput(RequestCreateInputGeneric):
    """Input model for creating a fetch request"""
    type: Literal[RequestType.FETCH] = RequestType.FETCH
    priority: Optional[int] = 10
    entities: List[CarrierEntityInput] #TODO simpler would be to just use carrier_ids: List[str]


# Fulfillment request ------------------------------------------------------------
class FulfillmentRequestCreateInput(RequestCreateInputGeneric):
    """Input model for creating a fulfillment request"""
    type: Literal[RequestType.FULFILLMENT] = RequestType.FULFILLMENT
    priority: Optional[int] = 10
    entities: List[SkuEntityInput]

# Replenishment request ------------------------------------------------------------

class ReplenishmentRequestCreateInput(RequestCreateInputGeneric):
    """Input model for creating a replenishment request"""
    type: Literal[RequestType.REPLENISHMENT] = RequestType.REPLENISHMENT
    priority: Optional[int] = 10
    entities: List[SkuEntityInput]


# Onboarding request ------------------------------------------------------------
class OnboardingRequestCreateInput(RequestCreateInputGeneric):
    """Input model for creating an onboarding request"""
    type: Literal[RequestType.ONBOARD] = RequestType.ONBOARD

# Offboarding request ------------------------------------------------------------
class OffboardingRequestCreateInput(RequestCreateInputGeneric):
    """Input model for creating an offboarding request"""
    type: Literal[RequestType.OFFBOARD] = RequestType.OFFBOARD
    bot_id: int

# RFID write request ------------------------------------------------------------
class RFIDWriteRequestCreateInput(RequestCreateInputGeneric):
    """Input model for creating an RFID write request"""
    type: Literal[RequestType.RFID_MAINTENANCE] = RequestType.RFID_MAINTENANCE
    level_id: int
    action_type: str #TODO simplify and strong type
    start_from_scratch: bool = True #TODO: is this needed?

# Level pause request ------------------------------------------------------------
class PauseRequestCreateInput(RequestCreateInputGeneric):
    """Input model for creating a pause request"""
    type: Literal[RequestType.PAUSE] = RequestType.PAUSE

# Level resume request ------------------------------------------------------------
class ResumeRequestCreateInput(RequestCreateInputGeneric):
    """Input model for creating a resume request"""
    type: Literal[RequestType.RESUME] = RequestType.RESUME

# Create the discriminated union
RequestCreateInput = Annotated[
    Union[
        FetchRequestCreateInput,
        FulfillmentRequestCreateInput,
        ReplenishmentRequestCreateInput,
        OnboardingRequestCreateInput,
        OffboardingRequestCreateInput,
        RFIDWriteRequestCreateInput,
        PauseRequestCreateInput,
        ResumeRequestCreateInput,
    ],
    Field(discriminator='type')
]

