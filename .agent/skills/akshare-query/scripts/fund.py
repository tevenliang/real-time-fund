#!/usr/bin/env python3
"""基金数据查询工具 - ETF行情、基金排名、基金净值、基金信息、持仓、分红"""

import akshare as ak
from lib.fallback import fetch_with_fallback
from lib.formatter import to_markdown
import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _find_column(df, candidates):
    """在 DataFrame 中查找第一个匹配的列名。"""
    for col in candidates:
        if col in df.columns:
            return col
    return None


def etf(args):
    df = fetch_with_fallback(
        lambda: ak.fund_etf_spot_em(),
        lambda: ak.fund_etf_spot_ths(),
    )
    if args.symbol:
        code_col = _find_column(df, ["代码", "基金代码"])
        if code_col:
            df = df[df[code_col] == args.symbol]
        if df.empty:
            print(f"未找到ETF代码: {args.symbol}", file=sys.stderr)
            sys.exit(1)
    if args.name:
        name_col = _find_column(df, ["名称", "基金简称"])
        if name_col:
            df = df[df[name_col].str.contains(args.name, na=False)]
        if df.empty:
            print(f"未找到匹配名称: {args.name}", file=sys.stderr)
            sys.exit(1)
    print(to_markdown(df, limit=args.limit))


def rank(args):
    df = fetch_with_fallback(
        lambda: ak.fund_open_fund_rank_em(symbol=args.type),
    )
    print(to_markdown(df, limit=args.limit))


def nav(args):
    df = fetch_with_fallback(
        lambda: ak.fund_open_fund_info_em(
            symbol=args.symbol, indicator="单位净值走势"),
    )
    print(to_markdown(df, limit=args.limit))


def info(args):
    df = fetch_with_fallback(
        lambda: ak.fund_individual_basic_info_xq(symbol=args.symbol),
        lambda: ak.fund_open_fund_info_em(
            symbol=args.symbol, indicator="单位净值走势"),
    )
    print(to_markdown(df, limit=None))


def portfolio(args):
    year = args.year or str(datetime.now().year)
    df = fetch_with_fallback(
        lambda: ak.fund_portfolio_hold_em(symbol=args.symbol, date=year),
    )
    print(to_markdown(df, limit=args.limit))


def dividend(args):
    if args.symbol:
        df = fetch_with_fallback(
            lambda: ak.fund_open_fund_info_em(
                symbol=args.symbol, indicator="分红送配详情"),
        )
    else:
        df = fetch_with_fallback(
            lambda: ak.fund_fh_rank_em(),
        )
    print(to_markdown(df, limit=args.limit))


def main():
    parser = argparse.ArgumentParser(description="基金数据查询")
    subparsers = parser.add_subparsers(dest="command")

    p_etf = subparsers.add_parser("etf", help="ETF实时行情")
    p_etf.add_argument("--symbol", help="ETF代码，如 510300")
    p_etf.add_argument("--name", help="ETF名称关键字，如 沪深300")
    p_etf.add_argument("--limit", type=int, default=50, help="返回行数限制")

    p_rank = subparsers.add_parser("rank", help="开放式基金排名")
    p_rank.add_argument("--type", default="全部",
                        help="基金类型: 全部/股票型/混合型/债券型/指数型/QDII")
    p_rank.add_argument("--limit", type=int, default=50, help="返回行数限制")

    p_nav = subparsers.add_parser("nav", help="基金净值")
    p_nav.add_argument("--symbol", required=True, help="基金代码，如 110011")
    p_nav.add_argument("--limit", type=int, default=50, help="返回行数限制")

    p_info = subparsers.add_parser("info", help="基金基本信息")
    p_info.add_argument("--symbol", required=True, help="基金代码，如 110011")

    p_portfolio = subparsers.add_parser("portfolio", help="基金持仓（十大重仓）")
    p_portfolio.add_argument("--symbol", required=True, help="基金代码，如 110011")
    p_portfolio.add_argument("--year", help="年份，如 2024，默认当年")
    p_portfolio.add_argument("--limit", type=int, default=10, help="返回行数限制")

    p_dividend = subparsers.add_parser("dividend", help="基金分红历史")
    p_dividend.add_argument("--symbol", help="基金代码（可选，不传则查全市场分红排名）")
    p_dividend.add_argument("--limit", type=int, default=50, help="返回行数限制")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        commands = {
            "etf": etf, "rank": rank, "nav": nav,
            "info": info, "portfolio": portfolio, "dividend": dividend,
        }
        commands[args.command](args)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
