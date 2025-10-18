from pydantic import BaseModel

class CreateIssueResponse(BaseModel):
    """Response model for issue creation endpoint"""
    key: str
    url: str
