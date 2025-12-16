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

        def query_trust_log(self, device_id):
            try:
                r = requests.get(f"{self.base_url}/api/v1/trust/{device_id}", timeout=10)
                r.raise_for_status()
                return r.json().get('trust_log')
            except Exception as e:
                print('Adapter query_trust_log error:', e)
                return None

        def get_recent_attacks(self, time_window=300):
            """Get recent attacks across all switches within time_window seconds"""
            try:
                r = requests.get(f"{self.base_url}/api/v1/attacks/recent?timeWindow={time_window}", timeout=10)
                r.raise_for_status()
                return r.json().get('attacks', [])
            except Exception as e:
                print('Adapter get_recent_attacks error:', e)
                return []

        def get_mitigation_action(self, switch_id, confidence):
            """Query blockchain for recommended mitigation action"""
            try:
                r = requests.post(f"{self.base_url}/api/v1/mitigation/action", 
                                json={"switch_id": switch_id, "confidence": confidence}, 
                                timeout=10)
                r.raise_for_status()
                return r.json().get('action', 'standard_mitigation')
            except Exception as e:
                print('Adapter get_mitigation_action error:', e)
                return 'standard_mitigation'

        def check_coordinated_attack(self, time_window=300, threshold=3):
            """Check if multiple switches are under coordinated attack"""
            try:
                r = requests.get(f"{self.base_url}/api/v1/attacks/coordinated?timeWindow={time_window}&threshold={threshold}", timeout=10)
                r.raise_for_status()
                result = r.json()
                return result.get('is_coordinated', False), result.get('affected_switches', [])
            except Exception as e:
                print('Adapter check_coordinated_attack error:', e)
                return False, []

    BLOCKCHAIN_ENABLED = True
else:
    from blockchain.fabric_client import BlockchainClient  # use CLI-based client
    BLOCKCHAIN_ENABLED = True

# Configuration
# APP_TYPE: 0 = data collection (ghi type = TEST_TYPE), 1 = detection (ML)
APP_TYPE = int(os.environ.get('APP_TYPE', '1'))
# TEST_TYPE: 0 = normal, 1 = attack (chỉ dùng khi APP_TYPE=0)
TEST_TYPE = int(os.environ.get('TEST_TYPE', '1'))
PREVENTION = 0  # DDoS prevention enabled
INTERVAL = 2  # Data collection interval in seconds
BLOCKCHAIN_LOG = False  # Enable blockchain logging

# ML Model Configuration
# Supported: 'decision_tree', 'random_forest', 'svm', 'naive_bayes'
ML_MODEL_TYPE = os.environ.get('ML_MODEL_TYPE', 'decision_tree')
# Confidence threshold: chỉ coi là attack nếu confidence >= ML_CONF_THRESHOLD
ML_CONF_THRESHOLD = float(os.environ.get('ML_CONF_THRESHOLD', '0.8'))

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
    Write a standardized result row to `data/result.csv`.

    Schema: time,sfe,ssip,rfip,label,reason,confidence,dpid
    """
    fname = get_data_path("result.csv")
    header = ['time', 'sfe', 'ssip', 'rfip', 'label', 'reason', 'confidence', 'dpid']

    t = timestamp if timestamp is not None else time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())
    sfe_val = str(row[0]) if len(row) > 0 else ''
    ssip_val = str(row[1]) if len(row) > 1 else ''
    rfip_val = str(row[2]) if len(row) > 2 else ''
    label_val = int(label)
    reason_val = str(reason)
    confidence_val = float(confidence)
    dpid_val = '' if dpid is None else str(dpid)

    write_header = not os.path.exists(fname) or os.path.getsize(fname) == 0
    try:
        with open(fname, 'a', newline='') as fh:
            writer = csv.writer(fh, delimiter=',')
            if write_header:
                writer.writerow(header)
            writer.writerow([t, sfe_val, ssip_val, rfip_val, label_val, reason_val, f"{confidence_val:.4f}", dpid_val])
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
        self.flow_thread = hub.spawn(self._flow_monitor)
        self.datapaths = {}
        self.mitigation = 0
        self.ml_detector = None
        self.arp_ip_to_port = {}
        self.blocked_ports = {}
        
        # Initialize blockchain client (must succeed)
        if BLOCKCHAIN_ENABLED and BLOCKCHAIN_LOG:
            self.blockchain_client = BlockchainClient()
            self.logger.info("✓ Blockchain client initialized successfully")
        else:
            self.blockchain_client = None

        # Initialize ML detector
        if APP_TYPE == 1:
            self.ml_detector = MLDetector(model_type=ML_MODEL_TYPE)
            self.logger.info(f"✓ ML Detector initialized with {ML_MODEL_TYPE.upper()} algorithm")

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
                    'timestamp': int(time.time()),
                    'trust_score': 1.0
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

    def _speed_of_source_ip(self, flows):
        """Calculate speed of source IP addresses (SSIP)"""
        global old_ssip_len
        ssip = []
        
        for flow in flows:
            for i in flow.match.items():
                key = list(i)[0]
                val = list(i)[1]
                if key == "ipv4_src":
                    if val not in ssip:
                        ssip.append(val)
        
        cur_ssip_len = len(ssip)
        ssip_result = cur_ssip_len - old_ssip_len
        old_ssip_len = cur_ssip_len
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
            ssip = self._speed_of_source_ip(gflows)
            rfip = self._ratio_of_flowpair(gflows)

            # Default label/reason values
            label = 0
            reason = 'collect' if APP_TYPE == 0 else 'ml'
            confidence = 1.0

            if APP_TYPE == 1:
                # ML Detection
                raw_result, confidence = self.ml_detector.classify([sfe, ssip, rfip])
                reason = 'ml'

                # Áp dụng confidence threshold:
                # - Chỉ coi là attack nếu model dự đoán 1 VÀ confidence >= ML_CONF_THRESHOLD
                # - Ngược lại gán label=0 (normal) để tránh false alarm quá lớn.
                if int(raw_result) == 1 and confidence >= ML_CONF_THRESHOLD:
                    label = 1
                    high_conf_attack = True
                else:
                    label = 0
                    high_conf_attack = False
                    if int(raw_result) == 1:
                        # Model báo attack nhưng độ tin cậy thấp → ghi log để theo dõi
                        self.logger.info(
                            "🤔 Low-confidence attack prediction ignored "
                            "(confidence={:.2f} < threshold {:.2f})".format(
                                confidence, ML_CONF_THRESHOLD
                            )
                        )
                
                if high_conf_attack:  # Attack detected with high confidence
                    self.logger.warning(
                        "🚨 ATTACK DETECTED! Confidence: {:.2f}% (threshold {:.2f})".format(
                            confidence * 100, ML_CONF_THRESHOLD * 100
                        )
                    )
                    
                    # Query blockchain for mitigation decision
                    mitigation_action = 'standard_mitigation'
                    if self.blockchain_client:
                        try:
                            # Get trust-based mitigation recommendation
                            mitigation_action = self.blockchain_client.get_mitigation_action(str(dpid), confidence)
                            self.logger.info(f"⛓️ Blockchain recommends: {mitigation_action}")
                            
                            # Check for coordinated attack
                            is_coordinated, affected_switches = self.blockchain_client.check_coordinated_attack(300, 3)
                            if is_coordinated:
                                self.logger.critical(f"🚨 COORDINATED ATTACK DETECTED! Affected switches: {affected_switches}")
                                mitigation_action = 'block_immediately'
                        except Exception as e:
                            self.logger.error(f"Blockchain query failed: {e}")
                    
                    # Apply mitigation based on blockchain recommendation
                    if mitigation_action == 'block_immediately':
                        self.mitigation = 2  # Aggressive mitigation
                        self.logger.warning("⚠️ Aggressive mitigation mode activated")
                    elif mitigation_action == 'standard_mitigation':
                        self.mitigation = 1  # Standard mitigation
                    elif mitigation_action == 'warn_only':
                        self.mitigation = 0  # No mitigation, only warning
                        self.logger.info("ℹ️ High trust score - monitoring only, no blocking")
                    
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
                                },
                                'confidence': float(confidence),
                                'trust_score': 1.0 - confidence,
                                'action': mitigation_action
                            }
                            self.blockchain_client.record_event(event_data)
                            self.logger.info("⛓️ Attack event logged to blockchain")
                        except Exception as e:
                            self.logger.error(f"Blockchain logging error: {e}")
                    
                    if PREVENTION == 1:
                        self.logger.info("🛡️ Mitigation Started")
                
                else:  # Normal traffic (hoặc attack low-confidence)
                    self.logger.info(
                        "✓ Normal / Low-risk Traffic - Confidence: {:.2f}%".format(
                            confidence * 100
                        )
                    )
                    
            else:
                # Data collection mode: label theo TEST_TYPE (0=normal, 1=attack)
                label = TEST_TYPE
                reason = 'collect'
                confidence = 1.0
                # Chỉ log khi có traffic thực sự (sfe != 0 hoặc ssip != 0)
                if sfe != 0 or ssip != 0:
                    self.logger.info(f"Features [sfe={sfe}, ssip={ssip}, rfip={rfip:.4f}] from switch {dpid}")

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

    def block_port(self, datapath, portnumber, reason="DDoS Attack"):
        """Block traffic from specific port"""
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(in_port=portnumber)
        actions = []
        flow_serial_no = get_flow_number()
        self.add_flow(datapath, 100, match, actions, flow_serial_no, hardtime=120)
        
        # Log blocking action to blockchain
        if self.blockchain_client:
            try:
                event_data = {
                    'event_type': 'port_blocked',
                    'switch_id': str(datapath.id),
                    'port': portnumber,
                    'timestamp': int(time.time()),
                    'reason': reason,
                    'trust_score': 0.0,
                    'action': 'blocked_for_120s'
                }
                self.blockchain_client.record_event(event_data)
                self.logger.info(f"⛓️ Port blocking logged to blockchain")
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
        
        # Check trust score from blockchain before processing
        if self.blockchain_client and hasattr(self, 'mitigation'):
            try:
                trust_log = self.blockchain_client.query_trust_log(str(dpid))
                if trust_log:
                    trust_score = trust_log.get('current_trust', 1.0)
                    status = trust_log.get('status', 'trusted')
                    
                    # If switch has very low trust, block all traffic from this port
                    if trust_score < 0.3 and status == 'blocked':
                        self.logger.warning(f"⛔ Switch {dpid} has low trust score ({trust_score:.2f}), blocking port {in_port}")
                        self.block_port(datapath, in_port, reason="Low Trust Score")
                        return
                    
                    # If suspicious, increase scrutiny
                    if status == 'suspicious':
                        self.logger.debug(f"⚠️ Switch {dpid} is suspicious (trust={trust_score:.2f})")
            except Exception as e:
                self.logger.debug(f"Trust check error: {e}")
        
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

                # Check for spoofing during mitigation
                if self.mitigation and PREVENTION:
                    if not (srcip in self.arp_ip_to_port[dpid][in_port]):
                        self.logger.warning(f"⚠️ IP Spoofing detected from port {in_port}, IP: {srcip}")
                        self.logger.info(f"🚫 Blocking port {in_port}")
                        self.block_port(datapath, in_port, reason="IP Spoofing Attack")
                        return

                match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, 
                                        ipv4_src=srcip, ipv4_dst=dstip)

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
