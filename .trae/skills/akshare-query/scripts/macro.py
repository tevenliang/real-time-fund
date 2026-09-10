#!/usr/bin/env python3
"""宏观经济数据查询工具 - GDP/CPI/PMI/LPR/M2/贸易差额"""

from lib.formatter import to_markdown
import akshare as ak
import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


COMMANDS = {
    "gdp": ("中国GDP数据", lambda: ak.macro_china_gdp()),
    "cpi": ("中国CPI数据", lambda: ak.macro_china_cpi()),
    "pmi": ("中国PMI数据", lambda: ak.macro_china_pmi()),
    "lpr": ("贷款市场报价利率", lambda: ak.macro_china_lpr()),
    "m2": ("M2货币供应量", lambda: ak.macro_china_m2_yearly()),
    "trade": ("贸易差额数据", lambda: ak.macro_china_trade_balance()),
}


def main():
    parser = argparse.ArgumentParser(description="宏观经济数据查询")
    subparsers = parser.add_subparsers(dest="command")
    for name, (desc, _) in COMMANDS.items():
        p = subparsers.add_parser(name, help=desc)
        p.add_argument("--limit", type=int, default=20, help="返回行数限制")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        _, fetch = COMMANDS[args.command]
        df = fetch()
        print(to_markdown(df, limit=args.limit))
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
