'use client';
import { useFundResearch } from '@/app/hooks/useFundResearch';

function ccolor(v) {
  if (v == null) return 'var(--foreground)';
  const n = parseFloat(v);
  if (isNaN(n)) return 'var(--foreground)';
  return n > 0 ? '#c0392b' : n < 0 ? '#1e8449' : 'var(--muted-foreground)';
}

function pct(v) {
  if (v == null) return '—';
  const n = parseFloat(v);
  if (isNaN(n)) return '—';
  return `${n > 0 ? '+' : ''}${n.toFixed(2)}%`;
}

function kpiCard(label, value, color) {
  return `<div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-3 text-center">
    <div class="text-base font-bold" style="color:${color || 'var(--foreground)'}">${value}</div>
    <div class="text-xs text-[var(--muted-foreground)] mt-0.5">${label}</div>
  </div>`;
}

export default function FundResearchPanel({ code }) {
  const { data, isLoading, error } = useFundResearch(code);

  if (isLoading) {
    return (
      <div className="py-8 text-center text-[var(--muted-foreground)] text-sm">
        <div className="animate-pulse">加载基金研究数据...</div>
      </div>
    );
  }

  if (error || !data?.signal) {
    return (
      <div className="py-8 text-center text-[var(--muted-foreground)] text-xs">
        数据加载失败，请检查网络后重试
      </div>
    );
  }

  const { signal, risk, perf, industries, fund_name, cached } = data;

  return (
    <div className="space-y-4">
      {/* 波段信号 */}
      <div className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4">
        <div className="text-sm font-semibold mb-3 flex items-center gap-2">
          <span style={{ borderLeft: '3px solid #874EA9', paddingLeft: 8 }}>波段信号</span>
          {cached && <span className="text-xs px-1.5 py-0.5 rounded bg-[var(--muted)] text-[var(--muted-foreground)]">缓存</span>}
        </div>
        <div className="flex items-center gap-3 mb-3">
          <span className="text-3xl font-bold" style={{ color: signal.zone_color }}>
            {signal.score}
          </span>
          <div>
            <div className="font-semibold text-sm" style={{ color: signal.zone_color }}>
              {signal.zone}
            </div>
            <div className="text-xs text-[var(--muted-foreground)]">
              建议：{signal.advice}
            </div>
          </div>
        </div>
        {/* 分项条 */}
        <div className="space-y-2">
          {[
            { label: '250日分位', value: signal.pct, max: 100 },
            { label: 'RSI14', value: signal.rsi, max: 100 },
            { label: 'BIAS20', value: signal.bias, max: 10, offset: 50 },
          ].map(item => {
            const pct_val = item.offset != null
              ? Math.min(100, Math.max(0, item.value + item.offset))
              : Math.min(100, item.value);
            const displayVal = item.offset != null
              ? `${item.value > 0 ? '+' : ''}${item.value}`
              : item.value;
            return (
              <div key={item.label} className="flex items-center gap-2 text-xs">
                <span className="w-20 text-right text-[var(--muted-foreground)]">{item.label}</span>
                <div className="flex-1 bg-[var(--muted)] rounded h-2 overflow-hidden">
                  <div
                    className="h-full rounded transition-all"
                    style={{ width: `${pct_val}%`, background: '#874EA9' }}
                  />
                </div>
                <span className="w-12 text-right">{displayVal}</span>
              </div>
            );
          })}
        </div>
        <div className="text-xs text-[var(--muted-foreground)] mt-2">
          综合分 = 250日分位×40% + RSI14×35% + BIAS20×25%
        </div>
      </div>

      {/* 风险指标 */}
      {risk && (
        <div className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4">
          <div className="text-sm font-semibold mb-3" style={{ borderLeft: '3px solid #874EA9', paddingLeft: 8 }}>
            风险分析
          </div>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: '成立来收益', value: pct(risk.total_ret), color: ccolor(risk.total_ret) },
              { label: '年化收益', value: pct(risk.cagr), color: ccolor(risk.cagr) },
              { label: '最大回撤', value: pct(risk.mdd), color: '#1e8449' },
              { label: '年化波动率', value: pct(risk.vol), color: '#b9770e' },
              { label: '夏普比率', value: risk.sharpe?.toFixed(2) ?? '—', color: '#874EA9' },
              { label: '今年来', value: pct(perf?.今年来), color: ccolor(perf?.今年来) },
            ].map(item => (
              <div key={item.label} dangerouslySetInnerHTML={{ __html: kpiCard(item.label, item.value, item.color) }} />
            ))}
          </div>
        </div>
      )}

      {/* 行业配置 */}
      {industries?.length > 0 && (
        <div className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4">
          <div className="text-sm font-semibold mb-3" style={{ borderLeft: '3px solid #874EA9', paddingLeft: 8 }}>
            行业配置
          </div>
          {(() => {
            const max = Math.max(...industries.map(i => i.pct));
            return (
              <div className="space-y-2">
                {industries.map((ind, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-xs">
                    <span className="w-16 text-right truncate text-[var(--muted-foreground)]">{ind.name}</span>
                    <div className="flex-1 bg-[var(--muted)] rounded h-2.5 overflow-hidden">
                      <div
                        className="h-full rounded"
                        style={{ width: `${(ind.pct / max) * 100}%`, background: '#874EA9' }}
                      />
                    </div>
                    <span className="w-14 text-right">{ind.pct.toFixed(2)}%</span>
                  </div>
                ))}
              </div>
            );
          })()}
          <div className="text-xs text-[var(--muted-foreground)] mt-2">数据来源: 东方财富(季报，存在滞后)</div>
        </div>
      )}

      <div className="text-xs text-[var(--muted-foreground)] text-center">
        AKshare · 仅供参考，不构成投资建议
      </div>
    </div>
  );
}
