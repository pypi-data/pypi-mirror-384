from typing import Any

from ipfabric import IPFClient
from pydantic import BaseModel, PrivateAttr

from ipfabric_infoblox.config import Configuration
from ipfabric_infoblox.infoblox.models import Log, Field
from ipfabric_infoblox.ipf_models.managed_ip import ManagedIP
from ipfabric_infoblox.sync.ip_sync import IPSync
from ipfabric_infoblox.sync.network_sync import NetworkSync


class Sync(BaseModel):
    config: Configuration
    logs: list[Log] = Field(default_factory=list)
    _ipf: IPFClient = PrivateAttr(None)
    _network_sync: NetworkSync = PrivateAttr(None)
    _ip_sync: list[ManagedIP] = PrivateAttr(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        self._ipf = IPFClient(
            base_url=self.config.ipfabric.base_url,
            auth=(
                self.config.ipfabric.token
                if self.config.ipfabric.token
                else (self.config.ipfabric.username, self.config.ipfabric.password)
            ),
            verify=self.config.ipfabric.verify,
            timeout=self.config.ipfabric.timeout,
            snapshot_id=self.config.ipfabric.snapshot_id,
        )
        self._network_sync = NetworkSync(ipf=self._ipf, config=self.config)
        self._ip_sync = IPSync(ipf=self._ipf).build()

    @property
    def network_sync(self) -> NetworkSync:
        return self._network_sync

    @property
    def ip_sync(self) -> list[ManagedIP]:
        return self._ip_sync
