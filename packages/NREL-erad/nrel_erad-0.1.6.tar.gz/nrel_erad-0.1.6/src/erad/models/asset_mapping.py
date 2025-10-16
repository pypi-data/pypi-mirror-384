from typing import Type, Callable

from pydantic import BaseModel, ConfigDict
from infrasys import Component

from erad.enums import AssetTypes


class BaseEradScenarioModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")


class ComponentFilterModel(BaseEradScenarioModel):
    component_type: Type[Component]
    component_filter: Callable | None = None


class AssetComponentMap(BaseEradScenarioModel):
    asset_type: AssetTypes
    filters: list[ComponentFilterModel] = []
