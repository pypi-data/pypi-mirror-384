#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/vector.h>

#include <algorithm>
#include <iostream>

#include "wrapperClasses.hpp"

namespace nb = nanobind;
using namespace nb::literals;

NB_MODULE(py_pcapplusplus_ext, m) {
    m.doc() = "This extension wraps Pcap++ library for parsing packets from pcap files, modifying them and sending them";

    nb::class_<pcpp::Packet>(m, "Packet", "Represents a network packet that can contain multiple protocol layers")
        .def(nb::init<>(), "Create an empty packet")
        .def("get_layer",  [](pcpp::Packet &packet, LayerType const& layerType){
            return packet.getLayerOfType(static_cast<pcpp::ProtocolType>(layerType));
        }
        , nb::rv_policy::reference
        , "type"_a, "Extract layer of requested type from a packet, returns None if no such layer exists in the packet")
        .def("add_layer", [](pcpp::Packet &packet, pcpp::Layer* newLayer){
                auto res = packet.addLayer(newLayer);
                if (res)
                    packet.computeCalculateFields();
                return res;
            }, "new_layer"_a, "Add a new layer as the last layer in the packet")
        .def("insert_layer", [](pcpp::Packet &packet, pcpp::Layer* prevLayer, pcpp::Layer* newLayer){
                return packet.insertLayer(prevLayer, newLayer);
            }, "prev_layer"_a, "new_layer"_a, "Insert a new layer after an existing layer in the packet.")
        .def("__repr__", [](pcpp::Packet& packet){
            return packet.toString();
        }, "Return a string representation of the packet")
        .def("__bytes__", [](pcpp::Packet const& packet){
            const uint8_t* rawData = packet.getRawPacket()->getRawData();
            int rawDataLen = packet.getRawPacket()->getRawDataLen();
            return nanobind::bytes(reinterpret_cast<const char*>(rawData), rawDataLen);
        }, "Return the raw bytes of the packet")
        .def("__getitem__", [](pcpp::Packet const& packet, LayerType const& layerType) -> pcpp::Layer* {
            return packet.getLayerOfType(static_cast<pcpp::ProtocolType>(layerType));
        }, nb::is_operator(), "Get a layer by type using packet[layer_type]")
        .def("__truediv__", [](pcpp::Packet* packet, pcpp::Layer* layer) -> pcpp::Packet* {  
            packet->addLayer(layer);
            packet->computeCalculateFields();
            return packet;
        }, nb::is_operator(), "Add a layer to the packet using packet / layer"); 

    nb::class_<pcpp::PcapFileReaderDevice>(m, "Reader", "Device for reading and parsing .pcap files")
        .def("__init__",
            [](pcpp::PcapFileReaderDevice* t, std::string const& pcap_path){
                new (t) pcpp::PcapFileReaderDevice(pcap_path);
                if(!t->open()) {
                    throw std::runtime_error("Failed to open pcap reader device");
                }
            }
        , "pcap_path"_a
        , "Initialize device and open requested pcap file")
        .def("__next__", [](pcpp::PcapFileReaderDevice& iter){
            pcpp::RawPacket* rawPacket = new pcpp::RawPacket();
            if (!iter.getNextPacket(*rawPacket)) {
                delete rawPacket;
                throw nb::stop_iteration("a stop iteration error");
            }
            else {
                return new pcpp::Packet(rawPacket, true);
            }
        }
        , "Get next packet from the pcap file")
        .def("__iter__", [](pcpp::PcapFileReaderDevice* reader){
            return reader;
        }
        , "Get an iterator for the pcap file");

    nb::enum_<LayerType>(m, "LayerType", "Enum for the different network protocol layer types")
        .value("EthLayer", LayerType::kEthLayer, "Ethernet layer")
        .value("IPv4Layer", LayerType::kIPv4Layer, "IPv4 layer")
        .value("IPv6Layer", LayerType::kIPv6Layer, "IPv6 layer")
        .value("TcpLayer", LayerType::kTcpLayer, "TCP layer")
        .value("UdpLayer", LayerType::kUdpLayer, "UDP layer")
        .value("ArpLayer", LayerType::kArpLayer, "ARP layer")
        .value("SomeIpLayer", LayerType::kSomeIpLayer, "SOME/IP layer")
        .value("SomeIpSdLayer", LayerType::kSomeIpSdLayer, "SOME/IP-SD layer")
        .value("DhcpLayer", LayerType::kDhcpLayer, "DHCP layer")
        .value("VlanLayer", LayerType::kVlanLayer, "VLAN layer")
        .value("PayloadLayer", LayerType::kPayloadLayer, "Payload layer")
        .export_values();

    nb::class_<pcpp::Layer>(m, "Layer", "Base class for all network protocol layers")
        .def("__repr__", [](pcpp::Layer const& layer){
            return layer.toString();
        }, "Return a string representation of the layer")
        .def("__bytes__", [](pcpp::Layer const& layer){
            const uint8_t* rawData = layer.getData();
            int rawDataLen = layer.getDataLen();
            return nanobind::bytes(reinterpret_cast<const char*>(rawData), rawDataLen);
        }, "Return the raw bytes of the layer");

    nb::class_<pcpp::EthLayer, pcpp::Layer>(m, "EthLayer", "Ethernet layer implementation")
        .def("__init__",
                [](pcpp::EthLayer* t, std::string const& src_mac_addr, std::string const& dst_mac_addr){
                    auto src_mac = src_mac_addr.size() > 0 ? pcpp::MacAddress(src_mac_addr) : pcpp::MacAddress();
                    auto dst_mac = dst_mac_addr.size() > 0 ? pcpp::MacAddress(dst_mac_addr) : pcpp::MacAddress();
                    new (t) pcpp::EthLayer(src_mac, dst_mac);
                }
        , "src_mac_addr"_a = "", "dst_mac_addr"_a = "", "Create an Ethernet layer with optional source and destination MAC addresses")
        .def_prop_rw("src_mac_addr",
            [](pcpp::EthLayer &t){
                return t.getSourceMac().toString();
            },
            [](pcpp::EthLayer &t, std::string const& addr){
                t.setSourceMac(pcpp::MacAddress(addr));
            },
            "Source MAC address")
        .def_prop_rw("dst_mac_addr",
            [](pcpp::EthLayer &t){
                return t.getDestMac().toString();
            },
            [](pcpp::EthLayer &t, std::string const& addr){
                t.setDestMac(pcpp::MacAddress(addr));
            },
            "Destination MAC address")
        .def_prop_rw("ether_type",
            [](pcpp::EthLayer &t){
                return t.getEthHeader()->etherType;
            },
            [](pcpp::EthLayer &t, bool ipv4){
                t.getEthHeader()->etherType = ipv4 ? 0x0800 :  0x86dd;
            },
            "Ethernet type (0x0800 for IPv4, 0x86dd for IPv6)");

    nb::class_<pcpp::VlanLayer, pcpp::Layer>(m, "VlanLayer", "VLAN layer implementation")
        .def("__init__",
                [](pcpp::VlanLayer* t, const uint16_t vlan_id, bool cfi, uint8_t priority, uint16_t ether_type){
                    new (t) pcpp::VlanLayer(vlan_id, cfi, priority, ether_type);
                }
        , "vlan_id"_a, "cfi"_a, "priority"_a, "ether_type"_a = 0)
        .def_prop_rw("vlan_id",
            [](pcpp::VlanLayer &t){
                return t.getVlanID();
            },
            [](pcpp::VlanLayer &t, uint16_t id){
                t.setVlanID(id);
            }
        )
        .def_prop_rw("cfi",
            [](pcpp::VlanLayer &t){
                return t.getCFI();
            },
            [](pcpp::VlanLayer &t, bool cfi){
                t.setCFI(cfi);
            }
        )
        .def_prop_rw("priority",
            [](pcpp::VlanLayer &t){
                return t.getPriority();
            },
            [](pcpp::VlanLayer &t, uint8_t priority){
                t.setPriority(priority);
            }
        );

    nb::class_<pcpp::IPv4Layer, pcpp::Layer>(m, "IPv4Layer", "IPv4 layer implementation")
        .def(nb::init<const std::string &, const std::string &>(),"src_addr"_a,"dst_addr"_a)
        .def_prop_rw("src_ip",
            // getter
            [](pcpp::IPv4Layer &t){
                return t.getSrcIPv4Address().toString();
            },
            // setter
            [](pcpp::IPv4Layer &t, std::string const& addr){
                t.setSrcIPv4Address(pcpp::IPv4Address(addr));
                t.computeCalculateFields();
            }
        )
        .def_prop_rw("dst_ip",
            // getter
            [](pcpp::IPv4Layer &t){
                return t.getDstIPv4Address().toString();
            },
            // setter
            [](pcpp::IPv4Layer &t, std::string const& addr){
                t.setDstIPv4Address(pcpp::IPv4Address(addr));
                t.computeCalculateFields();
            }
        )
        .def_prop_rw("ttl",
            // getter
            [](pcpp::IPv4Layer &t){
                return t.getIPv4Header()->timeToLive;
            },
            // setter
            [](pcpp::IPv4Layer &t, int ttl){
                t.getIPv4Header()->timeToLive = ttl;
            }
        )
        .def_prop_rw("ip_identification",
            // getter
            [](pcpp::IPv4Layer &t){
                return t.getIPv4Header()->ipId;
            },
            // setter
            [](pcpp::IPv4Layer &t, int ip_identification){
                t.getIPv4Header()->ipId = pcpp::hostToNet16(ip_identification);
            }
        )
        .def("clear_chksum", [](pcpp::IPv4Layer &t){
                auto header = t.getIPv4Header();
                if(header) {
                    header->headerChecksum = 0;
                }
                t.computeCalculateFields();
            }
        );

    nb::class_<pcpp::IPv6Layer, pcpp::Layer>(m, "IPv6Layer", "IPv6 layer implementation")
        .def(nb::init<const std::string &, const std::string &>(),"src_addr"_a,"dst_addr"_a)
        .def_prop_rw("src_ip",
            // getter
            [](pcpp::IPv6Layer &t){
                return t.getSrcIPv6Address().toString();
            },
            // setter
            [](pcpp::IPv6Layer &t, std::string const& addr){
                t.setSrcIPv6Address(pcpp::IPv6Address(addr));
            }
        )
        .def_prop_rw("dst_ip",
            // getter
            [](pcpp::IPv6Layer &t){
                return t.getDstIPv6Address().toString();
            },
            // setter
            [](pcpp::IPv6Layer &t, std::string const& addr){
                t.setDstIPv6Address(pcpp::IPv6Address(addr));
            }
        );
        

    nb::class_<pcpp::TcpLayer, pcpp::Layer>(m, "TcpLayer", "TCP layer implementation")
        .def(nb::init<uint16_t, uint16_t>(),"src_port"_a,"dst_port"_a)
        .def("clear_chksum", [](pcpp::TcpLayer &t){
                auto header = t.getTcpHeader();
                if(header) {
                    header->headerChecksum = 0;
                }
            }
        )
        .def_prop_ro("src_port",
            // getter
            [](pcpp::TcpLayer &t){
                return t.getSrcPort();
            }
        )
        .def_prop_ro("dst_port",
            // getter
            [](pcpp::TcpLayer &t){
                return t.getDstPort();
            }
        )
        .def_prop_rw("syn_flag",
            // getter
            [](pcpp::TcpLayer &t){
                return t.getTcpHeader()->synFlag;
            },
            // setter
            [](pcpp::TcpLayer &t, bool set){
                t.getTcpHeader()->synFlag = set ? 1 : 0;
            }
        )
        .def_prop_rw("ack_flag",
            // getter
            [](pcpp::TcpLayer &t){
                return t.getTcpHeader()->ackFlag;
            },
            // setter
            [](pcpp::TcpLayer &t, bool set){
                t.getTcpHeader()->ackFlag = set ? 1 : 0;
            }
        )
        .def_prop_rw("rst_flag",
            // getter
            [](pcpp::TcpLayer &t){
                return t.getTcpHeader()->rstFlag;
            },
            // setter
            [](pcpp::TcpLayer &t, bool set){
                t.getTcpHeader()->rstFlag = set ? 1 : 0;
            }
        );

    nb::class_<pcpp::UdpLayer, pcpp::Layer>(m, "UdpLayer", "UDP layer implementation")
        .def(nb::init<uint16_t, uint16_t>(),"src_port"_a,"dst_port"_a)
        .def("clear_chksum", [](pcpp::UdpLayer &t){
                auto header = t.getUdpHeader();
                if(header) {
                    header->headerChecksum = 0;
                }
            }
        )
        .def_prop_ro("src_port",
            // getter
            [](pcpp::UdpLayer &t){
                return t.getSrcPort();
            }
        )
        .def_prop_ro("dst_port",
            // getter
            [](pcpp::UdpLayer &t){
                return t.getDstPort();
            }
        );

    // Assuming MacAddress and IPv4Address have default constructors that create an empty address  
    nb::class_<pcpp::MacAddress>(m, "MacAddress")  
        .def(nb::init<>()) // Default constructor  
        .def(nb::init<const std::string &>())  
        .def("toString", &pcpp::MacAddress::toString);  
  
    nb::class_<pcpp::IPv4Address>(m, "IPv4Address")  
        .def(nb::init<>()) // Default constructor  
        .def(nb::init<const std::string &>())  
        .def("toString", &pcpp::IPv4Address::toString);  
    
    nb::enum_<pcpp::ArpOpcode>(m, "ArpOpcode", "ARP operation codes")
        .value("ARP_REQUEST", pcpp::ARP_REQUEST)  
        .value("ARP_REPLY", pcpp::ARP_REPLY)  
        .export_values();

    nb::class_<pcpp::ArpLayer, pcpp::Layer>(m, "ArpLayer", "ARP layer implementation")
        // Constructor with optional string arguments for MAC and IP addresses
        .def("__init__", 
            [](
                pcpp::ArpLayer *t, 
                pcpp::ArpOpcode opcode, 
                std::string const& src_mac_addr, 
                std::string const& src_ip_addr, 
                std::string const& dst_mac_addr, 
                std::string const& dst_ip_addr
            ){
                new (t) pcpp::ArpLayer(
                   opcode,
                   src_mac_addr.empty() ? pcpp::MacAddress() : pcpp::MacAddress(src_mac_addr),
                   src_ip_addr.empty() ? pcpp::IPv4Address() : pcpp::IPv4Address(src_ip_addr),
                   dst_mac_addr.empty() ? pcpp::MacAddress() : pcpp::MacAddress(dst_mac_addr),
                   dst_ip_addr.empty() ? pcpp::IPv4Address() : pcpp::IPv4Address(dst_ip_addr)
                ); 
            }, 
            "opcode"_a, "src_mac_addr"_a = "", "dst_mac_addr"_a = "", "src_ip_addr"_a = "", "dst_ip_addr"_a = ""
        )
        // Read-write property for sender MAC address
        .def_prop_rw("sender_mac_address",
            // Getter
            [](const pcpp::ArpLayer& t) { return t.getSenderMacAddress().toString(); },
            // Setter
            [](pcpp::ArpLayer& t, const std::string& macStr) {
                pcpp::MacAddress(macStr).copyTo(t.getArpHeader()->senderMacAddr);
            })
        // Read-write property for target MAC address
        .def_prop_rw("target_mac_address",
            // Getter
            [](const pcpp::ArpLayer& t) { return t.getTargetMacAddress().toString(); },
            // Setter
            [](pcpp::ArpLayer& t, const std::string& macStr) {
                pcpp::MacAddress(macStr).copyTo(t.getArpHeader()->targetMacAddr);
            })
        // Read-write property for sender IP address
        .def_prop_rw("sender_ip_address",
            // Getter
            [](const pcpp::ArpLayer& t) { return t.getSenderIpAddr().toString(); },
            // Setter
            [](pcpp::ArpLayer& t, const std::string& ipStr) {
                t.getArpHeader()->senderIpAddr = pcpp::IPv4Address(ipStr).toInt();
            })
        // Read-write property for target IP address
        .def_prop_rw("target_ip_address",
            // Getter
            [](const pcpp::ArpLayer& t) { return t.getTargetIpAddr().toString(); },
            // Setter
            [](pcpp::ArpLayer& t, const std::string& ipStr) {
                t.getArpHeader()->targetIpAddr = pcpp::IPv4Address(ipStr).toInt();
            })

        .def("getArpHeader", &pcpp::ArpLayer::getArpHeader)
        .def("getSenderMacAddress", &pcpp::ArpLayer::getSenderMacAddress)
        .def("getTargetMacAddress", &pcpp::ArpLayer::getTargetMacAddress)
        .def("getSenderIpAddr", &pcpp::ArpLayer::getSenderIpAddr)
        .def("getTargetIpAddr", &pcpp::ArpLayer::getTargetIpAddr)
        .def("parseNextLayer", &pcpp::ArpLayer::parseNextLayer)
        .def("getHeaderLen", &pcpp::ArpLayer::getHeaderLen)
        .def("computeCalculateFields", &pcpp::ArpLayer::computeCalculateFields)
        .def("isRequest", &pcpp::ArpLayer::isRequest)
        .def("isReply", &pcpp::ArpLayer::isReply)
        .def("toString", &pcpp::ArpLayer::toString)
        .def("getOsiModelLayer", &pcpp::ArpLayer::getOsiModelLayer);


    nb::class_<pcpp::PayloadLayer, pcpp::Layer>(m, "PayloadLayer", "Payload layer implementation")
        .def("__init__",
                [](pcpp::PayloadLayer* t, nb::bytes const& data){
                        new (t) pcpp::PayloadLayer(static_cast<const uint8_t*>(data.data()), data.size());
                }
                , "data"_a);

    m.def("send_eth_packets", &sendEthPackets, "eth_interface"_a, "packets"_a, "dst_ipv4_addr"_a, "Sends a list of packets over the specified network interface");

    m.def("sniff_eth", &sniffEth, "eth_interface"_a, "timeout"_a, "Sniff over the provided interface and capture packets up to provided timeout");

    nb::enum_<pcpp::SomeIpLayer::MsgType>(m, "SomeIpMsgType", "Enum for the different SOME/IP message types")
        .value("REQUEST", pcpp::SomeIpLayer::MsgType::REQUEST)
		.value("REQUEST_ACK", pcpp::SomeIpLayer::MsgType::REQUEST_ACK)
		.value("REQUEST_NO_RETURN", pcpp::SomeIpLayer::MsgType::REQUEST_NO_RETURN)
		.value("REQUEST_NO_RETURN_ACK", pcpp::SomeIpLayer::MsgType::REQUEST_NO_RETURN_ACK)
		.value("NOTIFICATION", pcpp::SomeIpLayer::MsgType::NOTIFICATION)
		.value("NOTIFICATION_ACK", pcpp::SomeIpLayer::MsgType::NOTIFICATION_ACK)
		.value("RESPONSE", pcpp::SomeIpLayer::MsgType::RESPONSE)
		.value("RESPONSE_ACK", pcpp::SomeIpLayer::MsgType::RESPONSE_ACK)
		.value("ERRORS", pcpp::SomeIpLayer::MsgType::ERRORS)
		.value("ERROR_ACK", pcpp::SomeIpLayer::MsgType::ERROR_ACK)
		.value("TP_REQUEST", pcpp::SomeIpLayer::MsgType::TP_REQUEST)
		.value("TP_REQUEST_NO_RETURN", pcpp::SomeIpLayer::MsgType::TP_REQUEST_NO_RETURN)
		.value("TP_NOTIFICATION", pcpp::SomeIpLayer::MsgType::TP_NOTIFICATION)
		.value("TP_RESPONSE", pcpp::SomeIpLayer::MsgType::TP_RESPONSE)
		.value("TP_ERROR", pcpp::SomeIpLayer::MsgType::TP_ERROR)
        .export_values();

    nb::enum_<pcpp::SomeIpSdEntry::EntryType>(m, "SomeIpSdEntryType", "Types of entries that can occur in SOME/IP-SD")
        .value("FindService", pcpp::SomeIpSdEntry::EntryType::FindService)
		.value("OfferService", pcpp::SomeIpSdEntry::EntryType::OfferService)
		.value("StopOfferService", pcpp::SomeIpSdEntry::EntryType::StopOfferService)
		.value("SubscribeEventgroup", pcpp::SomeIpSdEntry::EntryType::SubscribeEventgroup)
		.value("StopSubscribeEventgroup", pcpp::SomeIpSdEntry::EntryType::StopSubscribeEventgroup)
		.value("SubscribeEventgroupAck", pcpp::SomeIpSdEntry::EntryType::SubscribeEventgroupAck)
		.value("SubscribeEventgroupNack", pcpp::SomeIpSdEntry::EntryType::SubscribeEventgroupNack)
        .export_values();

    nb::enum_<pcpp::SomeIpSdIPv4Option::IPv4OptionType>(m, "SomeIpSdIPv4OptionType", "Types of IPv4 options in SOME/IP-SD")
        .value("IPv4Endpoint", pcpp::SomeIpSdIPv4Option::IPv4OptionType::IPv4Endpoint)
		.value("IPv4Multicast", pcpp::SomeIpSdIPv4Option::IPv4OptionType::IPv4Multicast)
		.value("IPv4SdEndpoint", pcpp::SomeIpSdIPv4Option::IPv4OptionType::IPv4SdEndpoint)
        .export_values();

    nb::enum_<pcpp::SomeIpSdIPv6Option::IPv6OptionType>(m, "SomeIpSdIPv6OptionType", "Types of IPv6 options in SOME/IP-SD")
        .value("IPv6Endpoint", pcpp::SomeIpSdIPv6Option::IPv6OptionType::IPv6Endpoint)
		.value("IPv6Multicast", pcpp::SomeIpSdIPv6Option::IPv6OptionType::IPv6Multicast)
		.value("IPv6SdEndpoint", pcpp::SomeIpSdIPv6Option::IPv6OptionType::IPv6SdEndpoint)
        .export_values();

    nb::enum_<pcpp::SomeIpSdProtocolType>(m, "SomeIpSdProtocolType", "Types of protocols that can be referenced in SOME/IP-SD")
        .value("SD_TCP", pcpp::SomeIpSdProtocolType::SD_TCP)
	    .value("SD_UDP", pcpp::SomeIpSdProtocolType::SD_UDP)
        .export_values();

    nb::enum_<pcpp::SomeIpSdOption::OptionType>(m, "SomeIpSdOptionType", "Types of options available for the SOME/IP-SD protocol")
		.value("Unknown", pcpp::SomeIpSdOption::OptionType::Unknown)
		.value("ConfigurationString", pcpp::SomeIpSdOption::OptionType::ConfigurationString)
		.value("LoadBalancing", pcpp::SomeIpSdOption::OptionType::LoadBalancing)
		.value("IPv4Endpoint", pcpp::SomeIpSdOption::OptionType::IPv4Endpoint)
		.value("IPv6Endpoint", pcpp::SomeIpSdOption::OptionType::IPv6Endpoint)
		.value("IPv4Multicast", pcpp::SomeIpSdOption::OptionType::IPv4Multicast)
		.value("IPv6Multicast", pcpp::SomeIpSdOption::OptionType::IPv6Multicast)
		.value("IPv4SdEndpoint", pcpp::SomeIpSdOption::OptionType::IPv4SdEndpoint)
		.value("IPv6SdEndpoint", pcpp::SomeIpSdOption::OptionType::IPv6SdEndpoint)
        .export_values();


    nb::enum_<pcpp::DhcpMessageType>(m, "DhcpMessageType", "DHCP message types")
		.value("DHCP_UNKNOWN_MSG_TYPE", pcpp::DhcpMessageType::DHCP_UNKNOWN_MSG_TYPE)
		.value("DHCP_DISCOVER", pcpp::DhcpMessageType::DHCP_DISCOVER)
		.value("DHCP_OFFER", pcpp::DhcpMessageType::DHCP_OFFER)
		.value("DHCP_REQUEST", pcpp::DhcpMessageType::DHCP_REQUEST)
		.value("DHCP_DECLINE", pcpp::DhcpMessageType::DHCP_DECLINE)
		.value("DHCP_ACK", pcpp::DhcpMessageType::DHCP_ACK)
		.value("DHCP_NAK", pcpp::DhcpMessageType::DHCP_NAK)
		.value("DHCP_RELEASE", pcpp::DhcpMessageType::DHCP_RELEASE)
		.value("DHCP_INFORM", pcpp::DhcpMessageType::DHCP_INFORM)
        .export_values();

    nb::class_<pcpp::DhcpLayer, pcpp::Layer>(m, "DhcpLayer", "DHCP layer implementation")
        .def("__init__",
                [](pcpp::DhcpLayer* t, pcpp::DhcpMessageType msg_type, std::string const& client_mac_addr){
                    auto client_mac = client_mac_addr.size() > 0 ? pcpp::MacAddress(client_mac_addr) : pcpp::MacAddress();
                    new (t) pcpp::DhcpLayer(msg_type, client_mac);
                }
        , "msg_type"_a = pcpp::DhcpMessageType::DHCP_UNKNOWN_MSG_TYPE, "client_mac_addr"_a = "")
        .def_prop_rw("server_ip",
            [](pcpp::DhcpLayer &t){
                return t.getServerIpAddress().toString();
            },
            [](pcpp::DhcpLayer &t, std::string const& addr){
                t.setServerIpAddress(pcpp::IPv4Address(addr));
            }
        )
        .def_prop_rw("gateway_ip",
            [](pcpp::DhcpLayer &t){
                return t.getGatewayIpAddress().toString();
            },
            [](pcpp::DhcpLayer &t, std::string const& addr){
                t.setGatewayIpAddress(pcpp::IPv4Address(addr));
            }
        )
        .def_prop_rw("client_ip",
            [](pcpp::DhcpLayer &t){
                return t.getClientIpAddress().toString();
            },
            [](pcpp::DhcpLayer &t, std::string const& addr){
                t.setClientIpAddress(pcpp::IPv4Address(addr));
            }
        )
        .def_prop_rw("your_ip",
            [](pcpp::DhcpLayer &t){
                return t.getYourIpAddress().toString();
            },
            [](pcpp::DhcpLayer &t, std::string const& addr){
                t.setYourIpAddress(pcpp::IPv4Address(addr));
            }
        )
        .def_prop_ro("flags",
            [](pcpp::DhcpLayer &t){
                return t.getDhcpHeader()->flags;
            }
        );

    nb::class_<pcpp::SomeIpLayer, pcpp::Layer>(m, "SomeIpLayer", "SOME/IP layer implementation")
        .def("__init__",
            [](pcpp::SomeIpLayer* t, uint16_t serviceID, uint16_t methodID, uint16_t clientID, uint16_t sessionID, uint8_t interfaceVersion,
				pcpp::SomeIpLayer::MsgType type, uint8_t returnCode, nb::bytes const& data){
                    new (t) pcpp::SomeIpLayer(serviceID, methodID, clientID, sessionID, interfaceVersion,
				            type, returnCode, static_cast<const uint8_t*>(data.data()), data.size());
            }
        , "service_id"_a=0, "method_id"_a=0, "client_id"_a=0, "session_id"_a=0, "interface_version"_a=0, "msg_type"_a=pcpp::SomeIpLayer::MsgType(), "return_code"_a=0, "payload"_a=nb::bytes(""))
        .def_static("from_bytes",
            [](nb::bytes const& data) -> pcpp::SomeIpLayer* {
                auto mem = new uint8_t[data.size()];
                std::memcpy(mem, data.data(), data.size());
                return dynamic_cast<pcpp::SomeIpLayer*>(pcpp::SomeIpLayer::parseSomeIpLayer(mem, data.size(), nullptr, nullptr));
            }
        , "raw_data"_a)
        .def_prop_rw("service_id",
            // getter
            [](pcpp::SomeIpLayer &t){
                return t.getServiceID();
            },
            // setter
            [](pcpp::SomeIpLayer &t, uint16_t serviceId){
                t.setServiceID(serviceId);
            }
        )
        .def_prop_rw("method_id",
            // getter
            [](pcpp::SomeIpLayer &t){
                return t.getMethodID();
            },
            // setter
            [](pcpp::SomeIpLayer &t, uint16_t method_id){
                t.setMethodID(method_id);
            })
        .def_prop_rw("client_id",
            // getter
            [](pcpp::SomeIpLayer &t){
                return t.getClientID();
            },
            // setter
            [](pcpp::SomeIpLayer &t, uint16_t client_id){
                t.setClientID(client_id);
            })
        .def_prop_rw("session_id",
            // getter
            [](pcpp::SomeIpLayer &t){
                return t.getSessionID();
            },
            // setter
            [](pcpp::SomeIpLayer &t, uint16_t session_id){
                t.setSessionID(session_id);
            })
        .def_prop_rw("interface_version",
            // getter
            [](pcpp::SomeIpLayer &t){
                return t.getInterfaceVersion();
            },
            // setter
            [](pcpp::SomeIpLayer &t, uint8_t interface_version){
                t.setInterfaceVersion(interface_version);
            })
        .def_prop_rw("message_type",
            // getter
            [](pcpp::SomeIpLayer &t){
                return t.getMessageType();
            },
            // setter
            [](pcpp::SomeIpLayer &t, pcpp::SomeIpLayer::MsgType message_type){
                t.setMessageType(message_type);
            })
        .def_prop_rw("return_code",
            // getter
            [](pcpp::SomeIpLayer &t){
                return t.getReturnCode();
            },
            // setter
            [](pcpp::SomeIpLayer &t, uint8_t return_code){
                t.setReturnCode(return_code);
            })
        .def_prop_rw("protocol_version",
            // getter
            [](pcpp::SomeIpLayer &t){
                return t.getProtocolVersion();
            },
            // setter
            [](pcpp::SomeIpLayer &t, uint8_t protocol_version){
                t.setProtocolVersion(protocol_version);
            })
        .def_prop_ro("payload",
            // getter
            [](pcpp::SomeIpLayer &t){
                return nb::bytes(t.getPduPayload(), t.getPduPayloadSize());
            });
            
    nb::class_<pcpp::SomeIpSdLayer, pcpp::SomeIpLayer>(m, "SomeIpSdLayer", "SOME/IP-SD layer implementation")
        .def(nb::init<uint16_t, uint16_t, uint16_t, uint16_t, uint8_t, pcpp::SomeIpLayer::MsgType, uint8_t, uint8_t>()
        , "service_id"_a=0xFFFF, "method_id"_a=0x8100, "client_id"_a=0x0000, "session_id"_a=0x0001, "interface_version"_a=0x01, "msg_type"_a=pcpp::SomeIpLayer::MsgType::NOTIFICATION, "return_code"_a=0x00, "flags"_a=0x80)
        .def_static("from_bytes",
            [](nb::bytes const& data) -> pcpp::SomeIpSdLayer* {
                auto mem = new uint8_t[data.size()];
                std::memcpy(mem, data.data(), data.size());
                return dynamic_cast<pcpp::SomeIpSdLayer*>(pcpp::SomeIpLayer::parseSomeIpLayer(mem, data.size(), nullptr, nullptr));
            }
        , "raw_data"_a)
        .def_prop_rw("flags",
            // getter
            [](pcpp::SomeIpSdLayer &t){
                return t.getFlags();
            },
            // setter
            [](pcpp::SomeIpSdLayer &t, uint8_t flags){
                t.setFlags(flags);
            })
        .def("add_entry",
            [](pcpp::SomeIpSdLayer &t, pcpp::SomeIpSdEntry const& entry) -> uint32_t {
                return t.addEntry(entry);
            }, "entry"_a)
        .def("add_option_to",
            [](pcpp::SomeIpSdLayer &t, uint32_t index, pcpp::SomeIpSdOption const& option) -> bool {
                return t.addOptionTo(index, option);
            }, "index"_a, "option"_a)
        .def("get_entries",
            [](pcpp::SomeIpSdLayer &t) -> std::vector<pcpp::SomeIpSdEntry*> {
                return t.getEntries();
            })
        .def("get_options",
            [](pcpp::SomeIpSdLayer &t) -> std::vector<pcpp::SomeIpSdOption*> {
                return t.getOptions();
            });

    nb::class_<pcpp::SomeIpSdEntry>(m, "SomeIpSdEntry")
        .def(nb::init<pcpp::SomeIpSdEntry::EntryType, uint16_t, uint16_t, uint8_t, uint32_t, uint32_t>()
        , "entry_type"_a, "service_id"_a, "instance_id"_a, "major_version"_a, "ttl"_a, "minor_version"_a
        , "Construct a new SOME/IP-SD Service Entry Type")
        .def(nb::init<pcpp::SomeIpSdEntry::EntryType, uint16_t, uint16_t, uint8_t, uint32_t, uint8_t, uint16_t>()
        , "entry_type"_a, "service_id"_a, "instance_id"_a, "major_version"_a, "ttl"_a, "counter"_a, "event_group_id"_a
        , "Construct a new SOME/IP-SD Service Entry Type")
        .def_prop_rw("service_id",
            // getter
            [](pcpp::SomeIpSdEntry &t){
                return t.getServiceId();
            },
            // setter
            [](pcpp::SomeIpSdEntry &t, uint16_t service_id){
                t.setServiceId(service_id);
            })
        .def_prop_rw("instance_id",
            // getter
            [](pcpp::SomeIpSdEntry &t){
                return t.getInstanceId();
            },
            // setter
            [](pcpp::SomeIpSdEntry &t, uint16_t instance_id){
                t.setInstanceId(instance_id);
            })
        .def_prop_rw("major_version",
            // getter
            [](pcpp::SomeIpSdEntry &t){
                return t.getMajorVersion();
            },
            // setter
            [](pcpp::SomeIpSdEntry &t, uint8_t major_version){
                t.setMajorVersion(major_version);
            })
        .def_prop_rw("minor_version",
            // getter
            [](pcpp::SomeIpSdEntry &t){
                return t.getMinorVersion();
            },
            // setter
            [](pcpp::SomeIpSdEntry &t, uint8_t minor_version){
                t.setMinorVersion(minor_version);
            })
        .def_prop_rw("ttl",
            // getter
            [](pcpp::SomeIpSdEntry &t){
                return t.getTtl();
            },
            // setter
            [](pcpp::SomeIpSdEntry &t, uint32_t ttl){
                t.setTtl(ttl);
            })
        .def_prop_rw("counter",
            // getter
            [](pcpp::SomeIpSdEntry &t){
                return t.getCounter();
            },
            // setter
            [](pcpp::SomeIpSdEntry &t, uint8_t counter){
                t.setCounter(counter);
            })
        .def_prop_rw("event_group_id",
            // getter
            [](pcpp::SomeIpSdEntry &t){
                return t.getEventgroupId();
            },
            // setter
            [](pcpp::SomeIpSdEntry &t, uint8_t EventgroupId){
                t.setEventgroupId(EventgroupId);
            })
        .def_prop_ro("type",
            // getter
            [](pcpp::SomeIpSdEntry &t) -> pcpp::SomeIpSdEntry::EntryType {
                return t.getType();
            })
        .def_prop_ro("index_1",
            // getter
            [](pcpp::SomeIpSdEntry &t) -> uint8_t {
                auto header = t.getSomeIpSdEntryHeader();
                return header->indexFirstOption;
            })
        .def_prop_ro("index_2",
            // getter
            [](pcpp::SomeIpSdEntry &t) -> uint8_t {
                auto header = t.getSomeIpSdEntryHeader();
                return header->indexSecondOption;
            })
        .def_prop_ro("n_opt_1",
            // getter
            [](pcpp::SomeIpSdEntry &t) -> uint8_t {
                auto header = t.getSomeIpSdEntryHeader();
                return header->nrOpt1;
            })
        .def_prop_ro("n_opt_2",
            // getter
            [](pcpp::SomeIpSdEntry &t) -> uint8_t {
                auto header = t.getSomeIpSdEntryHeader();
                return header->nrOpt2;
            });

    nb::class_<pcpp::SomeIpSdOption>(m, "SomeIpSdOption")
        .def_prop_ro("type",
            // getter
            [](pcpp::SomeIpSdOption &t) -> pcpp::SomeIpSdOption::OptionType {
                return t.getType();
            });

    nb::class_<pcpp::SomeIpSdIPv4Option, pcpp::SomeIpSdOption>(m, "SomeIpSdIPv4Option")
        .def("__init__",
            [](pcpp::SomeIpSdIPv4Option* t, pcpp::SomeIpSdIPv4Option::IPv4OptionType type, std::string const& ipAddress, uint16_t port, pcpp::SomeIpSdProtocolType l4Protocol){
                    new (t) pcpp::SomeIpSdIPv4Option(type, pcpp::IPv4Address(ipAddress), port, l4Protocol);
            }
            , "option_type"_a, "ipv4_addr"_a, "port"_a, "protocol_type"_a)
        .def_prop_ro("addr",
            // getter
            [](pcpp::SomeIpSdIPv4Option &t) -> std::string {
                return t.getIpAddress().toString();
            })
        .def_prop_ro("port",
            // getter
            [](pcpp::SomeIpSdIPv4Option &t) -> uint16_t {
                return t.getPort();
            })
        .def_prop_ro("protocol_type",
            // getter
            [](pcpp::SomeIpSdIPv4Option &t) -> pcpp::SomeIpSdProtocolType {
                return t.getProtocol();
            });


    nb::class_<pcpp::SomeIpSdIPv6Option, pcpp::SomeIpSdOption>(m, "SomeIpSdIPv6Option")
        .def("__init__",
            [](pcpp::SomeIpSdIPv6Option* t, pcpp::SomeIpSdIPv6Option::IPv6OptionType type, std::string const& ipAddress, uint16_t port, pcpp::SomeIpSdProtocolType l6Protocol){
                    new (t) pcpp::SomeIpSdIPv6Option(type, pcpp::IPv6Address(ipAddress), port, l6Protocol);
            }
            , "option_type"_a, "ipv6_addr"_a, "port"_a, "protocol_type"_a)
        .def_prop_ro("addr",
            // getter
            [](pcpp::SomeIpSdIPv6Option &t) -> std::string {
                return t.getIpAddress().toString();
            })
        .def_prop_ro("port",
            // getter
            [](pcpp::SomeIpSdIPv6Option &t) -> uint16_t {
                return t.getPort();
            })
        .def_prop_ro("protocol_type",
            // getter
            [](pcpp::SomeIpSdIPv6Option &t) -> pcpp::SomeIpSdProtocolType {
                return t.getProtocol();
            });


    nb::class_<WrappedRawSocketDevice>(m, "RawSocket", "Raw socket device for sending and receiving packets")
        .def("__init__",
                [](WrappedRawSocketDevice* t, std::string const& if_name){
                    new (t) WrappedRawSocketDevice(if_name);
                }
                , "if_name"_a)
        .def("send_packet",
            [](WrappedRawSocketDevice &raw_socket, pcpp::Packet const& packet) -> bool {
                return raw_socket.sendPacket(packet);
            }
            , "packet"_a)
        .def("receive_packet",
            [](WrappedRawSocketDevice &raw_socket, bool blocking, double timeout) -> pcpp::Packet* {
                return raw_socket.receivePacket(blocking, timeout);
            }
            , "blocking"_a = true, "timeout"_a = -1)
        .def("sniff",
            [](WrappedRawSocketDevice &raw_socket, double timeout) -> std::vector<pcpp::Packet> {
                return raw_socket.sniff(timeout);
            }
            , "timeout"_a = 1)
        .def("send_packets",
            [](WrappedRawSocketDevice &raw_socket, std::vector<pcpp::Packet>const& packets) -> int {
                return raw_socket.sendPackets(packets);
            }
            , "packets"_a
            , "Sends a list of packets over the specified network interface");
}