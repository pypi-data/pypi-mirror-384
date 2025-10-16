import re
from typing import Any, Literal

from pydantic import BaseModel, PrivateAttr, Field

from ipfabric_infoblox.config import Configuration, DEFAULT_VRF, NetworkView
from ipfabric_infoblox.ipf_models.managed_networks import ManagedNetworks, ManagedNetwork


class Map(BaseModel):
    include: set[NetworkView] = Field(default_factory=set)
    exclude: set[NetworkView] = Field(default_factory=set)


class NetworkSync(BaseModel):
    ipf: Any
    config: Configuration
    _networks: ManagedNetworks = PrivateAttr(None)
    _site_map: dict[str, Map] = PrivateAttr(default_factory=dict)
    _vrf_map: dict[str, Map] = PrivateAttr(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """
        Executes the post-initialization functions for the model and initializes various
        network data structures by mapping them using predefined configurations.

        1. VRF takes precedence as there can be overlapping networks in different VRFs.
        2. Network calculation is performed next on any network without a view as it is next significant in the logic.
        3. Site calculation is then performed on any network without a view .
        4. Finally if default view exists then networks without a view are assigned the default view if not excluded.
        """
        self._networks = self._get_ipv4_nets()
        self._site_map = {_: self._mapping(_, "sites") for _ in self._networks.sites}
        self._vrf_map = {_: self._mapping(_, "vrfs") for _ in self._networks.vrfs}
        self.map_vrf_view()
        self.map_net_view()
        self.map_site_view()
        self.map_default_view()

    @property
    def networks(self) -> ManagedNetworks:
        return self._networks

    def _calculate_vrf(self, vrf: str, sn: str) -> str:
        """
        Calculate the Virtual Routing and Forwarding (VRF) value based on specific conditions.

        This method determines the VRF value to use for a given device, based on its
        vendor and family information retrieved using the device serial number. If a
        provided VRF does not match the default VRF for the device, the method returns
        the given VRF; otherwise, it returns an empty string.

        Parameters
        ----------
        vrf : str
            The VRF value to be evaluated.
        sn : str
            The serial number of the device whose vendor and family information is
            being used to determine the default VRF.

        Returns
        -------
        str
            Returns the provided VRF value if it does not match the default VRF;
            otherwise, returns an empty string.
        """
        vendor, family = self.ipf.devices.by_sn[sn].vendor, self.ipf.devices.by_sn[sn].family
        if vendor not in DEFAULT_VRF:
            default_vrf = ""
        elif family not in DEFAULT_VRF[vendor]:
            default_vrf = DEFAULT_VRF[vendor].get(None, "")
        else:
            default_vrf = DEFAULT_VRF[vendor][family]
        return vrf if vrf != default_vrf else ""

    def _get_ipv4_nets(self) -> ManagedNetworks:
        """
        Retrieve a set of managed IPv4 networks, compute the VRF mapping for each network,
        and return a ManagedNetworks object containing the processed network data.

        Summary:
        This method fetches all managed IPv4 networks from the IP Fabric platform, calculates
        the VRF for each network using a predefined mapping or logic, and organizes them into
        a set. Each network is represented as a ManagedNetwork object with the relevant
        attributes. The collection of networks is then returned as a ManagedNetworks object.

        Returns:
            ManagedNetworks: A ManagedNetworks object consisting of a list of managed networks
            with their processed attributes.
        """
        networks = set()
        vrf_map = self.config.ipfabric.mapped_vrfs
        for net in self.ipf.technology.addressing.managed_ip_ipv4.all(
            columns=["siteName", "net", "vrf", "sn"],
            filters={"net": ["empty", False], "ip": ["nreg", "^0.0.0.0|^127\\."]},
        ):
            net["vrf"] = self._calculate_vrf(net["vrf"], net["sn"])
            net["mapped_vrf"] = net["vrf"]
            if net["vrf"] in vrf_map or net["vrf"].lower() in vrf_map:
                net["mapped_vrf"] = vrf_map[net["vrf"]] if net["vrf"] in vrf_map else vrf_map[net["vrf"].lower()]

            networks.add(ManagedNetwork(**net))
        return ManagedNetworks(networks=list(networks))

    @staticmethod
    def _map(value, test) -> bool:
        """
        Determines whether a given value matches a specified test condition.

        This static method evaluates if a value satisfies a provided condition encapsulated
        in a test object. The condition may involve regular expressions, case insensitivity,
        and string equality checks. If any of the specified conditions are met, the method
        returns True.

        Arguments:
            value (str): The value to be tested for a match against the condition.
            test (Test): An object containing the test attributes to apply the matching logic.

        Returns:
            bool: True if the value satisfies the test condition; otherwise, False.
        """
        if (
            (test.regex and re.match(test.value, value, flags=re.IGNORECASE if test.ignore_case else 0))
            or (test.ignore_case and test.value.lower() == value.lower())
            or test.value == value
        ):
            return True
        return False

    def _mapping(self, value: str, attr: str) -> Map:
        """
        Maps the provided value against network view configurations based on inclusion
        and exclusion rules. The mapping is performed against a specific attribute of
        the network view configurations. The result is returned as a dictionary
        containing sets of included and excluded network views based on the matching
        criteria.

        Args:
            value: The value to match against the network view configurations.
            attr: The attribute of the network views to evaluate for the mapping.

        Returns:
            A dictionary with two keys:
                - "include": A set of NetworkView objects that match the inclusion
                  criteria and do not overlap with exclusion criteria.
                - "exclude": A set of NetworkView objects that match the exclusion
                  criteria.
        """
        include, exclude = set(), set()
        for view in self.config.network_views:
            for inc in getattr(view.include, attr):
                if self._map(value, inc):
                    include.add(view)
                else:
                    exclude.add(view)
            for exc in getattr(view.exclude, attr):
                if self._map(value, exc):
                    exclude.add(view)
        return Map(include=include - exclude, exclude=exclude)

    def _if_included(self, view: NetworkView, network: ManagedNetwork) -> bool:
        """
        Determine if a network is included in a specific network view.

        This method evaluates whether a given network should be included in the provided
        network view by checking its site, VRF (Virtual Routing and Forwarding), and
        network attributes against the view's inclusion criteria.

        Args:
            view (NetworkView): The network view to evaluate inclusion against.
            network (ManagedNetwork): The network to check for inclusion.

        Returns:
            bool: True if the network is included in the network view, otherwise False.
        """
        if (
            view.name not in self._site_map[network.site_name].exclude
            and view.name not in self._vrf_map[network.vrf].exclude
            and view.pyt.get(network.network) == "INCLUDE"
        ):
            return True
        return False

    @staticmethod
    def _check_views(network: ManagedNetwork, tmp: set[NetworkView], error_gt_1: str, error_eq_0: str, success: str):
        """
        A static method to validate and assign network views to a ManagedNetwork object. This method
        checks the number of matching network views within the provided temporary set and updates
        the network object accordingly based on the results. If exactly one view matches, it sets the
        network view as this match. If more than one match is found, it flags the network with an
        error of multiple views. If no matches are found, it flags the network with an error indicating
        no matches.

        Args:
            network (ManagedNetwork): The network object whose view is being verified or updated.
            tmp (set[str]): A temporary set storing potential matching views of the network.
            error_gt_1 (str): The error message to use when multiple views are matched.
            error_eq_0 (str): The error message to use when no matching views are found.
            success (str): A success message to assign when exactly one view matches.

        Returns:
            ManagedNetwork: The updated network object with errors or view assignment based on the validation results.
        """
        if len(tmp) == 1:
            network.net_view = tmp.pop().name
            network.error.multiple_views, network.error.no_matching_view = False, False
            network.success.network_view = success
        elif len(tmp) > 1:
            network.error.multiple_views = True
            network.error.message.append(error_gt_1)
        elif not tmp:
            network.error.no_matching_view = True
            network.error.message.append(error_eq_0)
        return network

    def map_net_view(self):
        """
        Maps network views for each network in the network configuration.

        This method iterates over a collection of network configurations and determines
        the matching network views based on the provided network view configuration.
        It performs additional checks to ensure that the matching is valid and raises
        appropriate warnings or messages based on the findings during the mapping
        process.
        """
        for network in self._networks.networks:
            net = network.network
            if network.net_view or net not in self.config.pyt:
                continue
            tmp = {_ for _ in self.config.pyt[net] if self._if_included(self.config.view_dict[_], network)}
            self._check_views(
                network,
                tmp,
                f"Multiple matching Network Views based on Network Config found: {','.join([str(_) for _ in tmp])}",
                "No matching Network Views found based on Network Config will continue with Site and Default.",
                "Matched Network based on Network Mapping.",
            )

    def _map_view(
        self, mapping: dict[str, Map], attr: Literal["site_name", "vrf"], error_gt_1: str, error_eq_0: str, success: str
    ):
        """
        Maps network views based on specified mapping, attribute, and associated messages.

        This method processes networks and applies a given mapping to determine the inclusion
        of networks in specific categories defined by the `attr` parameter. It uses predefined
        messages to handle different cases based on the number of included results, such as
        errors and success notifications.

        Args:
            mapping: A dictionary of mappings where keys are strings, and values are Map objects
                     that facilitate inclusion checking for given attributes.
            attr: A literal specifying the attribute of the network to be used for mapping. Typical
                  values are "site_name" or "vrf".
            error_gt_1: A string message to be logged or notified if there are more than one matches
                        found in the mapping results.
            error_eq_0: A string message to be logged or notified if there are no matches found in
                        the mapping results.
            success: A string message to convey a successful mapping operation.
        """
        for network in self._networks.networks:
            if network.net_view:
                continue
            tmp = {_ for _ in mapping[getattr(network, attr)].include if self._if_included(_, network)}
            self._check_views(network, tmp, f"{error_gt_1}{','.join([str(_) for _ in tmp])}", error_eq_0, success)

    def map_vrf_view(self):
        """
        Maps the network to a view based on configured VRF.
        """
        self._map_view(
            self._vrf_map,
            "vrf",
            "Multiple matching Network Views based on VRF Config found: ",
            "No matching Network Views found based on VRF Config will continue with Network, Site, and Default.",
            "Matched Network based on VRF Mapping.",
        )

    def map_site_view(self):
        """
        Maps the network to a view based on configured site name.
        """
        self._map_view(
            self._site_map,
            "site_name",
            "Multiple matching Network Views based on Site Name Config found: ",
            "No matching Network Views found based on Site Name Config will continue with Default.",
            "Matched Network based on Site Name Mapping.",
        )

    def map_default_view(self):
        """
        Maps the default view to networks that do not have an assigned view. If a network does not
        match any specific rules and a default view is defined, it attempts to assign the default
        view. It also handles cases where no default view is specified or when the network is
        explicitly excluded by the default mapping rules.
        """
        default = self.config.default_view
        for network in self._networks.networks:
            if network.net_view:
                continue
            if not default:
                network.error.no_matching_view = True
                network.error.message.append("Network did not match any rules and no default assigned.")
            elif self._if_included(default, network):
                network.net_view = default.name
                network.error.multiple_views, network.error.no_matching_view = False, False
                network.success.network_view = "Matched Network based on Default Mapping."
            else:
                network.error.no_matching_view = True
                network.error.message.append("Network did not match any rules and excluded by default.")
