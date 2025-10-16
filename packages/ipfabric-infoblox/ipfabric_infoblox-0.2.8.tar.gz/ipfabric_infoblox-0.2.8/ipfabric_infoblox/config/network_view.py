from ipaddress import IPv4Network
from typing import Optional, Any, Literal, Union

from pydantic import BaseModel, Field, model_validator, field_validator, PrivateAttr, field_serializer
from pytricia import PyTricia

DEFAULT_NET = "0.0.0.0/0"
IP_LITERALS = Literal["RFC1918", "CGNAT"]
IP_TYPES = Optional[Union[IPv4Network, IP_LITERALS, list[Union[IPv4Network, IP_LITERALS]]]]
IP_LITERAL = {
    "CGNAT": {IPv4Network("100.64.0.0/10")},
    "RFC1918": {IPv4Network("10.0.0.0/8"), IPv4Network("172.16.0.0/12"), IPv4Network("192.168.0.0/16")},
}


def format_networks(data: Any) -> list[Union[str, IPv4Network]]:
    new_data = set()
    for _ in [data] if isinstance(data, str) else data:
        if _ and isinstance(_, str) and _.upper() in IP_LITERAL:
            new_data.update(IP_LITERAL[_.upper()])
        elif _:
            new_data.add(_)
    return list(new_data)


class StringConfig(BaseModel):
    value: str
    regex: bool = False
    ignore_case: bool = True


class ConfigList(BaseModel):
    vrfs: Optional[list[StringConfig]] = Field(default_factory=list)
    sites: Optional[list[StringConfig]] = Field(default_factory=list)
    networks: IP_TYPES = Field(default_factory=list)

    @field_validator("networks", mode="before")
    @classmethod
    def check_networks(cls, data: Any) -> list[Union[str, IPv4Network]]:
        return format_networks(data)

    @field_serializer("networks", when_used="json")
    def serialize_networks(self, networks: list[Any]):
        return [str(_) for _ in networks]

    @property
    def has_items(self) -> bool:
        return True if self.networks or self.vrfs or self.sites else False

    @property
    def vrf_names(self) -> list[StringConfig]:
        return [_ for _ in self.vrfs if not _.regex]

    @property
    def vrf_regex(self) -> list[StringConfig]:
        return [_ for _ in self.vrfs if _.regex]

    @property
    def site_names(self) -> list[StringConfig]:
        return [_ for _ in self.sites if not _.regex]

    @property
    def site_regex(self) -> list[StringConfig]:
        return [_ for _ in self.sites if _.regex]


class Include(ConfigList, BaseModel): ...


class Exclude(ConfigList, BaseModel): ...


class NetworkView(BaseModel):
    name: str
    default: bool = False
    include: Optional[Include] = Field(default_factory=Include)
    exclude: Optional[Exclude] = Field(default_factory=Exclude)
    create_containerless_nets: bool = False
    managed_ip_discovery: bool = True
    split_networks: bool = False
    smallest_v4_subnet: int = 31
    _pyt: PyTricia = PrivateAttr(default_factory=PyTricia)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return self.name == other.name

    def __str__(self):
        return self.name

    def model_post_init(self, __context: Any) -> None:
        if self.default or not self.include.networks:
            self._pyt.insert(DEFAULT_NET, "INCLUDE")
        else:
            for _ in self.include.networks:
                self._pyt.insert(_, "INCLUDE")
        for _ in self.exclude.networks:
            self._pyt.insert(_, "EXCLUDE")

    @model_validator(mode="after")
    def check_config(self):
        if self.default and self.include.has_items:
            raise ValueError("Default VRF can only exclude Networks, VRFs, or Site Names and cannot include items.")
        if not self.default and not self.include.has_items:
            raise ValueError("Non-default VRF must include at least one Network, VRF, or Site Name.")
        return self

    @property
    def include_has_vrf(self) -> bool:
        return True if self.include.vrfs else False

    @property
    def exclude_has_vrf(self) -> bool:
        return True if self.exclude.vrfs else False

    @property
    def include_has_sites(self) -> bool:
        return True if self.include.sites else False

    @property
    def exclude_has_sites(self) -> bool:
        return True if self.exclude.sites else False

    @property
    def pyt(self):
        return self._pyt
