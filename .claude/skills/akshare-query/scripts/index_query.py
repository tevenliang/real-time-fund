#!/usr/bin/env python3
"""指数数据查询工具 - A股指数、全球指数、成分股"""

from lib.formatter import to_markdown
import akshare as ak
import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def a_share(args):
    df = ak.stock_zh_index_spot_em(symbol="沪深重要指数")
    print(to_markdown(df, limit=args.limit))


def global_index(args):
    df = ak.index_global_spot_em()
    print(to_markdown(df, limit=args.limit))


def constituents(args):
    if not args.symbol:
        print("错误: constituents 命令需要 --symbol 参数", file=sys.stderr)
        sys.exit(1)
    df = ak.index_stock_cons_weight_csindex(symbol=args.symbol)
    print(to_markdown(df, limit=args.limit))


def main():
    parser = argparse.ArgumentParser(description="指数数据查询")
    subparsers = parser.add_subparsers(dest="command")

    p_ashare = subparsers.add_parser("a-share", help="A股主要指数")
    p_ashare.add_argument("--limit", type=int, default=50, help="返回行数限制")

    p_global = subparsers.add_parser("global", help="全球指数")
    p_global.add_argument("--limit", type=int, default=50, help="返回行数限制")

    p_cons = subparsers.add_parser("constituents", help="指数成分股")
    p_cons.add_argument("--symbol", required=True, help="指数代码，如 000300")
    p_cons.add_argument("--limit", type=int, default=50, help="返回行数限制")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        {"a-share": a_share, "global": global_index,
            "constituents": constituents}[args.command](args)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
