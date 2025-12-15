#!/bin/bash

# Script để xem logs của các component trong hệ thống

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

show_help() {
    echo "Usage: $0 [component]"
    echo ""
    echo "Components:"
    echo "  gateway     - Xem Gateway API log"
    echo "  ryu         - Xem Ryu Controller log"
    echo "  fabric      - Xem Fabric peer logs"
    echo "  all         - Xem tất cả logs (default)"
    echo ""
    echo "Options:"
    echo "  -f, --follow    - Theo dõi log real-time (như tail -f)"
    echo "  -n, --lines N   - Hiển thị N dòng cuối (default: 20)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Xem tất cả logs"
    echo "  $0 gateway -f        # Theo dõi Gateway log real-time"
    echo "  $0 ryu -n 50         # Xem 50 dòng cuối của Ryu log"
}

FOLLOW=false
LINES=20
COMPONENT="all"

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -n|--lines)
            LINES="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        gateway|ryu|fabric|all)
            COMPONENT="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

view_gateway() {
    local log_file="${PROJECT_ROOT}/blockchain/gateway.log"
    if [ ! -f "$log_file" ]; then
        echo "Gateway log not found: $log_file"
        return
    fi
    
    echo "=== GATEWAY LOG ==="
    if [ "$FOLLOW" = true ]; then
        tail -f "$log_file"
    else
        tail -n "$LINES" "$log_file"
    fi
}

view_ryu() {
    local log_file="${PROJECT_ROOT}/ryu_app/ryu_controller.log"
    if [ ! -f "$log_file" ]; then
        echo "Ryu log not found: $log_file"
        return
    fi
    
    echo "=== RYU CONTROLLER LOG ==="
    if [ "$FOLLOW" = true ]; then
        tail -f "$log_file"
    else
        tail -n "$LINES" "$log_file"
    fi
}

view_fabric() {
    echo "=== FABRIC PEER LOGS ==="
    if [ "$FOLLOW" = true ]; then
        docker logs -f peer0.org1.example.com 2>&1
    else
        echo "--- Peer0.Org1 ---"
        docker logs --tail "$LINES" peer0.org1.example.com 2>&1
        echo ""
        echo "--- Peer0.Org2 ---"
        docker logs --tail "$LINES" peer0.org2.example.com 2>&1
    fi
}

view_all() {
    if [ "$FOLLOW" = true ]; then
        echo "Cannot follow all logs at once. Please specify a component."
        exit 1
    fi
    
    view_gateway
    echo ""
    view_ryu
    echo ""
    view_fabric
}

case "$COMPONENT" in
    gateway)
        view_gateway
        ;;
    ryu)
        view_ryu
        ;;
    fabric)
        view_fabric
        ;;
    all)
        view_all
        ;;
    *)
        echo "Unknown component: $COMPONENT"
        show_help
        exit 1
        ;;
esac

