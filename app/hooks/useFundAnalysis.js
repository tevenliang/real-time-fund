'use client';
import { useQuery } from '@tanstack/react-query';

const fundAnalysisKey = (code) => ['fund-analysis', String(code || '').trim()];

export function useFundAnalysis(code) {
  return useQuery({
    queryKey: fundAnalysisKey(code),
    queryFn: async () => {
      const res = await fetch(`/api/analysis/${String(code).trim()}`, {
        signal: AbortSignal.timeout(25000),
      });
      if (!res.ok) throw new Error(`analysis ${res.status}`);
      return res.json();
    },
    staleTime: 4 * 60 * 60 * 1000,
    gcTime: 24 * 60 * 60 * 1000,
    retry: 0,
    enabled: !!code,
  });
}
