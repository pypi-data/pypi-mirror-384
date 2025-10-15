from typing import List, Optional
from pydantic import BaseModel

from .box_schema import BoxResponse

class CarrierResponse(BaseModel):
    x: Optional[int]
    y: Optional[int]
    id: Optional[int]
    carrier_id: Optional[str]
    boxes: Optional[List[BoxResponse]]
    level_id: Optional[int]
    level_height: Optional[int]
    depth: Optional[int]
    empty_space: Optional[str] 