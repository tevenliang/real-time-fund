#!/usr/bin/env python3
"""A股数据查询工具 - 实时行情、历史K线、个股信息、财务指标、板块、龙虎榜、资金流向"""

import akshare as ak
from lib.fallback import fetch_with_fallback
from lib.formatter import to_markdown
import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _infer_market(symbol):
    """根据股票代码推断市场：6→sh，0/3→sz，其余→bj"""
    if symbol.startswith("6"):
        return "sh"
    elif symbol.startswith("0") or symbol.startswith("3"):
        return "sz"
    return "bj"


def quotes(args):
    df = fetch_with_fallback(
        lambda: ak.stock_zh_a_spot_em(),
    )
    if args.symbol:
        df = df[df["代码"] == args.symbol]
        if df.empty:
            print(f"未找到股票代码: {args.symbol}", file=sys.stderr)
            sys.exit(1)
    if args.name:
        df = df[df["名称"].str.contains(args.name, na=False)]
        if df.empty:
            print(f"未找到匹配名称: {args.name}", file=sys.stderr)
            sys.exit(1)
    print(to_markdown(df, limit=args.limit))


def hist(args):
    df = fetch_with_fallback(
        lambda: ak.stock_zh_a_hist(
            symbol=args.symbol,
            period=args.period,
            start_date=args.start,
            end_date=args.end,
            adjust=args.adjust,
        ),
    )
    print(to_markdown(df, limit=args.limit))


def info(args):
    df = fetch_with_fallback(
        lambda: ak.stock_individual_info_em(symbol=args.symbol),
    )
    print(to_markdown(df, limit=None))


def finance(args):
    df = fetch_with_fallback(
        lambda: ak.stock_financial_analysis_indicator_em(symbol=args.symbol),
    )
    print(to_markdown(df, limit=args.limit))


def board(args):
    if args.action == "detail" and not args.name:
        print("错误: board detail 需要 --name 参数", file=sys.stderr)
        sys.exit(1)

    api_map = {
        ("list", "industry"): lambda: ak.stock_board_industry_name_em(),
        ("list", "concept"): lambda: ak.stock_board_concept_name_em(),
        ("detail", "industry"): lambda: ak.stock_board_industry_cons_em(symbol=args.name),
        ("detail", "concept"): lambda: ak.stock_board_concept_cons_em(symbol=args.name),
    }

    key = (args.action, args.type)
    df = fetch_with_fallback(api_map[key])
    print(to_markdown(df, limit=args.limit))


def lhb(args):
    if args.symbol:
        df = fetch_with_fallback(
            lambda: ak.stock_lhb_stock_detail_em(
                symbol=args.symbol,
                start_date="20200101",
                end_date="20991231",
            ),
        )
    else:
        date = args.date or datetime.now().strftime("%Y%m%d")
        df = fetch_with_fallback(
            lambda: ak.stock_lhb_detail_em(start_date=date, end_date=date),
        )
    print(to_markdown(df, limit=args.limit))


def fund_flow(args):
    market = _infer_market(args.symbol)
    df = fetch_with_fallback(
        lambda: ak.stock_individual_fund_flow(
            stock=args.symbol, market=market),
    )
    print(to_markdown(df, limit=args.limit))


def main():
    parser = argparse.ArgumentParser(description="A股数据查询")
    subparsers = parser.add_subparsers(dest="command")

    # quotes
    p_quotes = subparsers.add_parser("quotes", help="实时行情")
    p_quotes.add_argument("--symbol", help="股票代码，如 000001")
    p_quotes.add_argument("--name", help="股票名称关键字，如 茅台")
    p_quotes.add_argument("--limit", type=int, default=50, help="返回行数限制")

    # hist
    p_hist = subparsers.add_parser("hist", help="历史K线")
    p_hist.add_argument("--symbol", required=True, help="股票代码")
    p_hist.add_argument("--period", default="daily",
                        choices=["daily", "weekly", "monthly"], help="K线周期")
    p_hist.add_argument("--start", default="20240101", help="开始日期 YYYYMMDD")
    p_hist.add_argument("--end", default="20991231", help="结束日期 YYYYMMDD")
    p_hist.add_argument("--adjust", default="qfq",
                        choices=["qfq", "hfq", ""], help="复权方式")
    p_hist.add_argument("--limit", type=int, default=50, help="返回行数限制")

    # info
    p_info = subparsers.add_parser("info", help="个股基本信息")
    p_info.add_argument("--symbol", required=True, help="股票代码")

    # finance
    p_finance = subparsers.add_parser("finance", help="个股财务指标")
    p_finance.add_argument("--symbol", required=True, help="股票代码")
    p_finance.add_argument("--limit", type=int, default=20, help="返回行数限制")

    # board
    p_board = subparsers.add_parser("board", help="板块/行业查询")
    p_board.add_argument("--action", default="list",
                         choices=["list", "detail"], help="list=列出板块, detail=板块成分股")
    p_board.add_argument("--type", default="industry",
                         choices=["industry", "concept"], help="industry=行业, concept=概念")
    p_board.add_argument("--name", help="板块名称（detail 时必需）")
    p_board.add_argument("--limit", type=int, default=50, help="返回行数限制")

    # lhb
    p_lhb = subparsers.add_parser("lhb", help="龙虎榜")
    p_lhb.add_argument("--symbol", help="个股代码（查个股龙虎榜记录）")
    p_lhb.add_argument("--date", help="日期 YYYYMMDD（查全市场龙虎榜，默认当日）")
    p_lhb.add_argument("--limit", type=int, default=50, help="返回行数限制")

    # fund-flow
    p_ff = subparsers.add_parser("fund-flow", help="个股资金流向")
    p_ff.add_argument("--symbol", required=True, help="股票代码")
    p_ff.add_argument("--limit", type=int, default=50, help="返回行数限制")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        commands = {
            "quotes": quotes, "hist": hist, "info": info,
            "finance": finance, "board": board, "lhb": lhb, "fund-flow": fund_flow,
        }
        commands[args.command](args)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
