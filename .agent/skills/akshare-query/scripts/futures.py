#!/usr/bin/env python3
"""期货数据查询工具 - 现货价格、库存数据"""

from lib.formatter import to_markdown
import akshare as ak
import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def spot(args):
    date = args.date or datetime.now().strftime("%Y%m%d")
    df = ak.futures_spot_price(date=date)
    print(to_markdown(df, limit=args.limit))


def inventory(args):
    if not args.symbol:
        print("错误: inventory 命令需要 --symbol 参数", file=sys.stderr)
        sys.exit(1)
    df = ak.futures_inventory_em(symbol=args.symbol)
    print(to_markdown(df, limit=args.limit))


def main():
    parser = argparse.ArgumentParser(description="期货数据查询")
    subparsers = parser.add_subparsers(dest="command")

    p_spot = subparsers.add_parser("spot", help="期货现货价格")
    p_spot.add_argument("--date", help="日期 YYYYMMDD，默认今天")
    p_spot.add_argument("--limit", type=int, default=50, help="返回行数限制")

    p_inv = subparsers.add_parser("inventory", help="期货库存数据")
    p_inv.add_argument("--symbol", required=True, help="品种名称，如 铜、铝、螺纹钢")
    p_inv.add_argument("--limit", type=int, default=50, help="返回行数限制")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        {"spot": spot, "inventory": inventory}[args.command](args)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
