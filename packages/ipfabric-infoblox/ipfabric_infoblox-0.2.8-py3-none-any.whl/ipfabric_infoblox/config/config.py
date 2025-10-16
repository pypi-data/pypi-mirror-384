from typing import Any, Optional, Union

from pydantic import BaseModel, Field, PrivateAttr, model_validator
from pytricia import PyTricia

from .infoblox import Infoblox
from .ipfabric import IPFabric
from .network_view import NetworkView


class Configuration(BaseModel):
    ipfabric: Optional[IPFabric] = Field(default_factory=IPFabric)
    infoblox: Optional[Infoblox] = Field(default_factory=Infoblox)
    network_views: list[NetworkView] = Field(alias="networkViews")
    dry_run: bool = True
    _pyt: Any = PrivateAttr(default_factory=PyTricia)

    def model_post_init(self, __context: Any) -> None:
        self.build_pyt()

    @model_validator(mode="before")
    @classmethod
    def check_view_names(cls, data: Any) -> Any:
        if isinstance(data, dict) and "networkViews" in data:
            view_names = [_["name"] for _ in data["networkViews"]]
            if len(view_names) != len(set(view_names)):
                raise ValueError("Duplicate View Names found.")
        return data

    @model_validator(mode="after")
    def check_config(self):
        if len(self.network_views) == 0:
            raise ValueError("No Network Views configured.")
        if len([_ for _ in self.network_views if _.default]) > 1:
            raise ValueError(
                f"Only 1 default Network View can be configured and multiple found {list(self.default_view)}."
            )
        return self

    @property
    def default_view(self) -> Union[NetworkView, None]:
        if _ := [_ for _ in self.network_views if _.default]:
            return _[0]
        return None

    @property
    def view_dict(self) -> dict[str, NetworkView]:
        return {_.name: _ for _ in self.network_views}

    @property
    def pyt(self):
        return self._pyt

    def build_pyt(self):
        for view in self.network_views:
            for network in view.include.networks:
                if self._pyt.has_key(network):
                    # print(f"Duplicate network: {network}")
                    self._pyt[network].append(view)
                else:
                    self._pyt[network] = [view]
