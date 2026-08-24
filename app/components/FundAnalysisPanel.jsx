'use client';
import { useFundAnalysis } from '@/app/hooks/useFundAnalysis';

function ccolor(v) {
  if (v == null) return 'var(--foreground)';
  const n = parseFloat(v);
  if (isNaN(n)) return 'var(--foreground)';
  return n > 0 ? '#c0392b' : n < 0 ? '#1e8449' : 'var(--muted-foreground)';
}

function pct(v, digits = 2) {
  if (v == null) return '—';
  const n = parseFloat(v);
  if (isNaN(n)) return '—';
  return `${n > 0 ? '+' : ''}${n.toFixed(digits)}%`;
}

const ZONE_COLORS = {
  '优秀': '#1e8449',
  '良好': '#27ae60',
  '中性': '#b9770e',
  '偏弱': '#c0392b',
};

export default function FundAnalysisPanel({ code }) {
  const { data, isLoading, error } = useFundAnalysis(code);

  if (isLoading) {
    return (
      <div className="py-8 text-center text-[var(--muted-foreground)] text-sm">
        <div className="animate-pulse">生成深度分析报告...</div>
      </div>
    );
  }

  if (error || !data || data.error) {
    return (
      <div className="py-8 text-center text-[var(--muted-foreground)] text-xs">
        {data?.error || '分析数据加载失败，请稍后重试'}
      </div>
    );
  }

  const {
    fund_name,
    perf,
    risk,
    signal,
    industries,
    industry_summary,
    technical,
    style_tags,
    overall,
  } = data;

  const zoneColor = ZONE_COLORS[overall?.zone] || 'var(--muted-foreground)';
  const consecutive = technical?.consecutive_trend;
  const benchmark = technical?.benchmark_compare || {};

  return (
    <div className="space-y-4">
      {/* 综合评分 */}
      <div className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4">
        <div
          className="text-sm font-semibold mb-3"
          style={{ borderLeft: '3px solid #874EA9', paddingLeft: 8 }}
        >
          综合评分
        </div>
        <div className="flex items-center gap-4">
          <div className="text-center">
            <div
              className="text-4xl font-bold leading-none"
              style={{ color: zoneColor }}
            >
              {overall?.score?.toFixed(0) ?? '—'}
            </div>
            <div
              className="text-xs font-medium mt-1 px-2 py-0.5 rounded-full inline-block"
              style={{ color: zoneColor, background: `${zoneColor}15` }}
            >
              {overall?.zone}
            </div>
          </div>
          <div className="flex-1 space-y-2">
            {[
              { label: '波段信号', value: overall?.breakdown?.signal },
              { label: '风险调整', value: overall?.breakdown?.risk_adjusted },
              { label: '分散度', value: overall?.breakdown?.diversification },
              { label: '超额收益', value: overall?.breakdown?.excess_return },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-2 text-xs">
                <span className="w-16 text-right text-[var(--muted-foreground)]">
                  {item.label}
                </span>
                <div className="flex-1 bg-[var(--muted)] rounded h-2 overflow-hidden">
                  <div
                    className="h-full rounded transition-all"
                    style={{ width: `${Math.min(100, item.value ?? 50)}%`, background: '#874EA9' }}
                  />
                </div>
                <span className="w-10 text-right">{item.value ?? '—'}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 风格标签 */}
      {style_tags?.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {style_tags.map((tag) => (
            <span
              key={tag}
              className="px-3 py-1 rounded-full text-xs font-medium"
              style={{
                background: 'color-mix(in srgb, #874EA9 12%, transparent)',
                color: '#874EA9',
                border: '1px solid color-mix(in srgb, #874EA9 25%, transparent)',
              }}
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* 基准对比 */}
      {(benchmark.ret_1y != null || benchmark.ret_3y != null) && (
        <div className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4">
          <div
            className="text-sm font-semibold mb-3"
            style={{ borderLeft: '3px solid #874EA9', paddingLeft: 8 }}
          >
            超额收益（vs 沪深300 近似基准）
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-[var(--muted)] rounded-xl p-3">
              <div className="text-xs text-[var(--muted-foreground)] mb-1">近1年</div>
              <div className="font-bold" style={{ color: ccolor(benchmark.ret_1y) }}>
                {pct(benchmark.ret_1y)}
              </div>
              <div className="text-xs mt-1" style={{ color: ccolor(benchmark.excess_1y) }}>
                超额 {pct(benchmark.excess_1y)}
              </div>
            </div>
            <div className="bg-[var(--muted)] rounded-xl p-3">
              <div className="text-xs text-[var(--muted-foreground)] mb-1">近3年</div>
              <div className="font-bold" style={{ color: ccolor(benchmark.ret_3y) }}>
                {pct(benchmark.ret_3y)}
              </div>
              <div className="text-xs mt-1" style={{ color: ccolor(benchmark.excess_3y) }}>
                超额 {pct(benchmark.excess_3y)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 技术面 */}
      <div className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4">
        <div
          className="text-sm font-semibold mb-3"
          style={{ borderLeft: '3px solid #874EA9', paddingLeft: 8 }}
        >
          技术面信号
        </div>
        <div className="space-y-2 text-xs">
          <div className="flex justify-between items-center py-1">
            <span className="text-[var(--muted-foreground)]">连续趋势</span>
            <span className="font-medium">
              {consecutive?.type && consecutive?.days > 0
                ? `连续${consecutive.type === 'up' ? '上涨' : '下跌'} ${consecutive.days} 天`
                : '无明确趋势'}
            </span>
          </div>
          <div className="flex justify-between items-center py-1">
            <span className="text-[var(--muted-foreground)]">当前回撤</span>
            <span style={{ color: ccolor(technical?.max_drawdown_current) }}>
              {pct(technical?.max_drawdown_current)}
            </span>
          </div>
          {signal?.rsi != null && (
            <div className="flex justify-between items-center py-1">
              <span className="text-[var(--muted-foreground)]">RSI14</span>
              <span>{signal.rsi}</span>
            </div>
          )}
          {signal?.bias != null && (
            <div className="flex justify-between items-center py-1">
              <span className="text-[var(--muted-foreground)]">BIAS20</span>
              <span>{signal.bias > 0 ? '+' : ''}{signal.bias}%</span>
            </div>
          )}
        </div>
      </div>

      {/* 行业集中度 */}
      {industry_summary && industries?.length > 0 && (
        <div className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4">
          <div
            className="text-sm font-semibold mb-3"
            style={{ borderLeft: '3px solid #874EA9', paddingLeft: 8 }}
          >
            行业集中度
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between items-center py-1">
              <span className="text-[var(--muted-foreground)]">前三大行业占比</span>
              <span className="font-medium">{industry_summary.top3_concentration}%</span>
            </div>
            <div className="flex justify-between items-center py-1">
              <span className="text-[var(--muted-foreground)]">披露行业总数</span>
              <span>{industries.length}</span>
            </div>
            <div className="flex justify-between items-center py-1">
              <span className="text-[var(--muted-foreground)]">行业覆盖合计</span>
              <span>{industry_summary.total}%</span>
            </div>
          </div>
          <div className="mt-3 space-y-1.5">
            {industries.slice(0, 5).map((ind) => (
              <div key={ind.name} className="flex items-center gap-2 text-xs">
                <span className="w-20 truncate text-right text-[var(--muted-foreground)]">
                  {ind.name}
                </span>
                <div className="flex-1 bg-[var(--muted)] rounded h-2 overflow-hidden">
                  <div
                    className="h-full rounded"
                    style={{
                      width: `${(ind.pct / Math.max(...industries.map((i) => i.pct))) * 100}%`,
                      background: '#874EA9',
                    }}
                  />
                </div>
                <span className="w-14 text-right">{ind.pct.toFixed(2)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 阶段涨幅 */}
      {perf && Object.keys(perf).length > 0 && (
        <div className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4">
          <div
            className="text-sm font-semibold mb-3"
            style={{ borderLeft: '3px solid #874EA9', paddingLeft: 8 }}
          >
            阶段涨幅
          </div>
          <div className="grid grid-cols-4 gap-2 text-center text-xs">
            {[
              ['近1周', perf['近1周']],
              ['近1月', perf['近1月']],
              ['近3月', perf['近3月']],
              ['近6月', perf['近6月']],
              ['近1年', perf['近1年']],
              ['近3年', perf['近3年']],
              ['今年来', perf['今年来']],
              ['成立来', perf['成立来']],
            ].map(([label, val]) => (
              <div key={label} className="bg-[var(--muted)] rounded-lg p-2">
                <div className="text-[var(--muted-foreground)] text-[10px] mb-0.5">{label}</div>
                <div className="font-semibold" style={{ color: ccolor(val) }}>
                  {val != null ? pct(val, 1) : '—'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="text-xs text-[var(--muted-foreground)] text-center">
        综合评分 = 波段40% + 风险调整30% + 分散度15% + 超额收益15%
        <br />
        AKshare · 仅供参考，不构成投资建议
      </div>
    </div>
  );
}
