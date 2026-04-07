const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000';

const ANALYZE_RETRY_DELAY_MS = 800;
const BACKEND_READY_TIMEOUT_MS = 12000;
const BACKEND_READY_POLL_MS = 500;

export interface AnalyzeFeatures {
  entropy?: number;
  text_density?: number;
  subject_area_ratio?: number;
  edge_density?: number;
  color_saturation?: number;
}

export interface AnalyzeCTR {
  score: number;
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

const sleep = (ms: number) =>
  new Promise<void>((resolve) => {
    window.setTimeout(resolve, ms);
  });

async function waitForBackendReady(
  timeoutMs = BACKEND_READY_TIMEOUT_MS,
  pollMs = BACKEND_READY_POLL_MS,
): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        const data = (await res.json().catch(() => null)) as { status?: string } | null;
        if (data?.status === 'ok') {
          return true;
        }
      }
    } catch {
      // 后端还没起来时这里会失败，继续轮询即可。
    }

    await sleep(pollMs);
  }

  return false;
}

export async function analyzeImage(file: File): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append('file', file);

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      body: formData,
    });
  } catch (error) {
    const backendReady = await waitForBackendReady();
    if (!backendReady) {
      throw error;
    }

    await sleep(ANALYZE_RETRY_DELAY_MS);
    res = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      body: formData,
    });
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: '未知错误' }));
    throw new Error(err.error ?? `HTTP ${res.status}`);
  }

  const data = (await res.json()) as Partial<AnalyzeResponse>;

  const features: AnalyzeFeatures = {
    ...(typeof data.features?.entropy === 'number'
      ? { entropy: data.features.entropy }
      : {}),
    ...(typeof data.features?.text_density === 'number'
      ? { text_density: data.features.text_density }
      : {}),
    ...(typeof data.features?.subject_area_ratio === 'number'
      ? { subject_area_ratio: data.features.subject_area_ratio }
      : {}),
    ...(typeof data.features?.edge_density === 'number'
      ? { edge_density: data.features.edge_density }
      : {}),
    ...(typeof data.features?.color_saturation === 'number'
      ? { color_saturation: data.features.color_saturation }
      : {}),
  };

  return {
    features,
    ctr: {
      score: data.ctr?.score ?? 0.5,
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
    return await waitForBackendReady(BACKEND_READY_POLL_MS, BACKEND_READY_POLL_MS);
  } catch {
    return false;
  }
}
