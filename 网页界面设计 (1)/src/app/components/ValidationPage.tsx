import { motion } from 'motion/react';
import { TrendingUp, BarChart3, AlertCircle, CheckCircle } from 'lucide-react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Legend,
} from 'recharts';

export function ValidationPage() {
  const metrics = [
    { label: '同品类 Pearson r', value: '0.5952', color: 'green' },
    { label: 'MSE', value: '125.43', color: 'blue' },
    { label: 'MAE', value: '8.92', color: 'purple' },
    { label: '跨品类 Pearson r', value: '0.015', color: 'red' },
  ];

  const sameCategoryData = Array.from({ length: 50 }, (_, i) => ({
    真实值: Math.random() * 100 + 50,
    预测值: Math.random() * 100 + 50 + (Math.random() - 0.5) * 30,
  }));

  const crossCategoryData = Array.from({ length: 50 }, (_, i) => ({
    真实值: Math.random() * 100 + 50,
    预测值: Math.random() * 150 + 25,
  }));

  const errorDistribution = [
    { range: '[-100,-50]', same: 5, cross: 18 },
    { range: '[-50,-20]', same: 12, cross: 25 },
    { range: '[-20,0]', same: 28, cross: 32 },
    { range: '[0,20]', same: 35, cross: 28 },
    { range: '[20,50]', same: 15, cross: 22 },
    { range: '[50,100]', same: 5, cross: 15 },
  ];

  const featureImportance = [
    { feature: 'CLIP语义', importance: 0.42 },
    { feature: '视觉熵', importance: 0.28 },
    { feature: '文字密度', importance: 0.18 },
    { feature: '色彩复杂度', importance: 0.12 },
  ];

  return (
    <div className="h-full overflow-y-auto bg-white">
      <div className="max-w-7xl mx-auto p-12 space-y-12">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-5xl font-black mb-3">模型验证</h1>
          <p className="text-xl text-gray-600">实验结果与性能评估</p>
        </div>

        {/* Metrics Overview */}
        <div className="grid grid-cols-4 gap-8">
          {metrics.map((metric, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.1 }}
              whileHover={{ scale: 1.05, y: -4 }}
              className={`rounded-xl border-2 p-8 text-center cursor-pointer transition-all shadow-md hover:shadow-xl ${
                metric.color === 'green' ? 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-300 hover:border-green-400' :
                metric.color === 'blue' ? 'bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-300 hover:border-blue-400' :
                metric.color === 'purple' ? 'bg-gradient-to-br from-purple-50 to-fuchsia-50 border-purple-300 hover:border-purple-400' :
                'bg-gradient-to-br from-red-50 to-pink-50 border-red-300 hover:border-red-400'
              }`}
            >
              <div className="text-sm font-bold text-gray-600 mb-4">{metric.label}</div>
              <div className={`text-5xl font-black ${
                metric.color === 'green' ? 'text-green-600' :
                metric.color === 'blue' ? 'text-blue-600' :
                metric.color === 'purple' ? 'text-purple-600' : 'text-red-600'
              }`}>
                {metric.value}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Scatter Plots */}
        <div className="grid grid-cols-2 gap-8">
          <div className="bg-white rounded-xl border border-gray-200 p-8 shadow-md hover:shadow-xl transition-all">
            <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <CheckCircle size={24} className="text-green-600" />
              同品类预测vs真实值
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#d1d5db" />
                <XAxis type="number" dataKey="真实值" name="真实值" stroke="#374151" />
                <YAxis type="number" dataKey="预测值" name="预测值" stroke="#374151" />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{ backgroundColor: '#fff', border: '2px solid #000' }}
                />
                <Scatter name="同品类" data={sameCategoryData} fill="#16a34a" />
              </ScatterChart>
            </ResponsiveContainer>
            <p className="text-sm font-medium text-green-600 mt-4">✓ 显著正相关趋势，模型有效</p>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-8 shadow-md hover:shadow-xl transition-all">
            <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <AlertCircle size={24} className="text-red-600" />
              跨品类预测vs真实值
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#d1d5db" />
                <XAxis type="number" dataKey="真实值" name="真实值" stroke="#374151" />
                <YAxis type="number" dataKey="预测值" name="预测值" stroke="#374151" />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{ backgroundColor: '#fff', border: '2px solid #000' }}
                />
                <Scatter name="跨品类" data={crossCategoryData} fill="#dc2626" />
              </ScatterChart>
            </ResponsiveContainer>
            <p className="text-sm font-medium text-red-600 mt-4">⚠ 云团状分布，泛化失效</p>
          </div>
        </div>

        {/* Error Distribution */}
        <div className="bg-white rounded-xl border border-gray-200 p-8 shadow-md hover:shadow-xl transition-all">
          <h3 className="text-2xl font-bold mb-6 flex items-center gap-2">
            <BarChart3 size={24} className="text-blue-600" />
            误差分布对比
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={errorDistribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="#d1d5db" />
              <XAxis dataKey="range" stroke="#374151" />
              <YAxis stroke="#374151" />
              <Tooltip contentStyle={{ backgroundColor: '#fff', border: '2px solid #000' }} />
              <Legend />
              <Bar dataKey="same" fill="#16a34a" name="同品类" />
              <Bar dataKey="cross" fill="#dc2626" name="跨品类" />
            </BarChart>
          </ResponsiveContainer>
          <p className="text-sm font-medium text-gray-600 mt-4">同品类误差集中在[-20,20]区间，跨品类误差分布更宽且有偏</p>
        </div>

        {/* Feature Importance */}
        <div className="bg-white rounded-xl border border-gray-200 p-8 shadow-md hover:shadow-xl transition-all">
          <h3 className="text-2xl font-bold mb-8 text-gray-800">特征重要性分析</h3>
          <div className="space-y-6">
            {featureImportance.map((item, idx) => (
              <div key={idx}>
                <div className="flex justify-between text-sm font-bold mb-2">
                  <span className="text-gray-700">{item.feature}</span>
                  <span className="text-blue-600">{(item.importance * 100).toFixed(0)}%</span>
                </div>
                <div className="h-4 bg-gray-100 rounded-full border border-gray-200 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    whileInView={{ width: `${item.importance * 100}%` }}
                    viewport={{ once: true }}
                    transition={{ delay: idx * 0.1, duration: 0.8 }}
                    className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
