#!/usr/bin/env python3
"""新闻数据查询工具 - 个股新闻资讯与公告"""

from lib.formatter import to_markdown
import akshare as ak
import argparse
from curl_cffi import requests
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def fetch_stock_notices(symbol: str, page_size: int = 10, page_index: int = 1):
    """
    查询个股公告信息（东方财富公告接口）

    Args:
        symbol: 股票代码，如 002452
        page_size: 每页条数，默认10
        page_index: 页码，默认1

    Returns:
        pandas DataFrame 包含公告信息
    """
    import json
    import time

    url = "https://search-api-web.eastmoney.com/search/jsonp"

    # 构造 inner_param，与用户提供的参数格式一致
    inner_param = {
        "uid": "",
        "keyword": symbol,
        "type": ["noticeWeb"],
        "client": "web",
        "clientType": "web",
        "clientVersion": "curr",
        "param": {
            "noticeWeb": {
                "preTag": "<em class=\"red\">",
                "postTag": "</em>",
                "pageSize": page_size,
                "pageIndex": page_index
            }
        }
    }

    timestamp = int(time.time() * 1000)
    params = {
        "cb": f"jQuery35101792940631092459_{timestamp}",
        "param": json.dumps(inner_param, ensure_ascii=False),
        "_": str(timestamp + 1)
    }

    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en,zh-CN;q=0.9,zh;q=0.8",
        "cache-control": "no-cache",
        "connection": "keep-alive",
        "pragma": "no-cache",
        "referer": f"https://so.eastmoney.com/notice/s?keyword={symbol}",
        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "script",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
    }

    response = requests.get(
        url, params=params, headers=headers, timeout=30, impersonate="chrome120")
    response.raise_for_status()

    # 解析 JSONP 响应
    data_text = response.text
    callback = params["cb"]
    data_json = json.loads(data_text.strip(f"{callback}(")[:-1])

    # 解析公告数据
    notices = []
    if "result" in data_json and "noticeWeb" in data_json["result"]:
        for item in data_json["result"]["noticeWeb"]:
            title = item.get("title", "").replace(
                '<em class="red">', '').replace('</em>', '')
            # 从 title 中提取股票名称（格式："股票名称:公告标题"）
            name = ""
            if ":" in title:
                name = title.split(":")[0]
            notices.append({
                "公告标题": title,
                "公告日期": item.get("date", "").split()[0] if item.get("date") else "",
                "股票名称": item.get("securityFullName", name),
                "链接": item.get("url", "")
            })

    df = pd.DataFrame(notices)
    return df


def main():
    parser = argparse.ArgumentParser(description="个股新闻/公告查询")
    parser.add_argument("--symbol", required=True, help="股票代码，如 000001")
    parser.add_argument("--type", choices=["news", "notice"], default="news",
                        help="查询类型: news(新闻,默认)/notice(公告)")
    parser.add_argument("--limit", type=int, default=10, help="返回条数限制")

    args = parser.parse_args()

    try:
        if args.type == "notice":
            # 查询公告
            df = fetch_stock_notices(symbol=args.symbol, page_size=args.limit)
        else:
            # 查询新闻
            df = ak.stock_news_em(symbol=args.symbol)
            if "content" in df.columns:
                df = df.drop(columns=["content"])

        print(to_markdown(df, limit=args.limit))
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
