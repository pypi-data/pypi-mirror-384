from pydantic import BaseModel, Field
from typing import Optional

class Box(BaseModel):
    section_code: int = Field(
        description="8-digit string of 1's and 0's representing box placement on carrier. "
                   "First 4 digits represent top spaces, last 4 represent bottom spaces. "
                   "Examples: '11001100' = left half of carrier, '11000000' = small box in top-left"
    )

    class Config:
        orm_mode = True

class BoxCreate(BaseModel):
    section_code: Optional[int] = Field(
        default=None,
        description="8-digit string of 1's and 0's representing box placement on carrier. "
                   "First 4 digits represent top spaces, last 4 represent bottom spaces. "
                   "Examples: '11001100' = left half of carrier, '11000000' = small box in top-left"
    )

    class Config:
        orm_mode = True

class BoxPatch(BaseModel):
    section_code: Optional[int] = Field(
        default=None,
        description="8-digit string of 1's and 0's representing box placement on carrier. "
                   "First 4 digits represent top spaces, last 4 represent bottom spaces. "
                   "Examples: '11001100' = left half of carrier, '11000000' = small box in top-left"
    )

    class Config:
        orm_mode = True

class BoxResponse(Box):
    id: int 