from erad.default_fragility_curves.default_peak_ground_acceleration import (
    DEFAULT_PEAK_GROUND_ACCELERATION_FRAGILITY_CURVES,
)
from erad.default_fragility_curves.default_peak_ground_velocity import (
    DEFAULT_PEAK_GROUND_VELOCITY_FRAGILITY_CURVES,
)
from erad.default_fragility_curves.default_fire_boundary_dist import (
    DEFAULT_FIRE_BOUNDARY_FRAGILITY_CURVES,
)
from erad.default_fragility_curves.default_flood_velocity import (
    DEFAULT_FLOOD_VELOCITY_FRAGILITY_CURVES,
)
from erad.default_fragility_curves.default_flood_depth import DEFAULT_FLOOD_DEPTH_FRAGILITY_CURVES
from erad.default_fragility_curves.default_wind_speed import DEFAULT_WIND_SPEED_FRAGILITY_CURVES

DEFAULT_FRAGILTY_CURVES = [
    DEFAULT_PEAK_GROUND_ACCELERATION_FRAGILITY_CURVES,
    DEFAULT_PEAK_GROUND_VELOCITY_FRAGILITY_CURVES,
    DEFAULT_FIRE_BOUNDARY_FRAGILITY_CURVES,
    DEFAULT_FLOOD_VELOCITY_FRAGILITY_CURVES,
    DEFAULT_FLOOD_DEPTH_FRAGILITY_CURVES,
    DEFAULT_WIND_SPEED_FRAGILITY_CURVES,
]
