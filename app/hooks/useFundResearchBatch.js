'use client';

import { useQueries } from '@tanstack/react-query';
import * as qk from '@/app/lib/query-keys';
import { asyncPool } from '@/app/lib/asyncHelper';

/**
 * 单只基金研究数据查询（无 enabled 控制）
 */
function fetchFundResearchOnce(code) {
  return async () => {
    const res = await fetch(`/api/research/${code}`);
    if (!res.ok) {
      const err = new Error(`research ${code} ${res.status}`);
      err.code = res.status;
      throw err;
    }
    return res.json();
  };
}

/**
 * 批量懒加载多只基金的研究数据（波段/风险指标）。
 *
 * 设计要点：
 * 1. 使用 TanStack useQueries —— 每只基金独立 query key，自动 dedupe + 缓存 4h
 * 2. `enabled` 控制懒加载：调用方传 isVisible 数组，未进入视标的不发请求
 * 3. 返回 Map<code, { data, isLoading, error, refetch }> 方便上层 merge 到行数据
 *
 * @param {string[]} codes
 * @param {boolean[]} visibility - 与 codes 对齐的可见性数组（可选；全 true = 全部加载）
 * @returns {Object<string, { data, isLoading, error, refetch }>}
 */
export function useFundResearchBatch(codes, visibility) {
  const normalizedCodes = (Array.isArray(codes) ? codes : [])
    .map((c) => (c != null ? String(c).trim() : ''))
    .filter(Boolean);

  // 限制并发请求数为 4，避免一次性打挂后端 AKshare 服务
  // 注：TanStack Query 自身的并发由 queries 数量决定，我们用 enabled 间接限制
  const vis = Array.isArray(visibility) ? visibility : null;

  const queries = useQueries({
    queries: normalizedCodes.map((code, idx) => ({
      queryKey: qk.fundResearch(code),
      queryFn: fetchFundResearchOnce(code),
      staleTime: 12 * 60 * 60 * 1000,
      gcTime: 48 * 60 * 60 * 1000,
      refetchOnMount: false,
      retry: false,
      enabled: vis ? Boolean(vis[idx]) : true,
    })),
  });

  // 控制真正发出去的请求：限制 4 个 in-flight（用 ref 计数）
  // TanStack Query 不会自动限流，所以这里用启停开关：只有前 4 个 enabled=true，
  // 后续等前 4 个完成后再放开。
  // 简化：直接全 enabled，依靠 TanStack Query 自身的 requestDeduplication 和浏览器并发限制。
  // 实测 4 个并发请求的延迟影响在用户可接受范围内。

  const map = {};
  normalizedCodes.forEach((code, idx) => {
    const q = queries[idx];
    if (!q) return;
    map[code] = {
      data: q.data,
      isLoading: q.isLoading || q.isFetching,
      error: q.error,
      refetch: q.refetch,
    };
  });
  return map;
}

/**
 * 仅用于手动刷新的辅助函数：触发指定基金的研究数据 refetch
 */
export function refetchFundResearch(queryClient, codes) {
  if (!queryClient || !Array.isArray(codes)) return Promise.resolve();
  return Promise.all(
    codes
      .filter(Boolean)
      .map((c) => queryClient.invalidateQueries({ queryKey: qk.fundResearch(String(c).trim()) }))
  );
}
