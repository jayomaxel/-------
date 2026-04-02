import { ChangeEvent, useEffect, useMemo, useState } from 'react';

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

const datasetMeta: Record<CategoryOption, { label: string; key: string; count: number }> = {
  饮料: { label: '功能性饮料', key: '功能性饮料', count: 2115 },
  台灯: { label: '桌面台灯', key: '桌面台灯', count: 2681 },
};

const priorityClassMap: Record<string, string> = {
  高: 'advice-high',
  中: 'advice-medium',
  低: 'advice-low',
};

const asImageSrc = (base64?: string | null) => (base64 ? `data:image/png;base64,${base64}` : '');
const formatNumber = (value: number, digits = 2) => Number(value ?? 0).toFixed(digits);
const formatPercent = (value: number) => `${Math.round(Number(value ?? 0) * 100)}%`;

export default function DemoPage() {
  const [selectedCategory, setSelectedCategory] = useState<CategoryOption>('饮料');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!uploadedFile) {
      setPreviewUrl('');
      return;
    }

    const objectUrl = URL.createObjectURL(uploadedFile);
    setPreviewUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [uploadedFile]);

  const currentDataset = useMemo(() => datasetMeta[selectedCategory], [selectedCategory]);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const nextFile = event.target.files?.[0] ?? null;
    setUploadedFile(nextFile);
    setResult(null);
    setError('');
  };

  const handleAnalyze = async () => {
    if (!uploadedFile) {
      setError('请先上传一张图片。');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);
      formData.append('dataset_key', selectedCategory === '饮料' ? '功能性饮料' : '桌面台灯');

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

  return (
    <div className="page-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Fixed Sidebar</p>
          <h1>电商主图智能认知诊断系统</h1>
          <p className="sidebar-copy">
            上传商品主图后，系统会自动完成视觉特征提取、CTR 预测、热力图解释与相似爆款检索。
          </p>
        </div>

        <div className="sidebar-block">
          <label className="field-label" htmlFor="category-select">
            分析品类
          </label>
          <select
            id="category-select"
            className="input-control"
            value={selectedCategory}
            onChange={(event) => {
              setSelectedCategory(event.target.value as CategoryOption);
              setResult(null);
              setError('');
            }}
          >
            <option value="饮料">功能性饮料</option>
            <option value="台灯">桌面台灯</option>
          </select>
        </div>

        <div className="sidebar-block">
          <label className="field-label" htmlFor="file-upload">
            上传主图
          </label>
          <input id="file-upload" className="input-control file-input" type="file" accept="image/*" onChange={handleFileChange} />
          <button className="analyze-button" onClick={handleAnalyze} disabled={!uploadedFile || loading}>
            {loading ? '分析中...' : '开始分析'}
          </button>
        </div>

        <div className="sidebar-block stats-card">
          <span className="muted-label">数据集统计</span>
          <strong>{currentDataset.count} 张参考图</strong>
          <span>{currentDataset.label}</span>
          <span>前后端分离 · FastAPI</span>
        </div>

        <div className="sidebar-block sidebar-note">
          <span>侧边栏固定展开</span>
          <span>切换品类后会清空当前结果</span>
          <span>开发阶段跨域已全部放开</span>
        </div>

        {error ? <div className="error-banner">{error}</div> : null}
      </aside>

      <main className="main-content">
        <section className="panel preview-panel">
          <div className="panel-header">
            <div>
              <p className="panel-eyebrow">Zone 1</p>
              <h2>图片预览</h2>
            </div>
            <span className="panel-tag">本地文件读取</span>
          </div>

          <div className="preview-grid">
            <div className="image-frame">
              {previewUrl ? <img src={previewUrl} alt="上传预览" /> : <div className="empty-state">上传图片后在这里显示预览</div>}
            </div>
            <div className="file-meta">
              <div>
                <span className="meta-label">文件名</span>
                <strong>{uploadedFile?.name ?? '未上传'}</strong>
              </div>
              <div>
                <span className="meta-label">文件大小</span>
                <strong>{uploadedFile ? `${(uploadedFile.size / 1024).toFixed(1)} KB` : '--'}</strong>
              </div>
              <div>
                <span className="meta-label">当前品类</span>
                <strong>{currentDataset.label}</strong>
              </div>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-eyebrow">Zone 2</p>
              <h2>视觉指标卡片</h2>
            </div>
            <span className="panel-tag">extract_features</span>
          </div>

          <div className="metric-grid">
            <MetricCard title="视觉熵" value={result ? formatNumber(result.features.entropy, 2) : '--'} />
            <MetricCard title="文字密度" value={result ? formatPercent(result.features.text_density) : '--'} />
            <MetricCard title="亮度" value={result ? formatPercent(result.features.brightness) : '--'} />
            <MetricCard title="对比度" value={result ? formatNumber(result.features.contrast, 2) : '--'} />
            <MetricCard title="饱和度" value={result ? formatPercent(result.features.saturation) : '--'} />
          </div>
        </section>

        <section className="panel ctr-panel">
          <div className="panel-header">
            <div>
              <p className="panel-eyebrow">Zone 3</p>
              <h2>CTR 预测分数</h2>
            </div>
            <span className="panel-tag">predict_ctr</span>
          </div>

          <div className="ctr-layout">
            <div className="score-card">
              <span className="meta-label">CTR 分数</span>
              <strong>{result ? formatNumber(result.ctr.score, 4) : '--'}</strong>
            </div>
            <div className="percentile-card">
              <div className="progress-track">
                <div className="progress-fill" style={{ width: `${result?.ctr.percentile ?? 0}%` }} />
              </div>
              <p>{result ? `优于 ${result.ctr.percentile}% 同类商品` : '等待分析结果'}</p>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-eyebrow">Zone 4</p>
              <h2>热力图对比</h2>
            </div>
            <span className="panel-tag">generate_heatmap</span>
          </div>

          <div className="heatmap-grid">
            <div className="image-frame wide-frame">
              {previewUrl ? <img src={previewUrl} alt="原始图片" /> : <div className="empty-state">原图将在此处显示</div>}
              <span className="frame-label">原始图片</span>
            </div>
            <div className="image-frame wide-frame">
              {result?.heatmap_base64 ? <img src={asImageSrc(result.heatmap_base64)} alt="热力图" /> : <div className="empty-state">热力图将在分析完成后显示</div>}
              <span className="frame-label">热力图结果</span>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-eyebrow">Zone 5</p>
              <h2>相似爆款 Top 5</h2>
            </div>
            <span className="panel-tag">retrieve_similar</span>
          </div>

          <div className="similar-grid">
            {result?.similar?.length ? (
              result.similar.map((item) => (
                <article key={`${item.rank}-${item.img_name}`} className="similar-card">
                  <div className="similar-image-wrap">
                    {item.img_base64 ? (
                      <img src={asImageSrc(item.img_base64)} alt={item.img_name} />
                    ) : (
                      <div className="empty-thumb">图片缺失</div>
                    )}
                  </div>
                  <div className="similar-meta">
                    <strong>#{item.rank}</strong>
                    <span className="truncate" title={item.img_name}>
                      {item.img_name}
                    </span>
                    <span>相似度 {formatNumber(item.similarity, 4)}</span>
                    <span>CTR {formatNumber(item.relative_ctr, 4)}</span>
                    <span>价格 {formatNumber(item.price, 2)}</span>
                  </div>
                </article>
              ))
            ) : (
              <div className="empty-state block-empty">分析完成后展示 5 张相似主图</div>
            )}
          </div>
        </section>

        <section className="panel">
          <div className="panel-header">
            <div>
              <p className="panel-eyebrow">Zone 6</p>
              <h2>优化建议</h2>
            </div>
            <span className="panel-tag">generate_advice</span>
          </div>

          <div className="advice-list">
            {result?.advice?.length ? (
              result.advice.map((item, index) => (
                <article key={`${item.priority}-${item.category}-${index}`} className={`advice-item ${priorityClassMap[item.priority] ?? 'advice-low'}`}>
                  <div className="advice-topline">
                    <strong>{item.priority}</strong>
                    <span>{item.category}</span>
                  </div>
                  <p>{item.issue}</p>
                  <p className="advice-suggestion">{item.suggestion}</p>
                </article>
              ))
            ) : (
              <div className="empty-state block-empty">等待分析结果，生成针对性的主图优化建议</div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

type MetricCardProps = {
  title: string;
  value: string;
};

function MetricCard({ title, value }: MetricCardProps) {
  return (
    <article className="metric-card">
      <span>{title}</span>
      <strong>{value}</strong>
    </article>
  );
}
