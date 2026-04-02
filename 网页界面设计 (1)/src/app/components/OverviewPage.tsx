import { useEffect, useRef, useState } from 'react';
import { motion, useScroll, useTransform, useInView } from 'motion/react';
import { Brain, Zap, Eye, Database, Layers, ArrowRight, TrendingUp, Target, LineChart, Sparkles } from 'lucide-react';

interface OverviewPageProps {
  onNavigate: (page: string) => void;
}

function AnimatedCounter({ end, duration = 2 }: { end: number; duration?: number }) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (!isInView) return;
    let start = 0;
    const increment = end / (duration * 60);
    const timer = setInterval(() => {
      start += increment;
      if (start >= end) {
        setCount(end);
        clearInterval(timer);
      } else {
        setCount(Math.floor(start));
      }
    }, 1000 / 60);
    return () => clearInterval(timer);
  }, [end, duration, isInView]);

  return <div ref={ref}>{count}</div>;
}

export function OverviewPage({ onNavigate }: OverviewPageProps) {
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  });

  const heroY = useTransform(scrollYProgress, [0, 0.3], [0, -100]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.2], [1, 0]);

  return (
    <div ref={containerRef} className="h-full overflow-y-auto bg-white">
      {/* Hero Section */}
      <motion.section
        style={{ y: heroY, opacity: heroOpacity }}
        className="min-h-screen flex flex-col items-center justify-center px-8 relative"
      >
        <div className="max-w-6xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="mb-8"
          >
            <div className="inline-block mb-6">
              <div className="flex items-center gap-2 px-4 py-2 border-2 border-blue-500 bg-blue-50 text-sm font-bold text-blue-700 hover:border-blue-600 hover:bg-blue-100 transition-all">
                <Sparkles size={16} />
                神经营销学研究
              </div>
            </div>
            <h1 className="text-7xl font-black mb-6 leading-tight">
              电商主图CTR
              <br />
              <span className="text-blue-600">智能诊断系统</span>
            </h1>
            <p className="text-2xl text-gray-600 max-w-3xl mx-auto">
              基于深度学习与视觉特征工程的点击率预测与可解释分析平台
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="flex gap-4 justify-center mb-16"
          >
            <button
              onClick={() => onNavigate('demo')}
              className="px-8 py-4 bg-blue-600 text-white text-lg font-bold hover:bg-blue-700 hover:scale-105 transition-all flex items-center gap-2 shadow-lg hover:shadow-xl"
            >
              立即体验系统
              <ArrowRight size={20} />
            </button>
            <button
              onClick={() => onNavigate('research')}
              className="px-8 py-4 border-2 border-gray-300 text-gray-700 text-lg font-bold hover:border-blue-500 hover:text-blue-600 hover:scale-105 transition-all"
            >
              了解技术原理
            </button>
          </motion.div>

          {/* Stats Row */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="grid grid-cols-3 gap-8 max-w-4xl mx-auto"
          >
            <div className="text-center">
              <div className="text-5xl font-black text-blue-600 mb-2">
                <AnimatedCounter end={4796} duration={2} />
              </div>
              <div className="text-sm text-gray-600 font-medium">训练样本总数</div>
            </div>
            <div className="text-center">
              <div className="text-5xl font-black text-green-600 mb-2">0.595</div>
              <div className="text-sm text-gray-600 font-medium">同品类相关系数</div>
            </div>
            <div className="text-center">
              <div className="text-5xl font-black text-purple-600 mb-2">
                <AnimatedCounter end={768} duration={2} />
              </div>
              <div className="text-sm text-gray-600 font-medium">CLIP特征维度</div>
            </div>
          </motion.div>
        </div>

        {/* Scroll Indicator */}
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ repeat: Infinity, duration: 1.5 }}
          className="absolute bottom-8"
        >
          <div className="w-6 h-10 border-2 border-gray-400 rounded-full flex justify-center">
            <div className="w-1 h-2 bg-gray-600 rounded-full mt-2"></div>
          </div>
        </motion.div>
      </motion.section>

      {/* Core Capabilities */}
      <section className="py-32 px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-5xl font-black text-center mb-20"
          >
            三大核心能力
          </motion.h2>

          <div className="grid grid-cols-3 gap-8">
            {[
              {
                icon: Brain,
                title: '视觉特征提取',
                desc: '视觉熵 + 文字密度 + CLIP语义嵌入',
                color: 'blue',
                stats: '768维特征',
              },
              {
                icon: Target,
                title: 'CTR精准预测',
                desc: 'XGBoost回归模型，同品类r=0.595',
                color: 'green',
                stats: '±8.92误差',
              },
              {
                icon: Eye,
                title: '可解释热力图',
                desc: 'Occlusion Sensitivity区域贡献分析',
                color: 'purple',
                stats: '32×32网格',
              },
            ].map((item, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1 }}
                whileHover={{ y: -8, scale: 1.02 }}
                className="bg-white border-2 border-gray-200 p-8 transition-all hover:border-blue-400 hover:shadow-xl rounded-lg cursor-pointer"
              >
                <div
                  className={`w-16 h-16 mb-6 flex items-center justify-center rounded-xl transition-all ${
                    item.color === 'blue'
                      ? 'bg-blue-500 text-white'
                      : item.color === 'green'
                      ? 'bg-green-500 text-white'
                      : 'bg-purple-500 text-white'
                  }`}
                >
                  <item.icon size={32} />
                </div>
                <h3 className="text-2xl font-bold mb-4">{item.title}</h3>
                <p className="text-gray-600 mb-4 leading-relaxed">{item.desc}</p>
                <div
                  className={`inline-block px-3 py-1 rounded-full text-sm font-bold ${
                    item.color === 'blue'
                      ? 'bg-blue-100 text-blue-700'
                      : item.color === 'green'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-purple-100 text-purple-700'
                  }`}
                >
                  {item.stats}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Dataset Overview */}
      <section className="py-32 px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-20"
          >
            <h2 className="text-5xl font-black mb-6">数据集规模</h2>
            <p className="text-xl text-gray-600">两大品类，近5000张真实电商主图</p>
          </motion.div>

          <div className="grid grid-cols-2 gap-12">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              whileHover={{ scale: 1.02 }}
              className="relative cursor-pointer group"
            >
              <div className="border-2 border-blue-300 p-12 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-2xl transition-all group-hover:border-blue-500 group-hover:shadow-2xl">
                <div className="text-8xl font-black mb-4 text-blue-600">2115</div>
                <h3 className="text-3xl font-bold mb-4">功能性饮料</h3>
                <div className="space-y-2 text-lg text-gray-700">
                  <div>• 京东/天猫爬取</div>
                  <div>• CTR范围: 1.2-12.5</div>
                  <div>• 平均价格: ¥45</div>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              whileHover={{ scale: 1.02 }}
              className="relative cursor-pointer group"
            >
              <div className="border-2 border-amber-300 p-12 bg-gradient-to-br from-yellow-50 to-amber-50 rounded-2xl transition-all group-hover:border-amber-500 group-hover:shadow-2xl">
                <div className="text-8xl font-black mb-4 text-amber-600">2681</div>
                <h3 className="text-3xl font-bold mb-4">桌面台灯</h3>
                <div className="space-y-2 text-lg text-gray-700">
                  <div>• 京东/天猫爬取</div>
                  <div>• CTR范围: 0.8-10.3</div>
                  <div>• 平均价格: ¥128</div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Key Metrics */}
      <section className="py-32 px-8 bg-black text-white">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-20"
          >
            <h2 className="text-5xl font-black mb-6">核心指标亮点</h2>
            <p className="text-xl text-gray-400">品类内预测准确，跨品类特异性显著</p>
          </motion.div>

          <div className="grid grid-cols-2 gap-12">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              whileHover={{ scale: 1.05 }}
              className="border-2 border-white/30 p-12 text-center rounded-2xl bg-white/5 backdrop-blur-sm hover:bg-white/10 transition-all cursor-pointer"
            >
              <div className="text-sm font-bold mb-4 tracking-wider text-green-300">同品类模型</div>
              <div className="text-8xl font-black mb-6 text-green-400">0.595</div>
              <div className="text-2xl font-bold mb-4">Pearson相关系数</div>
              <p className="text-gray-400">饮料品类内预测，显著正相关</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              whileHover={{ scale: 1.05 }}
              className="border-2 border-white/30 p-12 text-center rounded-2xl bg-white/5 backdrop-blur-sm hover:bg-white/10 transition-all cursor-pointer"
            >
              <div className="text-sm font-bold mb-4 tracking-wider text-red-300">跨品类迁移</div>
              <div className="text-8xl font-black mb-6 text-red-400">0.015</div>
              <div className="text-2xl font-bold mb-4">Pearson相关系数</div>
              <p className="text-gray-400">饮料→台灯泛化失效，验证品类特异性</p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="py-32 px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-5xl font-black text-center mb-20"
          >
            技术栈
          </motion.h2>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="flex items-center justify-center gap-8 flex-wrap"
          >
            {['OpenAI CLIP', 'XGBoost', 'OpenCV', 'Occlusion Sensitivity', 'Python', 'scikit-learn'].map(
              (tech, idx) => (
                <motion.div
                  key={idx}
                  whileHover={{ scale: 1.1, y: -4 }}
                  className="px-8 py-4 border-2 border-gray-300 bg-white text-xl font-bold hover:border-blue-500 hover:text-blue-600 hover:shadow-lg transition-all cursor-pointer rounded-lg"
                >
                  {tech}
                </motion.div>
              )
            )}
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 px-8 bg-blue-600 text-white">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-5xl font-black mb-6">准备好体验了吗？</h2>
            <p className="text-2xl mb-12 text-blue-100">上传您的主图，获取专业CTR诊断报告</p>
            <motion.button
              onClick={() => onNavigate('demo')}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-12 py-5 bg-white text-blue-600 text-xl font-bold hover:bg-blue-50 transition-colors inline-flex items-center gap-3 rounded-xl shadow-lg hover:shadow-2xl"
            >
              开始使用系统
              <ArrowRight size={24} />
            </motion.button>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
