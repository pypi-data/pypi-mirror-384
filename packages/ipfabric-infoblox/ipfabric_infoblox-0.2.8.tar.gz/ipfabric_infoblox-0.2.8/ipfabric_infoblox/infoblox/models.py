from typing import Optional

from pydantic import BaseModel, Field, computed_field, field_serializer

from ipfabric_infoblox.ipf_models import ManagedNetwork


class Ref(BaseModel):
    ref: str = Field(alias="_ref")
    comment: Optional[str] = None


class View(Ref, BaseModel):
    name: str
    is_default: bool


class Container(Ref, BaseModel):
    network: str
    network_view: str


class Network(Container, BaseModel):
    network_container: str
    conflict_count: int
    dynamic_hosts: int
    static_hosts: int
    total_hosts: int
    unmanaged_count: int

    @property
    def has_hosts(self) -> bool:
        return (
            self.total_hosts + self.conflict_count + self.dynamic_hosts + self.static_hosts + self.unmanaged_count
        ) > 0


class Log(BaseModel):
    """
    A Log object representing the status and outcome of network validation and management operations.

    This model is used to track the state of a network during validation, creation, or updates.
    It includes properties for various stages of the process, such as whether the network has a parent,
    whether it matches an existing network, or if it needs to be created. The class also provides computed
    fields for dynamically determining the network's status.

    Attributes:
        network (str): The CIDR or address of the network being validated.
        network_view (str): The name of the network view associated with the network.
        create_containerless_nets (bool): Whether to create containerless networks. Default is False.
        split_networks (bool): Whether to split larger networks into smaller subnets. Default is False.
        smallest_v4_subnet (int): The smallest allowable IPv4 subnet size. Default is 31.
        ipf_networks (set[ManagedNetwork]): A set of IP Fabric managed networks relevant to the current network.
        network_container (Optional[Container]): The container network (if applicable).
        parent_network (Optional[Network]): The parent network of the current network (if any).
        network_match (Optional[Network]): The matching network (if a match exists).
        created_network (Optional[Network]): The network object created during the process (if any).
        has_child_network (bool): Indicates whether the network has any child subnets. Default is False.
        failure (Optional[str]): A message describing the failure reason, if the process failed.
        skip_reason (Optional[str]): A message describing why the network was skipped, if applicable.

    Computed Properties:
        has_parent_network (bool): Indicates if the current network has a parent network.
        parent_network_has_hosts (bool): Indicates if the parent network has associated hosts.
        network_is_container (bool): Indicates if the current network is a container network.
        has_network_match (bool): Indicates if the current network matches an existing network.
        skipped (bool): Indicates if the network was skipped.
        failed (bool): Indicates if the process failed for the current network.
        create (bool): Indicates if the network needs to be created (not skipped, not failed, and no match exists).
        status (str): The status of the network, dynamically computed as one of:
            - "failed": If the network validation failed.
            - "skipped": If the network was skipped.
            - "create": If the network needs to be created.
            - "exists": If the network matches an existing one.
            - "unknown": If none of the above conditions apply.

    Methods:
        __str__(): Returns a string representation of the Log object in the format: "network - network_view".
        __hash__(): Generates a hash value based on the string representation of the Log object.
    """

    network: str
    network_view: str
    create_containerless_nets: bool = False
    split_networks: bool = False
    smallest_v4_subnet: int = 31
    ipf_networks: set[ManagedNetwork] = Field(default_factory=set, exclude=False)
    network_container: Optional[Container] = None
    parent_network: Optional[Network] = None
    network_match: Optional[Network] = None
    created_network: Optional[Network] = None
    has_child_network: bool = False
    failure: Optional[str] = None
    skip_reason: Optional[str] = None
    skip_but_discover: bool = False

    def __str__(self):
        return f"{self.network} - {self.network_view}"

    def __hash__(self):
        return hash(str(self))

    @field_serializer("ipf_networks")
    def serialize_dt(self, networks: set, _info):
        return list(networks)

    @computed_field
    @property
    def has_parent_network(self) -> bool:
        return self.parent_network is not None

    @computed_field
    @property
    def parent_network_has_hosts(self) -> bool:
        return self.parent_network.has_hosts if self.parent_network else False

    @computed_field
    @property
    def network_is_container(self) -> bool:
        return self.network_container.network == self.network if self.network_container else False

    @computed_field
    @property
    def has_network_match(self) -> bool:
        return self.network_match is not None

    @computed_field
    @property
    def skipped(self) -> bool:
        return self.skip_reason is not None

    @computed_field
    @property
    def failed(self) -> bool:
        return self.failure is not None

    @computed_field
    @property
    def create(self) -> bool:
        return not self.failed and not self.skipped and not self.has_network_match

    @computed_field
    @property
    def status(self) -> str:
        """Dynamically computed status based on log properties."""
        if self.failed:
            return "failed"
        elif self.skipped:
            return "skipped"
        elif self.create:
            return "create"
        elif self.has_network_match:
            return "exists"
        return "unknown"
