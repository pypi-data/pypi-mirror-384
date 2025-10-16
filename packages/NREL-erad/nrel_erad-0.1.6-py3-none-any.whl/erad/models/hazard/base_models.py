import plotly.graph_objects as go
from pydantic import ConfigDict
from infrasys import Component


class BaseDisasterModel(Component):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    def plot(
        self, time_index: int, figure: go.Figure, map_obj: go.Scattergeo | go.Scattermap
    ) -> int:
        raise NotImplementedError("This method should be implemented in the derived classes")
