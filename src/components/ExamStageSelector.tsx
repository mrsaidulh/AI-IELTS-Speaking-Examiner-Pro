import React from 'react';
import { TestPart } from '../types';
import { Play, FileText, MessageSquare, Award, Clock } from 'lucide-react';

interface ExamStageSelectorProps {
  currentPart: TestPart;
  setCurrentPart: (part: TestPart) => void;
  onResetTest: () => void;
  onFinishTest: () => void;
  messageCount: number;
}

export const ExamStageSelector: React.FC<ExamStageSelectorProps> = ({
  currentPart,
  setCurrentPart,
  onResetTest,
  onFinishTest,
  messageCount,
}) => {
  const parts: { id: TestPart; title: string; desc: string; icon: any; duration: string }[] = [
    {
      id: 'part1',
      title: 'Part 1',
      desc: 'Intro & Everyday Topics',
      icon: MessageSquare,
      duration: '4-5 min',
    },
    {
      id: 'part2',
      title: 'Part 2',
      desc: 'Individual Long Turn (Cue Card)',
      icon: FileText,
      duration: '3-4 min',
    },
    {
      id: 'part3',
      title: 'Part 3',
      desc: 'Two-Way Abstract Discussion',
      icon: MessageSquare,
      duration: '4-5 min',
    },
  ];

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 sm:p-5 shadow-sm mb-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        
        {/* Stage Buttons */}
        <div className="grid grid-cols-3 gap-2 sm:gap-3 flex-1">
          {parts.map((p) => {
            const Icon = p.icon;
            const isActive = currentPart === p.id;

            return (
              <button
                key={p.id}
                onClick={() => setCurrentPart(p.id)}
                className={`p-3 rounded-xl border text-left transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-indigo-900/60 to-slate-900 border-indigo-500/80 text-white shadow-md shadow-indigo-900/20'
                    : 'bg-slate-800/40 border-slate-700/60 text-slate-300 hover:bg-slate-800/80 hover:text-white'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-xs sm:text-sm font-bold ${isActive ? 'text-indigo-300' : 'text-slate-200'}`}>
                    {p.title}
                  </span>
                  <span className="text-[10px] text-slate-400 flex items-center space-x-0.5">
                    <Clock className="w-2.5 h-2.5 inline mr-0.5" />
                    {p.duration}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 truncate hidden sm:block">{p.desc}</p>
              </button>
            );
          })}
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-2 sm:space-x-3 self-end md:self-auto">
          <button
            onClick={onResetTest}
            className="px-3 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 bg-slate-800/80 hover:bg-slate-700/80 rounded-xl border border-slate-700 transition-colors"
          >
            Restart Test
          </button>

          <button
            onClick={onFinishTest}
            disabled={messageCount < 2}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all shadow-md ${
              messageCount >= 2
                ? 'bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold shadow-amber-500/20'
                : 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
            }`}
          >
            <Award className="w-4 h-4 text-slate-950" />
            <span>Generate Band Score</span>
          </button>
        </div>

      </div>
    </div>
  );
};
