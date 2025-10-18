from typing import Optional
from pydantic import BaseModel, validator
from pydantic.error_wrappers import ValidationError

class LoadResponse(BaseModel):
    sku_id: str
    name: Optional[str]
    item_count: int
    item_count_max: int

    class Config:
        orm_mode = True

    @classmethod
    def from_orm(cls, obj):
        return cls(
            sku_id=obj.sku.id if obj.sku else None,
            name=obj.sku.name if obj.sku else None,
            item_count=obj.item_count,
            item_count_max=obj.item_count_max
        )

class LoadCreate(BaseModel):
    sku_id: str
    item_count: int
    item_count_max: int

class LoadPatch(BaseModel):
    sku_id: Optional[str]
    item_count: Optional[int]
    item_count_max: Optional[int]