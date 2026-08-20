export const fetchFundValuationTrend = async (code, range = '3m') => {
if (typeof window === 'undefined' || typeof document === 'undefined') return [];
