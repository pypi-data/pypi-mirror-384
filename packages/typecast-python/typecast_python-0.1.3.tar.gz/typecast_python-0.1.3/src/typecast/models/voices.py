
from pydantic import BaseModel


class VoicesResponse(BaseModel):
    voice_id: str
    voice_name: str
    model: str
    emotions: list[str]
