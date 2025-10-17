#include <Packet.h>
#include <PcapFileDevice.h>
#include <EthLayer.h>
#include <VlanLayer.h>
#include <TcpLayer.h>
#include <UdpLayer.h>
#include <IPv4Layer.h>
#include <IPv6Layer.h>
#include <ArpLayer.h>
#include <SomeIpLayer.h>
#include <SomeIpSdLayer.h>
#include <PayloadLayer.h>
#include <MacAddress.h>
#include <IpAddress.h>
#include <RawSocketDevice.h>
#include <DhcpLayer.h>
#include <PcapLiveDevice.h>
#include "SystemUtils.h"

#include <nanobind/nanobind.h>

enum class LayerType : uint8_t
{
    kTcpLayer = pcpp::TCP,
    kUdpLayer = pcpp::UDP,
    kEthLayer = pcpp::Ethernet,
    kIPv4Layer = pcpp::IPv4,
    kIPv6Layer = pcpp::IPv6,
    kArpLayer = pcpp::ARP,
    kSomeIpLayer = pcpp::SomeIP,
    kSomeIpSdLayer = pcpp::SomeIP,
    kDhcpLayer = pcpp::DHCP,
    kVlanLayer = pcpp::VLAN,
    kPayloadLayer = pcpp::GenericPayload
};

int 
sendEthPackets(std::string const& ethInterface, std::vector<pcpp::Packet*> const& packets, std::string const& destAddr);

std::vector<pcpp::Packet>
sniffEth(std::string const& ethInterface, double timeoutSeconds);

class WrappedRawSocketDevice
{
    public:
        WrappedRawSocketDevice(std::string const& ifName);
        ~WrappedRawSocketDevice();

        std::vector<pcpp::Packet> sniff(double timeoutSeconds);        
        pcpp::Packet* receivePacket(bool blocking, double timeoutSeconds);
        bool sendPacket(pcpp::Packet const& packet);
        int sendPackets(std::vector<pcpp::Packet> const& packets);

    private:
        std::shared_ptr<pcpp::RawSocketDevice> m_rawSocket;
        pcpp::PcapLiveDevice* m_pcapDevice;
};