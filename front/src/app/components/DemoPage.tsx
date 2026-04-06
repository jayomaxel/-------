import { ChangeEvent, useEffect, useMemo, useRef, useState } from 'react';
import type { AnalysisTone } from '../../api/ai';
import AIAnalysisCard from '../../components/AIAnalysisCard';
import AIAnalysisSetupModal from '../../components/AIAnalysisSetupModal';
import { FeaturePanel } from '../../components/FeaturePanel';
import { HeatmapOverlay } from '../../components/HeatmapOverlay';
import { SimilarList } from '../../components/SimilarList';
import { useAnalyze } from '../../hooks/useAnalyze';
import {
  FEATURE_CONFIG,
  formatFeatureValue,
  normalizeFeature,
} from '../../utils/featureDisplay';

declare const window: Window & {
  Chart?: any;
  lucide?: { createIcons: () => void };
};

const AI_TONE_STORAGE_KEY = 'compet.ai.tone';
const AI_API_KEY_STORAGE_KEY = 'compet.ai.api_key';

type RadarDatum = {
  key: string;
  feature: string;
  value: number;
  rawValue: number;
  display: string;
};

const TEXT = {
  pleaseUpload: '请先上传图片。',
  pageTitle: '系统演示',
  pageSubtitle: '上传商品主图，先完成图像分析，再自动接续 AI 智能诊断。',
  uploadPrimary: '上传主图',
  uploadPreviewAlt: '上传预览',
  startAnalyze: '开始分析',
  analyzing: '分析中...',
  ctrPredictionScore: 'CTR 预测评分',
  ctrPredictionHint: '模型原始预测值，基于视觉特征估计点击表现。',
  visualFeatureAnalysis: '视觉特征分析',
  showRadarAfterAnalysis: '分析完成后显示雷达图',
  occlusionHeatmapAnalysis: '热力图分析',
  originalImage: '原始图片',
  originalImageAlt: '原始图片',
  algorithmOutput: '热力图结果',
  high: '高',
  medium: '中',
  low: '低',
} as const;

const EMPTY_RADAR_DATA: RadarDatum[] = FEATURE_CONFIG.map(({ key, label }) => ({
  key,
  feature: label,
  value: 0,
  rawValue: 0,
  display: '--',
}));

function loadSavedTone(): AnalysisTone {
  try {
    const savedTone = window.localStorage.getItem(AI_TONE_STORAGE_KEY);
    if (
      savedTone === 'professional' ||
      savedTone === 'gentle' ||
      savedTone === 'direct' ||
      savedTone === 'marketing'
    ) {
      return savedTone;
    }
  } catch {
    // 某些浏览器模式下可能拿不到本地存储，这里直接回退默认值。
  }

  return 'professional';
}

function loadSavedApiKey(): string {
  try {
    return window.localStorage.getItem(AI_API_KEY_STORAGE_KEY) ?? '';
  } catch {
    return '';
  }
}

const formatCTR = (value: number) => Number(value ?? 0).toFixed(2);

export function DemoPage() {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [aiTone, setAiTone] = useState<AnalysisTone>(loadSavedTone);
  const [aiApiKey, setAiApiKey] = useState(loadSavedApiKey);
  const [aiConfigOpen, setAiConfigOpen] = useState(false);
  const [startAfterAIConfig, setStartAfterAIConfig] = useState(false);
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
    const timerId = window.setTimeout(() => {
      try {
        window.lucide?.createIcons();
      } catch (iconError) {
        console.error('Failed to initialize Lucide icons', iconError);
      }
    }, 0);

    return () => {
      window.clearTimeout(timerId);
    };
  }, [result]);

  const radarData = useMemo<RadarDatum[]>(() => {
    if (!result) {
      return [];
    }

    return FEATURE_CONFIG.filter(
      ({ key }) => typeof result.features[key] === 'number',
    ).map(({ key, label }) => {
      const rawValue = Number(result.features[key]);

      return {
        key,
        feature: label,
        value: normalizeFeature(key, rawValue),
        rawValue,
        display: formatFeatureValue(rawValue),
      };
    });
  }, [result]);

  useEffect(() => {
    if (!radarData.length || !radarCanvasRef.current) {
      radarChartRef.current?.destroy();
      radarChartRef.current = null;
      return;
    }

    const Chart = window.Chart;
    if (!Chart) {
      return;
    }

    radarChartRef.current?.destroy();
    radarChartRef.current = new Chart(radarCanvasRef.current, {
      type: 'radar',
      data: {
        labels: radarData.map((item) => item.feature),
        datasets: [
          {
            data: radarData.map((item) => item.value),
            backgroundColor: 'rgba(59,130,246,0.2)',
            borderColor: 'rgba(59,130,246,0.8)',
            pointBackgroundColor: 'rgba(59,130,246,0.9)',
            pointBorderColor: '#ffffff',
            pointHoverBackgroundColor: '#2563eb',
            pointHoverBorderColor: '#ffffff',
            pointRadius: 4,
            pointHoverRadius: 5,
            pointHitRadius: 10,
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          r: {
            min: 0,
            max: 1,
            grid: { color: '#d1d5db' },
            angleLines: { color: '#e5e7eb' },
            ticks: { display: false },
            pointLabels: { color: '#374151', font: { size: 11 } },
          },
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: (items: Array<{ dataIndex: number }>) =>
                items.length ? radarData[items[0].dataIndex]?.feature ?? '' : '',
              label: (item: { dataIndex: number }) => {
                const datum = radarData[item.dataIndex];
                return datum ? `原始值 ${formatFeatureValue(datum.rawValue)}` : '';
              },
            },
          },
        },
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
  };

  const handleAnalyze = () => {
    if (!uploadedFile) {
      setUploadError(TEXT.pleaseUpload);
      return;
    }

    setAiConfigOpen(true);
    setStartAfterAIConfig(true);
  };

  const handleOpenAIConfig = () => {
    setAiConfigOpen(true);
    setStartAfterAIConfig(false);
  };

  const handleCancelAIConfig = () => {
    setAiConfigOpen(false);
    setStartAfterAIConfig(false);
  };

  const handleConfirmAIConfig = () => {
    try {
      window.localStorage.setItem(AI_TONE_STORAGE_KEY, aiTone);
      window.localStorage.setItem(AI_API_KEY_STORAGE_KEY, aiApiKey);
  } catch {
      // 本地存储失败不影响本次分析流程。
    }

    setAiConfigOpen(false);

    if (startAfterAIConfig && uploadedFile) {
      setUploadError(null);
      void analyze(uploadedFile);
    }

    setStartAfterAIConfig(false);
  };

  const displayError = uploadError ?? error;
  const scoreDisplay = result ? formatCTR(result.ctr.score) : '--';
  const topProducts = result?.similar ?? [];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="sticky top-0 z-20 border-b border-white/60 bg-gray-50/95 backdrop-blur supports-[backdrop-filter]:bg-gray-50/80">
        <div className="mx-auto max-w-[1800px] px-4 py-3 sm:px-6 lg:px-8 xl:px-12 xl:py-4">
          <h1 className="mb-2 text-3xl font-black text-gray-900 xl:text-4xl">
            {TEXT.pageTitle}
          </h1>
          <p className="text-base text-gray-600 xl:text-lg">{TEXT.pageSubtitle}</p>
        </div>
      </div>

      <div className="mx-auto max-w-[1800px] px-4 pb-8 pt-6 sm:px-6 lg:px-8 xl:px-12 xl:pb-12">
        <div className="grid items-start gap-6 lg:grid-cols-[minmax(280px,340px)_minmax(0,1fr)] xl:gap-8 xl:grid-cols-[minmax(300px,360px)_minmax(0,1fr)]">
          <aside className="lg:sticky lg:top-24 xl:top-28">
            <div className="space-y-6 rounded-2xl border border-gray-200 bg-white p-5 shadow-md sm:p-6">
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
                className="w-full rounded-xl border-2 border-dashed border-gray-300 bg-white p-6 text-center shadow-sm transition-all hover:border-blue-400 hover:bg-blue-50 hover:shadow-md sm:p-8"
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

              {displayError ? (
                <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
                  {displayError}
                </div>
              ) : null}
            </div>
          </aside>

          <main className="min-w-0 space-y-6 xl:space-y-8">
            <div className="grid gap-4 xl:grid-cols-[minmax(220px,280px)_minmax(0,1fr)] xl:gap-6">
              <div>
                <div className="flex h-full min-h-[180px] flex-col justify-center rounded-2xl border border-gray-200 bg-white p-5 shadow-md transition-all hover:shadow-xl sm:min-h-[220px] sm:p-6">
                    <h3 className="mb-2 text-sm font-medium text-gray-500">
                      {TEXT.ctrPredictionScore}
                    </h3>
                    <div className="text-5xl font-bold text-blue-600 tabular-nums">
                      {scoreDisplay}
                    </div>
                    <p className="mt-3 text-xs text-gray-400">{TEXT.ctrPredictionHint}</p>
                  </div>
                </div>

              <div>
                <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-md transition-all hover:shadow-xl sm:p-6">
                    <h3 className="mb-4 text-lg font-bold text-gray-800">
                      {TEXT.occlusionHeatmapAnalysis}
                    </h3>
                    <div className="grid gap-4 lg:grid-cols-2">
                      <div className="text-center">
                        <p className="mb-2 text-sm text-gray-500">{TEXT.originalImage}</p>
                        <div className="flex min-h-[220px] items-center justify-center overflow-hidden rounded-lg border border-gray-200 bg-gray-50 p-4 sm:min-h-[260px]">
                          {previewUrl ? (
                            <img
                              src={previewUrl}
                              alt={TEXT.originalImageAlt}
                              className="max-h-[240px] w-full object-contain sm:max-h-[280px]"
                            />
                          ) : (
                            <div className="flex h-full min-h-[240px] w-full items-center justify-center">
                              <i
                                data-lucide="image"
                                className="text-gray-300"
                                style={{ width: 48, height: 48 }}
                              />
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="text-center">
                        <p className="mb-2 text-sm text-gray-500">{TEXT.algorithmOutput}</p>
                        {previewUrl && result?.heatmap_base64 ? (
                          <HeatmapOverlay heatmapBase64={result.heatmap_base64} />
                        ) : (
                          <div className="flex min-h-[220px] items-center justify-center rounded-lg border border-gray-200 bg-gradient-to-br from-red-200 via-yellow-200 to-green-200 p-4 sm:min-h-[260px]">
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

            <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-md transition-all hover:shadow-xl sm:p-6">
                <h3 className="mb-4 flex items-center gap-2 text-lg font-bold text-gray-800">
                  <i
                    data-lucide="trending-up"
                    className="text-blue-600"
                    style={{ width: 20, height: 20 }}
                  />
                  {TEXT.visualFeatureAnalysis}
                </h3>
                <div className="grid gap-6 lg:grid-cols-[minmax(240px,320px)_minmax(0,1fr)] lg:items-center">
                  <div className="flex justify-center">
                    <div className="h-[240px] w-full max-w-[280px] sm:h-[280px] sm:max-w-[320px]">
                      {radarData.length ? (
                        <canvas ref={radarCanvasRef} style={{ width: '100%', height: '100%' }} />
                      ) : (
                        <div className="flex size-full items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50 text-sm font-medium text-gray-500">
                          {TEXT.showRadarAfterAnalysis}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="w-full">
                    {result ? (
                      <FeaturePanel features={result.features} />
                    ) : (
                      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-2 xl:grid-cols-4">
                        {EMPTY_RADAR_DATA.map((item) => (
                          <div
                            key={item.key}
                            className="rounded-xl border border-gray-100 bg-gray-50 px-2 py-4 text-center"
                          >
                            <div className="text-xl font-bold leading-tight text-blue-600 tabular-nums">
                              {item.display}
                            </div>
                            <div className="mt-1.5 truncate text-xs text-gray-500">
                              {item.feature}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <AIAnalysisCard
                features={(result?.features ?? {}) as Record<string, number>}
                ctrScore={result?.ctr.score ?? 0}
                ready={Boolean(result)}
                tone={aiTone}
                apiKey={aiApiKey}
                onToneChange={setAiTone}
                onOpenConfig={handleOpenAIConfig}
              />

            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-md transition-all hover:shadow-xl sm:p-8">
                <SimilarList
                  items={
                    topProducts.length
                      ? topProducts
                      : Array.from({ length: 5 }, (_, index) => ({
                          rank: index + 1,
                          similarity: 0,
                          relative_ctr: 0,
                          price: 0,
                          img_base64: null,
                        }))
                  }
                />
            </div>
          </main>
        </div>
      </div>

      <AIAnalysisSetupModal
        open={aiConfigOpen}
        apiKey={aiApiKey}
        tone={aiTone}
        loading={loading && startAfterAIConfig}
        onApiKeyChange={setAiApiKey}
        onToneChange={setAiTone}
        onCancel={handleCancelAIConfig}
        onConfirm={handleConfirmAIConfig}
      />
    </div>
  );
}
