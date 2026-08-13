import React from 'react';
import { Mic, BarChart3, Server, Settings, Award, Volume2, ShieldAlert } from 'lucide-react';
import { TestMode, ExaminerAccent } from '../types';

interface HeaderProps {
  activeTab: 'practice' | 'report' | 'guide';
  setActiveTab: (tab: 'practice' | 'report' | 'guide') => void;
  mode: TestMode;
  setMode: (mode: TestMode) => void;
  accent: ExaminerAccent;
  setAccent: (accent: ExaminerAccent) => void;
  targetBand: number;
  setTargetBand: (band: number) => void;
  showSettings: boolean;
  setShowSettings: (show: boolean) => void;
  onOpenServerStatus: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  mode,
  setMode,
  accent,
  setAccent,
  targetBand,
  setTargetBand,
  showSettings,
  setShowSettings,
  onOpenServerStatus,
}) => {
  return (
    <header className="sticky top-0 z-30 bg-slate-900/95 backdrop-blur-md border-b border-slate-800 text-slate-100 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-sky-500 flex items-center justify-center text-white font-bold shadow-lg shadow-indigo-500/20">
              <Mic className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight text-white">IELTS Speaking</span>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  AI Examiner
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">Real-time Examiner Simulator & Score Evaluator</p>
            </div>
          </div>

          {/* Center Navigation Tabs */}
          <nav className="flex items-center space-x-1 sm:space-x-2 bg-slate-800/80 p-1 rounded-xl border border-slate-700/60">
            <button
              onClick={() => setActiveTab('practice')}
              className={`flex items-center space-x-2 px-3 sm:px-4 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                activeTab === 'practice'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              <Mic className="w-4 h-4" />
              <span>Practice Test</span>
            </button>

            <button
              onClick={() => setActiveTab('report')}
              className={`flex items-center space-x-2 px-3 sm:px-4 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                activeTab === 'report'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              <span>Band Report</span>
            </button>

            <button
              onClick={() => setActiveTab('guide')}
              className={`flex items-center space-x-2 px-3 sm:px-4 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                activeTab === 'guide'
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              <Server className="w-4 h-4" />
              <span className="hidden sm:inline">Local AI Setup</span>
              <span className="sm:hidden">Local Setup</span>
            </button>
          </nav>

          {/* Mode Switcher & Settings */}
          <div className="flex items-center space-x-2 sm:space-x-3">
            <button
              onClick={onOpenServerStatus}
              className="flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800/90 hover:bg-slate-700 text-slate-200 border border-slate-700/80 transition-all shadow-sm"
              title="Check Server & Component Connection Status (Ollama, FastAPI, Kokoro, Whisper, GPU)"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <Server className="w-3.5 h-3.5 text-indigo-400" />
              <span className="hidden lg:inline">Server Status</span>
            </button>

            <button
              onClick={() => setMode(mode === 'exam' ? 'training' : 'exam')}
              className={`hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                mode === 'exam'
                  ? 'bg-amber-500/10 text-amber-300 border-amber-500/30 hover:bg-amber-500/20'
                  : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/20'
              }`}
              title="Click to toggle between Exam Mode and Training Mode"
            >
              <Award className="w-3.5 h-3.5" />
              <span>{mode === 'exam' ? 'Strict Exam Mode' : 'Training Mode'}</span>
            </button>

            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700/80 transition-colors"
              title="Examiner Settings"
            >
              <Settings className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Settings Modal */}
      {showSettings && (
        <div className="border-t border-slate-800 bg-slate-900/98 py-4 px-4 sm:px-8 shadow-inner animate-in fade-in slide-in-from-top-2">
          <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
            
            {/* Mode Selection */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">
                Practice Mode
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setMode('exam')}
                  className={`p-2.5 rounded-lg border text-left text-xs transition-all ${
                    mode === 'exam'
                      ? 'bg-indigo-600/30 border-indigo-500 text-white font-medium'
                      : 'bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <div className="font-semibold text-indigo-300 flex items-center space-x-1">
                    <ShieldAlert className="w-3.5 h-3.5 inline mr-1" />
                    Exam Mode
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">Realistic test without mid-speech corrections</div>
                </button>

                <button
                  onClick={() => setMode('training')}
                  className={`p-2.5 rounded-lg border text-left text-xs transition-all ${
                    mode === 'training'
                      ? 'bg-emerald-600/30 border-emerald-500 text-white font-medium'
                      : 'bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <div className="font-semibold text-emerald-300 flex items-center space-x-1">
                    <Award className="w-3.5 h-3.5 inline mr-1" />
                    Training Mode
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">Real-time grammar & vocabulary enhancements</div>
                </button>
              </div>
            </div>

            {/* Examiner Accent */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">
                Examiner Accent
              </label>
              <div className="flex space-x-2">
                {(['british', 'australian', 'american'] as ExaminerAccent[]).map((acc) => (
                  <button
                    key={acc}
                    onClick={() => setAccent(acc)}
                    className={`flex-1 py-2 px-3 rounded-lg border text-xs capitalize transition-all ${
                      accent === acc
                        ? 'bg-indigo-600/30 border-indigo-500 text-indigo-200 font-semibold'
                        : 'bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-800'
                    }`}
                  >
                    <Volume2 className="w-3 h-3 inline mr-1 text-slate-400" />
                    {acc}
                  </button>
                ))}
              </div>
            </div>

            {/* Target Band */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">
                Target IELTS Band
              </label>
              <div className="flex space-x-2">
                {[6.5, 7.0, 7.5, 8.0, 8.5].map((band) => (
                  <button
                    key={band}
                    onClick={() => setTargetBand(band)}
                    className={`flex-1 py-2 rounded-lg border text-xs font-semibold transition-all ${
                      targetBand === band
                        ? 'bg-amber-500/20 border-amber-500 text-amber-300'
                        : 'bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-800'
                    }`}
                  >
                    {band.toFixed(1)}
                  </button>
                ))}
              </div>
            </div>

          </div>

          {/* Diagnostics Launcher Bar */}
          <div className="max-w-4xl mx-auto mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2 text-slate-400">
              <Server className="w-4 h-4 text-indigo-400" />
              <span>Pipeline Status: FastAPI (8000), Ollama (11434), Whisper, Kokoro & GPU</span>
            </div>
            <button
              onClick={() => {
                setShowSettings(false);
                onOpenServerStatus();
              }}
              className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold flex items-center space-x-1.5 transition-colors"
            >
              <Server className="w-3.5 h-3.5" />
              <span>Check Component Connections & Diagnostics</span>
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
