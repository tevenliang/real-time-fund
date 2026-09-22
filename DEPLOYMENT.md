# DEPLOYMENT.md — 基估宝 (real-time-fund) 部署说明

本仓库包含可运行源码：Next.js 前端（静态导出到 out/）与总开关控制服务（Python）。
运行时数据来自 Supabase（托管），不在本仓库内。

## 所需环境变量（名称，值从外部 runtime.env 提供，严禁提交真实值）

- NEXT_PUBLIC_SUPABASE_URL
- NEXT_PUBLIC_SUPABASE_ANON_KEY
- NEXT_PUBLIC_WEB3FORMS_ACCESS_KEY
- NEXT_PUBLIC_GA_ID
- NEXT_PUBLIC_GITHUB_LATEST_RELEASE_URL
- NEXT_PUBLIC_IS_GITHUB_LOGIN
- ENCRYPTION_KEY

完整字段说明见 env.example。构建时 NEXT_PUBLIC_* 会注入静态产物；
运行时密钥集中存放在 /home/ubuntu/.config/real-time-fund/runtime.env（chmod 600）。

## 依赖

- Node.js 18+（构建静态导出）
- Python 3（总开关服务，仅标准库）
- Caddy 2（专用实例 + 主实例反代）

## 从 GitHub 恢复部署到新服务器

```bash
# 1. 拉取源码
git clone git@github.com:tevenliang/real-time-fund.git /home/ubuntu/apps/real-time-fund
cd /home/ubuntu/apps/real-time-fund

# 2. 配置环境变量（按上面清单从 runtime.env 复制）
#    构建需要 NEXT_PUBLIC_*；ENCRYPTION_KEY 供总开关签名使用

# 3. 安装依赖并构建静态站点
npm ci
npm run build          # 生成 out/

# 4. 安装 systemd 单元（scripts/ 内已含单元文件模板）
sudo cp scripts/real-time-fund.service /etc/systemd/system/
sudo cp scripts/fund-switch-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now real-time-fund fund-switch-server
```

说明：scripts/real-time-fund.service 用专用 Caddy 实例服务 out/ 静态目录，仅监听
127.0.0.1:3000；scripts/fund-switch-server.service 启动总开关服务，监听 127.0.0.1:3010。
两单元均以绝对路径引用本目录，恢复时请保持路径一致。

## 主 Caddy 反代（/etc/caddy/Caddyfile，需独立恢复）

- /__switch/* → 127.0.0.1:3010（总开关）
- /api/research/*、/api/analysis/* → 127.0.0.1:18081（fund-research-internal.service，独立仓库）
- 其余路径 → 127.0.0.1:3000（本站）

## 健康检查

```bash
curl -fsS http://127.0.0.1:3000/__health   # 期望: ok
curl -fsS http://127.0.0.1:3010/status     # 期望: JSON 状态（含开关状态）
# 外网验证: https://域名/ 页面可访问、估值数据可查询
```
