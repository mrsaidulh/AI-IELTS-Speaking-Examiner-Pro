import React from 'react';
import { TestPart, TestMode } from '../types';
import { Play, FileText, MessageSquare, Award, Clock, Database, RotateCcw } from 'lucide-react';

interface ExamStageSelectorProps {
  currentPart: TestPart;
  setCurrentPart: (part: TestPart) => void;
  onResetTest: () => void;
  onFinishTest: () => void;
  messageCount: number;
  onOpenQuestionBank?: () => void;
  questionBankTitle?: string;
  isExamActive?: boolean;
  onStartExam?: () => void;
  onStopExam?: () => void;
  mode?: TestMode;
  strictTimeRemaining?: number;
}

export const ExamStageSelector: React.FC<ExamStageSelectorProps> = ({
  currentPart,
  setCurrentPart,
  onResetTest,
  onFinishTest,
  messageCount,
  onOpenQuestionBank,
  questionBankTitle,
  isExamActive = false,
  onStartExam,
  onStopExam,
  mode = 'training',
  strictTimeRemaining,
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
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 sm:p-5 shadow-sm mb-6 space-y-3">
      
      {questionBankTitle && onOpenQuestionBank && (
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5 text-xs">
          <div className="flex items-center space-x-2">
            <span className="text-slate-400">Active Test Set:</span>
            <span className="font-semibold text-indigo-300 flex items-center gap-1.5 bg-indigo-950/40 px-2 py-0.5 rounded-md border border-indigo-500/30">
              <Database className="w-3 h-3 text-indigo-400" />
              {questionBankTitle}
            </span>
          </div>
          <button
            onClick={onOpenQuestionBank}
            className="text-[11px] text-indigo-400 hover:text-indigo-300 hover:underline font-medium flex items-center gap-1"
          >
            Change / Import Bank →
          </button>
        </div>
      )}

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
        <div className="flex items-center space-x-2 sm:space-x-2.5 self-end md:self-auto">
          {mode === 'training' ? (
            <>
              {/* Training Mode: Start / Stop Exam Button */}
              {isExamActive ? (
                <button
                  id="btn-start-exam-stage"
                  onClick={onStopExam}
                  className="flex items-center space-x-1.5 px-4 py-2 h-9 sm:h-9.5 rounded-xl text-xs sm:text-sm font-bold bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 transition-all shadow-sm cursor-pointer"
                  title="Stop or pause the active IELTS Speaking examination"
                >
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
                  <span>Stop</span>
                </button>
              ) : (
                <button
                  id="btn-start-exam-stage"
                  onClick={onStartExam}
                  className="flex items-center space-x-1.5 px-4 py-2 h-9 sm:h-9.5 rounded-xl text-xs sm:text-sm font-black bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 shadow-md shadow-emerald-500/20 transition-all transform hover:scale-105 active:scale-95 cursor-pointer"
                  title="Begin IELTS Speaking practice with Examiner"
                >
                  <Play className="w-3.5 h-3.5 fill-current text-slate-950" />
                  <span>Start</span>
                </button>
              )}

              {/* Training Mode: Reset Button */}
              <button
                id="btn-restart-exam"
                onClick={onResetTest}
                className="flex items-center space-x-1.5 px-4 py-2 h-9 sm:h-9.5 rounded-xl text-xs sm:text-sm font-black bg-gradient-to-r from-emerald-500/20 to-teal-500/20 hover:from-emerald-500/30 hover:to-teal-500/30 text-emerald-300 border border-emerald-500/40 shadow-sm transition-all transform hover:scale-105 active:scale-95 cursor-pointer"
                title="Reset speaking exam to Part 1 and clear session history"
              >
                <RotateCcw className="w-3.5 h-3.5 text-emerald-400" />
                <span>Reset</span>
              </button>
            </>
          ) : (
            /* Strict Exam Mode: Start / Reset buttons are hidden, display strict exam controller */
            <>
              {isExamActive ? (
                <div className="flex items-center space-x-2">
                  <div className="flex items-center space-x-1.5 px-3 py-1.5 bg-amber-500/15 border border-amber-500/40 rounded-xl text-amber-300 text-xs font-mono font-bold shadow-sm">
                    <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                    <span>Strict Exam:</span>
                    <span>
                      {typeof strictTimeRemaining === 'number'
                        ? `${Math.floor(strictTimeRemaining / 60)}:${(strictTimeRemaining % 60).toString().padStart(2, '0')}`
                        : 'Active'}
                    </span>
                  </div>
                  <button
                    onClick={onStopExam}
                    className="text-xs px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 border border-slate-700 transition-colors"
                    title="End strict exam early"
                  >
                    End Early
                  </button>
                </div>
              ) : (
                <button
                  id="btn-start-strict-exam"
                  onClick={onStartExam}
                  className="flex items-center space-x-1.5 px-4 py-2 h-9 sm:h-9.5 rounded-xl text-xs sm:text-sm font-black bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 shadow-md shadow-amber-500/20 transition-all transform hover:scale-105 active:scale-95 cursor-pointer"
                  title="Begin timed continuous IELTS Strict Exam Simulation"
                >
                  <Play className="w-3.5 h-3.5 fill-current text-slate-950" />
                  <span>Begin Official Exam</span>
                </button>
              )}
            </>
          )}

          {/* Generate Band Score Button */}
          <button
            id="btn-generate-report"
            onClick={onFinishTest}
            disabled={messageCount < 2}
            className={`flex items-center space-x-1.5 px-3.5 sm:px-4 py-2 h-9 sm:h-9.5 rounded-xl text-xs sm:text-sm font-bold transition-all shadow-md ${
              messageCount >= 2
                ? 'bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 shadow-amber-500/20 cursor-pointer'
                : 'bg-slate-800/60 text-slate-500 border border-slate-800 cursor-not-allowed opacity-60'
            }`}
            title={messageCount >= 2 ? "Generate comprehensive Cambridge IELTS band score evaluation" : "Speak at least once to generate band report"}
          >
            <Award className="w-4 h-4 text-slate-950" />
            <span className="hidden sm:inline">Band Score</span>
            <span className="sm:hidden">Report</span>
          </button>
        </div>

      </div>
    </div>
  );
};
