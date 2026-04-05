import { ChangeEvent, useEffect, useMemo, useRef, useState } from 'react';
import { AdviceList } from '../../components/AdviceList';
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

type RadarDatum = {
  key: string;
  feature: string;
  value: number;
  rawValue: number;
  display: string;
};

const TEXT = {
  high: '高',
  medium: '中',
  low: '低',
  pleaseUpload: '请先上传图片。',
  pageTitle: '系统演示',
  pageSubtitle: '上传主图，使用参考脚本同口径算法获取 CTR 预测与智能诊断。',
  uploadPrimary: '上传主图',
  uploadPreviewAlt: '上传预览',
  startAnalyze: '开始分析',
  analyzing: '分析中...',
  ctrPredictionScore: 'CTR 预测评分',
  ctrPredictionHint: '模型原始预测值，基于图像视觉特征的点击率预估',
  visualFeatureAnalysis: '视觉特征分析',
  showRadarAfterAnalysis: '分析完成后显示雷达图',
  occlusionHeatmapAnalysis: '参考算法热力图',
  originalImage: '原始图像',
  originalImageAlt: '原始图像',
  algorithmOutput: '注意力热力图',
  waitingResult: '等待结果',
  systemStatus: '系统状态',
  waitingAnalysisResult: '等待分析结果',
  waitingAdvice: '上传图片并点击“开始分析”后，将显示基于模型的优化建议。',
  warningsTitle: '系统降级提示',
  psychologicalReport: '参考脚本心理学诊断',
} as const;

const EMPTY_RADAR_DATA: RadarDatum[] = FEATURE_CONFIG.map(({ key, label }) => ({
  key,
  feature: label,
  value: 0,
  rawValue: 0,
  display: '--',
}));

const formatCTR = (value: number) => Number(value ?? 0).toFixed(2);

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

    return FEATURE_CONFIG.map(({ key, label }) => {
      const rawValue = Number(result.features[key] ?? 0);

      return {
        key,
        feature: label,
        value: normalizeFeature(key, rawValue),
        rawValue,
        display: formatFeatureValue(rawValue),
      };
    });
  }, [result]);

  const topProducts = result?.similar ?? [];
  const suggestions = result?.advice ?? [];
  const reportLines = result?.psychological_report?.lines ?? [];
  const warnings = result?.warnings ?? [];

  useEffect(() => {
    if (!radarData.length || !radarCanvasRef.current) {
      radarChartRef.current?.destroy();
      radarChartRef.current = null;
      return;
    }

    const Chart = window.Chart;
    if (!Chart) return;

    const radarIndicator = FEATURE_CONFIG.map(({ label, max }) => ({
      name: label,
      max: 1,
      rawMax: max,
    }));
    const radarValues = radarData.map((datum) => datum.value);

    console.log('=== 雷达图调试 ===');
    console.log('indicator:', JSON.stringify(radarIndicator));
    console.log('data:', JSON.stringify(radarValues));
    console.log(
      'rawData:',
      JSON.stringify(
        radarData.map((datum) => ({
          key: datum.key,
          label: datum.feature,
          rawValue: datum.rawValue,
          normalizedValue: datum.value,
        })),
      ),
    );

    radarChartRef.current?.destroy();
    radarChartRef.current = new Chart(radarCanvasRef.current, {
      type: 'radar',
      data: {
        labels: radarIndicator.map((item) => item.name),
        datasets: [
          {
            data: radarValues,
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
                return datum ? `原始值: ${formatFeatureValue(datum.rawValue)}` : '';
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

    setUploadError(null);
    void analyze(uploadedFile);
  };

  const displayError = uploadError ?? error;
  const scoreDisplay = result ? formatCTR(result.ctr.score) : '--';

  return (
    <div className="h-screen overflow-hidden bg-gray-50">
      <div className="mx-auto flex h-full max-w-[1800px] flex-col px-6 pb-6 pt-3 xl:px-12 xl:pb-12 xl:pt-4">
        <div className="shrink-0 border-b border-white/60 bg-gray-50/95 py-3 backdrop-blur supports-[backdrop-filter]:bg-gray-50/80 xl:py-4">
          <h1 className="mb-2 text-3xl font-black text-gray-900 xl:text-4xl">
            {TEXT.pageTitle}
          </h1>
          <p className="text-base text-gray-600 xl:text-lg">{TEXT.pageSubtitle}</p>
        </div>

        <div className="flex-1 min-h-0 overflow-x-hidden overflow-y-auto pt-6 xl:overflow-hidden">
          <div className="grid gap-8 xl:h-full xl:min-h-0 xl:grid-cols-[320px_minmax(0,1fr)] xl:items-stretch">
          <aside className="space-y-6 xl:self-start xl:pr-2">
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

            {displayError ? (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
                {displayError}
              </div>
            ) : null}

            {warnings.length ? (
              <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                <div className="font-semibold">{TEXT.warningsTitle}</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {warnings.map((warning) => (
                    <code
                      key={warning}
                      className="rounded-md bg-white/80 px-2 py-1 text-xs font-medium text-amber-900"
                    >
                      {warning}
                    </code>
                  ))}
                </div>
              </div>
            ) : null}
          </aside>

          <main className="min-w-0 space-y-8 overflow-x-hidden pb-12 xl:min-h-0 xl:overflow-y-auto xl:overscroll-contain xl:pr-3 xl:pb-20">
            <div className="flex flex-col gap-4 md:flex-row">
              <div className="w-full md:w-1/3">
                <div className="flex h-full min-h-[220px] flex-col justify-center rounded-2xl border border-gray-200 bg-white p-6 shadow-md transition-all hover:shadow-xl">
                  <h3 className="mb-2 text-sm font-medium text-gray-500">
                    {TEXT.ctrPredictionScore}
                  </h3>
                  <div className="text-5xl font-bold text-blue-600 tabular-nums">
                    {scoreDisplay}
                  </div>
                  <p className="mt-3 text-xs text-gray-400">
                    {TEXT.ctrPredictionHint}
                  </p>
                </div>
              </div>

              <div className="w-full md:w-2/3">
                <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-md transition-all hover:shadow-xl">
                  <h3 className="mb-4 text-lg font-bold text-gray-800">
                    {TEXT.occlusionHeatmapAnalysis}
                  </h3>
                  <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
                    <div className="flex-1 text-center">
                      <p className="mb-2 text-sm text-gray-500">{TEXT.originalImage}</p>
                      <div className="flex min-h-[260px] items-center justify-center overflow-hidden rounded-lg border border-gray-200 bg-gray-50 p-4">
                        {previewUrl ? (
                          <img
                            src={previewUrl}
                            alt={TEXT.originalImageAlt}
                            className="max-h-[240px] w-full object-contain"
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

                    <div className="flex-1 text-center">
                      <p className="mb-2 text-sm text-gray-500">{TEXT.algorithmOutput}</p>
                      {previewUrl && result?.heatmap_base64 ? (
                        <HeatmapOverlay heatmapBase64={result.heatmap_base64} />
                      ) : (
                        <div className="flex min-h-[260px] items-center justify-center rounded-lg border border-gray-200 bg-gradient-to-br from-red-200 via-yellow-200 to-green-200 p-4">
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

            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-md transition-all hover:shadow-xl">
              <h3 className="mb-4 flex items-center gap-2 text-lg font-bold text-gray-800">
                <i
                  data-lucide="trending-up"
                  className="text-blue-600"
                  style={{ width: 20, height: 20 }}
                />
                {TEXT.visualFeatureAnalysis}
              </h3>
              <div className="flex flex-col items-center gap-6 md:flex-row">
                <div className="flex w-full justify-center md:w-2/5">
                  <div className="h-[280px] w-[280px] max-w-full">
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
                </div>

                <div className="w-full md:w-3/5">
                  {result ? (
                    <FeaturePanel features={result.features} />
                  ) : (
                    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
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

            <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-md transition-all hover:shadow-xl">
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

            <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-md transition-all hover:shadow-xl">
              <h3 className="mb-6 text-2xl font-bold text-gray-800">
                {TEXT.psychologicalReport}
              </h3>
              {reportLines.length ? (
                <div className="space-y-3 text-sm leading-7 text-gray-700">
                  {reportLines.map((line, index) => (
                    <p key={`${index}-${line}`}>{line}</p>
                  ))}
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-gray-200 bg-gray-50 px-4 py-6 text-sm font-medium text-gray-500">
                  {TEXT.waitingAdvice}
                </div>
              )}
            </div>
          </main>
          </div>
        </div>
      </div>
    </div>
  );
}
