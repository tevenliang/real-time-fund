# ROLLBACK.md — 从 GitHub 回滚恢复

场景：服务器上的 /home/ubuntu/apps/real-time-fund 丢失、损坏或需要回到历史版本。
数据不受影响（Supabase 托管）。

## 回滚步骤

```bash
# 1. 重新拉取源码（或指定历史版本）
git clone git@github.com:tevenliang/real-time-fund.git /home/ubuntu/apps/real-time-fund
cd /home/ubuntu/apps/real-time-fund
git checkout <目标 commit SHA>   # 可选：回到指定版本，默认 master 最新

# 2. 恢复环境变量（值从 /home/ubuntu/.config/real-time-fund/runtime.env 提供）
#    构建 NEXT_PUBLIC_* 占位；ENCRYPTION_KEY 等按 runtime.env 注入

# 3. 安装依赖并构建
npm ci
npm run build

# 4. 恢复并启动 systemd 单元
sudo cp scripts/real-time-fund.service /etc/systemd/system/
sudo cp scripts/fund-switch-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart real-time-fund fund-switch-server
sudo systemctl enable real-time-fund fund-switch-server

# 5. 健康检查
curl -fsS http://127.0.0.1:3000/__health   # ok
curl -fsS http://127.0.0.1:3010/status     # JSON 状态
```

## 注意事项

- 单元文件内的绝对路径 /home/ubuntu/apps/real-time-fund 必须与 clone 路径一致，否则需修改单元后 daemon-reload。
- scripts/.switch-token 是总开关接口令牌，不随仓库分发；恢复后需重新放置（chmod 600）。
- 主 Caddy 反代配置（/etc/caddy/Caddyfile）独立于本仓库，按 DEPLOYMENT.md 中的路由恢复。
- 验证通过前不要删除旧目录；验证通过后再切换。
