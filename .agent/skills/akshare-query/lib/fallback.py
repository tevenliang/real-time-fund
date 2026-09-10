#!/usr/bin/env python3
"""通用数据源 fallback 工具 - 支持多数据源自动切换和重试。"""

import sys
import time

import pandas as pd


def fetch_with_fallback(*api_calls, retry=1):
    """依次尝试多个数据源，返回第一个成功且非空的 DataFrame。

    Args:
        *api_calls: 无参 callable，按优先级排序，如 lambda: ak.func()
        retry: 每个数据源的最大尝试次数，默认 1
    Returns:
        pd.DataFrame
    Raises:
        最后一个数据源的异常（若全部失败）
    """
    last_exc = None
    total = len(api_calls)

    for i, call in enumerate(api_calls, 1):
        for attempt in range(1, retry + 1):
            try:
                df = call()
                if df is not None and not df.empty:
                    return df
            except Exception as e:
                last_exc = e
                if attempt < retry:
                    time.sleep(0.5)
                    continue
                break

        if i < total:
            src_info = f"数据源[{i}]失败"
            if last_exc:
                src_info += f"({last_exc})"
            print(f"{src_info}，切换备用源...", file=sys.stderr)

    if last_exc:
        raise last_exc
    return pd.DataFrame()
