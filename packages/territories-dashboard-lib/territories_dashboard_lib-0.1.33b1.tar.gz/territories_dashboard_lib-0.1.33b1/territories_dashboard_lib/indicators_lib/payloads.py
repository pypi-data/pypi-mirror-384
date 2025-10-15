from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, Field

from territories_dashboard_lib.commons.types import MutualisedTerritoryCode, SQlName

from .enums import MeshLevel


class Territory(BaseModel):
    id: MutualisedTerritoryCode
    mesh: MeshLevel


def validate_territory(value):
    if value and "-" in value:
        return {"id": value.split("-")[0], "mesh": value.split("-")[1]}


class BasePayload(BaseModel):
    territory: Annotated[Territory, BeforeValidator(validate_territory)]


class SubMeshPayload(BasePayload):
    submesh: MeshLevel


class FlowsPayload(SubMeshPayload):
    prefix: SQlName
    dimension: SQlName | None = None


class ComparisonQueryPayload(SubMeshPayload):
    cmp_territory: Annotated[
        Territory, BeforeValidator(validate_territory), Field(alias="cmp-territory")
    ]


class OptionalComparisonQueryPayload(SubMeshPayload):
    cmp_territory: Annotated[
        Optional[Territory],
        BeforeValidator(validate_territory),
        Field(default=None, alias="cmp-territory"),
    ]


class IndicatorTablePayload(SubMeshPayload):
    column_order: SQlName | None = None
    column_order_flow: SQlName | None = None
    pagination: int = 1
    limit: int = 20
    previous_limit: int | None = None
    search: str | None = None
    year: int | None = None
    flows: bool | None = False
    focus: bool | None = False
