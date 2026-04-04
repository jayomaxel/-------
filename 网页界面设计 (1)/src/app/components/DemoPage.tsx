import { ChangeEvent, useEffect, useMemo, useRef, useState } from 'react';
import { AdviceList } from '../../components/AdviceList';
import { FeaturePanel } from '../../components/FeaturePanel';
import { HeatmapOverlay } from '../../components/HeatmapOverlay';
import { SimilarList } from '../../components/SimilarList';
import { useAnalyze } from '../../hooks/useAnalyze';

declare const window: Window & {
  Chart?: any;
  lucide?: { createIcons: () => void };
};

type RadarDatum = {
  feature: string;
  value: number;
  display: string;
};

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000';

const TEXT = {
  modelSummary: '\u7edf\u4e00\u591a\u54c1\u7c7b\u6a21\u578b',
  modelNote: '6 \u4e2a\u54c1\u7c7b\u8054\u5408\u8bad\u7ec3',
  high: '\u9ad8',
  medium: '\u4e2d',
  low: '\u4f4e',
  featureEntropy: '\u89c6\u89c9\u71b5',
  featureTextDensity: '\u6587\u5b57\u5bc6\u5ea6',
  featureBrightness: '\u4eae\u5ea6',
  featureContrast: '\u5bf9\u6bd4\u5ea6',
  featureSaturation: '\u9971\u548c\u5ea6',
  pleaseUpload: '\u8bf7\u5148\u4e0a\u4f20\u56fe\u7247\u3002',
  pageTitle: '\u7cfb\u7edf\u6f14\u793a',
  pageSubtitle:
    '\u4e0a\u4f20\u4e3b\u56fe\uff0c\u4f7f\u7528\u7edf\u4e00\u6a21\u578b\u83b7\u53d6 CTR \u9884\u6d4b\u4e0e\u667a\u80fd\u8bca\u65ad\u3002',
  uploadPrimary: '\u4e0a\u4f20\u4e3b\u56fe',
  uploadPreviewAlt: '\u4e0a\u4f20\u9884\u89c8',
  startAnalyze: '\u5f00\u59cb\u5206\u6790',
  analyzing: '\u5206\u6790\u4e2d...',
  modelStatus: '\u6a21\u578b\u72b6\u6001',
  modelEndpointPrefix:
    '\u524d\u7aef localhost:5173 \u00b7 \u63a5\u53e3 ',
  ctrPredictionScore: 'CTR\u9884\u6d4b\u8bc4\u5206',
  exceeds: '\u8d85\u8fc7',
  referenceSamples: '\u53c2\u8003\u6837\u672c',
  rawPrediction: '\u539f\u59cb\u9884\u6d4b\u503c',
  visualFeatureAnalysis: '\u89c6\u89c9\u7279\u5f81\u5206\u6790',
  showRadarAfterAnalysis:
    '\u5206\u6790\u5b8c\u6210\u540e\u663e\u793a\u96f7\u8fbe\u56fe',
  occlusionHeatmapAnalysis: '\u906e\u6321\u70ed\u529b\u56fe\u5206\u6790',
  originalImage: '\u539f\u59cb\u56fe\u50cf',
  originalImageAlt: '\u539f\u59cb\u56fe\u50cf',
  waitingResult: '\u7b49\u5f85\u7ed3\u679c',
  systemStatus: '\u7cfb\u7edf\u72b6\u6001',
  waitingAnalysisResult: '\u7b49\u5f85\u5206\u6790\u7ed3\u679c',
  waitingAdvice:
    '\u4e0a\u4f20\u56fe\u7247\u5e76\u70b9\u51fb\u201c\u5f00\u59cb\u5206\u6790\u201d\u540e\uff0c\u5c06\u663e\u793a\u57fa\u4e8e\u6a21\u578b\u7684\u4f18\u5316\u5efa\u8bae\u3002',
} as const;

const EMPTY_RADAR_DATA: RadarDatum[] = [
  { feature: TEXT.featureEntropy, value: 0, display: '--' },
  { feature: TEXT.featureTextDensity, value: 0, display: '--' },
  { feature: TEXT.featureBrightness, value: 0, display: '--' },
  { feature: TEXT.featureContrast, value: 0, display: '--' },
  { feature: TEXT.featureSaturation, value: 0, display: '--' },
];

const clamp = (value: number, min: number, max: number) =>
  Math.min(Math.max(value, min), max);

const normalize = (value: number, max: number) => clamp((value / max) * 100, 0, 100);

const formatNumber = (value: number, digits = 2) =>
  Number(value ?? 0).toFixed(digits);

const formatScore = (value: number) =>
  value <= 1 ? (value * 100).toFixed(1) : value.toFixed(2);

export function DemoPage() {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const { result, loading, error, analyze, reset } = useAnalyze();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const radarCanvasRef = useRef<HTMLCanvasElement>(null);
  const radarChartRef = useRef<any>(null);

  useEffect(() => {
    if (!uploadedFile) {
      setPreviewUrl('');
      return;
    }

    const objectUrl = URL.createObjectURL(uploadedFile);
    setPreviewUrl(objectUrl);

    return () => URL.revokeObjectURL(objectUrl);
  }, [uploadedFile]);

  useEffect(() => {
    window.lucide?.createIcons();
  });

  const radarData = useMemo<RadarDatum[]>(() => {
    if (!result) {
      return [];
    }

    return [
      {
        feature: TEXT.featureEntropy,
        value: normalize(result.features.entropy, 10),
        display: formatNumber(result.features.entropy, 2),
      },
      {
        feature: TEXT.featureTextDensity,
        value: normalize(result.features.text_density, 1),
        display: formatNumber(result.features.text_density, 2),
      },
      {
        feature: TEXT.featureBrightness,
        value: normalize(result.features.brightness, 1),
        display: formatNumber(result.features.brightness, 2),
      },
      {
        feature: TEXT.featureContrast,
        value: normalize(result.features.contrast, 100),
        display: formatNumber(result.features.contrast, 2),
      },
      {
        feature: TEXT.featureSaturation,
        value: normalize(result.features.saturation, 1),
        display: formatNumber(result.features.saturation, 2),
      },
    ];
  }, [result]);

  const topProducts = result?.similar ?? [];
  const suggestions = result?.advice ?? [];

  useEffect(() => {
    if (!radarData.length || !radarCanvasRef.current) return;

    radarChartRef.current?.destroy();
    radarChartRef.current = null;

    const Chart = window.Chart;
    if (!Chart) return;

    radarChartRef.current = new Chart(radarCanvasRef.current, {
      type: 'radar',
      data: {
        labels: radarData.map((datum) => datum.feature),
        datasets: [
          {
            data: radarData.map((datum) => datum.value),
            backgroundColor: 'rgba(37,99,235,0.3)',
            borderColor: '#2563eb',
            pointBackgroundColor: '#2563eb',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          r: {
            min: 0,
            max: 100,
            grid: { color: '#d1d5db' },
            ticks: { display: false },
            pointLabels: { color: '#374151', font: { size: 12 } },
          },
        },
        plugins: { legend: { display: false } },
      },
    });

    return () => {
      radarChartRef.current?.destroy();
      radarChartRef.current = null;
    };
  }, [radarData]);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0] ?? null;

    if (!nextFile) {
      return;
    }

    setUploadError(null);
    reset();
    setUploadedFile(nextFile);
    void analyze(nextFile);
  };

  const handleAnalyze = () => {
    if (!uploadedFile) {
      setUploadError(TEXT.pleaseUpload);
      return;
    }

    setUploadError(null);
    void analyze(uploadedFile);
  };

  const displayError = uploadError ?? error;

  const scoreDisplay = result ? formatScore(result.ctr.score) : '--';
  const rawScore = result ? formatNumber(result.ctr.score, 4) : '--';
  const percentile = result?.ctr.percentile ?? 0;
  const radius = 118;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference * (1 - percentile / 100);

  return (
    <div className="min-h-screen overflow-y-auto bg-gray-50">
      <div className="mx-auto max-w-[1800px] p-6 xl:p-12">
        <div className="mb-10 xl:mb-12">
          <h1 className="mb-3 text-4xl font-black text-gray-900 xl:text-5xl">
            {TEXT.pageTitle}
          </h1>
          <p className="text-lg text-gray-600 xl:text-xl">{TEXT.pageSubtitle}</p>
        </div>

        <div className="grid gap-8 xl:grid-cols-5">
          <div className="space-y-6 xl:col-span-1">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleFileChange}
            />

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-full rounded-xl border-2 border-dashed border-gray-300 bg-white p-8 text-center shadow-sm transition-all hover:border-blue-400 hover:bg-blue-50 hover:shadow-md"
            >
              <div className="flex flex-col items-center gap-4">
                <i
                  data-lucide="upload"
                  className="text-blue-500"
                  style={{ width: 48, height: 48 }}
                />
                <div>
                  <p className="mb-1 font-bold text-gray-800">{TEXT.uploadPrimary}</p>
                  <p className="text-sm text-gray-500">
                    {uploadedFile ? uploadedFile.name : 'JPG, PNG'}
                  </p>
                </div>
              </div>
            </button>

            <div className="aspect-square overflow-hidden rounded-xl border border-gray-200 bg-gray-50 shadow-sm transition-all hover:shadow-md">
              {previewUrl ? (
                <img
                  src={previewUrl}
                  alt={TEXT.uploadPreviewAlt}
                  className="size-full object-cover"
                />
              ) : (
                <div className="flex size-full items-center justify-center">
                  <i
                    data-lucide="image"
                    className="text-gray-300"
                    style={{ width: 48, height: 48 }}
                  />
                </div>
              )}
            </div>

            <button
              type="button"
              onClick={handleAnalyze}
              disabled={!uploadedFile || loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 py-4 font-bold text-white shadow-lg transition-all hover:scale-[1.02] hover:from-blue-700 hover:to-cyan-700 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:scale-100"
            >
              {loading ? (
                <i
                  data-lucide="loader-circle"
                  className="animate-spin"
                  style={{ width: 20, height: 20 }}
                />
              ) : null}
              {loading ? TEXT.analyzing : TEXT.startAnalyze}
            </button>

            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <div className="text-sm font-bold text-gray-600">{TEXT.modelStatus}</div>
              <div className="mt-2 text-2xl font-black text-gray-900">
                {TEXT.modelSummary}
              </div>
              <p className="mt-1 text-sm text-gray-600">{TEXT.modelNote}</p>
              <p className="mt-1 text-xs font-medium text-gray-500">
                {TEXT.modelEndpointPrefix}
                {API_BASE}
              </p>
            </div>

            {displayError ? (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
                {displayError}
              </div>
            ) : null}
          </div>

          <div className="space-y-8 xl:col-span-4">
            <div className="animate-fade-scale-in rounded-2xl border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-cyan-50 p-8 shadow-lg transition-all hover:shadow-2xl xl:p-12">
              <div className="flex flex-col gap-8 xl:flex-row xl:items-center xl:justify-between">
                <div>
                  <div className="mb-2 text-sm font-bold text-gray-600">
                    {TEXT.ctrPredictionScore}
                  </div>
                  <div className="text-7xl font-black text-blue-600 xl:text-9xl">
                    {scoreDisplay}
                  </div>
                  <p className="mt-4 text-lg text-gray-600 xl:text-xl">
                    {TEXT.exceeds}{' '}
                    <span className="font-bold text-green-600">{percentile}%</span>{' '}
                    {TEXT.referenceSamples}
                  </p>
                  <p className="mt-2 text-sm font-medium text-gray-500">
                    {TEXT.rawPrediction}: {rawScore}
                  </p>
                </div>

                <div className="relative h-64 w-64 self-center rounded-full border-4 border-blue-300 shadow-lg">
                  <svg
                    viewBox="0 0 256 256"
                    className="size-full -rotate-90 transform"
                  >
                    <circle
                      cx="128"
                      cy="128"
                      r={radius}
                      stroke="#e5e7eb"
                      strokeWidth="12"
                      fill="none"
                    />
                    <circle
                      cx="128"
                      cy="128"
                      r={radius}
                      stroke="url(#ctr-gradient)"
                      strokeWidth="12"
                      fill="none"
                      strokeLinecap="round"
                      strokeDasharray={circumference}
                      strokeDashoffset={dashOffset}
                      className="transition-all duration-1000"
                    />
                    <defs>
                      <linearGradient id="ctr-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#2563eb" />
                        <stop offset="100%" stopColor="#06b6d4" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center text-4xl font-black text-blue-600">
                    {percentile}%
                  </div>
                </div>
              </div>
            </div>

            <div className="grid gap-8 xl:grid-cols-2">
              <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-md transition-all hover:shadow-xl">
                <h3 className="mb-6 flex items-center gap-2 text-2xl font-bold text-gray-800">
                  <i
                    data-lucide="trending-up"
                    className="text-blue-600"
                    style={{ width: 24, height: 24 }}
                  />
                  {TEXT.visualFeatureAnalysis}
                </h3>

                <div className="h-80">
                  {radarData.length ? (
                    <canvas
                      ref={radarCanvasRef}
                      style={{ width: '100%', height: '100%' }}
                    />
                  ) : (
                    <div className="flex size-full items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50 text-sm font-medium text-gray-500">
                      {TEXT.showRadarAfterAnalysis}
                    </div>
                  )}
                </div>

                {result ? (
                  <FeaturePanel features={result.features} ctr={result.ctr} />
                ) : (
                  <div className="mt-6 grid grid-cols-2 gap-4 border-t-2 border-black pt-6 xl:grid-cols-5">
                    {EMPTY_RADAR_DATA.map((item) => (
                      <div key={item.feature} className="text-center">
                        <div className="text-3xl font-black text-blue-600">
                          {item.display}
                        </div>
                        <div className="mt-1 text-xs font-medium text-gray-600">
                          {item.feature}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-md transition-all hover:shadow-xl">
                <h3 className="mb-6 text-2xl font-bold text-gray-800">
                  {TEXT.occlusionHeatmapAnalysis}
                </h3>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <div className="mb-3 text-sm font-bold text-gray-600">
                      {TEXT.originalImage}
                    </div>
                    <div className="aspect-square overflow-hidden rounded-lg border-2 border-gray-200 bg-gray-50 transition-all hover:border-blue-300">
                      {previewUrl ? (
                        <img
                          src={previewUrl}
                          alt={TEXT.originalImageAlt}
                          className="size-full object-cover"
                        />
                      ) : (
                        <div className="flex size-full items-center justify-center">
                          <i
                            data-lucide="image"
                            className="text-gray-400"
                            style={{ width: 48, height: 48 }}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                  <div>
                    <div className="mb-3 text-sm font-bold text-gray-600">
                      热力图叠加预览
                    </div>
                    <div className="rounded-lg transition-all hover:border-blue-300">
                      {previewUrl && result?.heatmap_base64 ? (
                        <HeatmapOverlay
                          originalPreview={previewUrl}
                          heatmapBase64={result.heatmap_base64}
                        />
                      ) : (
                        <div className="flex aspect-square items-center justify-center rounded-lg border-2 border-gray-200 bg-gradient-to-br from-red-200 via-yellow-200 to-green-200">
                          <div className="text-center">
                            <div className="flex items-center justify-center gap-2 text-xs font-bold">
                              <div className="flex items-center gap-1">
                                <div className="h-4 w-4 rounded border border-gray-400 bg-red-500 shadow-sm" />
                                <span>{TEXT.high}</span>
                              </div>
                              <div className="flex items-center gap-1">
                                <div className="h-4 w-4 rounded border border-gray-400 bg-yellow-500 shadow-sm" />
                                <span>{TEXT.medium}</span>
                              </div>
                              <div className="flex items-center gap-1">
                                <div className="h-4 w-4 rounded border border-gray-400 bg-green-500 shadow-sm" />
                                <span>{TEXT.low}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-md transition-all hover:shadow-xl">
              <SimilarList
                items={
                  topProducts.length
                    ? topProducts
                    : Array.from({ length: 5 }, (_, index) => ({
                        rank: index + 1,
                        img_name: TEXT.waitingResult,
                        similarity: 0,
                        relative_ctr: 0,
                        price: 0,
                        img_base64: null,
                      }))
                }
              />
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-md transition-all hover:shadow-xl">
              <AdviceList
                items={
                  suggestions.length
                    ? suggestions
                    : [
                        {
                          priority: TEXT.low,
                          category: TEXT.systemStatus,
                          issue: TEXT.waitingAnalysisResult,
                          suggestion: TEXT.waitingAdvice,
                        },
                      ]
                }
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
