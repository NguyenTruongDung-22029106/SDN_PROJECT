#!/bin/bash
# Script để kiểm tra recent attacks từ blockchain

GATEWAY_URL="http://localhost:3001"

echo "=== Recent Attacks từ Blockchain ==="
echo ""

response=$(curl -s "$GATEWAY_URL/api/v1/attacks/recent?timeWindow=300")

if [ $? -eq 0 ]; then
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
else
    echo "  ❌ Không thể kết nối đến blockchain gateway"
fi

echo ""
echo "💡 Lưu ý: Blockchain chỉ để logging, không quyết định blocking"

