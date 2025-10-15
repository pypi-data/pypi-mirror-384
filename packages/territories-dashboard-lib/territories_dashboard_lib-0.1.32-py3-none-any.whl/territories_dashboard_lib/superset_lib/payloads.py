from pydantic import BaseModel

from territories_dashboard_lib.commons.types import SimpleIDType


class GuestTokenPayload(BaseModel):
    dashboard: SimpleIDType
