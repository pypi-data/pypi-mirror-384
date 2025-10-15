from pydantic import BaseModel

from territories_dashboard_lib.tracking_lib.enums import EventType


class EventPayload(BaseModel):
    indicator: str
    event: EventType
    objet: str
    type: str
