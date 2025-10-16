from datetime import datetime
import sqlite3
import os

from pydantic import field_serializer, field_validator
from infrasys.quantities import Distance
from shapely.geometry import Point
import plotly.graph_objects as go
import geopandas as gpd
import pandas as pd

from erad.models.hazard.common import ERAD_DB, HISTROIC_HURRICANE_TABLE
from erad.models.hazard.base_models import BaseDisasterModel
from erad.quantities import Speed, Pressure


class WindModel(BaseDisasterModel):
    timestamp: datetime
    center: Point
    max_wind_speed: Speed
    radius_of_max_wind: Distance
    radius_of_closest_isobar: Distance
    air_pressure: Pressure

    @field_validator("center", mode="before")
    def deserialize_point(cls, value):
        if isinstance(value, dict) and value.get("type") == "Point":
            coords = value["coordinates"]
            return Point(coords)
        return value

    @field_serializer("center")
    def serialize_location(self, point: Point, _info):
        return {"type": "Point", "coordinates": (point.x, point.y)}

    @classmethod
    def example(cls) -> "WindModel":
        return WindModel(
            name="hurricane 1",
            timestamp=datetime.now(),
            center=Point(-121.93036, 36.60144),
            max_wind_speed=Speed(50, "miles/hour"),
            air_pressure=Pressure(1013.25, "hPa"),
            radius_of_max_wind=Distance(50, "miles"),
            radius_of_closest_isobar=Distance(300, "miles"),
        )

    @classmethod
    def from_hurricane_sid(cls, hurricane_sid: str) -> list["WindModel"]:
        assert os.path.exists(ERAD_DB), f"The data file {ERAD_DB} not found"
        conn = sqlite3.connect(ERAD_DB)
        hurricane_data = pd.read_sql(
            f"SELECT * FROM {HISTROIC_HURRICANE_TABLE} WHERE `SID ` = '{hurricane_sid}';", conn
        )
        cols = [
            "LAT (degrees_north)",
            "LON (degrees_east)",
            "USA_WIND (kts)",
            "USA_ROCI (nmile)",
            "USA_RMW (nmile)",
            "USA_POCI (mb)",
            "ISO_TIME ",
        ]
        hurricane_data = hurricane_data[cols]
        for col in cols:
            hurricane_data = hurricane_data[hurricane_data[col] != " "]
        if hurricane_data.empty:
            raise ValueError(
                f"Hurricane '{hurricane_sid}'  not found in column 'SID', table '{HISTROIC_HURRICANE_TABLE}' in the database"
            )
        conn.close()
        geometry = [
            Point(lon, lat)
            for lat, lon in zip(
                hurricane_data["LAT (degrees_north)"], hurricane_data["LON (degrees_east)"]
            )
        ]
        hurricane_data["ISO_TIME "] = pd.to_datetime(hurricane_data["ISO_TIME "])
        hurricane_data = gpd.GeoDataFrame(hurricane_data, geometry=geometry)
        hurricane_data.set_crs("epsg:4326")
        track = []
        for idx, row in hurricane_data.iterrows():
            track.append(
                WindModel(
                    name=hurricane_sid,
                    timestamp=row["ISO_TIME "],
                    center=row["geometry"],
                    max_wind_speed=Speed(float(row["USA_WIND (kts)"]), "knots"),
                    radius_of_max_wind=Distance(float(row["USA_RMW (nmile)"]), "nautical_mile"),
                    radius_of_closest_isobar=Distance(
                        float(row["USA_ROCI (nmile)"]), "nautical_mile"
                    ),
                    air_pressure=Pressure(float(row["USA_POCI (mb)"]), "millibar"),
                )
            )

        return track

    def plot(
        self,
        time_index: int = 0,
        figure: go.Figure = go.Figure(),
        map_obj: type[go.Scattergeo | go.Scattermap] = go.Scattermap,
    ) -> int:
        figure.add_trace(
            map_obj(
                lat=[self.center.y],
                lon=[self.center.x],
                mode="markers",
                marker=dict(
                    size=[self.radius_of_closest_isobar.magnitude / 5],
                    color="lightblue",
                    opacity=0.4,
                ),
                name="Radius of closest isobar",  # Name for the legend
                visible=(time_index == 0),
            )
        )

        figure.add_trace(
            map_obj(
                lat=[self.center.y],
                lon=[self.center.x],
                mode="markers",
                marker=dict(
                    size=[self.radius_of_max_wind.magnitude / 5],
                    color=[self.max_wind_speed.magnitude],
                    showscale=False,
                    opacity=0.4,
                ),
                visible=(time_index == 0),
                hovertext=[
                    f"""
                    <br> <b>Max wind speed:</b> {self.max_wind_speed}
                    <br> <b>Radius of max wind speed:</b> {self.radius_of_max_wind}
                    <br> <b>Radius of closest isobar:</b> {self.radius_of_closest_isobar}
                    <br> <b>Air pressure:</b> {self.air_pressure}
                    """
                ],
                name="Radius of max wind",  # Name for the legend
            )
        )
        return 2
