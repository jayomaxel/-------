interface HeatmapOverlayProps {
  heatmapBase64: string;
}

export function HeatmapOverlay({ heatmapBase64 }: HeatmapOverlayProps) {
  return (
    <div className="flex min-h-[260px] items-center justify-center overflow-hidden rounded-lg border border-gray-200 bg-gray-50 p-4">
      <img
        src={`data:image/png;base64,${heatmapBase64}`}
        alt="注意力热力图"
        className="max-h-[240px] w-full object-contain"
      />
    </div>
  );
}
