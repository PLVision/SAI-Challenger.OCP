import logging
import time
import ipaddress
import macaddress

import dpkt
from saichallenger.common.sai_dataplane import SaiDataplane
from snappi import snappi

BASE_TENGINE_PORT = 5555

class SaiDataplaneImpl(SaiDataplane):

    def __init__(self, exec_params):
        self.alias = exec_params['alias']
        self.mode = exec_params['mode']
        super().__init__(exec_params)
        self.flows = []

    def init(self):
        # Configure a new API instance where the location points to controller
        # Ixia-C:       location = "https://<tgen-ip>:<port>"
        # IxNetwork:    location = "https://<tgen-ip>:<port>", ext="ixnetwork"
        # TRex:         location =         "<tgen-ip>:<port>", ext="trex"
        if self.mode == 'ixnet':
            self.api = snappi.api(location=self.exec_params['controller'], verify=False, ext='ixnetwork')
        elif self.mode == 'trex':
            self.api = snappi.api(location=self.exec_params['controller'], verify=False, ext='trex')
        else:
            self.api = snappi.api(location=self.exec_params['controller'], verify=False)
        logging.info("%s Starting connection to controller... " % time.strftime("%s"))

        # Create an empty configuration to be pushed to controller
        self.configuration = self.api.config()

        # Configure two ports where the location points to the port location:
        # Ixia-C:       port.location = "localhost:5555"
        # IxNetwork:    port.location = "<chassisip>;card;port"
        # TRex:         port.location = "localhost:5555"
        for pid, port in enumerate(self.exec_params['port_groups']):
            location = port.get('location', f"localhost:{BASE_TENGINE_PORT+pid}")
            self.configuration.ports.port(name=port[port['init']], location=location)

        cap = self.configuration.captures.capture(name="c1")[-1]
        cap.port_names = [p.name for p in self.configuration.ports]
        cap.format = cap.PCAP

        self.dataplane = self

    def remove(self):
        pass

    def setUp(self):
        super().setUp()
        self.set_config()
        self.start_capture()

    def tearDown(self):
        super().tearDown()
        self.stop_capture()
        self.configuration.flows.clear()
        self.flows.clear()

    @staticmethod
    def api_results_ok(results):
        if hasattr(results, 'warnings'):
            return True
        else:
            print(f'Results={results}')
            return False

    @staticmethod
    def check_warnings(response):
        if response.warnings:
            print("Warning: %s" % str(response.warnings))

    @staticmethod
    def get_capture_port_names(cfg):
        """
        Returns name of ports for which capture is enabled.
        """
        names = []
        for cap in cfg.captures:
            if cap._properties.get("port_names"):
                for name in cap.port_names:
                    if name not in names:
                        names.append(name)
        return names

    def set_config(self, return_time=False):
        start_time = time.time()
        logging.info('Setting config ...')
        res = self.api.set_config(self.configuration)
        assert self.api_results_ok(res), res
        if len(res.warnings) > 0:
            logging.info('Warnings in set_config : {}'.format(res.warnings))
        end_time = time.time()
        operation_time = (end_time - start_time) * 1000
        if return_time:
            return operation_time

    def start_capture(self):
        """ Start a capture which was already configured.
        """
        capture_names = self.get_capture_port_names(self.configuration)
        logging.info(f"Starting capture on ports {str(capture_names)}")
        cs = self.api.capture_state()
        cs.state = cs.START
        self.check_warnings(self.api.set_capture_state(cs))

    def stop_capture(self):
        capture_names = self.get_capture_port_names(self.configuration)
        logging.info(f"Stopping capture on ports {str(capture_names)}")
        cs = self.api.capture_state()
        cs.state = cs.STOP
        self.check_warnings(self.api.set_capture_state(cs))

    def get_all_captures(self):
        """
        Returns a dictionary where port name is the key and value is a list of
        frames where each frame is represented as a list of bytes.
        """
        cap_dict = {}
        for name in self.get_capture_port_names(self.configuration):
            print("Fetching captures from port %s" % name)
            request = self.api.capture_request()
            request.port_name = name
            pcap_bytes = self.api.get_capture(request)

            cap_dict[name] = []
            for ts, pkt in dpkt.pcap.Reader(pcap_bytes):
                cap_dict[name].append(list(pkt))

        return cap_dict

    def start_traffic(self):
        """ Start traffic flow(s) which are already configured.
        """
        ts = self.api.transmit_state()
        ts.state = ts.START
        logging.info('Start traffic')
        res = self.api.set_transmit_state(ts)
        assert self.api_results_ok(res), res

    def stop_traffic(self):
        """ Stop traffic flow(s) which are already configured.
        """
        ts = self.api.transmit_state()
        ts.state = ts.STOP
        logging.info('Stop traffic')
        res = self.api.set_transmit_state(ts)
        assert self.api_results_ok(res), res

    # PAUSE api not supported by Ixia-C
    def pause_traffic(self):
        """ Pause traffic flow(s) which are already configured.
        """
        ts = self.api.transmit_state()
        ts.state = ts.PAUSE
        logging.info('Pause traffic')
        res = self.api.set_transmit_state(ts)
        assert self.api_results_ok(res), res

    def is_traffic_stopped(self, flow_names=[]):
        """
        Returns true if traffic in stop state
        """
        fq = self.api.metrics_request()
        fq.flow.flow_names = flow_names
        metrics = self.api.get_metrics(fq).flow_metrics
        return all([m.transmit == "stopped" for m in metrics])

    def get_all_stats(self, print_output=True):
        """
        Returns all port and flow stats
        """
        print("Fetching all port stats ...")
        request = self.api.metrics_request()
        request.choice = request.PORT
        request.port
        port_results = self.api.get_metrics(request).port_metrics
        if port_results is None:
            port_results = []

        # print("Fetching all flow stats ...")
        # request = self.api.metrics_request()
        # request.choice = request.FLOW
        # request.flow
        # flow_results = self.api.get_metrics(request).flow_metrics
        # if flow_results is None:
        #     flow_results = []

        # if print_output:
        #     print_stats(port_stats=port_results, flow_stats=flow_results)

        return port_results

    def stats_ok(self, packets):
        """
        Returns true if stats are as expected, false otherwise.
        """
        _, flow_stats = self.get_all_stats()

        flow_rx = sum([f.frames_rx for f in flow_stats])
        return flow_rx == packets

    # number - count of steps to do
    def get_next_ip(self, ip = "192.168.0.1", step = "0.0.0.1", number = 1) -> str:
        if ip == None:
            ip = "192.168.0.1"
        if step == None:
            step = "0.0.0.1"
        if number == 0:
            return str(ipaddress.IPv4Address(ip))
        return str(ipaddress.IPv4Address(int(ipaddress.IPv4Address(ip)) + number * int(ipaddress.IPv4Address(step))))

    # number - count of steps to do
    def get_next_mac(self, mac = "00:00:00:AA:BB:01", step = "00:00:00:00:00:01", number = 1):
        if mac == None:
            mac = "00:00:00:AA:BB:01"
        if step == None:
            step = "00:00:00:00:00:01"
        if number == 0:
            return str(macaddress.MAC(mac))
        return str(macaddress.MAC(int(macaddress.MAC(mac)) + number * int(macaddress.MAC(step)))).replace('-', ':')

    def configure_vxlan_packet(self, VIP: dict, VNI: dict, CA_SMAC: dict, CA_DIP: dict):

        get_count = lambda dict_count: dict_count.get('count', 1)
        get_step = lambda dict_step: dict_step.get('step', None)

        print("Test config:")
        print(VIP)
        print(VNI)
        print(CA_SMAC)
        print(CA_DIP)

        print("Adding flows {} > {}:".format(self.configuration.ports[0].name, self.configuration.ports[1].name))
        vip_val = VIP['start']
        flow_count = 0
        for vip in range(0, get_count(VIP)):
            vni_val = VNI['start']
            print(f"\tVIP {vip_val}")

            for vni in range(0, get_count(VNI)):
                print(f"\t\tVNI {vni_val}")
                ca_smac_val = CA_SMAC['start']

                for ca_smac in range(0, get_count(CA_SMAC)):
                    print(f"\t\t\tCA SMAC: {ca_smac_val}")
                    # for ca_dip in range(0, get_count(CA_DIP)):
                    print(f"\t\t\t\tCA DIP {CA_DIP.get('start')}, count: {get_count(CA_DIP)}, step: {get_step(CA_DIP)}")

                    flow = self.add_flow("flow {} > {} |vip#{}|vni#{}|ca_dip#{}|ca_mac#{}".format(
                                          self.configuration.ports[0].name, self.configuration.ports[1].name, vip, vni, CA_DIP['start'], ca_smac),
                                         packet_count=get_count(CA_DIP))
                    flow_count += 1
                    self.add_ethernet_header(flow, dst_mac="00:00:02:03:04:05", src_mac="00:00:05:06:06:06")
                    self.add_ipv4_header(flow, dst_ip=vip_val, src_ip="172.16.1.1")
                    self.add_udp_header(flow, dst_port=80, src_port=11638)
                    self.add_vxlan_header(flow, vni=vni_val)
                    self.add_ethernet_header(flow, dst_mac="02:02:02:02:02:02", src_mac=ca_smac_val)

                    self.add_ipv4_header(flow, dst_ip=CA_DIP['start'], src_ip="10.1.1.10", dst_step=get_step(CA_DIP), dst_count=get_count(CA_DIP),
                                         dst_choice=snappi.PatternFlowIpv4Dst.INCREMENT)
                    self.add_udp_header(flow)

                    ca_smac_val = self.get_next_mac(ca_smac_val, get_step(CA_SMAC))

                vni_val += get_step(VNI)

            vip_val = self.get_next_ip(vip_val, get_step(VIP))

        print(f">>> FLOWS: {flow_count}")

    def prepare_vxlan_packets(self, test_conf: dict):
        VIP = test_conf['DASH_VIP']['vpe']['IPV4']
        VNI = test_conf['DASH_DIRECTION_LOOKUP']['dle']['VNI']
        CA_SMAC = test_conf['DASH_ENI_ETHER_ADDRESS_MAP']['eam']['MAC']
        CA_DIP = test_conf['DASH_OUTBOUND_CA_TO_PA']['ocpe']['DIP']

        if type(VIP) != dict:
            VIP = { 'count': 1, 'start': VIP, 'step': "0.0.0.1" }
        if type(VNI) != dict:
            VNI = { 'count': 1, 'start': VNI, 'step': 1 }
        if type(CA_SMAC) != dict:
            CA_SMAC = { 'count': 1, 'start': CA_SMAC, 'step': "00:00:00:00:00:01" }
        if type(CA_DIP) != dict:
            CA_DIP = { 'count': 1, 'start': CA_DIP, 'step': "0.0.0.1" }

        self.configure_vxlan_packet(VIP, VNI, CA_SMAC, CA_DIP)

    def add_flow(self,
                 name = "Default flow name",
                 packet_count = 1,
                 seconds_count = 0,
                 pps = 10,
                 force_pps = False
                 ):
        flow = self.configuration.flows.flow(name=name)[-1]

        flow.tx_rx.port.tx_name = self.configuration.ports[0].name
        flow.tx_rx.port.rx_name = self.configuration.ports[0].name

        if (seconds_count > 0):
            flow.duration.fixed_seconds.seconds = seconds_count
        else:
            flow.duration.fixed_packets.packets = packet_count

        flow.size.fixed = 128
        flow.metrics.enable = True

        # if (bmv2):
        #     dont change pps
        # else if (force_pps == True):
        #     change
        flow.rate.pps = pps

        self.flows.append(flow)
        return flow

    def check_flows_all_packets_metrics(self, flows = [], name = "Flow group", exp_tx = None, exp_rx = None, show = False):
        if not flows:
            print("Flows None or empty")
            return False, None
        if not exp_tx:
            # check if all flows are fixed_packets
            # sum of bool list == count of True in this list
            if sum([flow.duration.choice == snappi.FlowDuration.FIXED_PACKETS for flow in flows]) == len(flows):
                exp_tx = sum([flow.duration.fixed_packets.packets for flow in flows])
            else:
                print("{}: some flow in flow group doesn't configured to {}.".format( \
                        name, snappi.FlowDuration.FIXED_PACKETS))
                return False, None
        if not exp_rx:
            exp_rx = exp_tx

        act_tx = 0
        act_rx = 0
        success = 0

        for flow in flows:
            tmp = self.check_flow_packets_metrics(flow)
            success += tmp[0]
            act_tx += tmp[1]['TX']
            act_rx += tmp[1]['RX']

        # print(success)
        success = success == len(flows)
        # print(success)

        if show:
            # flow group name | exp tx | act tx | exp rx | act rx
            print(f"{name} | exp tx:{exp_tx} - tx:{act_tx} | exp rx:{exp_rx} - rx:{act_rx}")

        return success, { 'TX': act_tx, 'RX': act_rx }

    # exp = expected
    # act = actual
    # (bool, {'TX': int, 'RX': int})
    def check_flow_packets_metrics(self, flow: snappi.Flow, exp_tx = None, exp_rx = None, show = False):
        if not exp_tx:
            if flow.duration.choice == snappi.FlowDuration.FIXED_PACKETS:
                exp_tx = flow.duration.fixed_packets.packets
            else:
                print("{}: check for packet count failed. Flow configured to {} instead of {}".format( \
                        flow.name, flow.duration.choice, snappi.FlowDuration.FIXED_PACKETS))
                return False, None
        if not exp_rx:
            exp_rx = exp_tx

        req = self.api.metrics_request()
        req.flow.flow_names = [ flow.name ]
        req.flow.metric_names = [ snappi.FlowMetricsRequest.FRAMES_TX, snappi.FlowMetricsRequest.FRAMES_RX ]
        res = self.api.get_metrics(req)

        act_tx = res.flow_metrics[0].frames_tx
        act_rx = res.flow_metrics[0].frames_rx

        if show:
            # flow name | exp tx | act tx | exp rx | act rx
            print("{} | {} | {} | {} | {}".format(flow.name, exp_tx, act_tx, exp_rx, act_rx))

        if exp_tx == act_tx and exp_rx == act_rx and \
            res.flow_metrics[0].transmit == snappi.FlowMetric.STOPPED:
            return True, { 'TX': act_tx, 'RX': act_rx }

        return False, { 'TX': act_tx, 'RX': act_rx }

    # TODO
    def check_flows_all_seconds_metrics(self):
        pass

    def check_flow_seconds_metrics(self, flow: snappi.Flow, seconds = None, exp_tx = None, exp_rx = None, delta = None, show = False):
        if not seconds:
            if flow.duration.choice == snappi.FlowDuration.FIXED_SECONDS:
                seconds = flow.duration.fixed_seconds.seconds
            else:
                print("{}: check for packet count failed. Flow configured to {} instead of {}".format( \
                        flow.name, flow.duration.choice, snappi.FlowDuration.FIXED_SECONDS))
                return False, None
        if not exp_tx:
            exp_tx = flow.rate.pps * seconds
        if not exp_rx:
            exp_rx = exp_tx
        if not delta:
            # default delta is 10% of exp_tx. If it 0 (seconds < 10) then delta == pps
            tmp_delta = int(exp_tx / 10)
            delta = tmp_delta if tmp_delta > 0 else flow.rate.pps

        req = self.api.metrics_request()
        req.flow.flow_names = [ flow.name ]
        req.flow.metric_names = [ snappi.FlowMetricsRequest.FRAMES_TX, snappi.FlowMetricsRequest.FRAMES_RX ]
        res = self.api.get_metrics(req)

        act_tx = res.flow_metrics[0].frames_tx
        act_rx = res.flow_metrics[0].frames_rx

        if show:
            # flow name | [exp tx - delta, ext_tx + delta] | act tx | [exp rx - delta, exp_rx + delta] | act rx
            print("{} | [{}, {}] | {} | [{}, {}] | {}".format(flow.name, exp_tx - delta, exp_tx + delta, act_tx, \
                                                                exp_rx - delta, exp_rx + delta, act_rx))

        if act_tx in range(exp_tx - delta, exp_tx + delta) and \
            act_rx in range(exp_rx - delta, exp_rx + delta) and \
            res.flow_metrics[0].transmit == snappi.FlowMetric.STOPPED:
            return True, { 'TX': act_tx, 'RX': act_rx }

        return False, { 'TX': act_tx, 'RX': act_rx }

    # TODO
    def check_flows_all_continuous_metrics(self):
        pass

    # TODO
    def check_flow_continuous_metrics(self, flow: snappi.Flow):
        pass

    def add_simple_vxlan_packet(self,
        flow: snappi.Flow,
        outer_dst_mac,
        outer_src_mac,
        outer_dst_ip,
        outer_src_ip,
        dst_udp_port,
        src_udp_port,
        vni,
        inner_dst_mac,
        inner_src_mac,
        inner_dst_ip,
        inner_src_ip
    ):
        if flow == None:
            print("flow is None")
            return

        if flow.packet:
            print("packet in flow")
            return

        self.add_ethernet_header(flow, outer_dst_mac, outer_src_mac)
        self.add_ipv4_header(flow, outer_dst_ip, outer_src_ip)
        u = self.add_udp_header(flow, dst_udp_port, src_udp_port)
        # TODO: report ixia bug (udp checksum still generated)
        # u.checksum.choice = u.checksum.CUSTOM
        # u.checksum.custom = 1
        self.add_vxlan_header(flow, vni)
        self.add_ethernet_header(flow, inner_dst_mac, inner_src_mac)
        self.add_ipv4_header(flow, inner_dst_ip, inner_src_ip)
        self.add_udp_header(flow)

    def set_increment(self, field, choice, count, start, step):
        if choice == 'increment':
            field.choice = choice
            field.increment.count = count
            field.increment.start = start
            field.increment.step = step

    def add_ethernet_header(self,
        flow: snappi.Flow,
        dst_mac = "FF:FF:FF:FF:FF:FF",
        src_mac = "00:01:02:03:04:05",
        eth_type = 0x0800,
        dst_choice = snappi.PatternFlowEthernetDst.VALUE,
        dst_count = 1,
        dst_step = "00:00:00:00:00:01",
        src_choice = snappi.PatternFlowEthernetSrc.VALUE,
        src_count = 1,
        src_step = "00:00:00:00:00:01"
    ):
        if flow == None:
            return None

        ether = flow.packet.add().ethernet
        ether.dst.value = dst_mac
        ether.src.value = src_mac
        ether.ether_type.value = eth_type

        # Setup increment
        self.set_increment(ether.dst, dst_choice, dst_count, dst_mac, dst_step)
        self.set_increment(ether.src, src_choice, src_count, src_mac, src_step)

        return ether

    # TODO: add other fields
    def add_ipv4_header(self,
        flow: snappi.Flow,
        dst_ip = "192.168.0.1",
        src_ip = "192.168.0.2",
        dst_choice = snappi.PatternFlowIpv4Dst.VALUE,
        dst_count = 1,
        dst_step = "0.0.0.1",
        src_choice = snappi.PatternFlowIpv4Src.VALUE,
        src_count = 1,
        src_step = "0.0.0.1"
    ):
        if flow == None:
            return None

        ipv4 = flow.packet.add().ipv4
        ipv4.dst.value = dst_ip
        ipv4.src.value = src_ip

        # Setup increment
        self.set_increment(ipv4.dst, dst_choice, dst_count, dst_ip, dst_step)
        self.set_increment(ipv4.src, src_choice, src_count, src_ip, src_step)

        return ipv4

    def add_udp_header(self,
        flow: snappi.Flow,
        dst_port = 80,
        src_port = 1234,
        dst_choice = snappi.PatternFlowUdpDstPort.VALUE,
        dst_count = 1,
        dst_step = 1,
        src_choice = snappi.PatternFlowUdpSrcPort.VALUE,
        src_count = 1,
        src_step = 1
    ):
        if flow == None:
            return None

        udp = flow.packet.add().udp
        udp.dst_port.value = dst_port
        udp.src_port.value = src_port

        # Setup increment
        self.set_increment(udp.dst_port, dst_choice, dst_count, dst_port, dst_step)
        self.set_increment(udp.src_port, src_choice, src_count, src_port, src_step)

        return udp

    def add_vxlan_header(self,
        flow: snappi.Flow,
        vni = 100,
        vni_choice = snappi.PatternFlowVxlanVni.VALUE,
        vni_count = 1,
        vni_step = 1
    ):
        if flow == None:
            return None

        vxlan = flow.packet.add().vxlan
        vxlan.vni.value = vni

        # Setup increment
        self.set_increment(vxlan.vni, vni_choice, vni_count, vni, vni_step)

        return vxlan
