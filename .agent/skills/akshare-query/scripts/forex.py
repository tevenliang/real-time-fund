#!/usr/bin/env python3
"""外汇数据查询工具 - 实时汇率、中行牌价"""

from lib.formatter import to_markdown
import akshare as ak
import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def spot(args):
    df = ak.forex_spot_em()
    print(to_markdown(df, limit=args.limit))


def boc(args):
    df = ak.currency_boc_sina(symbol=args.symbol)
    print(to_markdown(df, limit=args.limit))


def main():
    parser = argparse.ArgumentParser(description="外汇数据查询")
    subparsers = parser.add_subparsers(dest="command")

    p_spot = subparsers.add_parser("spot", help="实时外汇行情")
    p_spot.add_argument("--limit", type=int, default=50, help="返回行数限制")

    p_boc = subparsers.add_parser("boc", help="中国银行外汇牌价")
    p_boc.add_argument("--symbol", default="美元", help="币种名称，如 美元、欧元、英镑")
    p_boc.add_argument("--limit", type=int, default=20, help="返回行数限制")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        {"spot": spot, "boc": boc}[args.command](args)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
