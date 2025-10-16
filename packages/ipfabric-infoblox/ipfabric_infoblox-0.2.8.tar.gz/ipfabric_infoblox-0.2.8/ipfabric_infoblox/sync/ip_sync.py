from collections import defaultdict
from typing import Any

from pydantic import BaseModel

from ipfabric_infoblox.ipf_models import VRF, VLAN, Interface, SNMP, ManagedIP


class IPSync(BaseModel):
    ipf: Any

    def build(self) -> list[ManagedIP]:
        vrf, vlan, interface = defaultdict(dict), defaultdict(dict), defaultdict(dict)
        for _ in self.ipf.technology.routing.vrf_interfaces.all(columns=["sn", "vrf", "intName", "rd"]):
            if _["vrf"] in vrf[_["sn"]]:
                vrf[_["sn"]][_["vrf"]][_["intName"]] = VRF(**_)
            else:
                vrf[_["sn"]][_["vrf"]] = {_["intName"]: VRF(**_)}
        for _ in self.ipf.technology.vlans.device_detail.all(columns=["sn", "vlanId", "vlanName"]):
            vlan[_["sn"]][_["vlanId"]] = VLAN(**_)
        for _ in self.ipf.inventory.interfaces.all(
            columns=["sn", "intName", "nameOriginal", "dscr", "duplex", "speed", "media"]
        ):
            interface[_["sn"]][_["intName"]] = Interface(**_)
        snmp = {
            _["sn"]: SNMP(**_)
            for _ in self.ipf.technology.management.snmp_summary.all(columns=["sn", "location", "contact"])
        }

        managed_ips = list()
        for ip in self.ipf.technology.addressing.managed_ip_ipv4.all(
            filters={"net": ["empty", False], "ip": ["nreg", "^0.0.0.0|^127\\."]}
        ):
            managed_ips.append(
                ManagedIP(
                    device=self.ipf.devices.by_sn[ip["sn"]],
                    interface=interface.get(ip["sn"], {}).get(ip["intName"], None),
                    snmp=snmp.get(ip["sn"], None),
                    snapshot=self.ipf.snapshot,
                    vrf_obj=vrf.get(ip["sn"], {}).get(ip["vrf"], {}).get(ip["intName"], None),
                    vlan_obj=vlan.get(ip["sn"], {}).get(ip["vlanId"], None),
                    **ip,
                )
            )
        return managed_ips
