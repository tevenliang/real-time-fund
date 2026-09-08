import { isBoolean, isFunction, isObject } from 'lodash';
import { create } from 'zustand';

/**
 * 本地配置状态 Zustand Store
 */
export const useSettingsStore = create((set) => ({
  tempSeconds: 60,
  containerWidth: 1200,
  showMarketIndexPc: true,
  showMarketIndexMobile: true,
  showGroupFundSearchPc: true,
  showGroupFundSearchMobile: true,
  dynamicStylePc: true,
  dynamicStyleMobile: true,
  showGroupDropdownPc: false,
  showGroupDropdownMobile: false,
  isGroupSummarySticky: false,

  setTempSeconds: (val) => set({ tempSeconds: isFunction(val) ? val(useSettingsStore.getState().tempSeconds) : val }),
  setContainerWidth: (val) =>
    set({ containerWidth: isFunction(val) ? val(useSettingsStore.getState().containerWidth) : val }),
  setShowMarketIndexPc: (val) =>
    set({ showMarketIndexPc: isFunction(val) ? val(useSettingsStore.getState().showMarketIndexPc) : val }),
  setShowMarketIndexMobile: (val) =>
    set({
      showMarketIndexMobile: isFunction(val) ? val(useSettingsStore.getState().showMarketIndexMobile) : val
    }),
  setShowGroupFundSearchPc: (val) =>
    set({
      showGroupFundSearchPc: isFunction(val) ? val(useSettingsStore.getState().showGroupFundSearchPc) : val
    }),
  setShowGroupFundSearchMobile: (val) =>
    set({
      showGroupFundSearchMobile: isFunction(val) ? val(useSettingsStore.getState().showGroupFundSearchMobile) : val
    }),
  setDynamicStylePc: (val) =>
    set({ dynamicStylePc: isFunction(val) ? val(useSettingsStore.getState().dynamicStylePc) : val }),
  setDynamicStyleMobile: (val) =>
    set({ dynamicStyleMobile: isFunction(val) ? val(useSettingsStore.getState().dynamicStyleMobile) : val }),
  setShowGroupDropdownPc: (val) =>
    set({
      showGroupDropdownPc: isFunction(val) ? val(useSettingsStore.getState().showGroupDropdownPc) : val
    }),
  setShowGroupDropdownMobile: (val) =>
    set({
      showGroupDropdownMobile: isFunction(val) ? val(useSettingsStore.getState().showGroupDropdownMobile) : val
    }),
  setIsGroupSummarySticky: (val) =>
    set({
      isGroupSummarySticky: isFunction(val) ? val(useSettingsStore.getState().isGroupSummarySticky) : val
    }),

  // 基估宝智能总开关（默认关闭，节省资源）
  // 持久化到 localStorage，页面刷新后恢复；UI 启动时由 page.jsx 调 /__switch/status 用后端真实状态覆盖
  fundEstimationEnabled: false,

  // 切换总开关（写本地 + localStorage 同步）
  toggleFundEstimation: (enabled) => {
    const next = isFunction(enabled) ? enabled(useSettingsStore.getState().fundEstimationEnabled) : enabled;
    if (typeof window !== 'undefined') {
      try { window.localStorage.setItem('fundEstimationEnabled', JSON.stringify(Boolean(next))); } catch (e) { /* ignore */ }
    }
    set({ fundEstimationEnabled: Boolean(next) });
  },

  // 强制启动（即使在非交易日也启动）
  forceStartFundEstimation: () => {
    if (typeof window !== 'undefined') {
      try { window.localStorage.setItem('fundEstimationEnabled', 'true'); } catch (e) { /* ignore */ }
    }
    set({ fundEstimationEnabled: true });
  },

  // 强制停止
  forceStopFundEstimation: () => {
    if (typeof window !== 'undefined') {
      try { window.localStorage.setItem('fundEstimationEnabled', 'false'); } catch (e) { /* ignore */ }
    }
    set({ fundEstimationEnabled: false });
  },

  // 用后端真实状态覆盖本地（页面 mount 时调一次，开关成功后用 server 返回的 active 校正）
  syncFundEstimationFromServer: (serverActive) => {
    if (typeof window !== 'undefined') {
      try { window.localStorage.setItem('fundEstimationEnabled', JSON.stringify(Boolean(serverActive))); } catch (e) { /* ignore */ }
    }
    set({ fundEstimationEnabled: Boolean(serverActive) });
  },

  /**
   * 从 customSettings 解析并同步配置到 Zustand 状态
   */
  syncFromCustomSettings: (customSettings) => {
    if (!customSettings || !isObject(customSettings)) return;
    try {
      const patch = {};
      const w = customSettings.pcContainerWidth;
      const num = Number(w);
      if (Number.isFinite(num)) {
        const maxWidth =
          typeof window !== 'undefined' && window.matchMedia('(max-width: 640px)').matches
            ? 99999
            : typeof window !== 'undefined'
              ? Math.max(window.innerWidth, 2000)
              : 1200;
        patch.containerWidth = Math.min(maxWidth, Math.max(600, num));
      }
      if (isBoolean(customSettings.showMarketIndexPc)) patch.showMarketIndexPc = customSettings.showMarketIndexPc;
      if (isBoolean(customSettings.showMarketIndexMobile))
        patch.showMarketIndexMobile = customSettings.showMarketIndexMobile;
      if (isBoolean(customSettings.showGroupFundSearchPc))
        patch.showGroupFundSearchPc = customSettings.showGroupFundSearchPc;
      if (isBoolean(customSettings.showGroupFundSearchMobile))
        patch.showGroupFundSearchMobile = customSettings.showGroupFundSearchMobile;
      if (isBoolean(customSettings.dynamicStylePc)) patch.dynamicStylePc = customSettings.dynamicStylePc;
      if (isBoolean(customSettings.dynamicStyleMobile)) patch.dynamicStyleMobile = customSettings.dynamicStyleMobile;
      if (isBoolean(customSettings.showGroupDropdownPc)) patch.showGroupDropdownPc = customSettings.showGroupDropdownPc;
      if (isBoolean(customSettings.showGroupDropdownMobile))
        patch.showGroupDropdownMobile = customSettings.showGroupDropdownMobile;

      if (Object.keys(patch).length > 0) {
        set(patch);
      }
    } catch (e) {
      // ignore
    }
  }
}));

/**
 * 从 localStorage 恢复 fundEstimationEnabled（在客户端 mount 后调用一次）
 * 真正的权威状态来自后端 /__switch/status，page.jsx 会进一步覆盖
 */
export const hydrateFundEstimationFromLocal = () => {
  if (typeof window === 'undefined') return;
  try {
    const raw = window.localStorage.getItem('fundEstimationEnabled');
    if (raw === null) return;
    const v = raw === 'true' || raw === true;
    useSettingsStore.setState({ fundEstimationEnabled: v });
  } catch (e) { /* ignore */ }
};

