import { useEffect, useState } from 'react';

interface HeatmapOverlayProps {
  originalPreview: string;
  heatmapBase64: string;
  opacity?: number;
}

export function HeatmapOverlay({
  originalPreview,
  heatmapBase64,
  opacity = 0.5,
}: HeatmapOverlayProps) {
  const [currentOpacity, setCurrentOpacity] = useState(opacity);

  useEffect(() => {
    setCurrentOpacity(opacity);
  }, [opacity]);

  return (
    <div className="space-y-4">
      <div className="overflow-hidden rounded-lg border-2 border-gray-200 bg-gray-50">
        <div className="relative aspect-square">
          <img
            src={originalPreview}
            alt="原始图片"
            className="block size-full object-cover"
          />
          <img
            src={`data:image/png;base64,${heatmapBase64}`}
            alt="热力图"
            className="pointer-events-none absolute inset-0 size-full object-cover"
            style={{
              opacity: currentOpacity,
              mixBlendMode: 'multiply',
            }}
          />
        </div>
      </div>

      <div>
        <div className="mb-2 flex items-center justify-between text-xs font-bold text-gray-600">
          <span>热力图透明度</span>
          <span>{Math.round(currentOpacity * 100)}%</span>
        </div>
        <input
          type="range"
          min="0"
          max="100"
          value={Math.round(currentOpacity * 100)}
          onChange={(event) => setCurrentOpacity(Number(event.target.value) / 100)}
          className="w-full accent-blue-600"
        />
      </div>
    </div>
  );
}
