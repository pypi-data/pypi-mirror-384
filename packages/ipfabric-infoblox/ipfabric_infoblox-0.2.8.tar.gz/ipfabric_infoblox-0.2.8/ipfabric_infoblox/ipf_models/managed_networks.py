from collections import defaultdict
from ipaddress import IPv4Interface, IPv4Network
from typing import Optional, Union

from pydantic import BaseModel, Field, PrivateAttr, ConfigDict, field_serializer


class Success(BaseModel):
    network_view: Optional[str] = None


class Error(BaseModel):
    multiple_views: bool = False
    no_matching_view: bool = False
    message: Optional[list[str]] = Field(default_factory=list)


class ManagedNetwork(BaseModel):
    site_name: str = Field(alias="siteName")
    network: IPv4Interface = Field(alias="net")
    vrf: Optional[str] = None
    mapped_vrf: Optional[str] = None
    # vlan: Optional[int] = Field(alias="vlanId")
    _net_view: str = PrivateAttr(None)
    _error: Error = PrivateAttr(default_factory=Error)
    _success: Success = PrivateAttr(default_factory=Success)
    _skip_reason: str = PrivateAttr(None)
    model_config = ConfigDict(extra="ignore")

    def __hash__(self):
        return hash(f"{self.network} - {self.site_name} - {str(self.mapped_vrf)}")

    @field_serializer("network")
    def serialize_dt(self, network: IPv4Interface, _info):
        return str(network.network)

    @property
    def error(self):
        return self._error

    @property
    def success(self):
        return self._success

    @property
    def net_view(self):
        return self._net_view

    @net_view.setter
    def net_view(self, value):
        self._net_view = value


class ManagedNetworks(BaseModel):
    networks: list[ManagedNetwork]

    @property
    def sites(self) -> set[str]:
        return {_.site_name for _ in self.networks}

    @property
    def vrfs(self) -> set[str]:
        return {_.vrf for _ in self.networks}

    @property
    def nets(self) -> list[IPv4Network]:
        return [_.network.network for _ in self.networks]

    @property
    def nets_by_view(self) -> dict[Union[str, None], list[ManagedNetwork]]:
        _ = defaultdict(list)
        for n in self.networks:
            _[n.net_view].append(n)
        return dict(_)
