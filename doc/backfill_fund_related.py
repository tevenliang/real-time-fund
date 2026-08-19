#!/usr/bin/env python3
"""回填 Supabase fund_related 表：从本地持仓导出 JSON 读取每只基金的 relatedSector。
只灌"名称型"板块（非 BK 开头 ID）；BK 开头的是板块 ID，无法映射为名称，交由前端显示。
用法: python3 backfill_fund_related.py <SERVICE_ROLE_KEY> <JSON路径>
"""
import sys, json, re, requests

SUPABASE_URL = "https://lkmdydlrnpukpxkyagit.supabase.co"

key = sys.argv[1] if len(sys.argv) > 1 else ""
json_path = sys.argv[2] if len(sys.argv) > 2 else "/Users/tianwenliang/Documents/agent_spaces/fund/持仓导出_基估宝.json"
if not key:
    print("请提供 service_role key")
    sys.exit(1)

with open(json_path, encoding="utf-8") as f:
    data = json.load(f)
funds = data.get("funds", data) if isinstance(data, dict) else data

rows = []
skip_bk = 0
for fund in funds:
    code = str(fund.get("code", "")).strip()
    rs = fund.get("relatedSector")
    if not code or not rs:
        continue
    rs = str(rs).strip()
    # 跳过 BK 开头的板块 ID
    if re.match(r"^BK\d+$", rs):
        skip_bk += 1
        continue
    if rs:
        rows.append({"fund_code": code, "related_sector": rs})

print(f"读取 {len(funds)} 只基金，可回填 {len(rows)} 条（跳过 BK-ID {skip_bk} 条）")

headers = {
    "apikey": key,
    "Authorization": "Bearer " + key,
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates",
}

BATCH = 100
total_ok = 0
for i in range(0, len(rows), BATCH):
    chunk = rows[i:i+BATCH]
    resp = requests.post(f"{SUPABASE_URL}/rest/v1/fund_related", headers=headers, json=chunk)
    if resp.status_code >= 400:
        print(f"批次 {i//BATCH} 失败: {resp.status_code} {resp.text[:200]}")
    else:
        total_ok += len(chunk)
        print(f"批次 {i//BATCH} 成功: {len(chunk)} 条")

print(f"完成，共写入 {total_ok} 条")
