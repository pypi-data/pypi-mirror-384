from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class Bot(BaseModel):
    """Bot model defining the core bot properties."""
    id: int
    level_id: int
    battery_level: int
    is_charging: bool
    lifted_carrier: Optional[int] = None

    class Config:
        orm_mode = True

class BotResponse(Bot):
    """Response model for bot data."""
    pass

class BotFilter(BaseModel):
    """Filter model for bot queries."""
    id__eq: Optional[str] = Field(None, description="Filter by bot ID")
    id__in: Optional[List[str]] = Field(None, description="Filter by bot IDs list")
    level_id__eq: Optional[int] = Field(None, description="Filter by level ID")
    level_id__in: Optional[List[int]] = Field(None, description="Filter by level IDs list")
    is_charging__eq: Optional[bool] = Field(None, description="Filter by charging status")

class BotChargingRequest(BaseModel):
    """Request model for charging operations."""
    bot_ids: List[str] = Field(..., description="List of bot IDs to send to charge; * for all bots")
    force: bool = Field(False, description="Force robots to go charging regardless of their state of charge")
    block_until_done: bool = Field(False, description="Block until all robots have gone charging")
    timeout: int = Field(180, description="Timeout for the block_until_done operation in seconds")

class BotChargingResponse(BaseModel):
    """Response model for charging operations."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None

class BotStopChargingRequest(BaseModel):
    """Request model for stop charging operations."""
    bot_ids: List[str] = Field(..., description="List of bot IDs to stop charging; * for all bots")
    force: bool = Field(False, description="Force robots to uncharge regardless of their state of charge")

class BotStopChargingResponse(BaseModel):
    """Response model for stop charging operations."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None

class BotRemoveRequest(BaseModel):
    """Request model for bot removal operations."""
    bot_ids: List[str] = Field(..., description="List of bot IDs to remove from database; * for all bots")

class BotRemoveResponse(BaseModel):
    """Response model for bot removal operations."""
    success: bool
    message: str

class BotSort(str, Enum):
    """Sort fields for bot queries."""
    ID = "id"
    NUMBER = "number"
    LEVEL_ID = "level_id"
    BATTERY_LEVEL = "battery_level"