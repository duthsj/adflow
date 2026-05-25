from pydantic import BaseModel
from datetime import datetime

class AssetOut(BaseModel):
    id: int
    client_id: int
    filename: str
    r2_key: str
    type: str
    size: int
    tags: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}
