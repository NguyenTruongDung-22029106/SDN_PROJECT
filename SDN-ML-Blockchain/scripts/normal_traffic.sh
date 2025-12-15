#!/bin/bash
# Normal traffic generation script (topology-aware)
# Default subnet aligns với topo MultiSwitch: 10.0.0.0/24 (h1-h12)
# Có thể override bằng biến ENV TARGET_SUBNET_PREFIX hoặc tham số $1 (ví dụ: 10.1.1)

TARGET_SUBNET_PREFIX=${1:-${TARGET_SUBNET_PREFIX:-"10.0.0"}}
TARGET_HOSTS=${TARGET_HOSTS:-"2 3 4 5 6 7 8 9 10 11 12"}  # bỏ qua chính mình nếu cần
LOOPS=${LOOPS:-300}               # số vòng lặp hợp lý để tránh flood
SLEEP_LOW=${SLEEP_LOW:-1}
SLEEP_HIGH=${SLEEP_HIGH:-3}

echo "[Normal] subnet=${TARGET_SUBNET_PREFIX}.X hosts=${TARGET_HOSTS} loops=${LOOPS}"

for i in $(seq 1 $LOOPS); do
  for h in $TARGET_HOSTS; do
    ip="${TARGET_SUBNET_PREFIX}.${h}"
    echo "[Normal] iter=${i} ping ${ip}"
    ping -c1 -W1 "${ip}" >/dev/null 2>&1
    # ngủ ngắn để không tràn băng thông/CPU
    sleep $((RANDOM % (SLEEP_HIGH - SLEEP_LOW + 1) + SLEEP_LOW))
  done
done
