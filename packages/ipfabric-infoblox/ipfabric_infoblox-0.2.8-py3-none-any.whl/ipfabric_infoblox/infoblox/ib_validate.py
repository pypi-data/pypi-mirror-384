import csv
from collections import defaultdict
from io import StringIO
from ipaddress import ip_interface
from ipaddress import ip_network
from pathlib import Path
from typing import Any

from pydantic import BaseModel, PrivateAttr
from pytricia import PyTricia
from rich.console import Console

from ipfabric_infoblox.config import NetworkView
from ipfabric_infoblox.ipf_models import ManagedNetwork, ManagedIP, Export, ManagedNetworks
from .infoblox import Infoblox
from .models import Log

console = Console()


class ViewValidation(BaseModel):
    view_config: NetworkView
    networks_pyt: Any
    containers_pyt: Any
    managed_networks: list[ManagedNetwork]
    _validated: set[Log] = PrivateAttr(default_factory=set)
    _matched: set[Log] = PrivateAttr(default_factory=set)
    _excluded: set[Log] = PrivateAttr(default_factory=set)
    _skip_but_discover: set[Log] = PrivateAttr(default_factory=set)

    @property
    def network_view(self) -> str:
        return self.view_config.name

    @property
    def validated(self) -> set[Log]:
        return self._validated

    @property
    def matched(self) -> set[Log]:
        return self._matched

    @property
    def excluded(self) -> set[Log]:
        return self._excluded

    @property
    def skip_but_discover(self) -> set[Log]:
        return self._skip_but_discover

    @property
    def logs(self) -> set[Log]:
        return self.validated | self.matched | self.excluded

    def model_post_init(self, __context: Any) -> None:
        self.validation()

    def _copy_pyt(self, network) -> PyTricia:
        if self.networks_pyt.has_key(network):
            return self.networks_pyt
        else:
            tmp = PyTricia()
            [tmp.insert(_, self.networks_pyt[_]) for _ in self.networks_pyt]
            tmp.insert(network, network)
            return tmp

    def _validate_network(self, log: Log, policy: str) -> Log:
        network = log.network
        ip = ip_network(network)
        if ip.version == 4 and ip.prefixlen > log.smallest_v4_subnet:
            log.skip_reason = f"Skipping IPF subnet '{network}' because mask is greater than `smallest_v4_subnet={log.smallest_v4_subnet}`."
            log.skip_but_discover = True
        elif self._copy_pyt(network).children(network):
            log.has_child_network = True
            log.failure = f"Failed for IPF subnet '{network}' because IB has children network(s)."
        elif network in self.networks_pyt and self.networks_pyt[network].has_hosts:
            log.parent_network = self.networks_pyt[network]
            log.failure = f"Failed for IPF subnet '{network}' because parent IB Network '{self.networks_pyt[network].network}' has hosts."
            log.skip_but_discover = True
        elif network in self.networks_pyt and not log.split_networks:
            log.parent_network = self.networks_pyt[network]
            log.skip_reason = f"Skipping IPF subnet '{network}' under parent IB Network '{self.networks_pyt[network].network}' because `{policy}` is True and `split_networks` is False."
            log.skip_but_discover = True
        elif network in self.networks_pyt:
            log.parent_network = self.networks_pyt[network]
        return log

    def validate_network(self, ipf_network: ManagedNetwork) -> Log:
        network = str(ipf_network.network)
        log = Log(
            network=network,
            network_view=self.network_view,
            create_containerless_nets=self.view_config.create_containerless_nets,
            split_networks=self.view_config.split_networks,
            smallest_v4_subnet=self.view_config.smallest_v4_subnet,
            ipf_networks={ipf_network},
        )
        if self.containers_pyt.has_key(network):
            log.network_container = self.containers_pyt[network]
            log.failure = (
                f"Failed for IPF subnet '{network}' because it is an IB Container '{log.network_container.network}'."
            )
        elif network in self.containers_pyt and self.networks_pyt.has_key(network):
            log.network_container = self.containers_pyt[network]
            log.network_match = self.networks_pyt[network]
        elif network in self.containers_pyt:
            log.network_container = self.containers_pyt[network]
            log = self._validate_network(log, "ib_create_network")
        elif self.networks_pyt.has_key(network):
            log.network_match = self.networks_pyt[network]
        elif not self.view_config.create_containerless_nets:
            log.skip_reason = f"Skipping IPF subnet '{network}' because `create_containerless_nets` is False."
            log.skip_but_discover = True
        else:
            log = self._validate_network(log, "ib_create_container")
        return log

    def validation(self):
        logs = [self.validate_network(_) for _ in self.managed_networks]
        validated = self.validate_logs(logs=[_ for _ in logs if _.create])
        self._matched = self.validate_logs(
            logs=[_ for _ in logs if not _.create and _.has_network_match], pyt_validate=False
        )
        self._excluded = self.validate_logs(
            logs=[_ for _ in logs if not _.create and not _.has_network_match], pyt_validate=False
        )
        self._skip_but_discover = self.validate_logs(
            logs=[_ for _ in logs if not _.create and _.skip_but_discover], pyt_validate=False
        )
        for _ in validated:
            if _.create:
                self._validated.add(_)
            else:
                self._excluded.add(_)
        for log in self.logs:
            console.print(f"{log.network_view} - {log.network} - {log.status}")
        return validated

    @staticmethod
    def _validate_logs(logs: set[Log]) -> set[Log]:
        pyt = PyTricia()
        skip, create = set(), set()
        for log in logs:
            if log.create:
                pyt[log.network] = log
            else:
                skip.add(log)

        for net in pyt:
            log = pyt[net]
            if pyt.parent(net) or pyt.children(net):
                log.failure = f"Failed for IPF subnet '{net}' because overlapping IP Fabric networks found."
            create.add(log)
        return skip | create

    def validate_logs(self, logs: list[Log], pyt_validate: bool = True) -> set[Log]:
        views = defaultdict(dict)
        for log in logs:
            if str(log) in views[log.network_view]:
                views[log.network_view][str(log)].ipf_networks.update(log.ipf_networks)
            else:
                views[log.network_view][str(log)] = log
        if not pyt_validate:
            return {log for logs in views.values() for log in logs.values()}

        final = set()
        for view, logs in views.items():
            tmp = {views[view][_] for _ in logs}
            final.update(self._validate_logs(tmp))
        return final


class NetworkValidation(BaseModel):
    ib: Infoblox
    view_configs: list[NetworkView]
    managed_networks: ManagedNetworks
    _views: dict[str, ViewValidation] = PrivateAttr(default_factory=dict)

    @property
    def views(self) -> dict[str, ViewValidation]:
        return self._views

    def model_post_init(self, __context: Any) -> None:
        for _ in self.view_configs:
            self._views[_.name] = ViewValidation(
                view_config=_,
                networks_pyt=self.ib.networks_pyt(_.name),
                containers_pyt=self.ib.containers_pyt(_.name),
                managed_networks=self.managed_networks.nets_by_view.get(_, []),
            )

    @property
    def create_networks(self) -> set[Log]:
        _ = set()
        for view in self.views.values():
            _.update(view.validated)
        return _

    @property
    def matched_networks(self) -> set[Log]:
        _ = set()
        for view in self.views.values():
            _.update(view.matched)
        return _

    @property
    def skip_but_discover_networks(self) -> set[Log]:
        _ = set()
        for view in self.views.values():
            _.update(view.skip_but_discover)
        return _

    @property
    def logs(self) -> set[Log]:
        _ = set()
        for view in self.views.values():
            _.update(view.logs)
        return _

    @property
    def validated_networks(self) -> set[Log]:
        return self.create_networks | self.matched_networks | self.skip_but_discover_networks

    def validated_ipf_networks(self):
        _ = dict()
        for log in self.validated_networks:
            for net in log.ipf_networks:
                site = _.setdefault(net.site_name, dict())
                vrf = site.setdefault(net.vrf, dict())
                vrf[str(net.network)] = log
        return _

    def create_csv(self, comment: str = "") -> StringIO:
        output = StringIO()
        csv_writer = csv.writer(output, dialect="excel", quoting=csv.QUOTE_ALL)
        csv_writer.writerow(["header-network", "address*", "netmask*", "comment", "network_view", "IMPORT-ACTION"])
        for log in self.create_networks:
            ip = ip_interface(log.network)
            csv_writer.writerow(
                [
                    "network",
                    str(ip.network.network_address),
                    str(ip.network.netmask),
                    comment,
                    log.network_view,
                    "IO" if log.has_parent_network else "I",
                ]
            )
        return output

    def export_logs_to_csv(self, file_path: str) -> None:
        file_path = Path(file_path)
        with file_path.open(mode="w", newline="") as csv_file:
            writer = csv.DictWriter(
                csv_file, fieldnames=list(Log.model_fields.keys()) + list(Log.model_computed_fields.keys())
            )
            writer.writeheader()
            for log in self.logs:
                log_dict = log.model_dump(exclude={"created_network"})
                empty_vrf = "''"
                log_dict["ipf_networks"] = "\n".join(
                    [
                        f"{_['network']} - Site: - VRF:{_['vrf'] or empty_vrf} - MappedVRF:{_['mapped_vrf']}"
                        for _ in log_dict["ipf_networks"]
                    ]
                )
                for key in ["network_match", "parent_network"]:
                    log_dict[key] = (
                        f"{log_dict[key]['network_view']}:{log_dict[key]['network_container']}:{log_dict[key]['network']}"
                        if log_dict[key]
                        else ""
                    )
                if log_dict["network_container"]:
                    log_dict["network_container"] = (
                        f"{log_dict['network_container']['network_view']}:{log_dict['network_container']['network']}"
                    )
                writer.writerow(log_dict)


class ManagedIPValidation(BaseModel):
    view_configs: list[NetworkView]
    validated_ipf_networks: dict
    ips: list[ManagedIP]
    _validated_ips: dict[str, list[Export]] = PrivateAttr(default_factory=dict)

    @property
    def validated_ips(self) -> dict[str, list[Export]]:
        return self._validated_ips

    def model_post_init(self, __context: Any) -> None:
        _ = defaultdict(list)
        for ip in self.ips:
            log = self.validated_ipf_networks.get(ip.siteName, {}).get(ip.vrf, {}).get(str(ip.net.network))
            if log:
                _[log.network_view].append(ip)
        self._validated_ips = self.validate_ips(_)

    @staticmethod
    def validate_ips(managed_ips: dict[str, list[ManagedIP]]) -> dict[str, list[Export]]:
        validated = {_: list() for _ in managed_ips}
        for view, ips in managed_ips.items():
            tmp = defaultdict(list)
            for ip in ips:
                tmp[ip.ip].append(ip)
            for ip, mips in tmp.items():
                if len(mips) == 1:
                    validated[view].append(mips[0].export())
                else:
                    validated[view].append(ManagedIP.join_ips(mips))
        return validated

    def create_discovery_csvs(self) -> dict[str, StringIO]:

        def view_csv(ips):
            output = StringIO()
            csv_writer = csv.DictWriter(
                output, dialect="excel", quoting=csv.QUOTE_ALL, fieldnames=list(Export.model_fields.keys())
            )
            csv_writer.writeheader()
            for ip in ips:
                csv_writer.writerow(ip.model_dump())
            return output

        enabled = {_.name: _.managed_ip_discovery for _ in self.view_configs}
        return {k: view_csv(v) for k, v in self.validated_ips.items() if enabled[k]}
