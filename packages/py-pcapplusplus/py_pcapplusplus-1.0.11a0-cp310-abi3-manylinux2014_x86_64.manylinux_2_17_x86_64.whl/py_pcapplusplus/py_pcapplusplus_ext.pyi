from collections.abc import Sequence
import enum
from typing import overload


class Packet:
    """Represents a network packet that can contain multiple protocol layers"""

    def __init__(self) -> None:
        """Create an empty packet"""

    def get_layer(self, type: LayerType) -> Layer:
        """
        Extract layer of requested type from a packet, returns None if no such layer exists in the packet
        """

    def add_layer(self, new_layer: Layer) -> bool:
        """Add a new layer as the last layer in the packet"""

    def insert_layer(self, prev_layer: Layer, new_layer: Layer) -> bool:
        """Insert a new layer after an existing layer in the packet."""

    def __repr__(self) -> str:
        """Return a string representation of the packet"""

    def __bytes__(self) -> bytes:
        """Return the raw bytes of the packet"""

    def __getitem__(self, arg: LayerType, /) -> Layer:
        """Get a layer by type using packet[layer_type]"""

    def __truediv__(self, arg: Layer, /) -> Packet:
        """Add a layer to the packet using packet / layer"""

class Reader:
    """Device for reading and parsing .pcap files"""

    def __init__(self, pcap_path: str) -> None:
        """Initialize device and open requested pcap file"""

    def __next__(self) -> Packet:
        """Get next packet from the pcap file"""

    def __iter__(self) -> Reader:
        """Get an iterator for the pcap file"""

class LayerType(enum.Enum):
    """Enum for the different network protocol layer types"""

    EthLayer = 1
    """Ethernet layer"""

    IPv4Layer = 2
    """IPv4 layer"""

    IPv6Layer = 3
    """IPv6 layer"""

    TcpLayer = 4
    """TCP layer"""

    UdpLayer = 5
    """UDP layer"""

    ArpLayer = 8
    """ARP layer"""

    SomeIpLayer = 45
    """SOME/IP layer"""

    SomeIpSdLayer = 45
    """SOME/IP-SD layer"""

    DhcpLayer = 20
    """DHCP layer"""

    VlanLayer = 9
    """VLAN layer"""

    PayloadLayer = 25
    """Payload layer"""

class EthLayer(Layer):
    """Ethernet layer implementation"""

    def __init__(self, src_mac_addr: str = '', dst_mac_addr: str = '') -> None:
        """
        Create an Ethernet layer with optional source and destination MAC addresses
        """

    @property
    def src_mac_addr(self) -> str:
        """Source MAC address"""

    @src_mac_addr.setter
    def src_mac_addr(self, arg: str, /) -> None: ...

    @property
    def dst_mac_addr(self) -> str:
        """Destination MAC address"""

    @dst_mac_addr.setter
    def dst_mac_addr(self, arg: str, /) -> None: ...

    @property
    def ether_type(self) -> int:
        """Ethernet type (0x0800 for IPv4, 0x86dd for IPv6)"""

    @ether_type.setter
    def ether_type(self, arg: bool, /) -> None: ...

class IPv4Layer(Layer):
    """IPv4 layer implementation"""

    def __init__(self, src_addr: str, dst_addr: str) -> None: ...

    @property
    def src_ip(self) -> str: ...

    @src_ip.setter
    def src_ip(self, arg: str, /) -> None: ...

    @property
    def dst_ip(self) -> str: ...

    @dst_ip.setter
    def dst_ip(self, arg: str, /) -> None: ...

    @property
    def ttl(self) -> int: ...

    @ttl.setter
    def ttl(self, arg: int, /) -> None: ...

    @property
    def ip_identification(self) -> int: ...

    @ip_identification.setter
    def ip_identification(self, arg: int, /) -> None: ...

    def clear_chksum(self) -> None: ...

class IPv6Layer(Layer):
    """IPv6 layer implementation"""

    def __init__(self, src_addr: str, dst_addr: str) -> None: ...

    @property
    def src_ip(self) -> str: ...

    @src_ip.setter
    def src_ip(self, arg: str, /) -> None: ...

    @property
    def dst_ip(self) -> str: ...

    @dst_ip.setter
    def dst_ip(self, arg: str, /) -> None: ...

class TcpLayer(Layer):
    """TCP layer implementation"""

    def __init__(self, src_port: int, dst_port: int) -> None: ...

    def clear_chksum(self) -> None: ...

    @property
    def src_port(self) -> int: ...

    @property
    def dst_port(self) -> int: ...

    @property
    def syn_flag(self) -> int: ...

    @syn_flag.setter
    def syn_flag(self, arg: bool, /) -> None: ...

    @property
    def ack_flag(self) -> int: ...

    @ack_flag.setter
    def ack_flag(self, arg: bool, /) -> None: ...

    @property
    def rst_flag(self) -> int: ...

    @rst_flag.setter
    def rst_flag(self, arg: bool, /) -> None: ...

class UdpLayer(Layer):
    """UDP layer implementation"""

    def __init__(self, src_port: int, dst_port: int) -> None: ...

    def clear_chksum(self) -> None: ...

    @property
    def src_port(self) -> int: ...

    @property
    def dst_port(self) -> int: ...

class ArpLayer(Layer):
    """ARP layer implementation"""

    def __init__(self, opcode: ArpOpcode, src_mac_addr: str = '', dst_mac_addr: str = '', src_ip_addr: str = '', dst_ip_addr: str = '') -> None: ...

    @property
    def sender_mac_address(self) -> str: ...

    @sender_mac_address.setter
    def sender_mac_address(self, arg: str, /) -> None: ...

    @property
    def target_mac_address(self) -> str: ...

    @target_mac_address.setter
    def target_mac_address(self, arg: str, /) -> None: ...

    @property
    def sender_ip_address(self) -> str: ...

    @sender_ip_address.setter
    def sender_ip_address(self, arg: str, /) -> None: ...

    @property
    def target_ip_address(self) -> str: ...

    @target_ip_address.setter
    def target_ip_address(self, arg: str, /) -> None: ...

    def getArpHeader(self) -> "pcpp::arphdr": ...

    def getSenderMacAddress(self) -> MacAddress: ...

    def getTargetMacAddress(self) -> MacAddress: ...

    def getSenderIpAddr(self) -> IPv4Address: ...

    def getTargetIpAddr(self) -> IPv4Address: ...

    def parseNextLayer(self) -> None: ...

    def getHeaderLen(self) -> int: ...

    def computeCalculateFields(self) -> None: ...

    def isRequest(self) -> bool: ...

    def isReply(self) -> bool: ...

    def toString(self) -> str: ...

    def getOsiModelLayer(self) -> "pcpp::OsiModelLayer": ...

class SomeIpLayer(Layer):
    """SOME/IP layer implementation"""

    def __init__(self, service_id: int = 0, method_id: int = 0, client_id: int = 0, session_id: int = 0, interface_version: int = 0, msg_type: SomeIpMsgType = SomeIpMsgType.REQUEST, return_code: int = 0, payload: bytes = ...) -> None: ...

    @staticmethod
    def from_bytes(raw_data: bytes) -> SomeIpLayer: ...

    @property
    def service_id(self) -> int: ...

    @service_id.setter
    def service_id(self, arg: int, /) -> None: ...

    @property
    def method_id(self) -> int: ...

    @method_id.setter
    def method_id(self, arg: int, /) -> None: ...

    @property
    def client_id(self) -> int: ...

    @client_id.setter
    def client_id(self, arg: int, /) -> None: ...

    @property
    def session_id(self) -> int: ...

    @session_id.setter
    def session_id(self, arg: int, /) -> None: ...

    @property
    def interface_version(self) -> int: ...

    @interface_version.setter
    def interface_version(self, arg: int, /) -> None: ...

    @property
    def message_type(self) -> SomeIpMsgType: ...

    @message_type.setter
    def message_type(self, arg: SomeIpMsgType, /) -> None: ...

    @property
    def return_code(self) -> int: ...

    @return_code.setter
    def return_code(self, arg: int, /) -> None: ...

    @property
    def protocol_version(self) -> int: ...

    @protocol_version.setter
    def protocol_version(self, arg: int, /) -> None: ...

    @property
    def payload(self) -> bytes: ...

class DhcpLayer(Layer):
    """DHCP layer implementation"""

    def __init__(self, msg_type: DhcpMessageType = DhcpMessageType.DHCP_UNKNOWN_MSG_TYPE, client_mac_addr: str = '') -> None: ...

    @property
    def server_ip(self) -> str: ...

    @server_ip.setter
    def server_ip(self, arg: str, /) -> None: ...

    @property
    def gateway_ip(self) -> str: ...

    @gateway_ip.setter
    def gateway_ip(self, arg: str, /) -> None: ...

    @property
    def client_ip(self) -> str: ...

    @client_ip.setter
    def client_ip(self, arg: str, /) -> None: ...

    @property
    def your_ip(self) -> str: ...

    @your_ip.setter
    def your_ip(self, arg: str, /) -> None: ...

    @property
    def flags(self) -> int: ...

class VlanLayer(Layer):
    """VLAN layer implementation"""

    def __init__(self, vlan_id: int, cfi: bool, priority: int, ether_type: int = 0) -> None: ...

    @property
    def vlan_id(self) -> int: ...

    @vlan_id.setter
    def vlan_id(self, arg: int, /) -> None: ...

    @property
    def cfi(self) -> int: ...

    @cfi.setter
    def cfi(self, arg: bool, /) -> None: ...

    @property
    def priority(self) -> int: ...

    @priority.setter
    def priority(self, arg: int, /) -> None: ...

class PayloadLayer(Layer):
    """Payload layer implementation"""

    def __init__(self, data: bytes) -> None: ...

class Layer:
    """Base class for all network protocol layers"""

    def __repr__(self) -> str:
        """Return a string representation of the layer"""

    def __bytes__(self) -> bytes:
        """Return the raw bytes of the layer"""

class MacAddress:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: str, /) -> None: ...

    def toString(self) -> str: ...

class IPv4Address:
    @overload
    def __init__(self) -> None: ...

    @overload
    def __init__(self, arg: str, /) -> None: ...

    def toString(self) -> str: ...

class ArpOpcode(enum.Enum):
    """ARP operation codes"""

    ARP_REQUEST = 1

    ARP_REPLY = 2

ARP_REQUEST: ArpOpcode = ArpOpcode.ARP_REQUEST

ARP_REPLY: ArpOpcode = ArpOpcode.ARP_REPLY

def send_eth_packets(eth_interface: str, packets: Sequence[Packet], dst_ipv4_addr: str) -> int:
    """Sends a list of packets over the specified network interface"""

def sniff_eth(eth_interface: str, timeout: float) -> list[Packet]:
    """
    Sniff over the provided interface and capture packets up to provided timeout
    """

class SomeIpMsgType(enum.Enum):
    """Enum for the different SOME/IP message types"""

    REQUEST = 0

    REQUEST_ACK = 64

    REQUEST_NO_RETURN = 1

    REQUEST_NO_RETURN_ACK = 65

    NOTIFICATION = 2

    NOTIFICATION_ACK = 66

    RESPONSE = 128

    RESPONSE_ACK = 192

    ERRORS = 129

    ERROR_ACK = 193

    TP_REQUEST = 32

    TP_REQUEST_NO_RETURN = 33

    TP_NOTIFICATION = 34

    TP_RESPONSE = 160

    TP_ERROR = 161

REQUEST: SomeIpMsgType = SomeIpMsgType.REQUEST

REQUEST_ACK: SomeIpMsgType = SomeIpMsgType.REQUEST_ACK

REQUEST_NO_RETURN: SomeIpMsgType = SomeIpMsgType.REQUEST_NO_RETURN

REQUEST_NO_RETURN_ACK: SomeIpMsgType = SomeIpMsgType.REQUEST_NO_RETURN_ACK

NOTIFICATION: SomeIpMsgType = SomeIpMsgType.NOTIFICATION

NOTIFICATION_ACK: SomeIpMsgType = SomeIpMsgType.NOTIFICATION_ACK

RESPONSE: SomeIpMsgType = SomeIpMsgType.RESPONSE

RESPONSE_ACK: SomeIpMsgType = SomeIpMsgType.RESPONSE_ACK

ERRORS: SomeIpMsgType = SomeIpMsgType.ERRORS

ERROR_ACK: SomeIpMsgType = SomeIpMsgType.ERROR_ACK

TP_REQUEST: SomeIpMsgType = SomeIpMsgType.TP_REQUEST

TP_REQUEST_NO_RETURN: SomeIpMsgType = SomeIpMsgType.TP_REQUEST_NO_RETURN

TP_NOTIFICATION: SomeIpMsgType = SomeIpMsgType.TP_NOTIFICATION

TP_RESPONSE: SomeIpMsgType = SomeIpMsgType.TP_RESPONSE

TP_ERROR: SomeIpMsgType = SomeIpMsgType.TP_ERROR

class SomeIpSdEntryType(enum.Enum):
    """Types of entries that can occur in SOME/IP-SD"""

    FindService = 0

    OfferService = 1

    StopOfferService = 2

    SubscribeEventgroup = 3

    StopSubscribeEventgroup = 4

    SubscribeEventgroupAck = 5

    SubscribeEventgroupNack = 6

FindService: SomeIpSdEntryType = SomeIpSdEntryType.FindService

OfferService: SomeIpSdEntryType = SomeIpSdEntryType.OfferService

StopOfferService: SomeIpSdEntryType = SomeIpSdEntryType.StopOfferService

SubscribeEventgroup: SomeIpSdEntryType = SomeIpSdEntryType.SubscribeEventgroup

StopSubscribeEventgroup: SomeIpSdEntryType = SomeIpSdEntryType.StopSubscribeEventgroup

SubscribeEventgroupAck: SomeIpSdEntryType = SomeIpSdEntryType.SubscribeEventgroupAck

SubscribeEventgroupNack: SomeIpSdEntryType = SomeIpSdEntryType.SubscribeEventgroupNack

class SomeIpSdIPv4OptionType(enum.Enum):
    """Types of IPv4 options in SOME/IP-SD"""

    IPv4Endpoint = 0

    IPv4Multicast = 1

    IPv4SdEndpoint = 2

IPv4Endpoint: SomeIpSdOptionType = SomeIpSdOptionType.IPv4Endpoint

IPv4Multicast: SomeIpSdOptionType = SomeIpSdOptionType.IPv4Multicast

IPv4SdEndpoint: SomeIpSdOptionType = SomeIpSdOptionType.IPv4SdEndpoint

class SomeIpSdIPv6OptionType(enum.Enum):
    """Types of IPv6 options in SOME/IP-SD"""

    IPv6Endpoint = 0

    IPv6Multicast = 1

    IPv6SdEndpoint = 2

IPv6Endpoint: SomeIpSdOptionType = SomeIpSdOptionType.IPv6Endpoint

IPv6Multicast: SomeIpSdOptionType = SomeIpSdOptionType.IPv6Multicast

IPv6SdEndpoint: SomeIpSdOptionType = SomeIpSdOptionType.IPv6SdEndpoint

class SomeIpSdProtocolType(enum.Enum):
    """Types of protocols that can be referenced in SOME/IP-SD"""

    SD_TCP = 6

    SD_UDP = 17

SD_TCP: SomeIpSdProtocolType = SomeIpSdProtocolType.SD_TCP

SD_UDP: SomeIpSdProtocolType = SomeIpSdProtocolType.SD_UDP

class SomeIpSdOptionType(enum.Enum):
    """Types of options available for the SOME/IP-SD protocol"""

    Unknown = 0

    ConfigurationString = 1

    LoadBalancing = 2

    IPv4Endpoint = 4

    IPv6Endpoint = 6

    IPv4Multicast = 20

    IPv6Multicast = 22

    IPv4SdEndpoint = 36

    IPv6SdEndpoint = 38

Unknown: SomeIpSdOptionType = SomeIpSdOptionType.Unknown

ConfigurationString: SomeIpSdOptionType = SomeIpSdOptionType.ConfigurationString

LoadBalancing: SomeIpSdOptionType = SomeIpSdOptionType.LoadBalancing

class DhcpMessageType(enum.Enum):
    """DHCP message types"""

    DHCP_UNKNOWN_MSG_TYPE = 0

    DHCP_DISCOVER = 1

    DHCP_OFFER = 2

    DHCP_REQUEST = 3

    DHCP_DECLINE = 4

    DHCP_ACK = 5

    DHCP_NAK = 6

    DHCP_RELEASE = 7

    DHCP_INFORM = 8

DHCP_UNKNOWN_MSG_TYPE: DhcpMessageType = DhcpMessageType.DHCP_UNKNOWN_MSG_TYPE

DHCP_DISCOVER: DhcpMessageType = DhcpMessageType.DHCP_DISCOVER

DHCP_OFFER: DhcpMessageType = DhcpMessageType.DHCP_OFFER

DHCP_REQUEST: DhcpMessageType = DhcpMessageType.DHCP_REQUEST

DHCP_DECLINE: DhcpMessageType = DhcpMessageType.DHCP_DECLINE

DHCP_ACK: DhcpMessageType = DhcpMessageType.DHCP_ACK

DHCP_NAK: DhcpMessageType = DhcpMessageType.DHCP_NAK

DHCP_RELEASE: DhcpMessageType = DhcpMessageType.DHCP_RELEASE

DHCP_INFORM: DhcpMessageType = DhcpMessageType.DHCP_INFORM

class SomeIpSdLayer(SomeIpLayer):
    """SOME/IP-SD layer implementation"""

    def __init__(self, service_id: int = 65535, method_id: int = 33024, client_id: int = 0, session_id: int = 1, interface_version: int = 1, msg_type: SomeIpMsgType = SomeIpMsgType.NOTIFICATION, return_code: int = 0, flags: int = 128) -> None: ...

    @staticmethod
    def from_bytes(raw_data: bytes) -> SomeIpSdLayer: ...

    @property
    def flags(self) -> int: ...

    @flags.setter
    def flags(self, arg: int, /) -> None: ...

    def add_entry(self, entry: SomeIpSdEntry) -> int: ...

    def add_option_to(self, index: int, option: SomeIpSdOption) -> bool: ...

    def get_entries(self) -> list[SomeIpSdEntry]: ...

    def get_options(self) -> list[SomeIpSdOption]: ...

class SomeIpSdEntry:
    @overload
    def __init__(self, entry_type: SomeIpSdEntryType, service_id: int, instance_id: int, major_version: int, ttl: int, minor_version: int) -> None:
        """Construct a new SOME/IP-SD Service Entry Type"""

    @overload
    def __init__(self, entry_type: SomeIpSdEntryType, service_id: int, instance_id: int, major_version: int, ttl: int, counter: int, event_group_id: int) -> None: ...

    @property
    def service_id(self) -> int: ...

    @service_id.setter
    def service_id(self, arg: int, /) -> None: ...

    @property
    def instance_id(self) -> int: ...

    @instance_id.setter
    def instance_id(self, arg: int, /) -> None: ...

    @property
    def major_version(self) -> int: ...

    @major_version.setter
    def major_version(self, arg: int, /) -> None: ...

    @property
    def minor_version(self) -> int: ...

    @minor_version.setter
    def minor_version(self, arg: int, /) -> None: ...

    @property
    def ttl(self) -> int: ...

    @ttl.setter
    def ttl(self, arg: int, /) -> None: ...

    @property
    def counter(self) -> int: ...

    @counter.setter
    def counter(self, arg: int, /) -> None: ...

    @property
    def event_group_id(self) -> int: ...

    @event_group_id.setter
    def event_group_id(self, arg: int, /) -> None: ...

    @property
    def type(self) -> SomeIpSdEntryType: ...

    @property
    def index_1(self) -> int: ...

    @property
    def index_2(self) -> int: ...

    @property
    def n_opt_1(self) -> int: ...

    @property
    def n_opt_2(self) -> int: ...

class SomeIpSdOption:
    @property
    def type(self) -> SomeIpSdOptionType: ...

class SomeIpSdIPv4Option(SomeIpSdOption):
    def __init__(self, option_type: SomeIpSdIPv4OptionType, ipv4_addr: str, port: int, protocol_type: SomeIpSdProtocolType) -> None: ...

    @property
    def addr(self) -> str: ...

    @property
    def port(self) -> int: ...

    @property
    def protocol_type(self) -> SomeIpSdProtocolType: ...

class SomeIpSdIPv6Option(SomeIpSdOption):
    def __init__(self, option_type: SomeIpSdIPv6OptionType, ipv6_addr: str, port: int, protocol_type: SomeIpSdProtocolType) -> None: ...

    @property
    def addr(self) -> str: ...

    @property
    def port(self) -> int: ...

    @property
    def protocol_type(self) -> SomeIpSdProtocolType: ...

class RawSocket:
    """Raw socket device for sending and receiving packets"""

    def __init__(self, if_name: str) -> None: ...

    def send_packet(self, packet: Packet) -> bool: ...

    def receive_packet(self, blocking: bool = True, timeout: float = -1) -> Packet: ...

    def sniff(self, timeout: float = 1) -> list[Packet]: ...

    def send_packets(self, packets: Sequence[Packet]) -> int:
        """Sends a list of packets over the specified network interface"""
