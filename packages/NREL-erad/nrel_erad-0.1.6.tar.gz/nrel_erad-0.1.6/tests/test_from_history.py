from erad.models.hazard import EarthQuakeModel, FireModel, WindModel


def test_earthquake_from_history():
    EarthQuakeModel.from_earthquake_code("ISCGEM851547")


def test_fire_from_history():
    FireModel.from_wildfire_name("GREAT LAKES FIRE")


def test_hurricane_from_history():
    WindModel.from_hurricane_sid("2017228N14314")
