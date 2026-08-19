'use client';
import { useQuery } from '@tanstack/react-query';

export function useFundResearch(code) {
  return useQuery({
    queryKey: ['fund-research', code],
    queryFn: async () => {
      const res = await fetch(`/api/research/${code}`, {
        signal: AbortSignal.timeout(20000), // 20s explicit timeout
      });
      if (!res.ok) throw new Error('failed');
      return res.json();
    },
    staleTime: 4 * 60 * 60 * 1000,  // 4h
    gcTime: 24 * 60 * 60 * 1000,
    retry: 0,  // no retry - show error immediately on failure
    enabled: !!code,
  });
}
