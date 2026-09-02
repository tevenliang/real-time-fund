#!/usr/bin/env python3
"""
基估宝总开关控制服务 - 统一管理一组 systemd 服务
- 监听 127.0.0.1:3010（仅 loopback，避免公网暴露）
- POST /switch/on        → 启动 SERVICES 列表中的所有服务
- POST /switch/off       → 停止 SERVICES 列表中的所有服务
- GET  /status           → 返回每个服务的实时状态（JSON）
- 鉴权：X-Token 头，token 写入 .switch-token（首次启动自动生成，仅 root 可读）
- 所有 systemctl 操作走 sudo NOPASSWD（见 /etc/sudoers.d/fund-switch）

总开关当前管理的服务：
  - real-time-fund.service          → 基估宝静态站 (Caddy + out/)
  - fund-research-internal.service  → 基金研究 API (波段信号/夏普/回撤等, 端口 18081)
"""
from __future__ import annotations
import json
import os
import secrets
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "127.0.0.1"
PORT = 3010
SERVICES = [
    "real-time-fund.service",
    "fund-research-internal.service",
    "fill-gs-qdii.timer",  # timer enable/disable 控制 fill_gs_qdii.py 是否被定时触发
]
TOKEN_FILE = Path(__file__).resolve().parent / ".switch-token"


def get_token() -> str:
    if TOKEN_FILE.exists():
        token = TOKEN_FILE.read_text().strip()
        if token:
            return token
    token = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(token)
    os.chmod(TOKEN_FILE, 0o600)
    print(f"[fund-switch] generated new token, written to {TOKEN_FILE}", file=sys.stderr)
    return token


def _run(cmd: list[str], timeout: int = 30) -> tuple[bool, str]:
    """执行 systemctl 命令。默认 30s 超时，足够 uvicorn 完成现有请求再退出。"""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return False, f"timeout after {timeout}s"
    except Exception as e:
        return False, f"exec error: {e}"


def systemctl_one(action: str, service: str) -> tuple[bool, str]:
    # 对 .service 用 start/stop，对 .timer 用 enable-now/disable-now
    if service.endswith(".timer"):
        if action == "start":
            action = "enable"
        elif action == "stop":
            action = "disable"
    if action not in ("start", "stop", "is-active", "enable", "disable"):
        return False, f"unknown action {action!r}"
    return _run(["sudo", "-n", "systemctl", action, service])


def get_service_state(service: str) -> dict:
    """获取单元状态。
    .service 用 is-active，.timer 用 is-enabled
    """
    if service.endswith(".timer"):
        ok, raw = systemctl_one("is-active", service)  # 用 is-active 检查 timer 是否在跑
        # timer 没有"active"概念，真正要看的是 is-enabled
        ok2, raw2 = _run(["sudo", "-n", "systemctl", "is-enabled", service])
        return {
            "service": service,
            "active": ok and raw == "active",
            "enabled": ok2 and raw2 == "enabled",
            "raw": raw,
            "kind": "timer",
        }
    else:
        ok, raw = systemctl_one("is-active", service)
        return {
            "service": service,
            "active": ok and raw == "active",
            "raw": raw,
            "kind": "service",
        }


def get_state() -> dict:
    """所有服务的状态聚合 + 总开关判定。"""
    services = [get_service_state(s) for s in SERVICES]
    # 对 .service：必须 active；对 .timer：必须 enabled
    def is_on(s):
        if s["kind"] == "timer":
            return s.get("enabled", False)
        return s["active"]
    all_active = all(is_on(s) for s in services) and len(services) > 0
    any_active = any(is_on(s) for s in services)
    return {
        "services": services,
        "active": all_active,
        "partial": any_active and not all_active,
    }


def apply_action(action: str) -> dict:
    """对所有单元应用 start/stop（timer 自动映射到 enable/disable）。
    对于 timer，disable 后还要 stop 关联的 service（防止正在跑的任务残留）。
    """
    results = []
    for s in SERVICES:
        ok, msg = systemctl_one(action, s)
        results.append({"service": s, "ok": ok, "message": msg})
        # 关闭时额外 stop 对应的 service（清理正在跑的任务）
        if action == "stop" and s.endswith(".timer"):
            service_name = s.replace(".timer", ".service")
            ok2, msg2 = systemctl_one("stop", service_name)
            results.append({"service": service_name, "ok": ok2, "message": msg2, "note": "killed running task"})
    return results


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("[fund-switch] " + fmt % args + "\n")

    def _send_json(self, code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _auth_ok(self) -> bool:
        token_provided = self.headers.get("X-Token", "")
        token_expected = _token
        if not token_provided or not token_expected:
            return False
        return secrets.compare_digest(token_provided, token_expected)

    def do_GET(self):
        if self.path in ("/status", "/__switch/status"):
            self._send_json(200, get_state())
            return
        if self.path in ("/health", "/__switch/health"):
            self._send_json(200, {"ok": True})
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if not self._auth_ok():
            self._send_json(401, {"error": "unauthorized"})

            return
        if self.path in ("/switch/on", "/__switch/on"):
            results = apply_action("start")
            ok = all(r["ok"] for r in results)
            self._send_json(200 if ok else 500, {**get_state(), "results": results, "action": "on"})
            return
        if self.path in ("/switch/off", "/__switch/off"):
            results = apply_action("stop")
            ok = all(r["ok"] for r in results)
            self._send_json(200 if ok else 500, {**get_state(), "results": results, "action": "off"})
            return
        self._send_json(404, {"error": "not found"})


_token = get_token()
print(f"[fund-switch] token = {_token}", file=sys.stderr)
print(f"[fund-switch] serving on {HOST}:{PORT} for services {SERVICES}", file=sys.stderr)

try:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
except OSError as e:
    print(f"[fund-switch] FATAL: cannot bind {HOST}:{PORT}: {e}", file=sys.stderr)
    sys.exit(1)

try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()