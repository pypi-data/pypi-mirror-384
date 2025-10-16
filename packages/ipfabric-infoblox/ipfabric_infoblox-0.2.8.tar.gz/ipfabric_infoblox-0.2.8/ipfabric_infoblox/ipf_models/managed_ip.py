"""https://www.dvolve.net/blog/2020/09/hacking-infoblox-discovery-for-fun-and-profit/"""

from ipaddress import IPv4Interface
from typing import Optional

from ipfabric.models import Device, Snapshot
from macaddress import MAC
from pydantic import BaseModel, ConfigDict, field_validator, Field

from ipfabric_infoblox.config import DEFAULT_VRF


def convert_none(value: Optional[str]) -> str:
    return value or ""


class VLAN(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sn: str
    vlanId: int
    vlanName: Optional[str] = ""
    _normalize_vlan = field_validator("vlanName")(convert_none)


class VRF(BaseModel):
    model_config = ConfigDict(extra="ignore")
    _normalize_rd = field_validator("rd")(convert_none)

    sn: str
    vrf: str
    intName: str
    rd: Optional[str] = ""


class SNMP(BaseModel):
    model_config = ConfigDict(extra="ignore")
    _normalize_snmp = field_validator("location", "contact")(convert_none)

    sn: str
    location: Optional[str] = ""
    contact: Optional[str] = ""


class Interface(BaseModel):
    model_config = ConfigDict(extra="ignore")
    _normalize_int = field_validator("dscr", "duplex", "media")(convert_none)

    sn: str
    intName: str
    nameOriginal: Optional[str] = ""
    dscr: Optional[str] = ""
    duplex: Optional[str] = ""
    speed: Optional[str] = ""
    media: Optional[str] = ""

    @property
    def calc_duplex(self) -> str:
        # Bad syntax for member 'port_duplex' in 'discovery_data' val:'auto' on insert err:'Values must be 'Full Half''
        if self.duplex in ["full", "half"]:
            return self.duplex.capitalize()
        return ""


class Export(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ip_address: str
    device_contact: str = ""
    device_location: str = ""
    device_model: str = ""
    device_vendor: str = ""
    device_port_name: str = ""
    device_port_type: str = ""
    discovered_name: str = ""
    discoverer: str = "IP Fabric"
    last_discovered_timestamp: str = ""
    mac_address: str = ""
    network_component_model: str = ""
    network_component_name: str = ""
    network_component_port_description: str = ""
    network_component_port_name: str = ""
    network_component_type: str = ""
    network_component_vendor: str = ""
    os: str = ""
    port_duplex: str = ""
    port_link_status: str = ""
    port_status: str = ""
    port_vlan_name: str = ""
    port_vlan_number: str = ""
    vrf_name: str = ""
    vrf_rd: str = ""
    task_name: str = Field("", exclude=True, description="DO NOT USE ME!")  # ATTENTION: NEVER SEND TO NIOS!!!!
    # ap_ip_address="",  # TODO: WIFI ARP Stuff
    # ap_name="",  # TODO: WIFI ARP Stuff
    # ap_ssid="",  # TODO: WIFI ARP Stuff
    # bgp_as="",  # TODO: Have to combine BGP advertised routes and neighbors?
    # bridge_domain="",  # TODO: ACI ARP Stuff
    # tenant="",  # TODO: ACI ARP Stuff
    # endpoint_groups="",  # TODO: ACI ARP Stuff


class ManagedIP(BaseModel):
    model_config = ConfigDict(extra="ignore")
    _normalize_ip = field_validator("stateL1", "stateL2", "mac", "vrf", "type")(convert_none)

    hostname: str
    ip: str
    sn: str
    intName: str
    stateL1: Optional[str] = ""
    stateL2: Optional[str] = ""
    siteName: str
    vlanId: Optional[int] = None
    net: IPv4Interface
    mac: Optional[str] = ""
    device: Device
    vrf: str = ""
    type: Optional[str] = ""
    snmp: Optional[SNMP] = None
    interface: Optional[Interface] = None
    snapshot: Snapshot
    vrf_obj: Optional[VRF] = None
    vlan_obj: Optional[VLAN] = None

    @property
    def calc_vrf(self) -> str:
        if self.device.vendor not in DEFAULT_VRF:
            default_vrf = ""
        elif self.device.family not in DEFAULT_VRF[self.device.vendor]:
            default_vrf = DEFAULT_VRF[self.device.vendor].get(None, "")
        else:
            default_vrf = DEFAULT_VRF[self.device.vendor][self.device.family]
        return self.vrf if self.vrf != default_vrf else ""

    @staticmethod
    def calc_state(state) -> str:
        # Bad syntax for member 'port_link_status':'Values must be 'Connected Not\ Connected Unknown''
        if state in ["up"]:
            return "Connected"
        if state in ["down"]:
            return "Not Connected"
        return "Unknown"

    @staticmethod
    def calc_status(status) -> str:
        # Bad syntax for member 'port_status':'Values must be 'Up Down Unknown'
        if status in ["up", "down"]:
            return status.capitalize()
        return "Unknown"

    def export(self) -> Export:
        # wapidoc/additional/structs.html#struct-discoverydata
        return Export(
            ip_address=self.ip,
            device_contact=self.snmp.contact if self.snmp else "",
            device_location=self.snmp.location if self.snmp else "",
            device_model=self.device.model or "",
            device_vendor=self.device.vendor,
            device_port_type=self.interface.media if self.interface else self.intName,
            discovered_name=self.device.fqdn if self.device.fqdn else self.hostname,
            last_discovered_timestamp=(
                self.device.ts_discovery_start if self.device.ts_discovery_start else self.snapshot.start
            ).strftime("%Y-%m-%d %H:%M:%S"),
            mac_address=str(MAC(self.mac)).replace("-", ":").lower() if self.mac else "",
            network_component_model=self.device.model or "",
            network_component_name=self.hostname,
            network_component_port_description=self.interface.dscr if self.interface else "",
            network_component_port_name=self.intName,
            network_component_type=self.device.dev_type,
            network_component_vendor=self.device.vendor,
            os=self.device.version or "",
            port_duplex=self.interface.calc_duplex if self.interface else "",
            port_link_status=self.calc_state(self.stateL1),
            port_status=self.calc_status(self.stateL2),
            port_vlan_name=self.vlan_obj.vlanName if self.vlan_obj else "",
            port_vlan_number=str(self.vlanId or ""),
            vrf_name=self.calc_vrf,
            vrf_rd=self.vrf_obj.rd if self.vrf_obj else "",
            task_name=self.device.task_key or "",  # This may work but would it be any benefit?
        )

    @classmethod
    def join_ips(cls, ips: list["ManagedIP"]) -> Export:
        joined = dict(
            port_vlan_name=set(),
            port_vlan_number=set(),
            vrf_name=set(),
            vrf_rd=set(),
            mac_address=set(),
        )
        for ip in ips:
            for k, v in ip.export().model_dump().items():
                if k in joined and v:
                    joined[k].add(v)
        for k, v in joined.items():
            joined[k] = v.pop() if len(v) == 1 else ""

        ip = ips[0]
        return Export(
            ip_address=ip.ip,
            discovered_name=",".join({_.device.fqdn if _.device.fqdn else _.hostname for _ in ips}),
            last_discovered_timestamp=ip.snapshot.start.strftime("%Y-%m-%d %H:%M:%S"),
            network_component_name=",".join({_.hostname for _ in ips}),
            task_name=f"IP Fabric Snapshot {ip.snapshot.snapshot_id}",
            **joined,
        )


"""
Do not use the following:
Bad syntax for member 'network_component_port_number' in 'discovery_data' val:'0/0/2.0' on insert err:'Invalid integer.'
network_component_port_number=self.interface.calc_name[1]

Bad syntax for member 'port_speed' in 'discovery_data' val:'auto' on insert err:'Values must be '10M 100M 1G 10G 100G Unknown''
port_speed=self.interface.calc_speed,

NEVER SEND TASK_NAME!!!!
The task name must be unique or else previously discovered data with that task name is removed.
"""
