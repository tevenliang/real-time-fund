#!/bin/bash
# 基估宝总开关 - 命令行版
# 转发到 fund-switch-server.py 的 HTTP API
# 用法:
#   ./fund-switch.sh on       # 启动基估宝服务
#   ./fund-switch.sh off      # 停止基估宝服务
#   ./fund-switch.sh status   # 查看状态
#   ./fund-switch.sh restart  # 重启

set -euo pipefail

TOKEN_FILE="$(dirname "$(readlink -f "$0")")/.switch-token"
if [ ! -f "$TOKEN_FILE" ]; then
  echo "[fund-switch] FATAL: token file not found: $TOKEN_FILE" >&2
  exit 1
fi
TOKEN=$(cat "$TOKEN_FILE")

URL_BASE="http://127.0.0.1:3010"

case "${1:-}" in
  on|start)
    curl -fsS -X POST -H "X-Token: $TOKEN" "$URL_BASE/switch/on"
    echo
    ;;
  off|stop)
    curl -fsS -X POST -H "X-Token: $TOKEN" "$URL_BASE/switch/off"
    echo
    ;;
  status)
    curl -fsS "$URL_BASE/status"
    echo
    ;;
  restart)
    "$0" off
    sleep 1
    "$0" on
    ;;
  *)
    echo "用法: $0 {on|off|status|restart}" >&2
    exit 1
    ;;
esac