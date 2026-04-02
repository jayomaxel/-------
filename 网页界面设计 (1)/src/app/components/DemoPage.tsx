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

type CategoryOption = '楗枡' | '鍙扮伅';

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
  楗枡: { label: '鍔熻兘鎬чギ鏂?, key: '鍔熻兘鎬чギ鏂?, count: 2115 },
  鍙扮伅: { label: '妗岄潰鍙扮伅', key: '妗岄潰鍙扮伅', count: 2681 },
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
  if (priority === '楂?) return 'high';
  if (priority === '涓?) return 'medium';
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
      label: '楂?,
    };
  }
  if (level === 'medium') {
    return {
      container:
        'bg-yellow-50 border-yellow-300 hover:border-yellow-400 hover:shadow-md',
      badge: 'bg-yellow-500 text-white',
      label: '涓?,
    };
  }
  return {
    container:
      'bg-green-50 border-green-300 hover:border-green-400 hover:shadow-md',
    badge: 'bg-green-500 text-white',
    label: '浣?,
  };
};

export function DemoPage() {
  const [selectedCategory, setSelectedCategory] = useState<CategoryOption>('楗枡');
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
        feature: '瑙嗚鐔?,
        value: normalize(result.features.entropy, 10),
        display: formatNumber(result.features.entropy, 2),
      },
      {
        feature: '鏂囧瓧瀵嗗害',
        value: normalize(result.features.text_density, 1),
        display: formatNumber(result.features.text_density, 2),
      },
      {
        feature: '浜害',
        value: normalize(result.features.brightness, 1),
        display: formatNumber(result.features.brightness, 2),
      },
      {
        feature: '瀵规瘮搴?,
        value: normalize(result.features.contrast, 100),
        display: formatNumber(result.features.contrast, 2),
      },
      {
        feature: '楗卞拰搴?,
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
      setError('璇峰厛涓婁紶鍥剧墖銆?);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);
      formData.append(
        'dataset_key',
        selectedCategory === '楗枡' ? '鍔熻兘鎬чギ鏂? : '妗岄潰鍙扮伅',
      );

      const res = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.error ?? '鍒嗘瀽澶辫触锛岃绋嶅悗鍐嶈瘯銆?);
      }
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : '鍒嗘瀽澶辫触锛岃绋嶅悗鍐嶈瘯銆?);
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
            绯荤粺婕旂ず
          </h1>
          <p className="text-lg text-gray-600 xl:text-xl">
            涓婁紶涓诲浘锛岃幏鍙朇TR棰勬祴涓庢櫤鑳借瘖鏂?          </p>
        </div>

        <div className="grid gap-8 xl:grid-cols-5">
          <div className="space-y-6 xl:col-span-1">
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm transition-all hover:shadow-md">
              <label className="mb-3 block text-sm font-bold text-gray-700">
                閫夋嫨鍝佺被
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
                <option value="楗枡">鍔熻兘鎬чギ鏂?/option>
                <option value="鍙扮伅">妗岄潰鍙扮伅</option>
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
                  <p className="mb-1 font-bold text-gray-800">涓婁紶涓诲浘</p>
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
                  alt="涓婁紶棰勮"
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
              {loading ? '鍒嗘瀽涓?..' : '寮€濮嬪垎鏋?}
            </button>

            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <div className="text-sm font-bold text-gray-600">褰撳墠鏁版嵁闆?/div>
              <div className="mt-2 text-2xl font-black text-gray-900">
                {currentDataset.count}
              </div>
              <p className="mt-1 text-sm text-gray-600">{currentDataset.label}</p>
              <p className="mt-1 text-xs font-medium text-gray-500">
                鍓嶇 localhost:5173 路 鎺ュ彛 localhost:8000
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
                    CTR棰勬祴璇勫垎
                  </div>
                  <div className="text-7xl font-black text-blue-600 xl:text-9xl">
                    {scoreDisplay}
                  </div>
                  <p className="mt-4 text-lg text-gray-600 xl:text-xl">
                    瓒呰繃 <span className="font-bold text-green-600">{percentile}%</span>{' '}
                    鍚岀被鍟嗗搧
                  </p>
                  <p className="mt-2 text-sm font-medium text-gray-500">
                    鍘熷棰勬祴鍊?{rawScore}
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
                  瑙嗚鐗瑰緛鍒嗘瀽
                </h3>

                <div className="h-80">
                  {radarData.length ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={radarData}>
                        <PolarGrid stroke="#d1d5db" />
                        <PolarAngleAxis dataKey="feature" stroke="#374151" />
                        <PolarRadiusAxis domain={[0, 100]} stroke="#6b7280" />
                        <Radar
                          name="鐗瑰緛鍊?
                          dataKey="value"
                          stroke="#2563eb"
                          fill="#2563eb"
                          fillOpacity={0.3}
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex size-full items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50 text-sm font-medium text-gray-500">
                      鍒嗘瀽瀹屾垚鍚庢樉绀洪浄杈惧浘
                    </div>
                  )}
                </div>

                <div className="mt-6 grid grid-cols-2 gap-4 border-t-2 border-black pt-6 xl:grid-cols-5">
                  {(radarData.length
                    ? radarData
                    : [
                        { feature: '瑙嗚鐔?, value: 0, display: '--' },
                        { feature: '鏂囧瓧瀵嗗害', value: 0, display: '--' },
                        { feature: '浜害', value: 0, display: '--' },
                        { feature: '瀵规瘮搴?, value: 0, display: '--' },
                        { feature: '楗卞拰搴?, value: 0, display: '--' },
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
                  閬尅鐑姏鍥惧垎鏋?                </h3>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <div className="mb-3 text-sm font-bold text-gray-600">
                      鍘熷鍥惧儚
                    </div>
                    <div className="aspect-square overflow-hidden rounded-lg border-2 border-gray-200 bg-gray-50 transition-all hover:border-blue-300">
                      {previewUrl ? (
                        <img
                          src={previewUrl}
                          alt="鍘熷鍥惧儚"
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
                      CTR璐＄尞鐑姏鍥?                    </div>
                    <div className="aspect-square overflow-hidden rounded-lg border-2 border-gray-200 bg-gray-50 transition-all hover:border-blue-300">
                      {result?.heatmap_base64 ? (
                        <img
                          src={asImageSrc(result.heatmap_base64)}
                          alt="CTR鐑姏鍥?
                          className="size-full object-cover"
                        />
                      ) : (
                        <div className="flex size-full items-center justify-center bg-gradient-to-br from-red-200 via-yellow-200 to-green-200">
                          <div className="text-center">
                            <div className="flex items-center justify-center gap-2 text-xs font-bold">
                              <div className="flex items-center gap-1">
                                <div className="h-4 w-4 rounded border border-gray-400 bg-red-500 shadow-sm" />
                                <span>楂?/span>
                              </div>
                              <div className="flex items-center gap-1">
                                <div className="h-4 w-4 rounded border border-gray-400 bg-yellow-500 shadow-sm" />
                                <span>涓?/span>
                              </div>
                              <div className="flex items-center gap-1">
                                <div className="h-4 w-4 rounded border border-gray-400 bg-green-500 shadow-sm" />
                                <span>浣?/span>
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
                Top 5 鐩镐技鐖嗘
              </h3>
              <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-5">
                {(topProducts.length
                  ? topProducts
                  : Array.from({ length: 5 }, (_, index) => ({
                      rank: index + 1,
                      img_name: '绛夊緟缁撴灉',
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
                        <span className="text-gray-600">鐩镐技搴?/span>
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
                        <span className="text-gray-600">浠锋牸</span>
                        <span className="text-gray-800">
                          楼{formatNumber(product.price, 2)}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-8 shadow-md transition-all hover:shadow-xl">
              <h3 className="mb-6 text-2xl font-bold text-gray-800">浼樺寲寤鸿</h3>
              <div className="space-y-4">
                {(suggestions.length
                  ? suggestions
                  : [
                      {
                        priority: '浣?,
                        category: '绯荤粺鐘舵€?,
                        issue: '绛夊緟鍒嗘瀽缁撴灉',
                        suggestion: '涓婁紶鍥剧墖骞剁偣鍑烩€滃紑濮嬪垎鏋愨€濆悗锛屽皢鏄剧ず鍩轰簬妯″瀷鐨勪紭鍖栧缓璁€?,
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
