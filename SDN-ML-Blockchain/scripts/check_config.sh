#!/bin/bash
###############################################################################
# Script kiểm tra cấu hình hệ thống
###############################################################################

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}            KIỂM TRA CẤU HÌNH HỆ THỐNG                         ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Auto-detect project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Check if Ryu is running
if ! pgrep -f "ryu-manager" > /dev/null; then
    echo -e "${YELLOW}⚠ Ryu Controller không chạy${NC}"
    echo "Chạy: ./scripts/start_system.sh"
    exit 1
fi

echo -e "${GREEN}✓ Ryu Controller đang chạy${NC}"
echo ""

# Check logs
LOG_FILE="${PROJECT_ROOT}/logs/ryu_controller.log"

if [ ! -f "$LOG_FILE" ]; then
    echo -e "${YELLOW}⚠ Log file không tồn tại: ${LOG_FILE}${NC}"
    exit 1
fi

echo -e "${BLUE}📋 CẤU HÌNH HIỆN TẠI:${NC}"
echo ""

# Extract configuration from logs
echo "┌─────────────────────────────────────────────────────────────┐"

# ML Detector
ML_MODEL=$(grep "ML Detector loaded" "$LOG_FILE" | tail -1 | sed 's/.*ML Detector loaded: //')
if [ -n "$ML_MODEL" ]; then
    echo -e "│ ML Model Type:              ${GREEN}${ML_MODEL}${NC}"
else
    echo -e "│ ML Model Type:              ${YELLOW}Not detected${NC}"
fi

# IP Spoofing Detection
IP_SPOOFING=$(grep "IP Spoofing Detection:" "$LOG_FILE" | tail -1)
if echo "$IP_SPOOFING" | grep -q "ENABLED"; then
    echo -e "│ IP Spoofing Detection:      ${GREEN}ENABLED${NC}"
elif echo "$IP_SPOOFING" | grep -q "DISABLED"; then
    echo -e "│ IP Spoofing Detection:      ${YELLOW}DISABLED${NC}"
else
    echo -e "│ IP Spoofing Detection:      ${YELLOW}Unknown${NC}"
fi

echo "└─────────────────────────────────────────────────────────────┘"
echo ""

# Check recent activity
echo -e "${BLUE}📊 HOẠT ĐỘNG GẦN ĐÂY (10 dòng cuối):${NC}"
echo ""

# Show last 10 lines with highlights
tail -10 "$LOG_FILE" | while IFS= read -r line; do
    if echo "$line" | grep -q "Attack Traffic detected"; then
        echo -e "${GREEN}$line${NC}"
    elif echo "$line" | grep -q "IP Spoofing detected"; then
        echo -e "${YELLOW}$line${NC}"
    elif echo "$line" | grep -q "Normal Traffic"; then
        echo "$line"
    else
        echo "$line"
    fi
done

echo ""

# Check data/result.csv
DATA_CSV="${PROJECT_ROOT}/data/result.csv"
if [ -f "$DATA_CSV" ]; then
    TOTAL_LINES=$(wc -l < "$DATA_CSV")
    ATTACK_LINES=$(grep ",1$" "$DATA_CSV" | wc -l)
    NORMAL_LINES=$(grep ",0$" "$DATA_CSV" | wc -l)
    
    echo -e "${BLUE}📁 DATA/RESULT.CSV:${NC}"
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo -e "│ Total entries:              ${TOTAL_LINES}"
    echo -e "│ Normal traffic (label=0):   ${NORMAL_LINES}"
    echo -e "│ Attack traffic (label=1):   ${GREEN}${ATTACK_LINES}${NC}"
    echo "└─────────────────────────────────────────────────────────────┘"
    echo ""
    
    if [ "$ATTACK_LINES" -gt 0 ]; then
        echo -e "${GREEN}✓ ML đã phát hiện attack!${NC}"
        echo ""
        echo "Xem chi tiết:"
        echo "  tail -20 $DATA_CSV | grep ',1$'"
    else
        echo -e "${YELLOW}⚠ Chưa có attack nào được phát hiện${NC}"
        echo ""
        echo "Để test:"
        echo "  1. Chạy Mininet: cd topology && sudo python3 custom_topo.py"
        echo "  2. Trong Mininet CLI: h2 bash ../scripts/attack_traffic.sh &"
    fi
else
    echo -e "${YELLOW}⚠ File data/result.csv chưa tồn tại${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Xem log đầy đủ: tail -f ${LOG_FILE}"
echo "Xem hướng dẫn: cat docs/IP_SPOOFING_DETECTION.md"
echo ""

