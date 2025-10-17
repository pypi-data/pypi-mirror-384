#include "wrapperClasses.hpp"

#include <arpa/inet.h>
#include <net/if.h>
#include <ifaddrs.h>
#include <algorithm>
#include <array>
#include <chrono>
#include <condition_variable>
#include <iostream>
#include <mutex>
#include <PcapFilter.h>
#include <RawPacket.h>
#include <PcapLiveDevice.h>
#include <PcapLiveDeviceList.h>
#include <NetworkUtils.h>
#include <NdpLayer.h>
#include <nanobind/nanobind.h>

pcpp::MacAddress
getMacAddressViaNdp(pcpp::MacAddress const& srcMac, pcpp::IPv6Address const& dstIp, pcpp::PcapLiveDevice* dev, double timeoutSeconds)
{
    if (dev == nullptr || dstIp == pcpp::IPv6Address::Zero) {
        return pcpp::MacAddress::Zero;
    }

    if (!dev->isOpened()) {
        if (!dev->open()) {
            return pcpp::MacAddress::Zero;
        }
    }

    pcpp::MacAddress sourceMac = srcMac;
    if (sourceMac == pcpp::MacAddress::Zero) {
        sourceMac = dev->getMacAddress();
    }

    if (sourceMac == pcpp::MacAddress::Zero) {
        return pcpp::MacAddress::Zero;
    }

    pcpp::IPv6Address sourceIp = dev->getIPv6Address();
    if (sourceIp == pcpp::IPv6Address::Zero) {
        return pcpp::MacAddress::Zero;
    }

    std::array<uint8_t, 16> solicitedNodeBytes{};
    solicitedNodeBytes[0] = 0xff;
    solicitedNodeBytes[1] = 0x02;
    solicitedNodeBytes[11] = 0x01;
    solicitedNodeBytes[12] = 0xff;

    auto targetBytes = dstIp.toByteArray();
    solicitedNodeBytes[13] = targetBytes[13];
    solicitedNodeBytes[14] = targetBytes[14];
    solicitedNodeBytes[15] = targetBytes[15];

    pcpp::IPv6Address solicitedNodeAddr(solicitedNodeBytes);
    pcpp::MacAddress multicastMac(0x33, 0x33, 0xff, targetBytes[13], targetBytes[14], targetBytes[15]);

    pcpp::Packet solicitationPacket(128);
    pcpp::EthLayer ethLayer(sourceMac, multicastMac, PCPP_ETHERTYPE_IPV6);
    pcpp::IPv6Layer ipv6Layer(sourceIp, solicitedNodeAddr);
    ipv6Layer.getIPv6Header()->hopLimit = 255;
    pcpp::NDPNeighborSolicitationLayer ndpLayer(0, dstIp, sourceMac);

    if (!solicitationPacket.addLayer(&ethLayer) || !solicitationPacket.addLayer(&ipv6Layer) ||
        !solicitationPacket.addLayer(&ndpLayer)) {
        return pcpp::MacAddress::Zero;
    }

    solicitationPacket.computeCalculateFields();

    bool filterApplied = false;
    pcpp::BPFStringFilter ndpFilter("icmp6 && ip6[40] == 136");
    if (dev->setFilter(ndpFilter)) {
        filterApplied = true;
    }

    struct CaptureContext
    {
        std::mutex mutex;
        std::condition_variable cond;
        pcpp::IPv6Address targetIp = pcpp::IPv6Address::Zero;
        pcpp::MacAddress resolvedMac = pcpp::MacAddress::Zero;
        bool resolved = false;
    } context;

    context.targetIp = dstIp;

    auto onPacket = [](pcpp::RawPacket* rawPacket, pcpp::PcapLiveDevice*, void* userCookie) {
        if (userCookie == nullptr) {
            return;
        }

        auto* ctx = static_cast<CaptureContext*>(userCookie);

        pcpp::Packet packet(rawPacket);
        auto ndpAdv = packet.getLayerOfType<pcpp::NDPNeighborAdvertisementLayer>();
        if (ndpAdv == nullptr) {
            return;
        }

        if (ndpAdv->getTargetIP() != ctx->targetIp) {
            return;
        }

        pcpp::MacAddress mac = pcpp::MacAddress::Zero;
        if (ndpAdv->hasTargetMacInfo()) {
            mac = ndpAdv->getTargetMac();
        }

        if (mac == pcpp::MacAddress::Zero) {
            if (auto ethLayer = packet.getLayerOfType<pcpp::EthLayer>(); ethLayer != nullptr) {
                mac = ethLayer->getSourceMac();
            }
        }

        if (mac == pcpp::MacAddress::Zero) {
            return;
        }

        {
            std::lock_guard<std::mutex> lock(ctx->mutex);
            if (ctx->resolved) {
                return;
            }

            ctx->resolvedMac = mac;
            ctx->resolved = true;
        }

        ctx->cond.notify_one();
    };

    if (!dev->startCapture(onPacket, &context)) {
        if (filterApplied) {
            dev->clearFilter();
        }
        return pcpp::MacAddress::Zero;
    }

    pcpp::MacAddress result = pcpp::MacAddress::Zero;
    double effectiveTimeout = timeoutSeconds > 0.0 ? timeoutSeconds : 5.0;

    if (dev->sendPacket(&solicitationPacket)) {
        std::unique_lock<std::mutex> lock(context.mutex);
        bool notified = context.cond.wait_for(lock, std::chrono::duration<double>(effectiveTimeout), [&context]() {
            return context.resolved;
        });
        if (notified && context.resolved) {
            result = context.resolvedMac;
        }
    }

    dev->stopCapture();

    if (filterApplied) {
        dev->clearFilter();
    }

    return result;
}

bool 
replaceLinkLayerWithFreshEthLayer(pcpp::Packet* packet, pcpp::MacAddress const& srcMac, pcpp::MacAddress const& dstMac)
{
    // replace first layer with clean Eth layer
    if(!packet->removeFirstLayer()) return false;

    uint16_t etherType = PCPP_ETHERTYPE_IP;
    if (packet->isPacketOfType(pcpp::IPv6)) {
        etherType = PCPP_ETHERTYPE_IPV6;
    }

    if(!packet->insertLayer(nullptr, new pcpp::EthLayer(srcMac, dstMac, etherType), true)) return false;

    packet->computeCalculateFields();
    return true;
}

int sendEthPackets(std::string const& ethInterface, std::vector<pcpp::Packet*>const& packets, std::string const& destAddr)
{
    pcpp::PcapLiveDevice* dev = pcpp::PcapLiveDeviceList::getInstance().getDeviceByName(ethInterface);
    if (!dev) {
        return 0;
    }

    if (!dev->open()) {
        return 0;
    }

    pcpp::MacAddress dstMac;
    if (pcpp::IPv4Address::isValidIPv4Address(destAddr)) {
        pcpp::IPv4Address destIp(destAddr);
        // send an ARP request to determine dst MAC address
        double arpResTO = 0;
        dstMac = pcpp::NetworkUtils::getInstance().getMacAddress(destIp, dev, arpResTO);
    }
    else if (pcpp::IPv6Address::isValidIPv6Address(destAddr)) {
        pcpp::IPv6Address destIp(destAddr);

        if (destIp.isMulticast()) {
            auto targetBytes = destIp.toByteArray();
            dstMac = pcpp::MacAddress(0x33, 0x33, targetBytes[12], targetBytes[13], targetBytes[14], targetBytes[15]);
        }
        else {
            dstMac = getMacAddressViaNdp(pcpp::MacAddress::Zero, destIp, dev, 5.0);
        }
    }
    auto srcMac = dev->getMacAddress();

    int packetSent = 0;
    for (auto packet : packets) {
        if (replaceLinkLayerWithFreshEthLayer(packet, srcMac, dstMac)) {
            packetSent += dev->sendPacket(packet) ? 1 : 0;
        }
    }

    dev->close();
    return packetSent;
}


std::vector<pcpp::Packet>
sniffEth(std::string const& ethInterface, double timeoutSeconds)
{
    pcpp::PcapLiveDevice* dev = pcpp::PcapLiveDeviceList::getInstance().getDeviceByName(ethInterface);
    if (!dev) {
        nanobind::raise("Invalid interface provided");
    }

    if (!dev->open()) {
        nanobind::raise("Error opening pcap live device");
    }

    std::vector<pcpp::Packet> retPackets;
    pcpp::OnPacketArrivesStopBlocking cb = [&retPackets](pcpp::RawPacket* inPacket, pcpp::PcapLiveDevice* device, void*)->bool {
        retPackets.push_back(pcpp::Packet(inPacket));
        return false;
    };

    if (0 == dev->startCaptureBlockingMode(cb, nullptr, timeoutSeconds)) {
        dev->close();
        nanobind::raise("Error while capturing from device");
    }
    dev->close();
    return retPackets;
}

pcpp::IPAddress
getDefaultGateway(std::string const& ifName)
{
    // find interface name and index from IP address
	struct ifaddrs* addrs;
	getifaddrs(&addrs);
    pcpp::IPAddress ret_addr;
	for (struct ifaddrs* curAddr = addrs; curAddr != NULL; curAddr = curAddr->ifa_next)
	{
		if (curAddr->ifa_addr && (curAddr->ifa_flags & IFF_UP) && std::string(curAddr->ifa_name) == ifName)
		{
			if  (curAddr->ifa_addr->sa_family == AF_INET)
			{
				struct sockaddr_in* sockAddr = (struct sockaddr_in*)(curAddr->ifa_addr);
				char addrAsCharArr[32];
				inet_ntop(curAddr->ifa_addr->sa_family, (void *)&(sockAddr->sin_addr), addrAsCharArr, sizeof(addrAsCharArr));
				ret_addr = pcpp::IPAddress(addrAsCharArr);
			}
			else if (curAddr->ifa_addr->sa_family == AF_INET6)
			{
				struct sockaddr_in6* sockAddr = (struct sockaddr_in6*)(curAddr->ifa_addr);
				char addrAsCharArr[40];
				inet_ntop(curAddr->ifa_addr->sa_family, (void *)&(sockAddr->sin6_addr), addrAsCharArr, sizeof(addrAsCharArr));
				ret_addr = pcpp::IPAddress(addrAsCharArr);
			}
		}
	}
    freeifaddrs(addrs);
    if (ret_addr.isZero()) {
        nanobind::raise("Failed to find default gateway");
    }
    return ret_addr;
}

WrappedRawSocketDevice::WrappedRawSocketDevice(std::string const& ifName)
: m_rawSocket(nullptr)
, m_pcapDevice(nullptr)
{
    auto addr = getDefaultGateway(ifName);
    m_rawSocket = std::make_shared<pcpp::RawSocketDevice>(addr);
    if(!m_rawSocket->open()) {
        nanobind::raise("Failed to open Raw socket device with the provided interface ip");
    }
    m_pcapDevice = pcpp::PcapLiveDeviceList::getInstance().getDeviceByName(ifName);
    if (!m_pcapDevice) {
        nanobind::raise("Invalid interface provided");
    }

    if (!m_pcapDevice->open()) {
        nanobind::raise("Error opening pcap live device");
    }
}

WrappedRawSocketDevice::~WrappedRawSocketDevice()
{
    m_rawSocket->close();
    m_pcapDevice->close();
}

std::vector<pcpp::Packet> 
WrappedRawSocketDevice::sniff(double timeoutSeconds)
{
    std::vector<pcpp::Packet> retPackets;
    pcpp::OnPacketArrivesStopBlocking cb = [&retPackets](pcpp::RawPacket* inPacket, pcpp::PcapLiveDevice* device, void*)->bool {
        retPackets.push_back(pcpp::Packet(inPacket));
        return false;
    };

    if (0 == m_pcapDevice->startCaptureBlockingMode(cb, nullptr, timeoutSeconds)) {
        nanobind::raise("Error while capturing from device");
    }
    return retPackets;
}

pcpp::Packet*
WrappedRawSocketDevice::receivePacket(bool blocking, double timeoutSeconds)
{
    auto rawPacket = new pcpp::RawPacket();
    auto res = m_rawSocket->receivePacket(*rawPacket, blocking, timeoutSeconds);
    if (res == pcpp::RawSocketDevice::RecvPacketResult::RecvSuccess) {
        return new pcpp::Packet(rawPacket, true);
    }
    else {
        delete rawPacket;
        return nullptr;
    }
}

bool 
WrappedRawSocketDevice::sendPacket(pcpp::Packet const& packet)
{
    return m_rawSocket->sendPacket(packet.getRawPacket());
}   

int
WrappedRawSocketDevice::sendPackets(std::vector<pcpp::Packet>const& packets)
{
    int packetSent = 0;
    for (auto packet : packets) {
        packetSent += sendPacket(packet) ? 1 : 0;
    }
    return packetSent;
}