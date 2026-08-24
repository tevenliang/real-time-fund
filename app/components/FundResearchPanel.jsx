'use client';
import { useFundResearch } from '@/app/hooks/useFundResearch';
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

export default function FundResearchPanel({ code }) {
  const research = useFundResearch(code);
  const analysis = useFundAnalysis(code);

  const data = research.data;
  const aData = analysis.data;

  if (research.isLoading) {
    return (
      <div className="py-8 text-center text-[var(--muted-foreground)] text-sm">
        <div className="animate-pulse">加载基金研究数据...</div>
      </div>
    );
  }

  if (research.error || !data?.signal) {
    return (
      <div className="py-8 text-center text-[var(--muted-foreground)] text-xs">
        数据加载失败，请检查网络后重试
      </div>
    );
  }

  const { signal, risk, perf, industries } = data;
  const technical = aData?.technical || {};
  const consecutive = technical.consecutive_trend;
  const benchmark = technical.benchmark_compare || {};

  return (
    <div className="space-y-4">
      {/* 波段信号 */}
      <div className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4">
        <div className="text-sm font-semibold mb-3 flex items-center gap-2">
          <span style={{ borderLeft: '3px solid #874EA9', paddingLeft: 8 }}>波段信号</span>
          {data.cached && <span className="text-xs px-1.5 py-0.5 rounded bg-[var(--muted)] text-[var(--muted-foreground)]">缓存</span>}
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
        <div className="text-xs text-[var(--muted-foreground)] mt-2 space-y-1">
          <p>综合分 = 250日分位×40% + RSI14×35% + BIAS20×25%</p>
          <p>· 250日分位：当前净值在近一年净值区间中的位置（越高越贵）</p>
          <p>· RSI14：近14日相对强弱指标（&gt;70 超买，&lt;30 超卖）</p>
          <p>· BIAS20：当前净值偏离20日均线的百分比（正=高于均线）</p>
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
              <div key={item.label} className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-3 text-center">
                <div className="text-base font-bold" style={{ color: item.color }}>{item.value}</div>
                <div className="text-xs text-[var(--muted-foreground)] mt-0.5">{item.label}</div>
              </div>
            ))}
          </div>
          <div className="text-xs text-[var(--muted-foreground)] mt-2 space-y-1">
            <p>· 最大回撤：历史最高点到最低点的最大跌幅（越小越抗跌）</p>
            <p>· 年化波动率：日收益率标准差×√252（越大波动越剧烈）</p>
            <p>· 夏普比率：(年化收益−无风险利率)/波动率（&gt;1 较好，&lt;0 收益不抵风险）</p>
          </div>
        </div>
      )}

      {/* 技术面信号 */}
      {(consecutive?.days > 0 || technical?.max_drawdown_current != null) && (
        <div className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4">
          <div className="text-sm font-semibold mb-3" style={{ borderLeft: '3px solid #874EA9', paddingLeft: 8 }}>
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
              <span style={{ color: ccolor(technical.max_drawdown_current) }}>
                {pct(technical.max_drawdown_current)}
              </span>
            </div>
          </div>
          <div className="text-xs text-[var(--muted-foreground)] mt-2 space-y-1">
            <p>· 连续趋势：从最新交易日往前的连续涨/跌天数（≥3 天才显示）</p>
            <p>· 当前回撤：最新净值相对历史最高净值的跌幅（负值，越接近0越接近高点）</p>
          </div>
        </div>
      )}

      {/* 超额收益 */}
      {(benchmark.ret_1y != null || benchmark.ret_3y != null) && (
        <div className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4">
          <div className="text-sm font-semibold mb-3" style={{ borderLeft: '3px solid #874EA9', paddingLeft: 8 }}>
            超额收益
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
          <div className="text-xs text-[var(--muted-foreground)] mt-2">
            · 超额收益 = 基金同期涨幅 − 沪深300 近似基准涨幅（正数=跑赢大盘）
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
