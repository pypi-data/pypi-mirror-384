import unittest

import py_pcapplusplus as pcap


class TestPcapplusplusExt(unittest.TestCase):
    def test_macaddress_str_roundtrip(self):
        mac = pcap.MacAddress("aa:bb:cc:dd:ee:ff")
        self.assertEqual(mac.toString(), "aa:bb:cc:dd:ee:ff")

    def test_ipv4address_str_roundtrip(self):
        ip = pcap.IPv4Address("1.2.3.4")
        self.assertEqual(ip.toString(), "1.2.3.4")

    def test_ethlayer_properties(self):
        eth = pcap.EthLayer("00:11:22:33:44:55", "aa:bb:cc:dd:ee:ff")
        self.assertEqual(eth.src_mac_addr, "00:11:22:33:44:55")
        eth.src_mac_addr = "ff:ff:ff:ff:ff:ff"
        self.assertEqual(eth.src_mac_addr, "ff:ff:ff:ff:ff:ff")
        self.assertEqual(eth.dst_mac_addr, "aa:bb:cc:dd:ee:ff")

        eth.ether_type = False
        self.assertEqual(eth.ether_type, 0x86DD)
        eth.ether_type = True
        self.assertEqual(eth.ether_type, 0x0800)

    def test_ipv4layer_properties(self):
        ip = pcap.IPv4Layer("10.0.0.1", "192.168.1.1")
        self.assertEqual(ip.src_ip, "10.0.0.1")
        self.assertEqual(ip.dst_ip, "192.168.1.1")
        ip.ttl = 42
        self.assertEqual(ip.ttl, 42)
        ip.ip_identification = 12345
        ip.clear_chksum()

    def test_ipv6layer_properties(self):
        ip6 = pcap.IPv6Layer("1234::1", "5678::2")
        self.assertTrue(ip6.src_ip.startswith("1234"))
        ip6.src_ip = "::3"
        self.assertEqual(ip6.src_ip, "::3")

    def test_tcplayer_properties_flags(self):
        tcp = pcap.TcpLayer(1234, 80)
        self.assertEqual(tcp.src_port, 1234)
        self.assertEqual(tcp.dst_port, 80)
        for flag in ("syn_flag", "ack_flag", "rst_flag"):
            setattr(tcp, flag, True)
            self.assertTrue(getattr(tcp, flag))
            setattr(tcp, flag, False)
            self.assertFalse(getattr(tcp, flag))
        tcp.clear_chksum()

    def test_udplayer_properties(self):
        udp = pcap.UdpLayer(111, 222)
        self.assertEqual(udp.src_port, 111)
        self.assertEqual(udp.dst_port, 222)
        udp.clear_chksum()

    def test_vlanlayer_properties(self):
        vlan = pcap.VlanLayer(666, True, 7, 0x8100)
        self.assertEqual(vlan.vlan_id, 666)
        vlan.vlan_id = 42
        self.assertEqual(vlan.vlan_id, 42)
        vlan.cfi = False
        self.assertFalse(vlan.cfi)
        vlan.priority = 5
        self.assertEqual(vlan.priority, 5)

    def test_arplayer_properties(self):
        arp = pcap.ArpLayer(
            pcap.ArpOpcode.ARP_REQUEST,
            "aa:bb:cc:dd:ee:ff",
            "1.2.3.4",
            "11:22:33:44:55:66",
            "4.3.2.1",
        )
        self.assertEqual(arp.sender_mac_address, "aa:bb:cc:dd:ee:ff")
        self.assertEqual(arp.target_mac_address, "11:22:33:44:55:66")
        self.assertEqual(arp.sender_ip_address, "1.2.3.4")
        self.assertEqual(arp.target_ip_address, "4.3.2.1")
        arp.sender_mac_address = "ff:ee:dd:cc:bb:aa"
        self.assertEqual(arp.sender_mac_address, "ff:ee:dd:cc:bb:aa")
        arp.sender_ip_address = "8.8.8.8"
        self.assertEqual(arp.sender_ip_address, "8.8.8.8")
        self.assertIsInstance(arp.getHeaderLen(), int)
        arp.computeCalculateFields()
        self.assertTrue(hasattr(arp, "isRequest"))
        self.assertTrue(hasattr(arp, "isReply"))

    def test_payloadlayer_bytes(self):
        data = b"payload"
        payload = pcap.PayloadLayer(data)
        self.assertEqual(bytes(payload), data)

    def test_packet_add_and_repr(self):
        pkt = pcap.Packet()
        eth = pcap.EthLayer()
        pkt.add_layer(eth)
        self.assertIn("Ethernet", repr(pkt))
        bval = bytes(pkt)
        self.assertIsInstance(bval, bytes)
        ipv4 = pcap.IPv4Layer("1.1.1.1", "2.2.2.2")
        pkt.insert_layer(eth, ipv4)
        self.assertIsNotNone(pkt.get_layer(pcap.LayerType.EthLayer))
        self.assertIsNotNone(pkt[pcap.LayerType.IPv4Layer])
        pkt2 = pkt / pcap.PayloadLayer(b"abc")
        self.assertIsInstance(pkt2, pcap.Packet)

    def test_someiplayer_properties(self):
        someip = pcap.SomeIpLayer(
            0x1234, 0x0101, 0x0001, 0x0002, 1, pcap.SomeIpMsgType.REQUEST, 0, b"abc"
        )
        self.assertEqual(someip.service_id, 0x1234)
        someip.service_id = 123
        self.assertEqual(someip.service_id, 123)
        someip.method_id = 9
        someip.client_id = 77
        someip.session_id = 8
        someip.interface_version = 2
        someip.message_type = pcap.SomeIpMsgType.RESPONSE
        someip.return_code = 1
        someip.protocol_version = 1
        self.assertEqual(someip.payload, b"abc")
        s2 = pcap.SomeIpLayer.from_bytes(bytes(someip))
        self.assertIsInstance(s2, pcap.SomeIpLayer)

    def test_someipsdlayer_add_entry_and_option(self):
        sd = pcap.SomeIpSdLayer()
        entry = pcap.SomeIpSdEntry(pcap.SomeIpSdEntryType.FindService, 100, 2, 1, 10, 1)
        idx = sd.add_entry(entry)
        self.assertIsInstance(idx, int)
        opt = pcap.SomeIpSdIPv4Option(
            pcap.SomeIpSdIPv4OptionType.IPv4Endpoint,
            "8.8.8.8",
            665,
            pcap.SomeIpSdProtocolType.SD_TCP,
        )
        self.assertTrue(sd.add_option_to(idx, opt))
        entries = sd.get_entries()
        self.assertTrue(all(isinstance(e, pcap.SomeIpSdEntry) for e in entries))
        options = sd.get_options()
        self.assertTrue(all(isinstance(o, pcap.SomeIpSdOption) for o in options))

    def test_someipsd_ipv4_option_properties(self):
        ipv4opt = pcap.SomeIpSdIPv4Option(
            pcap.SomeIpSdIPv4OptionType.IPv4Endpoint,
            "192.168.1.1",
            12345,
            pcap.SomeIpSdProtocolType.SD_TCP,
        )
        self.assertEqual(ipv4opt.addr, "192.168.1.1")
        self.assertEqual(ipv4opt.port, 12345)
        self.assertEqual(ipv4opt.protocol_type, pcap.SomeIpSdProtocolType.SD_TCP)

    def test_dhcplayer_properties(self):
        d = pcap.DhcpLayer(pcap.DhcpMessageType.DHCP_DISCOVER, "01:02:03:04:05:06")
        d.server_ip = "10.1.1.1"
        self.assertEqual(d.server_ip, "10.1.1.1")
        d.gateway_ip = "10.1.1.2"
        d.client_ip = "10.1.1.3"
        d.your_ip = "10.1.1.4"
        self.assertIsInstance(d.flags, int)
        
    def test_packet_chaining_truediv(self):  
        pkt = pcap.Packet()  
        eth_layer = pcap.EthLayer("00:11:22:33:44:55", "aa:bb:cc:dd:ee:ff")  
        ip_layer = pcap.IPv4Layer("1.2.3.4", "5.6.7.8")  
        tcp_layer = pcap.TcpLayer(1000, 80)  
        payload_layer = pcap.PayloadLayer(b"foobar")  
        pkt = pkt / eth_layer / ip_layer / tcp_layer / payload_layer
    
        # Top-level should still be a Packet  
        self.assertIsInstance(pkt, pcap.Packet)  
    
        # All layers should be found  
        eth_layer = pkt.get_layer(pcap.LayerType.EthLayer)  
        self.assertIsNotNone(eth_layer)  
        self.assertEqual(eth_layer.src_mac_addr, "00:11:22:33:44:55")  
    
        ip_layer = pkt.get_layer(pcap.LayerType.IPv4Layer)  
        self.assertIsNotNone(ip_layer)  
        self.assertEqual(ip_layer.src_ip, "1.2.3.4")  
        self.assertEqual(ip_layer.dst_ip, "5.6.7.8")  
    
        tcp_layer = pkt.get_layer(pcap.LayerType.TcpLayer)  
        self.assertIsNotNone(tcp_layer)  
        self.assertEqual(tcp_layer.src_port, 1000)  
        self.assertEqual(tcp_layer.dst_port, 80)  
    
        # Payload layer: test access by LayerType, and bytes at end  
        payload_layer = pkt.get_layer(pcap.LayerType.PayloadLayer)  
        self.assertIsNotNone(payload_layer)  
        self.assertEqual(bytes(payload_layer), b"foobar")  
        # Alternatively, test __bytes__ for packet as a whole  
        self.assertIn(b"foobar", bytes(pkt))  
    


if __name__ == "__main__":
    unittest.main()
