from datetime import datetime
import sqlite3
import os

from pydantic import field_serializer, field_validator
from gdm.quantities import Distance
from shapely.geometry import Point
import plotly.graph_objects as go
import pandas as pd

from erad.models.hazard.common import ERAD_DB, HISTROIC_EARTHQUAKE_TABLE
from erad.models.hazard.base_models import BaseDisasterModel


class EarthQuakeModel(BaseDisasterModel):
    timestamp: datetime
    origin: Point
    depth: Distance
    magnitude: float

    @field_validator("origin", mode="before")
    def deserialize_point(cls, value):
        if isinstance(value, dict) and value.get("type") == "Point":
            coords = value["coordinates"]
            return Point(coords)
        return value

    @field_serializer("origin")
    def serialize_location(self, point: Point, _info):
        return {"type": "Point", "coordinates": (point.x, point.y)}

    @classmethod
    def example(cls) -> "EarthQuakeModel":
        return EarthQuakeModel(
            name="earthquake 1",
            timestamp=datetime.now(),
            origin=Point(-120.93036, 36.60144),
            depth=Distance(300, "km"),
            magnitude=5.0,
        )

    @classmethod
    def from_earthquake_code(cls, earthquake_code: str) -> "EarthQuakeModel":
        assert os.path.exists(ERAD_DB), f"The data file {ERAD_DB} not found"

        conn = sqlite3.connect(ERAD_DB)
        earthquake_data = pd.read_sql(
            f"SELECT * FROM {HISTROIC_EARTHQUAKE_TABLE} WHERE ID = '{earthquake_code}'", conn
        )
        conn.close()

        assert not earthquake_data.empty, f"No earthquake {earthquake_code} found in the database"

        earthquake_data["Date"] = pd.to_datetime(earthquake_data["Date"])
        earthquake_data["Time"] = pd.to_datetime(earthquake_data["Time"])
        earthquake_data["DateTime"] = earthquake_data.apply(
            lambda row: datetime.combine(row["Date"].date(), row["Time"].time()), axis=1
        )

        long = earthquake_data.Longitude.values[0]
        lat = earthquake_data.Latitude.values[0]

        return cls(
            name=earthquake_code,
            timestamp=earthquake_data.DateTime.values[0].astype("datetime64[ms]").astype(datetime),
            origin=Point(long, lat),
            depth=Distance(earthquake_data.Depth.values[0], "km"),
            magnitude=earthquake_data.Magnitude.values[0],
        )

    def plot(
        self,
        time_index: int = 0,
        figure: go.Figure = go.Figure(),
        map_obj: type[go.Scattergeo | go.Scattermap] = go.Scattermap,
    ) -> int:
        figure.add_trace(
            map_obj(
                lat=[self.origin.y],
                lon=[self.origin.x],
                mode="markers",
                marker=dict(size=[self.magnitude * 10], color=[self.depth.magnitude], opacity=0.4),
                name="Earthquake",
                hovertext=[
                    f"""
                    <br> <b>Earthquake depth:</b> {self.depth}
                    <br> <b>Earthquake magnitude:</b> {self.magnitude}
                    """
                ],
                visible=(time_index == 0),
            )
        )
        return 1
