import { useEffect, useMemo, useRef, useState } from 'react';
import {
  fetchAIAnalysis,
  type AIAnalysisResult,
  type AnalysisTone,
} from '../api/ai';

interface Props {
  features: Record<string, number>;
  ctrScore: number;
  ready: boolean;
  tone: AnalysisTone;
  apiKey: string;
  onToneChange: (tone: AnalysisTone) => void;
  onOpenConfig: () => void;
}

const TONE_OPTIONS: Array<{ key: AnalysisTone; label: string; emoji: string }> = [
  { key: 'professional', label: '专业分析', emoji: '📊' },
  { key: 'gentle', label: '温和建议', emoji: '🤝' },
  { key: 'direct', label: '直接犀利', emoji: '⚡' },
  { key: 'marketing', label: '增长导向', emoji: '🚀' },
];

export default function AIAnalysisCard({
  features,
  ctrScore,
  ready,
  tone,
  apiKey,
  onToneChange,
  onOpenConfig,
}: Props) {
  const [result, setResult] = useState<AIAnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const cacheRef = useRef<Map<string, AIAnalysisResult>>(new Map());
  const requestIdRef = useRef(0);

  const normalizedApiKey = apiKey.trim();
  const analysisFingerprint = useMemo(
    () => JSON.stringify({ features, ctrScore }),
    [features, ctrScore],
  );
  const cacheKey = useMemo(
    () => `${analysisFingerprint}::${tone}::${normalizedApiKey || '__server_default__'}`,
    [analysisFingerprint, tone, normalizedApiKey],
  );

  useEffect(() => {
    if (!ready) {
      requestIdRef.current += 1;
      setResult(null);
      setLoading(false);
      return;
    }

    const cached = cacheRef.current.get(cacheKey);
    if (cached) {
      setResult(cached);
      setLoading(false);
      return;
    }

    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    setLoading(true);
    setResult(null);

    void (async () => {
      try {
        const data = await fetchAIAnalysis(features, ctrScore, tone, normalizedApiKey);
        if (requestId !== requestIdRef.current) {
          return;
        }

        cacheRef.current.set(cacheKey, data);
        setResult(data);
      } catch {
        if (requestId !== requestIdRef.current) {
          return;
        }

        const fallbackResult: AIAnalysisResult = {
          tone,
          summary: '',
          strengths: [],
          problems: [],
          suggestions: [],
          success: false,
          error: 'AI 分析暂时不可用',
        };
        setResult(fallbackResult);
      } finally {
        if (requestId === requestIdRef.current) {
          setLoading(false);
        }
      }
    })();
  }, [cacheKey, ctrScore, features, normalizedApiKey, ready, tone]);

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-md transition-all hover:shadow-xl">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="flex items-center gap-2 text-lg font-bold text-gray-900">
            <span>🤖</span>
            <span>AI 智能分析</span>
          </h3>
          <p className="mt-2 text-sm leading-6 text-gray-500">
            选择喜欢的语言风格后，AI 会基于当前主图特征和 CTR 预测生成总结、亮点、问题与建议。
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <span className="rounded-full bg-slate-100 px-3 py-2 text-xs font-medium text-slate-500">
            API Key：{normalizedApiKey ? '已配置' : '使用服务端默认'}
          </span>
          <button
            type="button"
            onClick={onOpenConfig}
            className="rounded-full border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 transition hover:bg-slate-50"
          >
            AI 设置
          </button>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        {TONE_OPTIONS.map((option) => (
          <button
            key={option.key}
            type="button"
            onClick={() => onToneChange(option.key)}
            className={`rounded-full px-4 py-2 text-sm font-medium transition-all ${
              tone === option.key
                ? 'bg-blue-600 text-white shadow-md'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {option.emoji} {option.label}
          </button>
        ))}
      </div>

      {!ready ? (
        <div className="mt-6 rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-5 py-10 text-center text-sm font-medium text-slate-500">
          先点击“开始分析”，系统会先完成图片分析，再自动继续生成 AI 诊断内容。
        </div>
      ) : null}

      {ready && loading ? (
        <div className="mt-6 flex items-center justify-center gap-3 rounded-2xl bg-slate-50 py-10 text-gray-400">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
          <span>AI 正在分析中...</span>
        </div>
      ) : null}

      {ready && !loading && result && result.success ? (
        <div className="mt-6 space-y-5">
          {result.summary ? (
            <div className="rounded-xl bg-blue-50 p-4">
              <p className="leading-relaxed text-gray-700">{result.summary}</p>
            </div>
          ) : null}

          {result.strengths.length > 0 ? (
            <div>
              <h4 className="mb-2 text-sm font-semibold text-green-600">✅ 亮点</h4>
              <ul className="space-y-1.5">
                {result.strengths.map((item, index) => (
                  <li
                    key={`${index}-${item}`}
                    className="relative pl-4 text-sm text-gray-600 before:absolute before:left-0 before:text-green-500 before:content-['•']"
                  >
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {result.problems.length > 0 ? (
            <div>
              <h4 className="mb-2 text-sm font-semibold text-orange-600">⚠️ 问题</h4>
              <ul className="space-y-1.5">
                {result.problems.map((item, index) => (
                  <li
                    key={`${index}-${item}`}
                    className="relative pl-4 text-sm text-gray-600 before:absolute before:left-0 before:text-orange-500 before:content-['•']"
                  >
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {result.suggestions.length > 0 ? (
            <div>
              <h4 className="mb-2 text-sm font-semibold text-blue-600">💡 建议</h4>
              <ul className="space-y-1.5">
                {result.suggestions.map((item, index) => (
                  <li
                    key={`${index}-${item}`}
                    className="relative pl-4 text-sm text-gray-600 before:absolute before:left-0 before:text-blue-500 before:content-['•']"
                  >
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}

      {ready && !loading && result && !result.success ? (
        <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 py-8 text-center text-gray-400">
          <p>AI 分析暂时不可用</p>
          <p className="mt-1 text-xs">{result.error || '请稍后重试'}</p>
        </div>
      ) : null}
    </div>
  );
}
