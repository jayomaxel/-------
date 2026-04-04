import type { AdviceItem } from '../api/analyze';

const priorityColor: Record<string, string> = {
  高: '#ff4d4f',
  中: '#faad14',
  低: '#52c41a',
};

interface AdviceListProps {
  items: AdviceItem[];
}

export function AdviceList({ items }: AdviceListProps) {
  return (
    <div>
      <h3 className="mb-6 text-2xl font-bold text-gray-800">优化建议</h3>
      <div className="space-y-4">
        {items.map((item, index) => (
          <div
            key={`${item.category}-${index}`}
            className="suggestion-hover rounded-xl border border-gray-200 bg-white p-5 shadow-sm"
            style={{ borderLeft: `4px solid ${priorityColor[item.priority] ?? '#999'}` }}
          >
            <strong className="text-base text-gray-800">
              [{item.priority}] {item.category}
            </strong>
            <p className="mt-2 text-sm font-medium text-gray-700">问题：{item.issue}</p>
            <p className="mt-2 text-sm text-gray-600">建议：{item.suggestion}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
