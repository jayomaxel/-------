import type { SimilarItem } from '../api/analyze';

interface SimilarListProps {
  items: SimilarItem[];
}

export function SimilarList({ items }: SimilarListProps) {
  return (
    <div>
      <h3 className="mb-6 text-2xl font-bold text-gray-800">相似竞品图片</h3>
      <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-5">
        {items.map((item) => (
          <div
            key={`${item.rank}-${item.img_name}`}
            className="card-hover rounded-lg border-2 border-gray-200 p-4 transition-all hover:border-blue-400 hover:shadow-lg"
          >
            <div className="mb-4 aspect-square overflow-hidden rounded-lg border border-gray-200 bg-gray-50">
              {item.img_base64 ? (
                <img
                  src={`data:image/png;base64,${item.img_base64}`}
                  alt={item.img_name}
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

            <div className="space-y-2 text-sm">
              <div className="truncate text-sm font-bold text-gray-700">
                #{item.rank} {item.img_name}
              </div>
              <p className="flex justify-between font-bold">
                <span className="text-gray-600">相似度</span>
                <span className="text-blue-600">
                  {(item.similarity * 100).toFixed(1)}%
                </span>
              </p>
              <p className="flex justify-between font-bold">
                <span className="text-gray-600">相对CTR</span>
                <span className="text-green-600">{item.relative_ctr.toFixed(2)}</span>
              </p>
              <p className="flex justify-between font-bold">
                <span className="text-gray-600">价格</span>
                <span className="text-gray-800">¥{item.price.toFixed(2)}</span>
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
