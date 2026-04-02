import { Home, Microscope, TrendingUp, FolderOpen, BookOpen } from 'lucide-react';

interface SidebarProps {
  currentPage: string;
  onPageChange: (page: string) => void;
  mode: 'demo' | 'complete';
}

export function Sidebar({ currentPage, onPageChange, mode }: SidebarProps) {
  const demoItems = [
    { id: 'demo-mode', icon: '📊', label: '演示模式', disabled: true },
    { id: 'category', icon: '', label: '品类：功能性饮料 ▾', subdued: true },
    { id: 'upload', icon: '', label: '上传主图...', subdued: true },
    { id: 'analyze', icon: '▶', label: '开始分析', highlight: true },
  ];

  const completeItems = [
    { id: 'overview', icon: Home, label: '项目概览' },
    { id: 'demo', icon: Microscope, label: '系统演示' },
    { id: 'validation', icon: TrendingUp, label: '模型验证' },
    { id: 'dataset', icon: FolderOpen, label: '数据集概览' },
    { id: 'research', icon: BookOpen, label: '研究背景' },
  ];

  const items = mode === 'demo' ? demoItems : completeItems;

  return (
    <div className="w-72 bg-gradient-to-b from-slate-50 to-white border-r border-gray-200 flex flex-col shadow-sm">
      <div className="p-8 border-b border-gray-200">
        <div className="text-3xl font-black mb-2 bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
          CTR诊断
        </div>
        <div className="text-sm font-medium text-gray-600">电商主图智能分析</div>
      </div>

      <div className="flex-1 p-6 overflow-y-auto">
        {mode === 'complete' ? (
          <div className="space-y-2">
            {items.map((item) => {
              const Icon = item.icon as any;
              const isActive = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onPageChange(item.id)}
                  className={`w-full flex items-center gap-3 px-4 py-4 rounded-lg font-bold transition-all ${
                    isActive
                      ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg scale-105'
                      : 'bg-white text-gray-700 hover:bg-gray-100 hover:text-blue-600 hover:scale-102 border border-gray-200'
                  }`}
                >
                  <Icon size={20} />
                  <span className="text-sm">{item.label}</span>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="space-y-3">
            {items.map((item, idx) => {
              if (idx === 0) {
                return (
                  <div
                    key={item.id}
                    className="px-4 py-4 rounded-lg bg-gradient-to-r from-blue-100 to-cyan-100 border border-blue-300 font-bold text-sm text-blue-700"
                  >
                    {item.icon} {item.label}
                  </div>
                );
              }
              if (item.subdued) {
                return (
                  <div key={item.id} className="px-4 py-2 text-sm font-medium text-gray-600">
                    {item.label}
                  </div>
                );
              }
              if (item.highlight) {
                return (
                  <button
                    key={item.id}
                    className="w-full px-4 py-4 bg-gradient-to-r from-blue-600 to-cyan-600 text-white text-sm font-bold hover:from-blue-700 hover:to-cyan-700 hover:scale-105 transition-all rounded-lg shadow-md hover:shadow-lg"
                  >
                    {item.icon} {item.label}
                  </button>
                );
              }
              return null;
            })}
            <div className="h-px bg-gray-300 my-4" />
          </div>
        )}
      </div>

      <div className="p-6 border-t border-gray-200">
        <div className="text-xs font-bold text-center text-gray-500">
          神经营销学研究项目
        </div>
      </div>
    </div>
  );
}
