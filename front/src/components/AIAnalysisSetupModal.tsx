import type { AnalysisTone } from '../api/ai';

interface AIAnalysisSetupModalProps {
  open: boolean;
  apiKey: string;
  tone: AnalysisTone;
  loading: boolean;
  onApiKeyChange: (value: string) => void;
  onToneChange: (value: AnalysisTone) => void;
  onCancel: () => void;
  onConfirm: () => void;
}

const TONE_OPTIONS: Array<{ key: AnalysisTone; label: string; description: string }> = [
  { key: 'professional', label: '专业分析', description: '更适合汇报和正式诊断' },
  { key: 'gentle', label: '温和建议', description: '先肯定亮点，再温和指出问题' },
  { key: 'direct', label: '直接犀利', description: '快速定位问题，不绕弯' },
  { key: 'marketing', label: '增长导向', description: '更聚焦点击率和转化率' },
];

export default function AIAnalysisSetupModal({
  open,
  apiKey,
  tone,
  loading,
  onApiKeyChange,
  onToneChange,
  onCancel,
  onConfirm,
}: AIAnalysisSetupModalProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 px-4 backdrop-blur-sm">
      <div className="w-full max-w-2xl rounded-3xl bg-white p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-2xl font-black text-slate-900">开始分析前，先确认 AI 设置</h3>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              这里可以先选择本次要使用的 AI 语言风格，并填写 API Key。确认后会开始图片分析，等
              `/analyze` 返回后自动继续跑 `/ai-analysis`。
            </p>
          </div>

          <button
            type="button"
            onClick={onCancel}
            className="rounded-full bg-slate-100 px-3 py-2 text-sm font-medium text-slate-500 transition hover:bg-slate-200"
          >
            关闭
          </button>
        </div>

        <div className="mt-6">
          <label className="block text-sm font-semibold text-slate-800">AI API Key</label>
          <input
            type="password"
            value={apiKey}
            onChange={(event) => onApiKeyChange(event.target.value)}
            placeholder="可填写临时 API Key；留空则尝试使用服务端配置"
            className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-100"
          />
          <p className="mt-2 text-xs text-slate-400">
            已填写的 Key 只保存在当前浏览器本地，便于你后续继续切换语气复用。
          </p>
        </div>

        <div className="mt-6">
          <div className="text-sm font-semibold text-slate-800">AI 语言风格</div>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {TONE_OPTIONS.map((option) => {
              const active = option.key === tone;

              return (
                <button
                  key={option.key}
                  type="button"
                  onClick={() => onToneChange(option.key)}
                  className={`rounded-2xl border px-4 py-4 text-left transition ${
                    active
                      ? 'border-blue-500 bg-blue-50 shadow-sm'
                      : 'border-slate-200 bg-slate-50 hover:border-blue-300 hover:bg-blue-50/60'
                  }`}
                >
                  <div className="text-sm font-bold text-slate-900">{option.label}</div>
                  <div className="mt-1 text-xs leading-5 text-slate-500">{option.description}</div>
                </button>
              );
            })}
          </div>
        </div>

        <div className="mt-8 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-semibold text-slate-600 transition hover:bg-slate-50"
          >
            取消
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={loading}
            className="rounded-2xl bg-gradient-to-r from-blue-600 to-cyan-600 px-5 py-3 text-sm font-semibold text-white shadow-lg transition hover:from-blue-700 hover:to-cyan-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? '正在启动分析...' : '确认并开始分析'}
          </button>
        </div>
      </div>
    </div>
  );
}
