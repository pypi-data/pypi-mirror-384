from typing import Optional, Union, List, Literal, Annotated
from pydantic import BaseModel, Field, validator
from pydantic.error_wrappers import ValidationError
from datetime import datetime
from fastapi import Query
from nys_constants.nys_constants import OnEmptySKUAction, MeasurementUnit
from enum import Enum

class Sku(BaseModel):
    id: str
    name: Optional[str] = None
    measurement_unit: Optional[MeasurementUnit] = MeasurementUnit.PIECE
    on_empty_sku_action: Optional[OnEmptySKUAction] = OnEmptySKUAction.UNASSIGN

    class Config:
        orm_mode = True

    @validator('id', pre=True)
    def validate_id(cls, v):
        if v == 'null':
            raise ValidationError('id cannot be null')
        if v == '\"null\"':
            raise ValidationError('id cannot be \"null\"')
        return v

class SkuCreate(Sku):
    pass

class SkuPatch(BaseModel):
    name: Optional[str]
    measurement_unit: Optional[MeasurementUnit]
    on_empty_sku_action: Optional[OnEmptySKUAction]

class SkuResponse(Sku):
    total_quantity: int
    max_quantity: int
    total_positive_inventory_bookings: int
    total_negative_inventory_bookings: int
    fulfillable: int    
    replenishable: int
    load_count: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    image_url : Optional[str]
    carrier_utilization: float


class SkuSearch(str, Enum):
    """Valid search options for SKU endpoints."""
    ID = 'id'
    NAME = 'name'
    CARRIER_UTILIZATION = 'carrier_utilization'

class SkuSort(str, Enum):
    """Valid sort options for SKU endpoints."""
    ID = 'id'
    NAME = 'name'
    MEASUREMENT_UNIT = 'measurement_unit'
    ON_EMPTY_SKU_ACTION = 'on_empty_sku_action'
    TOTAL_QUANTITY = 'total_quantity'
    MAX_QUANTITY = 'max_quantity'
    TOTAL_POSITIVE_INVENTORY_BOOKINGS = 'total_positive_inventory_bookings'
    TOTAL_NEGATIVE_INVENTORY_BOOKINGS = 'total_negative_inventory_bookings'
    FULFILLABLE = 'fulfillable'
    REPLENISHABLE = 'replenishable'
    LOAD_COUNT = 'load_count'
    CREATED_AT = 'created_at'
    UPDATED_AT = 'updated_at'
    DELETED_AT = 'deleted_at'
    CARRIER_UTILIZATION = 'carrier_utilization'


class SkuFilter(BaseModel):
    id__eq: Optional[str] = Field(None, description="Filter by SKU ID (exact match)")
    id__ilike: Optional[str] = Field(None, description=f'ilike match')
    name__ilike: Optional[str] = Field(None, description="Filter by SKU Name (partial match)")
    measurement_unit__in: Optional[Annotated[List[str], Query(None, description="Filter by measurement unit")]] = None
    on_empty_sku_action__in: Optional[Annotated[List[str], Query(None, description="Filter by on empty action")]] = None
    created_at__lte: Optional[datetime] = Field(None, description="Filter by created_at end date")
    created_at__gte: Optional[datetime] = Field(None, description="Filter by created_at start date")
    updated_at__lte: Optional[datetime] = Field(None, description="Filter by updated_at end date")
    updated_at__gte: Optional[datetime] = Field(None, description="Filter by updated_at start date")
    deleted_at__lte: Optional[datetime] = Field(None, description="Filter by deleted_at end date")
    deleted_at__gte: Optional[datetime] = Field(None, description="Filter by deleted_at start date")
    total_quantity__ilike: Optional[int] = Field(None, description="ilike total quantity")
    total_quantity__eq: Optional[int] = Field(None, description="Exact total quantity")
    total_quantity__gte: Optional[int] = Field(None, description="gte total quantity")
    total_quantity__lte: Optional[int] = Field(None, description="lte total quantity")
    max_quantity__ilike: Optional[int] = Field(None, description="ilike max quantity")
    max_quantity__eq: Optional[int] = Field(None, description="max quantity")
    max_quantity__gte: Optional[int] = Field(None, description="gte max quantity")
    max_quantity__lte: Optional[int] = Field(None, description="lte max quantity")
    load_count__ilike: Optional[int] = Field(None, description="ilike load count")
    load_count__eq: Optional[int] = Field(None, description=" load count")
    fulfillable__ilike: Optional[int] = Field(None, description="ilike fulfillable")
    replenishable__ilike: Optional[int] = Field(None, description="ilike replenishable")
    carrier_utilization__ilike: Optional[float] = Field(None, description="ilike carrier utilization")

    class Config:
        extra = "forbid"  # This makes the model reject unexpected fields
