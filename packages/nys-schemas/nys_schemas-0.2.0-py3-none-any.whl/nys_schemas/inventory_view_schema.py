from typing import Optional, Union, List, Literal, Annotated
from pydantic import BaseModel, Field
from datetime import datetime
from fastapi import Query
from enum import Enum

class InventoryViewResponse(BaseModel):
    id: str #TODO rename "key"?
    carrier_id : str
    content_codes: Optional[str]
    level_id : int
    position_x : Optional[int]
    position_y : Optional[int]
    box_id : Optional[int]
    box_size : Optional[int]
    box_size_string : Optional[str]
    box_height_string_max : Optional[int]
    section_code : Optional[str] = Field(
        default=None,
        description="8-digit string of 1's and 0's representing box placement on carrier. "
                   "First 4 digits represent top spaces, last 4 represent bottom spaces. "
                   "Examples: '11001100' = left half of carrier, '11000000' = small box in top-left"
    )
    sku_id : Optional[str]
    sku_name : Optional[str]
    measurement_unit: Optional[str]
    on_empty_sku_action: Optional[str]
    item_count : Optional[int]
    item_count_max : Optional[int]
    depth : Optional[int]
    eta : Optional[float]
    eta_int : Optional[int]
    system_quantity : Optional[int]
    updated_at : Optional[datetime]
    class Config:
        orm_mode = True

class InventoryViewSort(str, Enum):
    ID = 'id' #TODO rename "key"?
    CARRIER_ID = 'carrier_id'
    LEVEL_ID = 'level_id'
    POSITION_X = 'position_x'
    POSITION_Y = 'position_y'
    BOX_ID = 'box_id'
    BOX_SIZE = 'box_size'
    BOX_SIZE_STRING = 'box_size_string'
    BOX_HEIGHT_STRING_MAX = 'box_height_string_max'
    SECTION_CODE = 'section_code'
    SKU_ID = 'sku_id'
    SKU_NAME = 'sku_name'
    ITEM_COUNT = 'item_count'
    ITEM_COUNT_MAX = 'item_count_max'
    DEPTH = 'depth'
    ETA = 'eta'
    ETA_INT = 'eta_int'
    SYSTEM_QUANTITY = 'system_quantity'
    CONTENT_CODES = 'content_codes'
    MEASUREMENT_UNIT = 'measurement_unit'
    UPDATED_AT = 'updated_at'
class InventoryViewSearch(str, Enum):
    CARRIER_ID = 'carrier_id'
    BOX_SIZE_STRING = 'box_size_string'
    BOX_HEIGHT_STRING_MAX = 'box_height_string_max'
    SECTION_CODE = 'section_code'
    SKU_ID = 'sku_id'
    SKU_NAME = 'sku_name'

class InventoryViewFilter(BaseModel):
    # carrier_id: Optional[str] = Field(None, description="Filter by Carrier ID (exact match)")
    carrier_id__eq: Optional[str] = Field(None, description="Filter by Carrier id (exact match)")
    carrier_id__ilike: Optional[str] = Field(None, description=f'ilike match')
    level_id__in: Optional[Annotated[List[str], Query(None, description="Filter by level")]] = None

    box_id__eq: Optional[str] = Field(None, description="Filter by box_id (exact match), 'none' for empty spaces")
    box_id__ilike: Optional[str] = Field(None, description=f'ilike match')

    position_x__eq: Optional[int] = Field(None, description="Exact position_x")
    position_x__ilike: Optional[str] = Field(None, description=f'ilike match')
    position_y__eq: Optional[int] = Field(None, description="Exact position_y")
    position_y__ilike: Optional[str] = Field(None, description=f'ilike match')

    box_size_string__eq: Optional[str] = Field(None, description="Filter by box_size_string (exact match)")
    box_size_string__in: Optional[Annotated[List[str], Query(None, description="Filter by box_size_string (in list)")]] = None
    box_size_string__ilike: Optional[str] = Field(None, description=f'ilike match')

    box_height_string_max__eq: Optional[str] = Field(None, description="Filter by box_height_string_max (exact match)")
    box_height_string_max__ilike: Optional[str] = Field(None, description=f'ilike match')

    sku_id__eq: Optional[str] = Field(None, description="Filter by sku_id (exact match)")
    sku_id__ilike: Optional[str] = Field(None, description=f'ilike match')
    sku_name__ilike: Optional[str] = Field(None, description=f'ilike match')
    measurement_unit__in: Optional[Annotated[List[str], Query(None, description="Filter by measurement_unit (in list)")]] = None

    item_count__eq: Optional[str] = Field(None, description="Filter by item_count (exact match)")
    item_count__ilike: Optional[str] = Field(None, description=f'ilike match')
    item_count_max__eq: Optional[str] = Field(None, description="Filter by item_count_max (exact match)")
    item_count_max__ilike: Optional[str] = Field(None, description=f'ilike match')
    system_quantity__eq: Optional[str] = Field(None, description="Filter by system_quantity (exact match)")
    system_quantity__ilike: Optional[str] = Field(None, description=f'ilike match')
    depth__eq: Optional[int] = Field(None, description=f'Filter by exact match for carrier depth from autobahn')
    depth__ilike: Optional[str] = Field(None, description=f'ilike match')
    eta_int__ilike: Optional[str] = Field(None, description=f'ilike match')
    updated_at__gte: Optional[datetime] = Field(None, description="Filter by updated_at greater than or equal to")
    updated_at__lte: Optional[datetime] = Field(None, description="Filter by updated_at less than or equal to")
    content_codes__ilike: Optional[str] = Field(None, description=f'ilike match') # TODO deprecate

    class Config:
        extra = "forbid"  # This makes the model reject unexpected fields