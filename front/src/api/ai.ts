const AI_API_BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000';

export type AnalysisTone = 'professional' | 'gentle' | 'direct' | 'marketing';

export interface AIAnalysisResult {
  tone: string;
  summary: string;
  strengths: string[];
  problems: string[];
  suggestions: string[];
  success: boolean;
  error?: string;
}

export async function fetchAIAnalysis(
  features: Record<string, number>,
  ctrScore: number,
  tone: AnalysisTone = 'professional',
  apiKey = '',
): Promise<AIAnalysisResult> {
  const response = await fetch(`${AI_API_BASE}/ai-analysis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      tone,
      features,
      ctr_score: ctrScore,
      api_key: apiKey.trim() || undefined,
    }),
  });

  const data = (await response.json().catch(() => ({
    success: false,
    error: 'AI 分析请求失败，请稍后重试。',
  }))) as Partial<AIAnalysisResult>;

  return {
    tone: data.tone ?? tone,
    summary: data.summary ?? '',
    strengths: data.strengths ?? [],
    problems: data.problems ?? [],
    suggestions: data.suggestions ?? [],
    success: data.success ?? response.ok,
    error: data.error,
  };
}
