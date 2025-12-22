"""
SDN Controller with Machine Learning and Blockchain Integration
Enhanced version of the original controller with blockchain logging capabilities
"""
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import in_proto
from ryu.lib.packet import ipv4
from ryu.lib.packet import icmp
from ryu.lib.packet import tcp
from ryu.lib.packet import udp
from ryu.lib.packet import arp
from ryu.lib import hub

import csv
import time
import math
import statistics
import json
import sys
import os
import logging

# Add blockchain path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'blockchain'))
sys.path.append(os.path.dirname(__file__))  # Add ryu_app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..')) # Add parent directory to path

try:
    from ryu_app.ml_detector import MLDetector
except ImportError:
    from ml_detector import MLDetector

import requests

# If BLOCKCHAIN_ADAPTER_URL is set, use REST adapter; otherwise fall back to CLI client
BLOCKCHAIN_ADAPTER_URL = os.environ.get('BLOCKCHAIN_ADAPTER_URL', 'http://localhost:3001')
if BLOCKCHAIN_ADAPTER_URL:
    class BlockchainClient:
        def __init__(self, base_url=BLOCKCHAIN_ADAPTER_URL):
            self.base_url = base_url.rstrip('/')

        def record_event(self, event):
            try:
                r = requests.post(f"{self.base_url}/api/v1/events", json=event, timeout=10)
                r.raise_for_status()
                return True
            except Exception as e:
                print('Adapter record_event error:', e)
                return False

        def get_recent_attacks(self, time_window=300):
            """Get recent attacks across all switches within time_window seconds"""
            try:
                r = requests.get(f"{self.base_url}/api/v1/attacks/recent?timeWindow={time_window}", timeout=10)
                r.raise_for_status()
                return r.json().get('attacks', [])
            except Exception as e:
                print('Adapter get_recent_attacks error:', e)
                return []


    BLOCKCHAIN_ENABLED = True
else:
    from blockchain.fabric_client import BlockchainClient  # use CLI-based client
    BLOCKCHAIN_ENABLED = True

# Configuration
# APP_TYPE: 0 = data collection (ghi type = TEST_TYPE), 1 = detection (ML)
APP_TYPE = int(os.environ.get('APP_TYPE', '1'))
# TEST_TYPE: 0 = normal, 1 = attack (chỉ dùng khi APP_TYPE=0)
TEST_TYPE = int(os.environ.get('TEST_TYPE', '1'))
# PREVENTION: 0 = no blocking, 1 = block attacks (default: 1 for detection mode, 0 for collection mode)
PREVENTION = int(os.environ.get('PREVENTION', '1' if APP_TYPE == 1 else '0'))
INTERVAL = 2  # Data collection interval in seconds
BLOCKCHAIN_LOG = True  # Enable blockchain logging

# IP Spoofing Detection Configuration
# Set to 0 to disable IP Spoofing Detection (allow ML to handle all detection)
# Set to 1 to enable IP Spoofing Detection (blocks spoofed IPs before ML)
ENABLE_IP_SPOOFING_DETECTION = int(os.environ.get('ENABLE_IP_SPOOFING_DETECTION', '0'))

# ML Model Configuration
# Supported: 'decision_tree', 'random_forest', 'svm', 'naive_bayes'
ML_MODEL_TYPE = os.environ.get('ML_MODEL_TYPE', 'decision_tree')

# Logging setup: always write to logs/ryu_controller.log (alongside stdout).
# Attach handler to the ROOT logger so self.logger (from Ryu) also propagates.
def _ensure_file_logger():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    logs_dir = os.path.join(root_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, 'ryu_controller.log')

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    for h in root_logger.handlers:
        if isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "") == log_file:
            return

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

_ensure_file_logger()

# Global variables
gflows = []
old_ssip_len = 0
prev_flow_count = 0
FLOW_SERIAL_NO = 0
iteration = 0


def get_flow_number():
    global FLOW_SERIAL_NO
    FLOW_SERIAL_NO = FLOW_SERIAL_NO + 1
    return FLOW_SERIAL_NO


def get_data_path(filename):
    """Get path for data files, create directory if needed"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, filename)


def init_portcsv(dpid):
    fname = get_data_path("switch_" + str(dpid) + "_data.csv")
    # Only write header if file doesn't exist or is empty
    write_header = False
    if not os.path.exists(fname) or os.path.getsize(fname) == 0:
        write_header = True
    with open(fname, 'a', newline='') as fh:
        writ = csv.writer(fh, delimiter=',')
        if write_header:
            header = ["time", "sfe", "ssip", "rfip", "type"]
            writ.writerow(header)


def init_flowcountcsv(dpid):
    fname = get_data_path("switch_" + str(dpid) + "_flowcount.csv")
    write_header = False
    if not os.path.exists(fname) or os.path.getsize(fname) == 0:
        write_header = True
    with open(fname, 'a', newline='') as fh:
        writ = csv.writer(fh, delimiter=',')
        if write_header:
            header = ["time", "flowcount"]
            writ.writerow(header)


def update_flowcountcsv(dpid, row):
    fname = get_data_path("switch_" + str(dpid) + "_flowcount.csv")
    writ = csv.writer(open(fname, 'a', buffering=1), delimiter=',')
    writ.writerow(row)


def update_portcsv(dpid, row, label):
    """
    Append a row to per-switch data CSV and include the provided label.
    """
    fname = get_data_path("switch_" + str(dpid) + "_data.csv")
    # Ensure file has header (init_portcsv should have created it)
    with open(fname, 'a', newline='') as fh:
        writ = csv.writer(fh, delimiter=',')
        row_to_write = list(row)
        row_to_write.append(str(label))
        writ.writerow(row_to_write)
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except Exception:
            pass


def update_resultcsv(row, label, reason='ml', confidence=1.0, dpid=None, timestamp=None):
    """
    Write result row to appropriate location based on APP_TYPE:
    - APP_TYPE=0 (Collection): ghi vào dataset/result.csv (ground truth for training)
    - APP_TYPE=1 (Detection): ghi vào data/result.csv (ML predictions for analysis)
    
    Schema: sfe,ssip,rfip,label (4 cột - format giống tác giả gốc)
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Chọn thư mục dựa trên APP_TYPE
    if APP_TYPE == 0:
        # Collection mode → dataset/result.csv (training data)
        target_dir = os.path.join(base_dir, '..', 'dataset')
        os.makedirs(target_dir, exist_ok=True)
        fname = os.path.join(target_dir, 'result.csv')
    else:
        # Detection mode → data/result.csv (detection results)
        target_dir = os.path.join(base_dir, '..', 'data')
        os.makedirs(target_dir, exist_ok=True)
        fname = os.path.join(target_dir, 'result.csv')
    
    # Header 4 cột giống tác giả gốc
    header = ['sfe', 'ssip', 'rfip', 'label']

    # Lấy giá trị, default về 0/1.0 nếu thiếu
    sfe_val = str(row[0]) if len(row) > 0 else '0'
    ssip_val = str(row[1]) if len(row) > 1 else '0'
    rfip_val = str(row[2]) if len(row) > 2 else '1.0'
    label_val = int(label)

    write_header = not os.path.exists(fname) or os.path.getsize(fname) == 0
    try:
        with open(fname, 'a', newline='') as fh:
            writer = csv.writer(fh, delimiter=',')
            if write_header:
                writer.writerow(header)
            # Chỉ ghi 4 cột: sfe, ssip, rfip, label
            writer.writerow([sfe_val, ssip_val, rfip_val, label_val])
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except Exception:
                pass
    except Exception as e:
        try:
            print(f"Error writing result.csv: {e}")
        except Exception:
            pass


class BlockchainSDNController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(BlockchainSDNController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}  # Per-switch MAC to port mapping
        self.mac_to_dpid = {}  # Global MAC to switch mapping
        self.mac_to_ip = {}  # MAC address to IP mapping (to protect real host IPs)
        self.flow_thread = hub.spawn(self._flow_monitor)
        self.datapaths = {}
        self.ml_detector = None
        self.arp_ip_to_port = {}
        self.blocked_ports = {}
        self.last_normal_traffic_log = {}  # Track last normal traffic log time per switch (to avoid spam)
        self.old_ssip_len_per_switch = {}  # Track old SSIP length per switch (for accurate SSIP calculation)
        
        # Initialize blockchain client (must succeed)
        if BLOCKCHAIN_ENABLED and BLOCKCHAIN_LOG:
            self.blockchain_client = BlockchainClient()
            self.logger.info("✓ Blockchain client initialized successfully")
        else:
            self.blockchain_client = None

        # Initialize ML detector
        if APP_TYPE == 1:
            # Initialize ML detector for attack detection (GIỐNG TÁC GIẢ GỐC)
            self.ml_detector = MLDetector(model_type=ML_MODEL_TYPE)
            self.logger.info(f"✓ ML Detector loaded: {ML_MODEL_TYPE}")
        
        # Log IP Spoofing Detection status
        if ENABLE_IP_SPOOFING_DETECTION:
            self.logger.info("✓ IP Spoofing Detection: ENABLED")
        else:
            self.logger.info("✓ IP Spoofing Detection: DISABLED (ML will handle all detection)")

    def _flow_monitor(self):
        """Monitor flow statistics periodically"""
        hub.sleep(5)  # Initial delay
        while True:
            for dp in self.datapaths.values():
                self.request_flow_metrics(dp)
            hub.sleep(INTERVAL)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """Handle switch connection"""
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        self.datapaths[datapath.id] = datapath

        flow_serial_no = get_flow_number()
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions, flow_serial_no)

        init_portcsv(datapath.id)
        init_flowcountcsv(datapath.id)
        
        # Log switch connection to blockchain
        if self.blockchain_client:
            try:
                event_data = {
                    'event_type': 'switch_connected',
                    'switch_id': str(datapath.id),
                    'timestamp': int(time.time())
                }
                self.blockchain_client.record_event(event_data)
                self.logger.info(f"⛓️ Switch {datapath.id} connection logged to blockchain")
            except Exception as e:
                self.logger.error(f"Blockchain logging error: {e}")

    def request_flow_metrics(self, datapath):
        """Request flow statistics from switch"""
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        req = ofp_parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    def _speed_of_flow_entries(self, flows):
        """Calculate speed of flow entries (SFE)"""
        global prev_flow_count
        curr_flow_count = len(flows)
        sfe = curr_flow_count - prev_flow_count
        prev_flow_count = curr_flow_count
        return sfe

    def _speed_of_source_ip(self, flows, dpid):
        """Calculate speed of source IP addresses (SSIP) - per switch"""
        ssip = []
        
        for flow in flows:
            for i in flow.match.items():
                key = list(i)[0]
                val = list(i)[1]
                if key == "ipv4_src":
                    if val not in ssip:
                        ssip.append(val)
        
        cur_ssip_len = len(ssip)
        old_ssip_len = self.old_ssip_len_per_switch.get(dpid, 0)
        ssip_result = cur_ssip_len - old_ssip_len
        self.old_ssip_len_per_switch[dpid] = cur_ssip_len
        return ssip_result

    def _ratio_of_flowpair(self, flows):
        """Calculate ratio of flow pairs (RFIP)"""
        flow_count = len(flows) - 1  # Exclude table miss entry
        
        if flow_count <= 0:
            return 1.0
        
        collaborative_flows = {}
        
        for flow in flows:
            srcip = dstip = None
            for i in flow.match.items():
                key = list(i)[0]
                val = list(i)[1]
                if key == "ipv4_src":
                    srcip = val
                if key == "ipv4_dst":
                    dstip = val
            
            if srcip and dstip:
                fwdflowhash = srcip + "_" + dstip
                revflowhash = dstip + "_" + srcip
                
                if not fwdflowhash in collaborative_flows:
                    if not revflowhash in collaborative_flows:
                        collaborative_flows[fwdflowhash] = {}
                    else:
                        collaborative_flows[revflowhash][fwdflowhash] = 1
        
        onesideflow = iflow = 0
        for key in collaborative_flows:
            if collaborative_flows[key] == {}:
                onesideflow += 1
            else:
                iflow += 2
        
        if flow_count != 0:
            rfip = float(iflow) / flow_count
            return rfip
        return 1.0

    @set_ev_cls([ofp_event.EventOFPFlowStatsReply], MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        """Handle flow statistics reply"""
        global gflows
        
        t_flows = ev.msg.body
        flags = ev.msg.flags
        dpid = ev.msg.datapath.id
        gflows.extend(t_flows)

        if flags == 0:
            # Calculate features
            sfe = self._speed_of_flow_entries(gflows)
            ssip = self._speed_of_source_ip(gflows, dpid)
            rfip = self._ratio_of_flowpair(gflows)

            # Default label/reason values
            label = 0
            reason = 'collect' if APP_TYPE == 0 else 'ml'
            confidence = 1.0

            if APP_TYPE == 1:
                # ML Detection 
                result = self.ml_detector.classify([sfe, ssip, rfip])
                reason = 'ml'

                # Phân loại đơn giản giống tác giả gốc
                # result is numpy array, e.g. array([1]) or array([0])
                # Convert to int for comparison to avoid FutureWarning
                prediction = int(result[0]) if len(result) > 0 else 0
                
                if prediction == 1:
                    label = 1
                    self.logger.warning(
                        "🚨 ATTACK DETECTED! (Switch {}, SFE={:.1f}, SSIP={:.1f}, RFIP={:.2f})".format(
                            dpid, sfe, ssip, rfip
                        )
                    )
                    self.mitigation = 1
                    
                    # Log to blockchain
                    if self.blockchain_client:
                        try:
                            event_data = {
                                'event_type': 'attack_detected',
                                'switch_id': str(dpid),
                                'timestamp': int(time.time()),
                                'features': {
                                    'sfe': float(sfe),
                                    'ssip': float(ssip),
                                    'rfip': float(rfip)
                                }
                            }
                            self.blockchain_client.record_event(event_data)
                            self.logger.info("⛓️ Attack event logged to blockchain")
                        except Exception as e:
                            self.logger.error(f"Blockchain logging error: {e}")
                    
                    if PREVENTION == 1:
                        self.logger.info("🛡️ Prevention Enabled - Mitigation Started")
                
                elif prediction == 0:
                    label = 0
                    self.logger.info("✓ Normal Traffic (Switch {})".format(dpid))
                    
                    # Gửi normal traffic event để logging (tránh spam: mỗi 30 giây)
                    if self.blockchain_client:
                        current_time = time.time()
                        last_log_time = self.last_normal_traffic_log.get(dpid, 0)
                        
                        if current_time - last_log_time >= 30:
                            try:
                                event_data = {
                                    'event_type': 'normal_traffic',
                                    'switch_id': str(dpid),
                                    'timestamp': int(time.time()),
                                    'features': {
                                        'sfe': float(sfe),
                                        'ssip': float(ssip),
                                        'rfip': float(rfip)
                                    }
                                }
                                self.blockchain_client.record_event(event_data)
                                self.last_normal_traffic_log[dpid] = current_time
                                self.logger.info(f"⛓️ Normal traffic logged to blockchain (switch {dpid})")
                            except Exception as e:
                                self.logger.debug(f"Blockchain logging error (normal traffic): {e}")
                    
            else:
                # Data collection mode: label theo TEST_TYPE (0=normal, 1=attack)
                label = TEST_TYPE
                reason = 'collect'
                confidence = 1.0
                # Chỉ log khi có traffic thực sự (sfe != 0 hoặc ssip != 0)
                if sfe != 0 or ssip != 0:
                    label_text = "ATTACK" if label == 1 else "NORMAL"
                    self.logger.info(
                        f"📊 Data Collection Mode (TEST_TYPE={TEST_TYPE}): "
                        f"Features [sfe={sfe}, ssip={ssip}, rfip={rfip:.4f}] from switch {dpid} → Label={label} ({label_text})"
                    )

            # Chỉ ghi vào CSV khi có traffic thực sự (tránh spam dữ liệu [0,0,1.0])
            # Hoặc trong detection mode thì luôn ghi (để theo dõi ML predictions)
            if APP_TYPE == 1 or (sfe != 0 or ssip != 0):
                t = time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())
                row = [t, str(sfe), str(ssip), str(rfip)]
                update_portcsv(dpid, row, label)
                update_resultcsv([str(sfe), str(ssip), str(rfip)], label, reason=reason,
                                 confidence=confidence, dpid=dpid, timestamp=t)
            
            gflows = []

            # Update flowcount
            t = time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())
            update_flowcountcsv(dpid, [t, str(prev_flow_count)])

    def add_flow(self, datapath, priority, match, actions, serial_no, buffer_id=None, idletime=0, hardtime=0):
        """Add flow entry to switch"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, cookie=serial_no, buffer_id=buffer_id,
                                    idle_timeout=idletime, hard_timeout=hardtime,
                                    priority=priority, match=match, instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, cookie=serial_no, priority=priority,
                                    idle_timeout=idletime, hard_timeout=hardtime,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def block_port(self, datapath, portnumber, src_ip=None, dst_ip=None, reason="DDoS Attack", block_mode="port_only"):
        """
        Block traffic from specific port (giống repo tham khảo)
        Chỉ block port number, không block theo IP
        
        Args:
            portnumber: Port to block
            src_ip: Source IP (deprecated - không dùng nữa, chỉ để backward compatibility)
            dst_ip: Destination IP (deprecated - không dùng nữa, chỉ để backward compatibility)
            reason: Reason for blocking
            block_mode: "port_only" - chỉ block port number (mặc định)
        """
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        
        # Block port number (giống repo tham khảo) - block tất cả traffic từ port này
        match_args = {'in_port': portnumber}
        match = parser.OFPMatch(**match_args)
        actions = []
        flow_serial_no = get_flow_number()
        self.add_flow(datapath, 100, match, actions, flow_serial_no, hardtime=60)
        
        self.logger.warning(f"🚫 BLOCKING PORT {portnumber} on switch {dpid} for 60s (reason: {reason})")
        action_desc = f"port_blocked_for_60s"
        
        # Log blocking action to blockchain
        if self.blockchain_client:
            try:
                event_data = {
                    'event_type': 'port_blocked',
                    'switch_id': str(datapath.id),
                    'port': portnumber,
                    'src_ip': src_ip if src_ip else None,
                    'dst_ip': dst_ip if dst_ip else None,
                    'timestamp': int(time.time()),
                    'reason': reason,
                    'action': action_desc,
                    'block_mode': 'port_only'
                }
                self.blockchain_client.record_event(event_data)
                self.logger.info(f"⛓️ Port blocking logged to blockchain (mode: port_only)")
            except Exception as e:
                self.logger.error(f"Blockchain logging error: {e}")

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """Handle packet in events"""
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        
        dst = eth.dst
        src = eth.src
        dpid = datapath.id
        
        
        self.mac_to_port.setdefault(dpid, {})
        self.arp_ip_to_port.setdefault(dpid, {})
        self.arp_ip_to_port[dpid].setdefault(in_port, [])
        
        # Learn MAC address on this switch
        self.mac_to_port[dpid][src] = in_port
        # Learn which switch this MAC is on
        self.mac_to_dpid[src] = dpid

        # Handle ARP packets specially - always flood to allow learning
        if eth.ethertype == ether_types.ETH_TYPE_ARP:
            a = pkt.get_protocol(arp.arp)
            if a:
                if not a.src_ip in self.arp_ip_to_port[dpid][in_port]:
                    self.arp_ip_to_port[dpid][in_port].append(a.src_ip)
                # Lưu mapping MAC -> IP để bảo vệ IP thật của host
                if src not in self.mac_to_ip:
                    self.mac_to_ip[src] = set()
                self.mac_to_ip[src].add(a.src_ip)
                # Always flood ARP to allow cross-switch communication
                out_port = ofproto.OFPP_FLOOD
                actions = [parser.OFPActionOutput(out_port)]
        else:
            # For non-ARP packets, determine output port
            if dst in self.mac_to_port[dpid]:
                # Destination MAC is on this switch
                out_port = self.mac_to_port[dpid][dst]
            elif dst in self.mac_to_dpid:
                # Destination MAC is on another switch
                dst_dpid = self.mac_to_dpid[dst]
                if dpid == 1:  # We're on central switch (s1)
                    # Find port to destination switch
                    # s2 (dpid=2) -> port 2, s3 (dpid=3) -> port 3, s4 (dpid=4) -> port 4
                    # But we need to discover this - for now, flood
                    out_port = ofproto.OFPP_FLOOD
                else:
                    # We're on leaf switch, forward to central switch
                    # Port 1 is typically the link to s1 (central switch)
                    out_port = 1
            else:
                # Unknown destination - flood to learn
                out_port = ofproto.OFPP_FLOOD
            
            actions = [parser.OFPActionOutput(out_port)]

        # Install flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            if eth.ethertype == ether_types.ETH_TYPE_IP:
                ip = pkt.get_protocol(ipv4.ipv4)
                srcip = ip.src
                dstip = ip.dst

                # Check for spoofing during prevention (only if enabled)
                if PREVENTION and ENABLE_IP_SPOOFING_DETECTION:
                    # Kiểm tra IP có trong ARP table không
                    is_spoofed = not (srcip in self.arp_ip_to_port[dpid][in_port])
                    
                    # BẢO VỆ: Không block IP thật của host
                    # Kiểm tra xem IP này có phải là IP thật của host (dựa trên MAC address) không
                    if is_spoofed and src in self.mac_to_ip:
                        # Nếu MAC address này đã có IP được học (từ ARP), và IP hiện tại là một trong những IP đó
                        # → Đây là IP thật của host, không phải spoofed
                        if srcip in self.mac_to_ip[src]:
                            is_spoofed = False
                            self.logger.debug(f"⚠️ IP {srcip} from MAC {src} is known host IP, not blocking")
                    
                    # Chỉ block nếu chắc chắn là IP spoofed
                    if is_spoofed:
                        # Kiểm tra thêm: Nếu port này đã có IP được học, và IP hiện tại không phải IP đó
                        # → Chắc chắn là IP spoofed
                        known_ips_on_port = self.arp_ip_to_port[dpid].get(in_port, [])
                        if len(known_ips_on_port) > 0:
                            self.logger.warning(f"⚠️ IP Spoofing detected from port {in_port}, IP: {srcip}")
                            
                            # Block port khi phát hiện IP spoofing
                            self.block_port(
                                datapath,
                                in_port,
                                reason="IP Spoofing Attack",
                                block_mode="port_only",
                            )
                            return
                        else:
                            # Port này chưa có IP nào được học, có thể là IP thật của host chưa được học
                            # Không block để tránh block nhầm IP thật
                            self.logger.debug(f"⚠️ Potential IP spoofing from port {in_port}, IP: {srcip}, but not blocking (port has no known IPs yet)")

                match = parser.OFPMatch(
                    eth_type=ether_types.ETH_TYPE_IP,
                    ipv4_src=srcip,
                    ipv4_dst=dstip,
                )

                flow_serial_no = get_flow_number()
                if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                    self.add_flow(datapath, 1, match, actions, flow_serial_no, buffer_id=msg.buffer_id)
                    return
                else:
                    self.add_flow(datapath, 1, match, actions, flow_serial_no)
        
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
