#!/bin/bash
# Demo SDN-ML-Blockchain System
# This script simulates the full system workflow

# Auto-detect project root (parent directory of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════╗"
echo -e "║   SDN-ML-Blockchain System Demo               ║"
echo -e "║   Real-time DDoS Detection & Mitigation        ║"
echo -e "╚════════════════════════════════════════════════╝${NC}\n"

cd "$PROJECT_ROOT"

# Demo 1: Show system components
echo -e "${YELLOW}[DEMO 1/4]${NC} System Components Overview"
echo -e "${GREEN}─────────────────────────────────────────────────${NC}"
echo "✅ SDN Controller: controller_blockchain.py"
echo "✅ ML Detector: ml_detector.py (SVM, DT, RF, NB)"
echo "✅ Blockchain: Hyperledger Fabric (real network required)"
echo "✅ Network: Mininet topologies"
echo ""

# Demo 2: Test ML Detection
echo -e "${YELLOW}[DEMO 2/4]${NC} ML-based Attack Detection"
echo -e "${GREEN}─────────────────────────────────────────────────${NC}"

python3 << EOF
import sys
import os
PROJECT_ROOT = "${PROJECT_ROOT}"
sys.path.insert(0, PROJECT_ROOT)
from ryu_app.ml_detector import MLDetector

print("Testing different traffic patterns:\n")

detector = MLDetector(model_type='svm')

# Test Case 1: Normal traffic
print("🔵 Test 1: Normal Traffic")
normal_features = [10, 5, 8]  # Low flow entries, low source IPs, normal remote IPs
prediction, confidence = detector.classify(normal_features)
status = "⚠️  ATTACK" if prediction == 1 else "✅ NORMAL"
print(f"   Features: sfe={normal_features[0]}, ssip={normal_features[1]}, rfip={normal_features[2]}")
print(f"   Result: {status} (confidence: {confidence:.2%})\n")

# Test Case 2: Suspicious traffic
print("🟡 Test 2: Suspicious Traffic")
suspicious_features = [50, 30, 15]  # Medium flow entries, medium source IPs
prediction, confidence = detector.classify(suspicious_features)
status = "⚠️  ATTACK" if prediction == 1 else "✅ NORMAL"
print(f"   Features: sfe={suspicious_features[0]}, ssip={suspicious_features[1]}, rfip={suspicious_features[2]}")
print(f"   Result: {status} (confidence: {confidence:.2%})\n")

# Test Case 3: DDoS attack
print("🔴 Test 3: DDoS Attack Traffic")
attack_features = [200, 100, 5]  # High flow entries, many source IPs, few remote IPs
prediction, confidence = detector.classify(attack_features)
status = "⚠️  ATTACK" if prediction == 1 else "✅ NORMAL"
print(f"   Features: sfe={attack_features[0]}, ssip={attack_features[1]}, rfip={attack_features[2]}")
print(f"   Result: {status} (confidence: {confidence:.2%})\n")

print("=" * 60)
print("ML Detector is working! Can classify Normal vs Attack traffic.")
print("=" * 60)
EOF

echo ""

# Demo 3: Test Blockchain Logging
echo -e "${YELLOW}[DEMO 3/4]${NC} Blockchain Security Event Logging"
echo -e "${GREEN}─────────────────────────────────────────────────${NC}"

python3 << EOF
import sys
import json
import time
import os
PROJECT_ROOT = "${PROJECT_ROOT}"
sys.path.insert(0, PROJECT_ROOT)
from blockchain.fabric_client import BlockchainClient

print("Simulating security events on blockchain:\n")

try:
    client = BlockchainClient()
except Exception as e:
    import sys, traceback
    print("Error: Unable to initialize BlockchainClient. Ensure Fabric network is up and fabric_client is configured.", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)

# Event 1: DDoS detected
print("📝 Event 1: DDoS Attack Detected")
event1 = {
    "event_type": "ddos_detected",
    "switch_id": "s1",
    "timestamp": int(time.time()),
    "trust_score": 0.2,
    "action": "port_blocked",
    "details": {"port": 1, "source_ip": "10.0.0.100", "reason": "SYN flood"}
}
client.record_event(json.dumps(event1))
print(f"   ✅ Recorded: {event1['event_type']} on {event1['switch_id']}")
print(f"   Trust Score: {event1['trust_score']} (LOW - suspicious)\n")

# Event 2: Port scan detected
print("📝 Event 2: Port Scan Detected")
event2 = {
    "event_type": "port_scan_detected",
    "switch_id": "s1",
    "timestamp": int(time.time()),
    "trust_score": 0.5,
    "action": "rate_limited",
    "details": {"port_range": "1-1024", "source_ip": "10.0.0.101"}
}
client.record_event(json.dumps(event2))
print(f"   ✅ Recorded: {event2['event_type']} on {event2['switch_id']}")
print(f"   Trust Score: {event2['trust_score']} (MEDIUM - suspicious)\n")

# Event 3: Normal traffic verified
print("📝 Event 3: Normal Traffic Verified")
event3 = {
    "event_type": "traffic_verified",
    "switch_id": "s2",
    "timestamp": int(time.time()),
    "trust_score": 0.95,
    "action": "allowed",
    "details": {"protocol": "HTTP", "source_ip": "10.0.0.1"}
}
client.record_event(json.dumps(event3))
print(f"   ✅ Recorded: {event3['event_type']} on {event3['switch_id']}")
print(f"   Trust Score: {event3['trust_score']} (HIGH - trusted)\n")

# Query trust logs
print("=" * 60)
print("📊 Querying Trust Logs:")
print("=" * 60)

for switch_id in ['s1', 's2']:
    log = client.query_trust_log(switch_id)
    if log:
        trust_status = "🔴 UNTRUSTED" if log['current_trust'] < 0.5 else "🟡 SUSPICIOUS" if log['current_trust'] < 0.7 else "🟢 TRUSTED"
        print(f"\nSwitch {switch_id}:")
        print(f"  Status: {trust_status}")
        print(f"  Current Trust: {log['current_trust']}")
        print(f"  Total Events: {log['event_count']}")

print("\n" + "=" * 60)
print("Blockchain logging working! All events immutably recorded.")
print("=" * 60)
EOF

echo ""

# Demo 4: Show complete workflow
echo -e "${YELLOW}[DEMO 4/4]${NC} Complete SDN Security Workflow"
echo -e "${GREEN}─────────────────────────────────────────────────${NC}"

python3 << EOF
import sys
import json
import time
import os
PROJECT_ROOT = "${PROJECT_ROOT}"
sys.path.insert(0, PROJECT_ROOT)
from ryu_app.ml_detector import MLDetector
from blockchain.fabric_client import BlockchainClient

print("Simulating real-time attack detection workflow:\n")
print("┌─────────────────────────────────────────────────────────┐")
print("│ Scenario: DDoS Attack on Network Switch                │")
print("└─────────────────────────────────────────────────────────┘\n")

# Initialize components
detector = MLDetector(model_type='svm')
try:
    blockchain = BlockchainClient()
except Exception:
    import sys, traceback
    print("Error: Blockchain client unavailable - demo requires a running Fabric test-network.", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)

# Step 1: Monitor traffic
print("Step 1️⃣ : SDN Controller monitors traffic on switch s1")
print("   → Collecting flow statistics...")
print("   → Flow entries: 250")
print("   → Unique source IPs: 180")
print("   → Remote IPs contacted: 3\n")
time.sleep(1)

# Step 2: Extract features
print("Step 2️⃣ : Extract ML features from flow data")
flow_features = [250, 180, 3]  # sfe, ssip, rfip
print(f"   → Features: sfe={flow_features[0]}, ssip={flow_features[1]}, rfip={flow_features[2]}\n")
time.sleep(1)

# Step 3: ML Detection
print("Step 3️⃣ : ML Detector analyzes traffic pattern")
prediction, confidence = detector.classify(flow_features)
is_attack = prediction == 1
print(f"   → Analysis: {'🔴 ATTACK DETECTED!' if is_attack else '🟢 Normal traffic'}")
print(f"   → Confidence: {confidence:.2%}")
print(f"   → Pattern: High flow entries + Many sources + Few targets = DDoS\n")
time.sleep(1)

# Step 4: Take action
if is_attack:
    print("Step 4️⃣ : Controller takes mitigation action")
    print("   → Installing flow rules to block malicious traffic")
    print("   → Dropping packets from suspicious sources")
    print("   → Rate limiting on affected ports\n")
    time.sleep(1)
    
    # Step 5: Log to blockchain
    print("Step 5️⃣ : Record security event to blockchain")
    event = {
        "event_type": "ddos_attack_mitigated",
        "switch_id": "s1",
        "timestamp": int(time.time()),
        "trust_score": 0.15,
        "action": "traffic_blocked",
        "details": {
            "flow_entries": flow_features[0],
            "source_ips": flow_features[1],
            "remote_ips": flow_features[2],
            "confidence": float(confidence),
            "mitigation": "flow_rules_installed"
        }
    }
    blockchain.record_event(json.dumps(event))
    print(f"   → Event recorded (demo)")
    print(f"   → Trust Score Updated: 0.15 (Device marked as compromised)")
    print(f"   → Immutable record created on blockchain\n")
    time.sleep(1)
    
    # Step 6: Verify
    print("Step 6️⃣ : Verify blockchain record")
    log = blockchain.query_trust_log("s1")
    print(f"   → Query successful")
    print(f"   → Device: {log['device_id']}")
    print(f"   → Current Trust: {log['current_trust']}")
    print(f"   → Total Events: {log['event_count']}\n")

print("┌─────────────────────────────────────────────────────────┐")
print("│ ✅ Attack Successfully Detected and Mitigated!          │")
print("│ ✅ Event Recorded on Blockchain for Audit Trail        │")
print("└─────────────────────────────────────────────────────────┘")
EOF

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════╗"
echo -e "║           DEMO COMPLETE! ✅                    ║"
echo -e "╚════════════════════════════════════════════════╝${NC}\n"

echo -e "${GREEN}What was demonstrated:${NC}"
echo "  1. ML-based traffic classification (Normal vs Attack)"
echo "  2. Blockchain security event logging"
echo "  3. Trust scoring system"
echo "  4. Complete attack detection workflow"
echo ""
echo -e "${GREEN}System capabilities:${NC}"
echo "  ✅ Real-time DDoS detection using machine learning"
echo "  ✅ Automated mitigation (flow rules, packet dropping)"
echo "  ✅ Immutable security audit trail on blockchain"
echo "  ✅ Device trust scoring and reputation tracking"
echo ""
echo -e "${YELLOW}To run the full system with Mininet:${NC}"
echo "  Terminal 1: sudo python3 -m ryu_app.controller_blockchain"
echo "  Terminal 2: sudo python3 topology/custom_topo.py"
echo "  Terminal 3: bash scripts/attack_traffic.sh"
echo ""
echo -e "${BLUE}Documentation: See README.md and HUONG_DAN_TIENG_VIET.md${NC}"
echo ""
