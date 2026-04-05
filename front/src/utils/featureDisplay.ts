import type { AnalyzeFeatures } from '../api/analyze';

export type FeatureKey = keyof AnalyzeFeatures;

export const FEATURE_CONFIG: Array<{
  key: FeatureKey;
  label: string;
  max: number;
}> = [
  { key: 'entropy', label: '信息熵', max: 8 },
  { key: 'text_density', label: '文字密度', max: 1 },
  { key: 'brightness', label: '亮度', max: 1 },
  { key: 'contrast', label: '对比度', max: 100 },
  { key: 'saturation', label: '饱和度', max: 1 },
  { key: 'subject_area_ratio', label: '主体占比', max: 1 },
  { key: 'edge_density', label: '边缘密度', max: 1 },
  { key: 'color_saturation', label: '颜色饱和度', max: 1 },
];

export const FEATURE_MAX_VALUES: Record<FeatureKey, number> = FEATURE_CONFIG.reduce(
  (acc, item) => {
    acc[item.key] = item.max;
    return acc;
  },
  {} as Record<FeatureKey, number>,
);

const clamp = (value: number, min: number, max: number) =>
  Math.min(Math.max(value, min), max);

export function normalizeFeature(key: FeatureKey, value: number): number {
  const max = FEATURE_MAX_VALUES[key] || 1;
  const safeValue = Number.isFinite(value) ? value : 0;
  return clamp(safeValue / max, 0, 1);
}

export function formatFeatureValue(value: number): string {
  const safeValue = Number.isFinite(value) ? value : 0;

  if (Math.abs(safeValue) >= 100) {
    return safeValue.toFixed(0);
  }

  if (Math.abs(safeValue) >= 10) {
    return safeValue.toFixed(1);
  }

  if (Math.abs(safeValue) >= 1) {
    return safeValue.toFixed(2);
  }

  return safeValue.toFixed(3);
}
