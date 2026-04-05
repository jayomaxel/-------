const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000';

export interface AnalyzeFeatures {
  entropy: number;
  text_density: number;
  brightness: number;
  contrast: number;
  saturation: number;
  subject_area_ratio?: number;
  edge_density?: number;
  color_saturation?: number;
}

export interface AnalyzeCTR {
  score: number;
  percentile: number | null;
  percentile_available?: boolean;
}

export interface PsychologicalReport {
  lines: string[];
  text: string;
}

export interface SimilarItem {
  rank: number;
  dataset_key?: string;
  dataset_name?: string;
  img_name?: string;
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
  psychological_report: PsychologicalReport;
  warnings?: string[];
}

export async function analyzeImage(file: File): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: '未知错误' }));
    throw new Error(err.error ?? `HTTP ${res.status}`);
  }

  const data = (await res.json()) as Partial<AnalyzeResponse>;

  return {
    features: {
      entropy: data.features?.entropy ?? 0,
      text_density: data.features?.text_density ?? 0,
      brightness: data.features?.brightness ?? 0,
      contrast: data.features?.contrast ?? 0,
      saturation: data.features?.saturation ?? 0,
      subject_area_ratio: data.features?.subject_area_ratio ?? 0,
      edge_density: data.features?.edge_density ?? 0,
      color_saturation: data.features?.color_saturation ?? 0,
    },
    ctr: {
      score: data.ctr?.score ?? 0.5,
      percentile: data.ctr?.percentile ?? null,
      percentile_available: data.ctr?.percentile_available ?? false,
    },
    heatmap_base64: data.heatmap_base64 ?? '',
    similar: (data.similar ?? []).map((item) => ({
      rank: item.rank ?? 0,
      dataset_key: item.dataset_key ?? '',
      dataset_name: item.dataset_name ?? '',
      img_name: item.img_name ?? '',
      similarity: item.similarity ?? 0,
      relative_ctr: item.relative_ctr ?? 0,
      price: item.price ?? 0,
      img_base64: item.img_base64 ?? null,
    })),
    advice: data.advice ?? [],
    psychological_report: {
      lines: data.psychological_report?.lines ?? [],
      text: data.psychological_report?.text ?? '',
    },
    warnings: data.warnings ?? [],
  };
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
