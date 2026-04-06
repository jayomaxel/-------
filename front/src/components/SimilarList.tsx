import type { SimilarItem } from '../api/analyze';

interface SimilarListProps {
  items: SimilarItem[];
}

type RelativeCtrMeta = {
  label: string;
  badgeClassName: string;
  valueClassName: string;
};

function formatRelativeCtrValue(value: number): string {
  const safeValue = Number.isFinite(value) ? Math.max(value, 0) : 0;
  const digits = safeValue >= 10 ? 1 : 2;
  return `${safeValue.toFixed(digits)}x`;
}

function describeRelativeCtr(value: number): string {
  const safeValue = Number.isFinite(value) ? Math.max(value, 0) : 0;

  if (safeValue >= 1.05) {
    const digits = safeValue >= 10 ? 1 : 2;
    return `约为同行均值的 ${safeValue.toFixed(digits)} 倍`;
  }

  if (safeValue >= 0.95) {
    return '与同行均值基本持平';
  }

  return `约为同行均值的 ${(safeValue * 100).toFixed(0)}%`;
}

function getRelativeCtrMeta(value: number): RelativeCtrMeta {
  const safeValue = Number.isFinite(value) ? Math.max(value, 0) : 0;

  if (safeValue < 0.8) {
    return {
      label: '低于同行',
      badgeClassName: 'bg-amber-100 text-amber-700',
      valueClassName: 'text-amber-600',
    };
  }

  if (safeValue < 1.2) {
    return {
      label: '接近均值',
      badgeClassName: 'bg-slate-100 text-slate-700',
      valueClassName: 'text-slate-700',
    };
  }

  if (safeValue < 3) {
    return {
      label: '优于同行',
      badgeClassName: 'bg-emerald-100 text-emerald-700',
      valueClassName: 'text-emerald-600',
    };
  }

  if (safeValue < 10) {
    return {
      label: '明显领先',
      badgeClassName: 'bg-green-100 text-green-700',
      valueClassName: 'text-green-600',
    };
  }

  return {
    label: '爆款潜力',
    badgeClassName: 'bg-rose-100 text-rose-700',
    valueClassName: 'text-rose-600',
  };
}

export function SimilarList({ items }: SimilarListProps) {
  return (
    <div>
      <div className="mb-6 flex flex-col gap-2">
        <h3 className="text-2xl font-bold text-gray-800">相似竞品图片</h3>
        <p className="text-sm text-gray-500">
          基准：同类竞品平均 CTR = 1.0，数值越大说明相对点击表现越强。
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-5">
        {items.map((item) => {
          const relativeCtrMeta = getRelativeCtrMeta(item.relative_ctr);

          return (
            <div
              key={`${item.rank}-${item.dataset_key ?? ''}-${item.dataset_name ?? ''}`}
              className="card-hover rounded-lg border-2 border-gray-200 p-4 transition-all hover:border-blue-400 hover:shadow-lg"
            >
              <div className="mb-4 aspect-square overflow-hidden rounded-lg border border-gray-200 bg-gray-50">
                {item.img_base64 ? (
                  <img
                    src={`data:image/png;base64,${item.img_base64}`}
                    alt={`相似竞品 ${item.rank}`}
                    className="size-full object-cover"
                  />
                ) : (
                  <div className="flex size-full items-center justify-center">
                    <i
                      data-lucide="image"
                      className="text-gray-400"
                      style={{ width: 32, height: 32 }}
                    />
                  </div>
                )}
              </div>

              <div className="space-y-3 text-sm">
                {item.dataset_name ? (
                  <div className="inline-flex rounded-full bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700">
                    {item.dataset_name}
                  </div>
                ) : null}

                <p className="flex justify-between font-bold">
                  <span className="text-gray-600">相似度</span>
                  <span className="text-blue-600">
                    {(item.similarity * 100).toFixed(1)}%
                  </span>
                </p>

                <div
                  className="rounded-xl border border-gray-200 bg-gray-50/80 p-3"
                  title="以同类竞品平均 CTR = 1.0 为基准，数值越大说明相对点击表现越强。"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-xs font-semibold text-gray-600">
                      CTR 相对行业均值
                    </span>
                    <span
                      className={`rounded-full px-2 py-1 text-[11px] font-semibold ${relativeCtrMeta.badgeClassName}`}
                    >
                      {relativeCtrMeta.label}
                    </span>
                  </div>

                  <div className={`mt-3 text-2xl font-black ${relativeCtrMeta.valueClassName}`}>
                    {formatRelativeCtrValue(item.relative_ctr)}
                  </div>

                  <p className="mt-1 text-xs leading-5 text-gray-600">
                    {describeRelativeCtr(item.relative_ctr)}
                  </p>
                </div>

                <p className="flex justify-between font-bold">
                  <span className="text-gray-600">价格</span>
                  <span className="text-gray-800">¥{item.price.toFixed(2)}</span>
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
