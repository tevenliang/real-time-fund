#!/usr/bin/env python3
"""DataFrame to Markdown table formatter."""

from tabulate import tabulate


def to_markdown(df, limit=50):
    """Convert a pandas DataFrame to a Markdown table string.

    Args:
        df: pandas DataFrame to format.
        limit: Maximum number of rows to include. None for all rows.

    Returns:
        Markdown table string.
    """
    if df is None or df.empty:
        return "（无数据）"

    if limit and len(df) > limit:
        df = df.head(limit)

    return tabulate(df, headers="keys", tablefmt="pipe", showindex=False)
