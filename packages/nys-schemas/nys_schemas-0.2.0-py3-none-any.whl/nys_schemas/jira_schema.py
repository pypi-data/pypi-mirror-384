from pydantic import BaseModel
from typing import Optional, List

class CreateIssuePayload(BaseModel):
    """Payload describing a user-submitted issue from the support dialog.

    Attachments are provided separately as UploadFile objects in the API layer.
    """
    title: str
    description: str
    category: Optional[str] = None
    steps_to_reproduce: Optional[str] = None
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    env_name: Optional[str] = None
    tags_enabled: List[str] = []
    email: Optional[str] = None