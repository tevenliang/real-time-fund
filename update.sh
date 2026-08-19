#!/bin/bash
# Real-time-fund 自部署更新脚本
# 自动获取 GitHub 最新 release tag 并同步 version 字段（绕过作者未更新 package.json 的 bug）
#
# 用法：./update.sh              # 拉最新 release → 重建 → 重启
#       ./update.sh --no-restart # 同上但不重启
set -e

APP_DIR=/home/ubuntu/apps/real-time-fund
REPO="hzm0321/real-time-fund"
cd "$APP_DIR"

echo "==> [1/6] 查 GitHub 最新 release..."
LATEST_TAG=$(curl -sL -m 30 "https://api.github.com/repos/$REPO/releases/latest" | python3 -c "import json,sys; print(json.load(sys.stdin)[\"tag_name\"])")
echo "       最新 release: $LATEST_TAG"

ZIP_URL="https://codeload.github.com/$REPO/zip/refs/tags/$LATEST_TAG"

echo "==> [2/6] 下载 $LATEST_TAG 源码..."
curl -sL -m 180 -o /tmp/rtf-update.zip "$ZIP_URL"

echo "==> [3/6] 解压..."
rm -rf /tmp/rtf-update
mkdir -p /tmp/rtf-update
cd /tmp/rtf-update
unzip -q /tmp/rtf-update.zip
NEW_DIR=$(ls -d */ | head -1)
echo "       解压到: /tmp/rtf-update/$NEW_DIR"

echo "==> [4/6] 同步新代码到部署目录（保留 .env）..."
cd "$APP_DIR"
[ -f .env ] && cp .env /tmp/rtf-update/.env.bak
rm -rf app components lib public instrumentation-client.js instrumentation.js next.config.js jsconfig.json \
       Dockerfile docker-compose.yml nginx.conf entrypoint.sh env.example package.json package-lock.json \
       postcss.config.mjs eslint.config.mjs eslint.config.mjs .dockerignore .eslintrc.json .prettierrc
cp -r /tmp/rtf-update/$NEW_DIR/. .
[ -f /tmp/rtf-update/.env.bak ] && mv /tmp/rtf-update/.env.bak .env

echo "==> [5/6] 强制同步 version 字段为最新 release tag（绕开作者未更新 package.json 的 bug）..."
python3 -c "
import json, re
tag = \"$LATEST_TAG\"
ver = re.sub(r\"^v\", \"\", tag)   # v2.7.1-pro → 2.7.1-pro
with open(\"package.json\") as f: d = json.load(f)
old = d[\"version\"]
d[\"version\"] = ver
with open(\"package.json\", \"w\") as f: json.dump(d, f, indent=2, ensure_ascii=False)
print(f\"       version: {old} → {ver}\")
"

if [ "$1" != "--no-restart" ]; then
  echo "==> [6/6] 重建镜像 + 重启容器..."
  docker compose build app 2>&1 | tail -3
  docker compose up -d
  sleep 8
  echo ""
  echo "===Health: $(docker inspect real-time-fund-app-1 --format '{{.State.Health.Status}}')"
  TITLE=$(curl -s --resolve www.aiflare.cloud:443:127.0.0.1 https://www.aiflare.cloud/ 2>/dev/null | grep -oE "基估宝 V[^\"<]*" | head -1)
  echo "===Title:  $TITLE"
fi
