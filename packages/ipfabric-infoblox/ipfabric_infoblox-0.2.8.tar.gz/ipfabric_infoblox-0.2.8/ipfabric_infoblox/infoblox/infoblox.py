from io import StringIO
from ipaddress import ip_network
from time import sleep
from typing import Any
from urllib.parse import urljoin

import urllib3
from httpx import Client
from pydantic import BaseModel, PrivateAttr
from pytricia import PyTricia
from requests import Session

from ipfabric_infoblox.config import Configuration
from .models import View, Container, Network

urllib3.disable_warnings()

NETWORK_FIELDS = [
    "network_container",
    "conflict_count",
    "dynamic_hosts",
    "static_hosts",
    "total_hosts",
    "unmanaged_count",
]
CSV_FIELDS = ["file_name", "end_time", "lines_failed", "lines_processed", "lines_warning", "start_time"]
CSV_STATUS = ["COMPLETED", "FAILED", "STOPPED"]
DISCOVERY_FIELDS = ["csv_file_name", "scheduled_run", "state", "status", "warning"]
DISCOVERY_STATUS = ["COMPLETE", "ERROR"]
RETURN = "_return_fields+"


class Infoblox(BaseModel):
    config: Configuration
    _client: Client = PrivateAttr(None)
    _views: dict[str, View] = PrivateAttr(None)
    _default_view: str = PrivateAttr(None)
    _session: Session = PrivateAttr(None)
    _base_url: str = PrivateAttr(None)

    # TODO IPv6

    def model_post_init(self, __context: Any) -> None:
        self._client = Client(
            base_url=self.config.infoblox.host,
            auth=(self.config.infoblox.username, self.config.infoblox.password),
            verify=self.config.infoblox.verify,
            headers={"Content-Type": "application/json"},
        )
        self._session = Session()
        self._session.verify = self.config.infoblox.verify
        self._session.auth = (self.config.infoblox.username, self.config.infoblox.password)
        resp = self._client.get("wapi/v1.0/?_schema")
        resp.raise_for_status()
        version = max(resp.json()["supported_versions"])  # TODO: Which versions to do we allow?
        self._base_url = f"{self.config.infoblox.host}/wapi/v{version}/"
        self._client.base_url = self._base_url
        self._views = {view["name"]: View(**view) for view in self.ib_pager("networkview")}
        self._default_view = next(view.name for view in self._views.values() if view.is_default)

    @property
    def ib_default_view(self) -> str:
        return self._default_view

    @property
    def views(self) -> dict[str, View]:
        return self._views

    def ib_pager(self, url: str, params: dict = None) -> list[dict]:
        url = url.replace(":", "%3A")
        params = params or {}
        params.update({"_max_results": 1000, "_paging": 1, "_return_as_object": 1})
        resp = self._client.get(url, params=params)
        resp.raise_for_status()
        r_json = resp.json()
        data, next_page_id = r_json["result"], r_json.get("next_page_id", None)
        while next_page_id:
            params["_page_id"] = next_page_id
            resp = self._client.get(url, params=params)
            resp.raise_for_status()
            r_json = resp.json()
            data.extend(r_json["result"])
            next_page_id = r_json.get("next_page_id", None)
        return data

    @staticmethod
    def ip_version(ip: str) -> int:
        return ip_network(ip).version

    def containers(self, view: str = None) -> list[Container]:
        return [
            Container(**_)
            for _ in self.ib_pager(
                "networkcontainer",
                params={"network_view": view or self.ib_default_view},
            )
        ]

    def containers_pyt(self, view: str = None) -> PyTricia:
        pyt = PyTricia()
        for container in self.containers(view):
            if self.ip_version(container.network) == 4:
                pyt[container.network] = container
        return pyt

    def networks(self, view: str = None) -> list[Network]:
        return [
            Network(**_)
            for _ in self.ib_pager(
                "network",
                params={
                    "network_view": view or self.ib_default_view,
                    RETURN: NETWORK_FIELDS,
                },
            )
        ]

    def networks_pyt(self, view: str = None) -> PyTricia:
        pyt = PyTricia()
        for network in self.networks(view):
            if self.ip_version(network.network) == 4:
                pyt[network.network] = network
        return pyt

    def _upload_init(self, csv_data: StringIO, filename: str = "ipfabric.csv") -> dict:
        # valid filename, only alphanumeric characters, underscores and periods are supported
        resp = self._client.post(
            urljoin(self._base_url, "fileop"), params={"_function": "uploadinit"}, json={"filename": filename}
        )
        resp.raise_for_status()
        data = resp.json()
        upload_resp = self._session.post(data["url"], files={"file": csv_data.getvalue()})
        upload_resp.raise_for_status()
        return data

    def wait_for_import(self, url, discovery: bool = False) -> tuple[bool, dict]:
        if discovery:
            params = {RETURN: DISCOVERY_FIELDS}
            status, finished_status = "state", DISCOVERY_STATUS
            timeout, retry = self.config.infoblox.discovery_timeout, self.config.infoblox.discovery_retry
        else:
            params = {RETURN: CSV_FIELDS}
            status, finished_status = "status", CSV_STATUS
            timeout, retry = self.config.infoblox.import_timeout, self.config.infoblox.import_retry
        for _ in range(0, retry):
            resp = self._client.get(url, params=params).json()
            if resp[status] in finished_status:
                return True, resp
            sleep(timeout if _ != retry - 1 else 0)

        return False, resp

    def csv_upload(self, csv_data: StringIO) -> tuple[bool, dict]:
        data = self._upload_init(csv_data, "ipfabric.csv")
        import_resp = self._client.post(
            "fileop",
            params={"_function": "csv_import"},
            json={"operation": "CUSTOM", "token": data["token"], "on_error": "CONTINUE"},
        )
        import_resp.raise_for_status()
        return self.wait_for_import(import_resp.json()["csv_import_task"]["_ref"])

    def csv_discovery_upload(self, csv_data: StringIO, view: str) -> tuple[bool, dict]:
        params = {RETURN: DISCOVERY_FIELDS}

        for _ in range(0, self.config.infoblox.discovery_retry):
            disc_status = self._client.get("discoverytask", params=params)
            disc_status.raise_for_status()
            disc_status = disc_status.json()
            if disc_status and {t["state"] for t in disc_status}.issubset(DISCOVERY_STATUS):
                break
            if _ == self.config.infoblox.discovery_retry - 1:
                return False, {"ERROR: Discovery import is already in progress.": disc_status}
            else:
                sleep(self.config.infoblox.discovery_timeout)

        data = self._upload_init(csv_data, "ipfDiscovery.csv")
        import_resp = self._client.post(
            "fileop",
            params={"_function": "setdiscoverycsv"},
            json={"merge_data": True, "token": data["token"], "network_view": view},
        )
        import_resp.raise_for_status()

        disc_resp = self._client.get("discoverytask", params=params)
        disc_resp.raise_for_status()
        task = {_["csv_file_name"]: _["_ref"] for _ in disc_resp.json()}.get("ipfDiscovery")
        return self.wait_for_import(task, True)
