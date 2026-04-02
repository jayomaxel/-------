import { motion } from 'motion/react';
import { useState } from 'react';
import { Database, Image as ImageIcon } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';

export function DatasetPage() {
  const [activeTab, setActiveTab] = useState<'drink' | 'lamp'>('drink');

  const drinkStats = {
    samples: 2115,
    ctrRange: '1.2 - 12.5',
    avgPrice: 45,
    distribution: [
      { range: '0-2', count: 120 },
      { range: '2-4', count: 280 },
      { range: '4-6', count: 450 },
      { range: '6-8', count: 580 },
      { range: '8-10', count: 425 },
      { range: '10-12', count: 200 },
      { range: '12+', count: 60 },
    ],
  };

  const lampStats = {
    samples: 2681,
    ctrRange: '0.8 - 10.3',
    avgPrice: 128,
    distribution: [
      { range: '0-2', count: 180 },
      { range: '2-4', count: 420 },
      { range: '4-6', count: 680 },
      { range: '6-8', count: 720 },
      { range: '8-10', count: 480 },
      { range: '10-12', count: 180 },
      { range: '12+', count: 21 },
    ],
  };

  const currentStats = activeTab === 'drink' ? drinkStats : lampStats;

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="max-w-7xl mx-auto p-12 space-y-12">
        {/* Header */}
        <div>
          <h1 className="text-5xl font-black mb-3">数据集概览</h1>
          <p className="text-xl text-gray-600">两大品类电商主图数据分析</p>
        </div>

        {/* Tab Switcher */}
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('drink')}
            className={`px-8 py-4 text-xl font-bold rounded-xl border-2 transition-all shadow-md hover:shadow-lg ${
              activeTab === 'drink'
                ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white border-blue-400 scale-105'
                : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400 hover:scale-102'
            }`}
          >
            功能性饮料
          </button>
          <button
            onClick={() => setActiveTab('lamp')}
            className={`px-8 py-4 text-xl font-bold rounded-xl border-2 transition-all shadow-md hover:shadow-lg ${
              activeTab === 'lamp'
                ? 'bg-gradient-to-r from-amber-600 to-yellow-600 text-white border-amber-400 scale-105'
                : 'bg-white text-gray-700 border-gray-300 hover:border-amber-400 hover:scale-102'
            }`}
          >
            桌面台灯
          </button>
        </div>

        {/* Stats Cards */}
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="grid grid-cols-3 gap-8"
        >
          <motion.div
            whileHover={{ scale: 1.05, y: -4 }}
            className={`rounded-xl border-2 p-8 cursor-pointer shadow-md hover:shadow-xl transition-all ${
              activeTab === 'drink'
                ? 'bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-300 hover:border-blue-400'
                : 'bg-gradient-to-br from-yellow-50 to-amber-50 border-amber-300 hover:border-amber-400'
            }`}
          >
            <div className={`text-6xl font-black mb-4 ${activeTab === 'drink' ? 'text-blue-600' : 'text-amber-600'}`}>
              {currentStats.samples}
            </div>
            <div className="text-lg font-bold text-gray-700">样本数量</div>
          </motion.div>
          <motion.div
            whileHover={{ scale: 1.05, y: -4 }}
            className={`rounded-xl border-2 p-8 cursor-pointer shadow-md hover:shadow-xl transition-all ${
              activeTab === 'drink'
                ? 'bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-300 hover:border-blue-400'
                : 'bg-gradient-to-br from-yellow-50 to-amber-50 border-amber-300 hover:border-amber-400'
            }`}
          >
            <div className={`text-4xl font-black mb-4 ${activeTab === 'drink' ? 'text-blue-600' : 'text-amber-600'}`}>
              {currentStats.ctrRange}
            </div>
            <div className="text-lg font-bold text-gray-700">CTR范围</div>
          </motion.div>
          <motion.div
            whileHover={{ scale: 1.05, y: -4 }}
            className={`rounded-xl border-2 p-8 cursor-pointer shadow-md hover:shadow-xl transition-all ${
              activeTab === 'drink'
                ? 'bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-300 hover:border-blue-400'
                : 'bg-gradient-to-br from-yellow-50 to-amber-50 border-amber-300 hover:border-amber-400'
            }`}
          >
            <div className={`text-6xl font-black mb-4 ${activeTab === 'drink' ? 'text-blue-600' : 'text-amber-600'}`}>
              ¥{currentStats.avgPrice}
            </div>
            <div className="text-lg font-bold text-gray-700">平均价格</div>
          </motion.div>
        </motion.div>

        {/* CTR Distribution */}
        <motion.div
          key={`chart-${activeTab}`}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="bg-white rounded-xl border border-gray-200 p-8 shadow-md hover:shadow-xl transition-all"
        >
          <h3 className="text-2xl font-bold mb-6 text-gray-800">CTR分布</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={currentStats.distribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="#d1d5db" />
              <XAxis dataKey="range" stroke="#374151" />
              <YAxis stroke="#374151" />
              <Tooltip contentStyle={{ backgroundColor: '#fff', border: '2px solid #000' }} />
              <Bar dataKey="count" fill={activeTab === 'drink' ? '#2563eb' : '#eab308'} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Sample Grid */}
        <div className="bg-white rounded-xl border border-gray-200 p-8 shadow-md hover:shadow-xl transition-all">
          <h3 className="text-2xl font-bold mb-6 text-gray-800">样本展示</h3>
          <div className="grid grid-cols-8 gap-4">
            {Array.from({ length: 16 }).map((_, idx) => (
              <motion.div
                key={idx}
                whileHover={{ scale: 1.1, rotate: 2 }}
                className="aspect-square border-2 border-gray-200 rounded-lg bg-gray-50 flex items-center justify-center cursor-pointer hover:border-blue-400 hover:shadow-md transition-all"
              >
                <ImageIcon size={24} className="text-gray-400" />
              </motion.div>
            ))}
          </div>
        </div>

        {/* Data Source */}
        <div className="bg-gradient-to-br from-gray-50 to-slate-50 rounded-xl border border-gray-200 p-8 shadow-md hover:shadow-xl transition-all">
          <h3 className="text-2xl font-bold mb-4 flex items-center gap-2 text-gray-800">
            <Database size={24} className="text-blue-600" />
            数据采集说明
          </h3>
          <div className="space-y-2 text-lg font-medium text-gray-700">
            <p>• 数据来源：京东商城、天猫商城</p>
            <p>• 采集时间：2023年6月 - 2023年9月</p>
            <p>• 清洗规则：去重、过滤低质量图片、标准化尺寸</p>
            <p>• 标注方式：基于真实点击数据计算CTR</p>
          </div>
        </div>
      </div>
    </div>
  );
}
