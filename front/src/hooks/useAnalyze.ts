import { useCallback, useState } from 'react';
import { analyzeImage, type AnalyzeResponse } from '../api/analyze';

interface UseAnalyzeReturn {
  result: AnalyzeResponse | null;
  loading: boolean;
  error: string | null;
  analyze: (file: File) => Promise<void>;
  reset: () => void;
}

export function useAnalyze(): UseAnalyzeReturn {
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyze = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await analyzeImage(file);
      setResult(data);
    } catch (err: any) {
      setError(err.message ?? '分析失败，请检查后端是否启动');
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setLoading(false);
  }, []);

  return { result, loading, error, analyze, reset };
}
