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


def _run(cmd: list[str], timeout: int = 10) -> tuple[bool, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, f"exec error: {e}"


def systemctl_one(action: str, service: str) -> tuple[bool, str]:
    if action not in ("start", "stop", "is-active"):
        return False, f"unknown action {action!r}"
    return _run(["sudo", "-n", "systemctl", action, service])


def get_service_state(service: str) -> dict:
    ok, raw = systemctl_one("is-active", service)
    return {
        "service": service,
        "active": ok and raw == "active",
        "raw": raw,
    }


def get_state() -> dict:
    """所有服务的状态聚合 + 总开关判定。"""
    services = [get_service_state(s) for s in SERVICES]
    all_active = all(s["active"] for s in services) and len(services) > 0
    any_active = any(s["active"] for s in services)
    return {
        "services": services,
        "active": all_active,  # "全开 = 开"，对应总开关亮起
        "partial": any_active and not all_active,  # 部分服务异常
    }


def apply_action(action: str) -> dict:
    """对所有服务应用 start/stop。返回每个服务的结果。"""
    results = []
    for s in SERVICES:
        ok, msg = systemctl_one(action, s)
        results.append({"service": s, "ok": ok, "message": msg})
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