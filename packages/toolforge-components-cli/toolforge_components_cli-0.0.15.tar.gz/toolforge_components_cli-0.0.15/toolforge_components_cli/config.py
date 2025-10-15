from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from toolforge_weld.config import Config, Section, load_config


@dataclass
class ComponentsConfig(Section):
    _NAME_: str = field(default="components", init=False)
    components_endpoint: str = "/components/v1"

    @classmethod
    def from_dict(cls, my_dict: dict[str, Any]):
        params = {}
        if "components_endpoint" in my_dict:
            params["components_endpoint"] = my_dict["components_endpoint"]
        return cls(**params)


@lru_cache(maxsize=None)
def get_loaded_config() -> Config:
    return load_config(client_name="components", extra_sections=[ComponentsConfig])
