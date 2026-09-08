#!/usr/bin/env python3
"""
基估宝总开关控制服务 - 统一管理一组 systemd 服务
- 监听 127.0.0.1:3010（仅 loopback，避免公网暴露）
- POST /switch/on        → 启动 SERVICES 列表中的所有服务
- POST /switch/off       → 停止 SERVICES 列表中的所有服务
- GET  /status           → 返回每个服务的实时状态（JSON）
- 鉴权：X-Token 头，token 写入 .switch-token（首次启动自动生成，仅 root 可读）
- 所有 systemctl 操作走 sudo NOPASSWD（见 /etc/sudoers.d/fund-switch）

【开机默认行为】
读 /etc/fund-switch-boot.conf（缺省 off）。服务随 systemd 启动后立即按配置调整：
- off → 对所有 SERVICES 单元 disable + stop（确保开关关闭时这些服务不会随开机自启）
- on  → 对所有 SERVICES 单元 enable + start
注意：fund-research-internal.service / fill-gs-qdii.timer 必须显式 disable，
否则它们自身的 [Install] WantedBy=multi-user.target 会让它们开机自启，
总开关的"关闭"语义会失效。

总开关当前管理的服务：
  - fund-research-internal.service  → 基金研究 API (波段信号/夏普/回撤等, 端口 18081)
  - fill-gs-qdii.timer              → QDII 数据填充定时器
  - real-time-fund.service          → 基估宝静态站 (Caddy + out/) — 不受总开关控制，
                                       关闭后页面仍可访问以查看历史快照
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
    # real-time-fund.service 不再受总开关控制 - 前端 SPA 始终服务，确保关闭后仍可访问页面查看历史快照
    "fund-research-internal.service",  # 基金研究 API（波段/夏普/回撤）
    "fill-gs-qdii.timer",  # timer 控制 fill_gs_qdii.py 是否被定时触发
]
TOKEN_FILE = Path(__file__).resolve().parent / ".switch-token"

# 开机默认状态：读取 /etc/fund-switch-boot.conf（缺省 off）
# 配置格式：单行，"on" / "off"，大小写不敏感；缺省文件或空内容按 off 处理
BOOT_CONFIG = Path("/etc/fund-switch-boot.conf")
BOOT_DEFAULT = "off"  # 缺省关闭，避免 systemd [Install] 自动 enable fund-research-internal / fill-gs-qdii.timer


def read_boot_default() -> str:
    """读取开机默认状态。off=on"""
    try:
        v = BOOT_CONFIG.read_text().strip().lower()
        if v in ("on", "off"):
            return v
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return BOOT_DEFAULT


def apply_boot_default() -> None:
    """开机时按 BOOT_DEFAULT 对 SERVICES 应用 start 或 stop，并打印日志。"""
    target = read_boot_default()
    action = "start" if target == "on" else "stop"
    print(f"[fund-switch] boot default = {target!r} → {action}", file=sys.stderr)
    try:
        apply_action(action)
    except Exception as e:
        print(f"[fund-switch] boot default apply failed: {e}", file=sys.stderr)


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
    """执行 systemctl 命令。
    对 .timer 单元：
      - "start" → "start"（让 timer 立即 active 并开始计时）+ "enable"
      - "stop"  → "stop"（彻底停止，不再触发）+ "disable"（下次开机不自启）
    对 .service 单元：直接 start/stop
    """
    if action not in ("start", "stop", "is-active", "enable", "disable"):
        return False, f"unknown action {action!r}"
    return _run(["sudo", "-n", "systemctl", action, service])


def get_service_state(service: str) -> dict:
    """获取单元状态。
    .service：is-active
    .timer：is-active（inactive=已停止）+ is-enabled
    """
    if service.endswith(".timer"):
        ok_active, raw_active = _run(["sudo", "-n", "systemctl", "is-active", service])
        ok_enabled, raw_enabled = _run(["sudo", "-n", "systemctl", "is-enabled", service])
        # timer "开"=active(真的在跑/等待) + enabled(下次开机自启)
        is_on = ok_active and raw_active == "active"
        return {
            "service": service,
            "active": is_on,
            "enabled": ok_enabled and raw_enabled == "enabled",
            "raw": f"active={raw_active}, enabled={raw_enabled}",
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
    all_active = all(s["active"] for s in services) and len(services) > 0
    any_active = any(s["active"] for s in services)
    return {
        "services": services,
        "active": all_active,
        "partial": any_active and not all_active,
    }


def apply_action(action: str) -> dict:
    """对所有单元应用 start/stop。
    对 .timer 单元：
      - start: start + enable
      - stop:  stop + disable（关键：stop 才会立即停止等待，否则只是 disable，下次触发时间到了仍会咔哒）
    """
    results = []
    for s in SERVICES:
        if action == "start":
            if s.endswith(".timer"):
                ok1, msg1 = systemctl_one("start", s)
                ok2, msg2 = systemctl_one("enable", s)
                ok, msg = ok1 and ok2, f"start: {msg1}; enable: {msg2}"
            else:
                ok, msg = systemctl_one("start", s)
        elif action == "stop":
            if s.endswith(".timer"):
                ok1, msg1 = systemctl_one("stop", s)
                ok2, msg2 = systemctl_one("disable", s)
                ok, msg = ok1 and ok2, f"stop: {msg1}; disable: {msg2}"
                # 额外 stop 关联 service（清理正在跑的任务）
                service_name = s.replace(".timer", ".service")
                ok3, msg3 = systemctl_one("stop", service_name)
                results.append({"service": service_name, "ok": ok3, "message": msg3, "note": "killed running task"})
            else:
                ok, msg = systemctl_one("stop", s)
        else:
            ok, msg = False, f"unknown action {action!r}"
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

# 开机时按 /etc/fund-switch-boot.conf 应用总开关默认状态
apply_boot_default()

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