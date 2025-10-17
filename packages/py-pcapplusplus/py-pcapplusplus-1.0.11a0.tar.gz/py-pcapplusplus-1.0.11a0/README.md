# py-pcapplusplus

[![pypi](https://img.shields.io/pypi/v/py-pcapplusplus)](https://pypi.org/project/py-pcapplusplus/)
[![downloads](https://static.pepy.tech/badge/py-pcapplusplus)](https://pepy.tech/projects/py-pcapplusplus)
[![downloads_monthly](https://static.pepy.tech/badge/py-pcapplusplus/month)](https://pepy.tech/projects/py-pcapplusplus)
[![Tests](https://github.com/CYMOTIVE/py-pcapplusplus/actions/workflows/ci.yml/badge.svg)](https://github.com/CYMOTIVE/py-pcapplusplus/actions/workflows/ci.yml)

A Python wrapper for the Pcap++ library using nanobind, providing a high-level interface for network packet manipulation, capture, and analysis.

## Features

- Read and parse PCAP files
- Create and modify network packets
- Support for multiple protocol layers:
  - Ethernet
  - IPv4/IPv6
  - TCP/UDP
  - ARP
  - VLAN
  - DHCP
  - SOME/IP and SOME/IP-SD
- Raw socket operations for packet capture and injection
- High-performance packet processing

## Installation

```bash
pip install py-pcapplusplus
```

## Quick Start

### Reading PCAP Files

```python
from py_pcapplusplus import Reader, Packet

# Open a PCAP file
reader = Reader("capture.pcap")

# Iterate through packets
for packet in reader:
    # Access different layers
    eth_layer = packet[LayerType.EthLayer]
    ip_layer = packet[LayerType.IPv4Layer]
    
    # Print packet information
    print(packet)
```

### Creating Packets

```python
from py_pcapplusplus import Packet, EthLayer, IPv4Layer, TcpLayer

# Create a new packet
packet = Packet()

# Add layers
eth = EthLayer(src_mac_addr="00:11:22:33:44:55", dst_mac_addr="66:77:88:99:aa:bb")
ip = IPv4Layer(src_addr="192.168.1.1", dst_addr="192.168.1.2")
tcp = TcpLayer(src_port=12345, dst_port=80)

# Add layers to packet
packet / eth / ip / tcp
```

### Packet Capture

```python
from py_pcapplusplus import RawSocket

# Create a raw socket on a specific interface
socket = RawSocket("eth0")

# Capture packets
packets = socket.sniff(timeout=5.0)  # Capture for 5 seconds

# Process captured packets
for packet in packets:
    print(packet)
```

## API Reference

### Core Classes

#### Packet
- `get_layer(layer_type)`: Get a specific layer from the packet
- `add_layer(layer)`: Add a new layer to the packet
- `insert_layer(prev_layer, new_layer)`: Insert a layer after an existing one

#### Layer Types
- `EthLayer`: Ethernet layer
- `IPv4Layer`: IPv4 layer
- `IPv6Layer`: IPv6 layer
- `TcpLayer`: TCP layer
- `UdpLayer`: UDP layer
- `ArpLayer`: ARP layer
- `VlanLayer`: VLAN layer
- `DhcpLayer`: DHCP layer
- `SomeIpLayer`: SOME/IP layer
- `SomeIpSdLayer`: SOME/IP-SD layer
- `PayloadLayer`: Raw payload layer

### Protocol-Specific Features

#### Ethernet Layer
```python
eth = EthLayer(src_mac_addr="00:11:22:33:44:55", dst_mac_addr="66:77:88:99:aa:bb")
eth.src_mac_addr = "00:11:22:33:44:55"  # Set source MAC
eth.dst_mac_addr = "66:77:88:99:aa:bb"  # Set destination MAC
eth.ether_type = True  # Set to IPv4 (False for IPv6)
```

#### IPv4 Layer
```python
ip = IPv4Layer(src_addr="192.168.1.1", dst_addr="192.168.1.2")
ip.src_ip = "192.168.1.1"  # Set source IP
ip.dst_ip = "192.168.1.2"  # Set destination IP
ip.ttl = 64  # Set TTL
ip.clear_chksum()  # Clear checksum for recalculation
```

#### TCP Layer
```python
tcp = TcpLayer(src_port=12345, dst_port=80)
tcp.syn_flag = True  # Set SYN flag
tcp.ack_flag = True  # Set ACK flag
tcp.rst_flag = False  # Set RST flag
```

### Raw Socket Operations

```python
socket = RawSocket("eth0")

# Send a single packet
socket.send_packet(packet)

# Send multiple packets
socket.send_packets([packet1, packet2, packet3])

# Receive a packet
packet = socket.receive_packet(blocking=True, timeout=1.0)

# Sniff packets
packets = socket.sniff(timeout=5.0)
```

## Dependencies

- Pcap++ library
- nanobind
- Python 3.10

## Acknowledgments

- Pcap++ library for the underlying packet processing capabilities
- nanobind for the Python binding framework