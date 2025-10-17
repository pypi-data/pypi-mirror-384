from pydantic import BaseModel
from datetime import datetime

class AppConnection(BaseModel):
    id: str
    app_id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime