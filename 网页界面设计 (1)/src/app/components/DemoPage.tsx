import { ChangeEvent, useEffect, useMemo, useRef, useState } from 'react';
import { motion } from 'motion/react';
import {
  Upload,
  TrendingUp,
  Image as ImageIcon,
  ArrowUp,
  ArrowDown,
  Minus,
  LoaderCircle,
} from 'lucide-react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from 'recharts';

type CategoryOption = '饮料' | '台灯';

type AnalyzeResponse = {
  features: {
    entropy: number;
    text_density: number;
    brightness: number;
    contrast: number;
    saturation: number;
  };
  ctr: {
    score: number;
    percentile: number;
  };
  heatmap_base64: string;
  similar: Array<{
    rank: number;
    img_name: string;
    similarity: number;
    relative_ctr: number;
    price: number;
    img_base64: string | null;
  }>;
  advice: Array<{
    priority: string;
    category: string;
    issue: string;
    suggestion: string;
  }>;
};

type RadarDatum = {
  feature: string;
  value: number;
  display: string;
};

type SuggestionLevel = 'high' | 'medium' | 'low';

const datasetMeta: Record<CategoryOption, { label: string; key: string; count: number }> = {
  饮料: { label: '功能性饮料', key: '功能性饮料', count: 2115 },
  台灯: { label: '桌面台灯', key: '桌面台灯', count: 2681 },
};

const clamp = (value: number, min: number, max: number) =>
  Math.min(Math.max(value, min), max);

const normalize = (value: number, max: number) => clamp((value / max) * 100, 0, 100);

const asImageSrc = (base64?: string | null) =>
  base64 ? `data:image/png;base64,${base64}` : '';

const formatNumber = (value: number, digits = 2) =>
  Number(value ?? 0).toFixed(digits);

const formatScore = (value: number) =>
  value <= 1 ? (value * 100).toFixed(1) : value.toFixed(2);

const getSuggestionLevel = (priority: string): SuggestionLevel => {
  if (priority === '高') return 'high';
  if (priority === '中') return 'medium';
  return 'low';
};

const getSuggestionIcon = (level: SuggestionLevel) => {
  if (level === 'high') {
    return <ArrowUp size={24} className="mt-1 shrink-0 text-gray-600" />;
  }
  if (level === 'medium') {
    return <ArrowDown size={24} className="mt-1 shrink-0 text-gray-600" />;
  }
  return <Minus size={24} className="mt-1 shrink-0 text-gray-600" />;
};

const getSuggestionStyle = (level: SuggestionLevel) => {
  if (level === 'high') {
    return {
      container:
        'bg-red-50 border-red-300 hover:border-red-400 hover:shadow-md',
      badge: 'bg-red-500 text-white',
      label: '高',
    };
  }
  if (level === 'medium') {
    return {
      container:
        'bg-yellow-50 border-yellow-300 hover:border-yellow-400 hover:shadow-md',
      badge: 'bg-yellow-500 text-white',
      label: '中',
    };
  }
  return {
    container:
      'bg-green-50 border-green-300 hover:border-green-400 hover:shadow-md',
    badge: 'bg-green-500 text-white',
    label: '低',
  };
};

export function DemoPage() {
  const [selectedCategory, setSelectedCategory] = useState<CategoryOption>('饮料');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!uploadedFile) {
      setPreviewUrl('');
      return;
    }

    const objectUrl = URL.createObjectURL(uploadedFile);
    setPreviewUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [uploadedFile]);

  const currentDataset = datasetMeta[selectedCategory];

  const radarData = useMemo<RadarDatum[]>(() => {
    if (!result) {
      return [];
    }

    return [
      {
        feature: '视觉熵',
        value: normalize(result.features.entropy, 10),
        display: formatNumber(result.features.entropy, 2),
      },
      {
        feature: '文字密度',
        value: normalize(result.features.text_density, 1),
        display: formatNumber(result.features.text_density, 2),
      },
      {
        feature: '亮度',
        value: normalize(result.features.brightness, 1),
        display: formatNumber(result.features.brightness, 2),
      },
      {
        feature: '对比度',
        value: normalize(result.features.contrast, 100),
        display: formatNumber(result.features.contrast, 2),
      },
      {
        feature: '饱和度',
        value: normalize(result.features.saturation, 1),
        display: formatNumber(result.features.saturation, 2),
      },
    ];
  }, [result]);

  const topProducts = result?.similar ?? [];

  const suggestions = useMemo(
    () =>
      (result?.advice ?? []).map((item) => ({
        ...item,
        level: getSuggestionLevel(item.priority),
      })),
    [result],
  );

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0] ?? null;
    setUploadedFile(nextFile);
    setResult(null);
    setError('');
  };

  const handleAnalyze = async () => {
    if (!uploadedFile) {
      setError('请先上传图片。');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);
      formData.append(
        'dataset_key',
        selectedCategory === '饮料' ? '功能性饮料' : '桌面台灯',
      );

      const res = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error ?? '分析失败，请稍后再试。');
      }
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : '分析失败，请稍后再试。');
    } finally {
      setLoading(false);
    }
  };

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
            系统演示
          </h1>
          <p className="text-lg text-gray-600 xl:text-xl">
            上传主图，获取 CTR 预测与智能诊断。
          </p>
        </div>

        <div className="grid gap-8 xl:grid-cols-5">
          <div className="space-y-6 xl:col-span-1">
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-all hover:shadow-md">
              <label className="mb-3 block text-sm font-bold text-gray-700">
                选择品类
              </label>
              <select
                value={selectedCategory}
                onChange={(event) => {
                  setSelectedCategory(event.target.value as CategoryOption);
                  setResult(null);
                  setError('');
                }}
                className="w-full cursor-pointer rounded-lg border-2 border-gray-300 px-4 py-3 font-medium transition-all hover:border-gray-400 focus:border-blue-500 focus:outline-none"
              >
                <option value="饮料">功能性饮料</option>
                <option value="台灯">桌面台灯</option>
              </select>
            </div>

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
                <Upload size={48} className="text-blue-500" />
                <div>
                  <p className="mb-1 font-bold text-gray-800">上传主图</p>
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
                  alt="上传预览"
                  className="size-full object-cover"
                />
              ) : (
                <div className="flex size-full items-center justify-center">
                  <ImageIcon size={48} className="text-gray-300" />
                </div>
              )}
            </div>

            <button
              type="button"
              onClick={handleAnalyze}
              disabled={!uploadedFile || loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 py-4 font-bold text-white shadow-lg transition-all hover:scale-[1.02] hover:from-blue-700 hover:to-cyan-700 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:scale-100"
            >
              {loading ? <LoaderCircle size={20} className="animate-spin" /> : null}
              {loading ? '分析中...' : '开始分析'}
            </button>

            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <div className="text-sm font-bold text-gray-600">当前数据集</div>
              <div className="mt-2 text-2xl font-black text-gray-900">
                {currentDataset.count}
              </div>
              <p className="mt-1 text-sm text-gray-600">{currentDataset.label}</p>
              <p className="mt-1 text-xs font-medium text-gray-500">
                前端 localhost:5173 · 接口 localhost:8000
              </p>
            </div>

            {error ? (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
                {error}
              </div>
            ) : null}
          </div>

          <div className="space-y-8 xl:col-span-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              className="rounded-2xl border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-cyan-50 p-8 shadow-lg transition-all hover:shadow-2xl xl:p-12"
            >
              <div className="flex flex-col gap-8 xl:flex-row xl:items-center xl:justify-between">
                <div>
                  <div className="mb-2 text-sm font-bold text-gray-600">
                    CTR预测评分
                  </div>
                  <div className="text-7xl font-black text-blue-600 xl:text-9xl">
                    {scoreDisplay}
                  </div>
                  <p className="mt-4 text-lg text-gray-600 xl:text-xl">
                    超过 <span className="font-bold text-green-600">{percentile}%</span>{' '}
                    同类商品
                  </p>
                  <p className="mt-2 text-sm font-medium text-gray-500">
                    原始预测值: {rawScore}
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
            </motion.div>

            <div className="grid gap-8 xl:grid-cols-2">
              <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-md transition-all hover:shadow-xl">
                <h3 className="mb-6 flex items-center gap-2 text-2xl font-bold text-gray-800">
                  <TrendingUp size={24} className="text-blue-600" />
                  视觉特征分析
                </h3>

                <div className="h-80">
                  {radarData.length ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={radarData}>
                        <PolarGrid stroke="#d1d5db" />
                        <PolarAngleAxis dataKey="feature" stroke="#374151" />
                        <PolarRadiusAxis domain={[0, 100]} stroke="#6b7280" />
                        <Radar
                          name="特征值"
                          dataKey="value"
                          stroke="#2563eb"
                          fill="#2563eb"
                          fillOpacity={0.3}
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex size-full items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50 text-sm font-medium text-gray-500">
                      分析完成后显示雷达图
                    </div>
                  )}
                </div>

                <div className="mt-6 grid grid-cols-2 gap-4 border-t-2 border-black pt-6 xl:grid-cols-5">
                  {(radarData.length
                    ? radarData
                    : [
                        { feature: '视觉熵', value: 0, display: '--' },
                        { feature: '文字密度', value: 0, display: '--' },
                        { feature: '亮度', value: 0, display: '--' },
                        { feature: '对比度', value: 0, display: '--' },
                        { feature: '饱和度', value: 0, display: '--' },
                      ]
                  ).map((item) => (
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
              </div>

              <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-md transition-all hover:shadow-xl">
                <h3 className="mb-6 text-2xl font-bold text-gray-800">
                  遮挡热力图分析
                </h3>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <div className="mb-3 text-sm font-bold text-gray-600">
                      原始图像
                    </div>
                    <div className="aspect-square overflow-hidden rounded-lg border-2 border-gray-200 bg-gray-50 transition-all hover:border-blue-300">
                      {previewUrl ? (
                        <img
                          src={previewUrl}
                          alt="原始图像"
                          className="size-full object-cover"
                        />
                      ) : (
                        <div className="flex size-full items-center justify-center">
                          <ImageIcon size={48} className="text-gray-400" />
                        </div>
                      )}
                    </div>
                  </div>
                  <div>
                    <div className="mb-3 text-sm font-bold text-gray-600">
                      CTR贡献热力图
                    </div>
                    <div className="aspect-square overflow-hidden rounded-lg border-2 border-gray-200 bg-gray-50 transition-all hover:border-blue-300">
                      {result?.heatmap_base64 ? (
                        <img
                          src={asImageSrc(result.heatmap_base64)}
                          alt="CTR热力图"
                          className="size-full object-cover"
                        />
                      ) : (
                        <div className="flex size-full items-center justify-center bg-gradient-to-br from-red-200 via-yellow-200 to-green-200">
                          <div className="text-center">
                            <div className="flex items-center justify-center gap-2 text-xs font-bold">
                              <div className="flex items-center gap-1">
                                <div className="h-4 w-4 rounded border border-gray-400 bg-red-500 shadow-sm" />
                                <span>高</span>
                              </div>
                              <div className="flex items-center gap-1">
                                <div className="h-4 w-4 rounded border border-gray-400 bg-yellow-500 shadow-sm" />
                                <span>中</span>
                              </div>
                              <div className="flex items-center gap-1">
                                <div className="h-4 w-4 rounded border border-gray-400 bg-green-500 shadow-sm" />
                                <span>低</span>
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
              <h3 className="mb-6 text-2xl font-bold text-gray-800">
                Top 5 相似爆款
              </h3>
              <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-5">
                {(topProducts.length
                  ? topProducts
                  : Array.from({ length: 5 }, (_, index) => ({
                      rank: index + 1,
                      img_name: '等待结果',
                      similarity: 0,
                      relative_ctr: 0,
                      price: 0,
                      img_base64: null,
                    }))
                ).map((product) => (
                  <motion.div
                    key={`${product.rank}-${product.img_name}`}
                    whileHover={{ scale: 1.05, y: -4 }}
                    className="cursor-pointer rounded-lg border-2 border-gray-200 p-4 transition-all hover:border-blue-400 hover:shadow-lg"
                  >
                    <div className="mb-4 aspect-square overflow-hidden rounded-lg border border-gray-200 bg-gray-50">
                      {product.img_base64 ? (
                        <img
                          src={asImageSrc(product.img_base64)}
                          alt={product.img_name}
                          className="size-full object-cover"
                        />
                      ) : (
                        <div className="flex size-full items-center justify-center">
                          <ImageIcon size={32} className="text-gray-400" />
                        </div>
                      )}
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="truncate text-sm font-bold text-gray-700">
                        #{product.rank} {product.img_name}
                      </div>
                      <div className="flex justify-between font-bold">
                        <span className="text-gray-600">相似度</span>
                        <span className="text-blue-600">
                          {(product.similarity * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="flex justify-between font-bold">
                        <span className="text-gray-600">CTR</span>
                        <span className="text-green-600">
                          {formatNumber(product.relative_ctr, 2)}
                        </span>
                      </div>
                      <div className="flex justify-between font-bold">
                        <span className="text-gray-600">价格</span>
                        <span className="text-gray-800">
                          ¥{formatNumber(product.price, 2)}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-md transition-all hover:shadow-xl">
              <h3 className="mb-6 text-2xl font-bold text-gray-800">优化建议</h3>
              <div className="space-y-4">
                {(suggestions.length
                  ? suggestions
                  : [
                      {
                        priority: '低',
                        category: '系统状态',
                        issue: '等待分析结果',
                        suggestion:
                          '上传图片并点击“开始分析”后，将显示基于模型的优化建议。',
                        level: 'low' as SuggestionLevel,
                      },
                    ]
                ).map((suggestion, index) => {
                  const style = getSuggestionStyle(suggestion.level);
                  return (
                    <motion.div
                      key={`${suggestion.category}-${index}`}
                      whileHover={{ x: 4 }}
                      className={`flex cursor-pointer items-start gap-4 rounded-xl border-2 p-6 transition-all ${style.container}`}
                    >
                      <div
                        className={`rounded-full px-3 py-1 text-sm font-bold ${style.badge}`}
                      >
                        {style.label}
                      </div>
                      {getSuggestionIcon(suggestion.level)}
                      <div className="flex-1">
                        <p className="font-semibold text-gray-800">
                          {suggestion.category}
                        </p>
                        <p className="mt-1 font-medium text-gray-700">
                          {suggestion.issue}
                        </p>
                        <p className="mt-2 text-sm text-gray-600">
                          {suggestion.suggestion}
                        </p>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
