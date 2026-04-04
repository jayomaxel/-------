import type { AnalyzeCTR, AnalyzeFeatures } from '../api/analyze';

interface FeaturePanelProps {
  features: AnalyzeFeatures;
  ctr: AnalyzeCTR;
}

export function FeaturePanel({ features, ctr }: FeaturePanelProps) {
  const featureLabels: Record<keyof AnalyzeFeatures, string> = {
    entropy: '信息熵',
    text_density: '文字密度',
    brightness: '亮度',
    contrast: '对比度',
    saturation: '饱和度',
  };

  return (
    <div className="mt-6 space-y-6 border-t-2 border-black pt-6">
      <div>
        <h3 className="text-lg font-bold text-gray-800">图像特征分析</h3>
        <ul className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          {Object.entries(features).map(([key, value]) => (
            <li
              key={key}
              className="rounded-xl border border-gray-200 bg-gray-50 px-4 py-5 text-center"
            >
              <div className="text-3xl font-black text-blue-600">
                {(value as number).toFixed(3)}
              </div>
              <div className="mt-2 text-xs font-semibold tracking-wide text-gray-600">
                {featureLabels[key as keyof AnalyzeFeatures]}
              </div>
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-xl bg-gradient-to-r from-blue-50 to-cyan-50 p-5">
        <h3 className="text-lg font-bold text-gray-800">CTR 预测</h3>
        <p className="mt-3 text-3xl font-black text-blue-600">
          预测点击率：{(ctr.score * 100).toFixed(2)}%
        </p>
        <p className="mt-2 text-sm font-medium text-gray-600">
          超越同类 {ctr.percentile}% 的商品
        </p>
      </div>
    </div>
  );
}
