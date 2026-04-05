import type { AnalyzeFeatures } from '../api/analyze';
import { FEATURE_CONFIG, formatFeatureValue } from '../utils/featureDisplay';

interface FeaturePanelProps {
  features: AnalyzeFeatures;
}

export function FeaturePanel({ features }: FeaturePanelProps) {
  const displayItems = FEATURE_CONFIG.filter(
    ({ key }) => typeof features[key] === 'number',
  );

  return (
    <ul className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {displayItems.map(({ key, label }) => (
        <li
          key={key}
          className="min-w-0 rounded-xl border border-gray-100 bg-gray-50 px-2 py-4 text-center"
        >
          <div
            className="whitespace-nowrap text-xl font-bold leading-tight text-blue-600 tabular-nums"
            title={String(features[key] ?? 0)}
          >
            {formatFeatureValue(Number(features[key] ?? 0))}
          </div>
          <div className="mt-1.5 truncate text-xs text-gray-500">{label}</div>
        </li>
      ))}
    </ul>
  );
}
