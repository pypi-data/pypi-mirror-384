from datetime import datetime
from typing import Optional, TypedDict
from pydantic import BaseModel

class App(BaseModel):
    id: str
    organization_id: str
    name: str
    webhook: str
    created_at: datetime
    # updated_at: datetime TODO: create updated_at field

class AppUpdateFields(TypedDict):
    name: Optional[str]
    webhook: Optional[str]
