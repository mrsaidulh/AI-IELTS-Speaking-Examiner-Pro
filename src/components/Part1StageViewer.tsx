import React from 'react';
import { MessageSquare, Sparkles, CheckCircle2, Clock, HelpCircle, ShieldCheck } from 'lucide-react';
import { Part1Topic } from '../types';
import { PART1_TOPICS } from '../data/topics';

interface Part1StageViewerProps {
  currentCategoryIndex: number;
  currentQuestionIndex: number;
  onSelectCategory: (index: number) => void;
  onAskQuestion: (question: string, index?: number) => void;
  topics?: Part1Topic[];
}

export const Part1StageViewer: React.FC<Part1StageViewerProps> = ({
  currentCategoryIndex,
  currentQuestionIndex = 0,
  onSelectCategory,
  onAskQuestion,
  topics = PART1_TOPICS,
}) => {
  const activeTopics = topics && topics.length > 0 ? topics : PART1_TOPICS;
  const currentTopic = activeTopics[currentCategoryIndex % activeTopics.length] || activeTopics[0];
  const totalQuestions = currentTopic.questions.length;
  const clampedQIndex = Math.min(currentQuestionIndex, totalQuestions - 1);

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-900/90 to-indigo-950/40 border border-indigo-500/30 rounded-2xl p-5 sm:p-6 shadow-xl mb-6 relative overflow-hidden">
      {/* Background Accent */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* Part 1 Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 mb-4 gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-1 text-xs font-bold rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              IELTS Speaking Part 1
            </span>
            <span className="text-xs text-slate-400">Introduction & Everyday Topics</span>
          </div>
          <h3 className="text-lg sm:text-xl font-extrabold text-white mt-1">
            {currentTopic.category}
          </h3>
        </div>

        {/* Topic Category Switcher */}
        <div className="flex flex-wrap items-center gap-1.5 self-start sm:self-auto">
          {activeTopics.map((topic, idx) => (
            <button
              key={idx}
              onClick={() => onSelectCategory(idx)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                currentCategoryIndex === idx
                  ? 'bg-indigo-600 border-indigo-500 text-white font-semibold shadow-sm shadow-indigo-600/30'
                  : 'bg-slate-800/80 border-slate-700/80 text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              {topic.category.split('&')[0].trim()}
            </button>
          ))}
        </div>
      </div>

      {/* Official Examiner Script & Standard Question List */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        
        {/* Examiner Official Protocol Script */}
        <div className="md:col-span-2 bg-slate-950/60 rounded-xl p-4 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center">
              <ShieldCheck className="w-3.5 h-3.5 text-indigo-400 mr-1.5" />
              Official Examiner Protocol
            </span>
            <span className="text-[11px] text-slate-400 flex items-center">
              <Clock className="w-3 h-3 mr-1 text-indigo-400" />
              Duration: 4–5 min
            </span>
          </div>

          <p className="text-xs text-slate-300 italic border-l-2 border-indigo-500 pl-3 py-1">
            "Good day. Welcome to the IELTS Speaking test. In this first part, I am going to ask you some general questions about yourself. Let's talk about {currentTopic.category.toLowerCase()}."
          </p>

          <div className="space-y-2 pt-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">
                Standard Test Questions:
              </span>
              <span className="text-[11px] font-mono text-indigo-300 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-500/30">
                Question {clampedQIndex + 1} of {totalQuestions}
              </span>
            </div>

            {/* Mini Progress Bar */}
            <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden border border-slate-800">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 transition-all duration-300"
                style={{ width: `${Math.min(100, Math.round(((clampedQIndex + 1) / totalQuestions) * 100))}%` }}
              />
            </div>

            <ul className="space-y-2 pt-1">
              {currentTopic.questions.map((q, idx) => {
                const isAnswered = idx < clampedQIndex;
                const isActive = idx === clampedQIndex;

                return (
                  <li
                    key={idx}
                    className={`flex items-start justify-between group text-xs p-2.5 rounded-xl border transition-all ${
                      isActive
                        ? 'bg-indigo-950/70 border-indigo-400/80 shadow-md shadow-indigo-500/15 ring-1 ring-indigo-500/40 text-white font-medium'
                        : isAnswered
                        ? 'bg-slate-900/40 border-emerald-500/30 text-slate-300'
                        : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-indigo-500/50'
                    }`}
                  >
                    <span className="flex items-start space-x-2.5 flex-1 pr-2">
                      {isAnswered ? (
                        <span className="w-4 h-4 rounded-full bg-emerald-950 text-emerald-300 text-[10px] flex items-center justify-center shrink-0 border border-emerald-700 mt-0.5" title="Answered">
                          ✓
                        </span>
                      ) : isActive ? (
                        <span className="w-4 h-4 rounded-full bg-indigo-600 text-white text-[10px] flex items-center justify-center font-bold shrink-0 shadow-sm shadow-indigo-500/50 mt-0.5">
                          {idx + 1}
                        </span>
                      ) : (
                        <span className="w-4 h-4 rounded-full bg-indigo-950 text-indigo-300 text-[10px] flex items-center justify-center font-mono border border-indigo-800 shrink-0 mt-0.5">
                          {idx + 1}
                        </span>
                      )}
                      
                      <div className="flex flex-col">
                        <div className="flex items-center space-x-2">
                          <span className={isActive ? 'text-white font-semibold' : ''}>{q}</span>
                          {isActive && (
                            <span className="text-[9px] uppercase tracking-wider font-bold bg-indigo-500/30 text-indigo-300 border border-indigo-400/40 px-1.5 py-0.2 rounded shrink-0 flex items-center">
                              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse mr-1" />
                              Active
                            </span>
                          )}
                          {isAnswered && (
                            <span className="text-[9px] uppercase tracking-wider font-semibold text-emerald-400 shrink-0">
                              Completed
                            </span>
                          )}
                        </div>
                      </div>
                    </span>

                    <button
                      onClick={() => onAskQuestion(q, idx)}
                      className={`text-[10px] px-2 py-0.5 rounded border transition-opacity shrink-0 ${
                        isActive
                          ? 'opacity-100 bg-indigo-600 hover:bg-indigo-500 text-white border-indigo-400'
                          : 'opacity-0 group-hover:opacity-100 text-indigo-400 hover:text-indigo-300 bg-slate-800 border-slate-700'
                      }`}
                      title="Direct examiner to ask this question"
                    >
                      {isActive ? 'Current' : 'Practice This'}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>

        {/* Candidate Strategy & Scoring Guide */}
        <div className="bg-slate-950/40 rounded-xl p-4 border border-slate-800 flex flex-col justify-between space-y-3">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center mb-2">
              <Sparkles className="w-3.5 h-3.5 text-amber-400 mr-1.5" />
              Band 7.5+ Strategy
            </span>

            <ul className="space-y-2 text-xs text-slate-300">
              <li className="flex items-start space-x-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                <span><strong>Target Length:</strong> 2 to 3 full sentences (15–25s).</span>
              </li>
              <li className="flex items-start space-x-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                <span><strong>Structure:</strong> Direct Answer + 1 Reason / Example.</span>
              </li>
              <li className="flex items-start space-x-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                <span><strong>Avoid:</strong> Just "Yes/No" or long 2-minute monologues.</span>
              </li>
            </ul>
          </div>

          <div className="bg-indigo-950/30 p-2.5 rounded-lg border border-indigo-500/20 text-[11px] text-indigo-300">
            💡 <strong>Examiner Tip:</strong> Part 1 tests your confidence and spontaneous speaking on familiar everyday topics.
          </div>
        </div>

      </div>

    </div>
  );
};
