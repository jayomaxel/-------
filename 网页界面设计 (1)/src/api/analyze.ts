const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000';

export interface AnalyzeFeatures {
  entropy: number;
  text_density: number;
  brightness: number;
  contrast: number;
  saturation: number;
}

export interface AnalyzeCTR {
  score: number;
  percentile: number;
}

export interface SimilarItem {
  rank: number;
  img_name: string;
  similarity: number;
  relative_ctr: number;
  price: number;
  img_base64: string | null;
}

export interface AdviceItem {
  priority: string;
  category: string;
  issue: string;
  suggestion: string;
}

export interface AnalyzeResponse {
  features: AnalyzeFeatures;
  ctr: AnalyzeCTR;
  heatmap_base64: string;
  similar: SimilarItem[];
  advice: AdviceItem[];
}

export async function analyzeImage(file: File): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: '\u672a\u77e5\u9519\u8bef' }));
    throw new Error(err.error ?? `HTTP ${res.status}`);
  }

  return res.json();
}

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    const data = await res.json();
    return data.status === 'ok';
  } catch {
    return false;
  }
}
