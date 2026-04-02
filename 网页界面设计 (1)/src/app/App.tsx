import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Sidebar } from './components/Sidebar';
import { OverviewPage } from './components/OverviewPage';
import { DemoPage } from './components/DemoPage';
import { ValidationPage } from './components/ValidationPage';
import { DatasetPage } from './components/DatasetPage';
import { ResearchPage } from './components/ResearchPage';

export default function App() {
  const [mode, setMode] = useState<'demo' | 'complete'>('complete');
  const [currentPage, setCurrentPage] = useState('overview');

  const renderPage = () => {
    if (mode === 'demo') {
      return <DemoPage />;
    }

    switch (currentPage) {
      case 'overview':
        return <OverviewPage onNavigate={setCurrentPage} />;
      case 'demo':
        return <DemoPage />;
      case 'validation':
        return <ValidationPage />;
      case 'dataset':
        return <DatasetPage />;
      case 'research':
        return <ResearchPage />;
      default:
        return <OverviewPage onNavigate={setCurrentPage} />;
    }
  };

  return (
    <div className="size-full flex bg-gradient-to-br from-gray-50 to-slate-100">
      {/* Sidebar */}
      <Sidebar currentPage={currentPage} onPageChange={setCurrentPage} mode={mode} />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header with Mode Toggle */}
        <div className="border-b border-gray-200 bg-white/80 backdrop-blur-sm px-8 py-6 flex items-center justify-between shadow-sm">
          <div>
            <h2 className="text-2xl font-black text-gray-800">
              {mode === 'demo' ? '演示模式' : '完整模式'}
            </h2>
            <p className="text-sm text-gray-600 font-medium mt-1">
              {mode === 'demo'
                ? '视觉冲击优先，评委3步内看到核心结果'
                : '信息完整，多页导航，每个模块独立可读'}
            </p>
          </div>

          {/* Mode Toggle */}
          <div className="flex items-center gap-4">
            <span className="text-sm font-bold text-gray-700">模式切换</span>
            <button
              onClick={() => {
                setMode(mode === 'demo' ? 'complete' : 'demo');
                if (mode === 'complete') {
                  setCurrentPage('demo');
                } else {
                  setCurrentPage('overview');
                }
              }}
              className="relative w-20 h-10 rounded-full border-2 border-gray-300 bg-gray-100 hover:bg-gray-200 transition-all shadow-sm"
            >
              <motion.div
                layout
                className="absolute top-1 left-1 w-8 h-6 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 shadow-md"
                animate={{ x: mode === 'demo' ? 0 : 40 }}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              />
            </button>
            <div className="flex gap-2 text-sm font-bold">
              <span className={mode === 'demo' ? 'text-blue-600' : 'text-gray-400'}>
                演示
              </span>
              <span className="text-gray-400">/</span>
              <span className={mode === 'complete' ? 'text-blue-600' : 'text-gray-400'}>
                完整
              </span>
            </div>
          </div>
        </div>

        {/* Page Content */}
        <div className="flex-1 overflow-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentPage + mode}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              {renderPage()}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}