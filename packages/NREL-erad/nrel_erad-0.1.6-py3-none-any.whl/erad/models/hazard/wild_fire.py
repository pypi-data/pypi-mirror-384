from datetime import datetime
import sqlite3
import os

from shapely.geometry import MultiPolygon, Polygon, Point
from pydantic import field_serializer, field_validator
import plotly.graph_objects as go
from gdm.quantities import Angle
from infrasys import Component
from shapely import wkb
import pandas as pd

from erad.models.hazard.common import ERAD_DB, HISTROIC_FIRE_TABLE
from erad.models.hazard.base_models import BaseDisasterModel
from erad.quantities import Speed


class FireModelArea(Component):
    name: str = ""
    affected_area: Polygon
    wind_speed: Speed
    wind_direction: Angle

    @field_validator("affected_area", mode="before")
    def deserialize_polygon(cls, value):
        if isinstance(value, dict) and value.get("type") == "Polygon":
            points = [Point(c) for c in value["coordinates"]]
            return Polygon(points)
        return value

    @field_serializer("affected_area")
    def serialize_polygon(self, poly: Polygon, _info):
        return {"type": "Polygon", "coordinates": list(poly.exterior.coords)}

    @classmethod
    def example(cls) -> "FireModelArea":
        return FireModelArea(
            affected_area=Polygon(
                [
                    (-120.93036, 36.60144),
                    (-120.91072, 36.60206),
                    (-120.91127, 36.5712),
                    (-120.93405, 36.58100),
                ]
            ),
            wind_speed=Speed(50, "miles/hour"),
            wind_direction=Angle(45, "deg"),
        )


class FireModel(BaseDisasterModel):
    timestamp: datetime
    affected_areas: list[FireModelArea]

    @classmethod
    def example(cls) -> "FireModel":
        return FireModel(
            name="fire 1",
            timestamp=datetime.now(),
            affected_areas=[FireModelArea.example()],
        )

    @classmethod
    def from_wildfire_name(cls, wildfire_name: str) -> "FireModel":
        assert os.path.exists(ERAD_DB), f"The data file {ERAD_DB} not found"
        conn = sqlite3.connect(ERAD_DB)
        fire_data = pd.read_sql(
            f"SELECT * FROM {HISTROIC_FIRE_TABLE} WHERE firename = '{wildfire_name}';", conn
        )
        if fire_data.empty:
            raise ValueError(
                f"Fire '{wildfire_name}'  not found in  table '{HISTROIC_FIRE_TABLE}' in the database"
            )
        conn.close()
        fire_data["discoverydatetime"] = pd.to_datetime(fire_data["discoverydatetime"])
        geometry: MultiPolygon = [wkb.loads(g) for g in fire_data.GEOMETRY][0]
        areas = []
        for i, poly in enumerate(geometry.geoms):
            areas.append(
                FireModelArea(
                    affected_area=poly,
                    wind_speed=Speed(-999, "miles/hour"),
                    wind_direction=Angle(0, "deg"),
                )
            )
        return cls(
            name=wildfire_name,
            timestamp=fire_data["discoverydatetime"]
            .values[0]
            .astype("datetime64[ms]")
            .astype(datetime),
            affected_areas=areas,
        )

    def plot(
        self,
        time_index: int = 0,
        figure: go.Figure = go.Figure(),
        map_obj: type[go.Scattergeo | go.Scattermap] = go.Scattermap,
    ) -> int:
        for area in self.affected_areas:
            lon, lat = area.affected_area.exterior.xy  # returns x and y sequences
            figure.add_trace(
                map_obj(
                    lon=lon.tolist(),
                    lat=lat.tolist(),
                    mode="markers+lines+text",
                    fill="toself",
                    marker={
                        "size": 10,
                        "color": [area.wind_speed.magnitude],
                    },
                    hovertemplate=f"""
                        <br> <b>Wind speed:</b> {area.wind_speed}
                        <br> <b>Wind direction:</b> {area.wind_direction}
                        """,
                    hoverinfo="text",
                    visible=(time_index == 0),
                )
            )
        return len(self.affected_areas)
