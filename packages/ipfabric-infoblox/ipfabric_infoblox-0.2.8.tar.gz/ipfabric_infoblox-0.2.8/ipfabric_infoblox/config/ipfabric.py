from functools import cached_property
from typing import Optional, Union, Literal
import ssl

from httpx import URL
from pydantic import Field, AliasChoices, BaseModel, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .models import TimeoutTypes


class VRF(BaseModel):
    names: list[str] = Field(default_factory=list, description="Names of VRFs to map.", examples=[["main", "default"]])
    ignore_case: bool = True


class IPFabric(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_prefix="ipf_", extra="ignore")
    base_url: Union[str, URL] = Field(None, validation_alias=AliasChoices("base_url", "ipf_url"))
    snapshot_id: Optional[Union[str, None]] = Field(
        "$last", validation_alias=AliasChoices("snapshot_id", "ipf_snapshot")
    )
    verify: Union[ssl.SSLContext, bool, str] = True
    timeout: Union[TimeoutTypes, Literal["DEFAULT"]] = 5.0
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    vrf_mapping: Optional[dict[str, VRF]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_model(self):
        _ = self.mapped_vrfs
        if not (self.token or (self.username and self.password)):
            raise SyntaxError("IP Fabric Token or Username/Password not supplied.")
        return self

    @cached_property
    def mapped_vrfs(self):
        tmp = dict()
        for name, vrf in self.vrf_mapping.items():
            for _ in vrf.names:
                v = _.lower() if vrf.ignore_case else _
                if v in tmp:
                    raise ValueError(f"VRF named {v} mapped to '{name}' and '{tmp[v]}'.")
                tmp[v] = name
        return tmp
