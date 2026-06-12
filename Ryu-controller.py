from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, arp, ipv4, tcp, udp, icmp, ether_types


class SpineLeafPolicy13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    # Tabel host: IP -> {name, mac, leaf_dpid, port_di_leaf}
    HOSTS = {
        "192.168.10.11": {"name": "h1", "mac": "00:00:10:01:00:11", "leaf": 3, "port": 1},
        "192.168.10.12": {"name": "h2", "mac": "00:00:10:01:00:12", "leaf": 3, "port": 2},
        "192.168.10.21": {"name": "h3", "mac": "00:00:10:02:00:21", "leaf": 4, "port": 1},
        "192.168.10.22": {"name": "h4", "mac": "00:00:10:02:00:22", "leaf": 4, "port": 2},
        "192.168.10.31": {"name": "h5", "mac": "00:00:10:03:00:31", "leaf": 5, "port": 1},
        "192.168.10.32": {"name": "h6", "mac": "00:00:10:03:00:32", "leaf": 5, "port": 2},
        "192.168.10.41": {"name": "h7", "mac": "00:00:10:04:00:41", "leaf": 6, "port": 1},
        "192.168.10.42": {"name": "h8", "mac": "00:00:10:04:00:42", "leaf": 6, "port": 2},
    }

    # Role setiap switch
    ROLE = {1: "spine", 2: "spine", 3: "leaf", 4: "leaf", 5: "leaf", 6: "leaf"}

    # Port di leaf yang menuju ke host
    LEAF_TO_HOST_PORT = {
        3: {"192.168.10.11": 1, "192.168.10.12": 2},
        4: {"192.168.10.21": 1, "192.168.10.22": 2},
        5: {"192.168.10.31": 1, "192.168.10.32": 2},
        6: {"192.168.10.41": 1, "192.168.10.42": 2},
    }

    # Port di leaf yang menuju ke spine
    LEAF_TO_SPINE_PORT = {
        3: {1: 3, 2: 4},
        4: {1: 3, 2: 4},
        5: {1: 3, 2: 4},
        6: {1: 3, 2: 4},
    }

    # Port di spine yang menuju ke leaf
    SPINE_TO_LEAF_PORT = {
        1: {3: 1, 4: 2, 5: 3, 6: 4},
        2: {3: 1, 4: 2, 5: 3, 6: 4},
    }

    # Aturan firewall: h4 <-> h8 diblokir di port 5001 (TCP & UDP)
    FIREWALL_RULES = [
        {"src": "192.168.10.22", "dst": "192.168.10.42", "proto": "tcp", "tp_dst": 5001},
        {"src": "192.168.10.22", "dst": "192.168.10.42", "proto": "udp", "tp_dst": 5001},
        {"src": "192.168.10.42", "dst": "192.168.10.22", "proto": "tcp", "tp_dst": 5001},
        {"src": "192.168.10.42", "dst": "192.168.10.22", "proto": "udp", "tp_dst": 5001},
    ]

    def __init__(self, *args, **kwargs):
        super(SpineLeafPolicy13, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.flow_to_spine = {}
        self.rr_index = 0

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.datapaths[datapath.id] = datapath
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions, idle_timeout=0, hard_timeout=0)

        role = "SPINE" if datapath.id in (1, 2) else "LEAF"
        self.logger.info("[+] Switch connected: s%d [%s]", datapath.id, role)

    def add_flow(self, datapath, priority, match, actions, idle_timeout=300, hard_timeout=0):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match,
            instructions=inst, idle_timeout=idle_timeout, hard_timeout=hard_timeout
        )
        datapath.send_msg(mod)

    def add_drop_flow(self, datapath, priority, match, idle_timeout=300, hard_timeout=0):
        parser = datapath.ofproto_parser
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match,
            instructions=[], idle_timeout=idle_timeout, hard_timeout=hard_timeout
        )
        datapath.send_msg(mod)

    def send_packet_out(self, datapath, in_port, out_port, data, buffer_id):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        actions = [parser.OFPActionOutput(out_port)]
        if buffer_id != ofproto.OFP_NO_BUFFER:
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=buffer_id,
                in_port=in_port, actions=actions, data=None
            )
        else:
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
                in_port=in_port, actions=actions, data=data
            )
        datapath.send_msg(out)

    def _select_spine(self, src_ip, dst_ip):
        key = tuple(sorted([src_ip, dst_ip]))
        if key not in self.flow_to_spine:
            self.flow_to_spine[key] = 1 if (self.rr_index % 2 == 0) else 2
            self.rr_index += 1
            self.logger.info("[ECMP] New flow %s<->%s -> Spine%d",
                             src_ip, dst_ip, self.flow_to_spine[key])
        return self.flow_to_spine[key]

    def _path_for(self, src_ip, dst_ip):
        src_leaf = self.HOSTS[src_ip]["leaf"]
        dst_leaf = self.HOSTS[dst_ip]["leaf"]
        if src_leaf == dst_leaf:
            return [src_leaf]
        spine = self._select_spine(src_ip, dst_ip)
        return [src_leaf, spine, dst_leaf]

    def _in_port_for_segment(self, path, idx, src_ip):
        dpid = path[idx]
        if len(path) == 1:
            return self.LEAF_TO_HOST_PORT[dpid][src_ip]
        if self.ROLE[dpid] == "leaf":
            if idx == 0:
                return self.LEAF_TO_HOST_PORT[dpid][src_ip]
            else:
                spine_id = path[idx - 1]
                return self.LEAF_TO_SPINE_PORT[dpid][spine_id]
        prev_leaf = path[idx - 1]
        return self.SPINE_TO_LEAF_PORT[dpid][prev_leaf]

    def _out_port_for_segment(self, path, idx, dst_ip):
        dpid = path[idx]
        if len(path) == 1:
            return self.LEAF_TO_HOST_PORT[dpid][dst_ip]
        if self.ROLE[dpid] == "leaf":
            if idx == 0:
                next_spine = path[idx + 1]
                return self.LEAF_TO_SPINE_PORT[dpid][next_spine]
            else:
                return self.LEAF_TO_HOST_PORT[dpid][dst_ip]
        next_leaf = path[idx + 1]
        return self.SPINE_TO_LEAF_PORT[dpid][next_leaf]

    def _proxy_arp_reply(self, datapath, in_port, src_mac, src_ip, dst_mac, dst_ip, buffer_id):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(
            ethertype=ether_types.ETH_TYPE_ARP, src=dst_mac, dst=src_mac))
        pkt.add_protocol(arp.arp(
            opcode=arp.ARP_REPLY,
            src_mac=dst_mac, src_ip=dst_ip,
            dst_mac=src_mac, dst_ip=src_ip))
        pkt.serialize()
        actions = [parser.OFPActionOutput(in_port)]
        if buffer_id != ofproto.OFP_NO_BUFFER:
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=buffer_id,
                in_port=ofproto.OFPP_CONTROLLER, actions=actions, data=None)
        else:
            out = parser.OFPPacketOut(
                datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
                in_port=ofproto.OFPP_CONTROLLER, actions=actions, data=pkt.data)
        datapath.send_msg(out)

    def _firewall_match(self, src_ip, dst_ip, pkt):
        tcp_seg  = pkt.get_protocol(tcp.tcp)
        udp_seg  = pkt.get_protocol(udp.udp)
        icmp_seg = pkt.get_protocol(icmp.icmp)
        if tcp_seg:
            proto, tp_dst = "tcp", tcp_seg.dst_port
        elif udp_seg:
            proto, tp_dst = "udp", udp_seg.dst_port
        elif icmp_seg:
            proto, tp_dst = "icmp", None
        else:
            return None
        for rule in self.FIREWALL_RULES:
            if rule["src"] != src_ip or rule["dst"] != dst_ip:
                continue
            if rule["proto"] != proto:
                continue
            if "tp_dst" in rule and tp_dst != rule["tp_dst"]:
                continue
            return rule
        return None

    def _install_firewall_drop(self, src_ip, dst_ip, rule):
        src_leaf = self.HOSTS[src_ip]["leaf"]
        dp = self.datapaths.get(src_leaf)
        if dp is None:
            return
        parser = dp.ofproto_parser
        match_kwargs = {
            "eth_type": ether_types.ETH_TYPE_IP,
            "ipv4_src": src_ip, "ipv4_dst": dst_ip,
        }
        if rule["proto"] == "tcp":
            match_kwargs["ip_proto"] = 6
            match_kwargs["tcp_dst"]  = rule["tp_dst"]
        elif rule["proto"] == "udp":
            match_kwargs["ip_proto"] = 17
            match_kwargs["udp_dst"]  = rule["tp_dst"]
        elif rule["proto"] == "icmp":
            match_kwargs["ip_proto"] = 1
        match = parser.OFPMatch(**match_kwargs)
        self.add_drop_flow(dp, priority=250, match=match, idle_timeout=0)
        self.logger.warning("[FIREWALL] DROP: %s -> %s (%s port=%s)",
                            src_ip, dst_ip, rule["proto"], rule.get("tp_dst", "*"))

    def _install_route(self, src_ip, dst_ip):
        for src, dst in [(src_ip, dst_ip), (dst_ip, src_ip)]:
            path = self._path_for(src, dst)
            for idx, dpid in enumerate(path):
                dp = self.datapaths.get(dpid)
                if dp is None:
                    continue
                parser   = dp.ofproto_parser
                in_port  = self._in_port_for_segment(path, idx, src)
                out_port = self._out_port_for_segment(path, idx, dst)
                match = parser.OFPMatch(
                    eth_type=ether_types.ETH_TYPE_IP,
                    ipv4_src=src, ipv4_dst=dst, in_port=in_port)
                actions = [parser.OFPActionOutput(out_port)]
                self.add_flow(dp, priority=100, match=match, actions=actions)
        self.logger.info("[ROUTE] %s <-> %s | path=%s",
                         src_ip, dst_ip, self._path_for(src_ip, dst_ip))

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg      = ev.msg
        datapath = msg.datapath
        dpid     = datapath.id
        in_port  = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        if eth is None:
            return
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        arp_pkt = pkt.get_protocol(arp.arp)
        if arp_pkt:
            if arp_pkt.opcode == arp.ARP_REQUEST and arp_pkt.dst_ip in self.HOSTS:
                dst_info = self.HOSTS[arp_pkt.dst_ip]
                self._proxy_arp_reply(
                    datapath=datapath, in_port=in_port,
                    src_mac=eth.src, src_ip=arp_pkt.src_ip,
                    dst_mac=dst_info["mac"], dst_ip=arp_pkt.dst_ip,
                    buffer_id=msg.buffer_id)
                self.logger.info("[ARP PROXY] %s -> %s replied with %s",
                                 arp_pkt.src_ip, arp_pkt.dst_ip, dst_info["mac"])
            return

        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if ip_pkt is None:
            return

        src_ip = ip_pkt.src
        dst_ip = ip_pkt.dst
        if src_ip not in self.HOSTS or dst_ip not in self.HOSTS:
            return

        rule = self._firewall_match(src_ip, dst_ip, pkt)
        if rule:
            self._install_firewall_drop(src_ip, dst_ip, rule)
            return

        self._install_route(src_ip, dst_ip)

        path = self._path_for(src_ip, dst_ip)
        if dpid not in path:
            return
        idx      = path.index(dpid)
        out_port = self._out_port_for_segment(path, idx, dst_ip)
        self.send_packet_out(datapath, in_port, out_port, msg.data, msg.buffer_id)
