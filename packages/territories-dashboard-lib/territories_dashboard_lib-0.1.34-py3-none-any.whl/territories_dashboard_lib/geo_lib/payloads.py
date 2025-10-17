from typing import List, Optional

from pydantic import BaseModel, field_validator

from territories_dashboard_lib.commons.types import TerritoryCode
from territories_dashboard_lib.indicators_lib.enums import (
    GeoLevel,
    MeshLevel,
)


class GeoFeaturesParams(BaseModel):
    mesh: MeshLevel
    geo_level: GeoLevel
    main_territories: List[TerritoryCode]
    last: Optional[int] = None
    limit: Optional[int] = 1000
    feature: int

    @field_validator("main_territories", mode="before")
    def split_main_territories(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v


class MainTerritoryParams(BaseModel):
    geo_level: GeoLevel
    geo_id: List[TerritoryCode]

    @field_validator("geo_id", mode="before")
    def split_main_territories(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v


class TerritoriesParams(BaseModel):
    mesh: MeshLevel
    territories: List[TerritoryCode]

    @field_validator("territories", mode="before")
    def split_main_territories(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v


class TerritoryFeatureParams(BaseModel):
    mesh: MeshLevel
    geo_level: GeoLevel | None = None
    main_territories: List[TerritoryCode] | None = None
    codes: List[TerritoryCode] | None = None

    @field_validator("main_territories", "codes", mode="before")
    def split_main_territories(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v


class SearchTerritoriesParams(BaseModel):
    mesh: MeshLevel
    search: str = ""
    offset: int = 0
