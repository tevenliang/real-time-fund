#!/usr/bin/env python3
"""回填 Supabase fund_secid 表：从 doc/related_sector_secid.csv 读取。
用法: python3 backfill_fund_secid.py <SERVICE_ROLE_KEY>
依赖: pip install requests
"""
import sys, csv, requests

SUPABASE_URL = "https://lkmdydlrnpukpxkyagit.supabase.co"
CSV_PATH = "/home/ubuntu/apps/real-time-fund/doc/related_sector_secid.csv"

key = sys.argv[1] if len(sys.argv) > 1 else ""
if not key:
    print("请提供 service_role key")
    sys.exit(1)

headers = {
    "apikey": key,
    "Authorization": "Bearer " + key,
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates",
}

rows = []
with open(CSV_PATH, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for r in reader:
        sector = (r.get("related_sector") or "").strip()
        secid = (r.get("secid") or "").strip()
        if sector and secid:
            rows.append({"related_sector": sector, "secid": secid})

print(f"读取到 {len(rows)} 条")

# 分批 upsert
BATCH = 200
total_ok = 0
for i in range(0, len(rows), BATCH):
    chunk = rows[i:i+BATCH]
    resp = requests.post(f"{SUPABASE_URL}/rest/v1/fund_secid", headers=headers, json=chunk)
    if resp.status_code >= 400:
        print(f"批次 {i//BATCH} 失败: {resp.status_code} {resp.text[:200]}")
    else:
        total_ok += len(chunk)
        print(f"批次 {i//BATCH} 成功: {len(chunk)} 条")

print(f"完成，共写入 {total_ok} 条")
