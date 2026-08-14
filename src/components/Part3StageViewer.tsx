import React from 'react';
import { MessageSquare, Sparkles, CheckCircle2, Clock, Link2, ShieldCheck } from 'lucide-react';
import { Part3Topic } from '../types';
import { PART3_TOPICS } from '../data/topics';

interface Part3StageViewerProps {
  currentTopicIndex: number;
  onSelectTopic: (index: number) => void;
  onAskQuestion: (question: string) => void;
  topics?: Part3Topic[];
}

export const Part3StageViewer: React.FC<Part3StageViewerProps> = ({
  currentTopicIndex,
  onSelectTopic,
  onAskQuestion,
  topics = PART3_TOPICS,
}) => {
  const activeTopics = topics && topics.length > 0 ? topics : PART3_TOPICS;
  const currentSet = activeTopics[currentTopicIndex % activeTopics.length] || activeTopics[0];

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-900/90 to-indigo-950/40 border border-indigo-500/30 rounded-2xl p-5 sm:p-6 shadow-xl mb-6 relative overflow-hidden">
      {/* Background Accent */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* Part 3 Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 mb-4 gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-1 text-xs font-bold rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              IELTS Speaking Part 3
            </span>
            <span className="text-xs text-slate-400">Two-Way Abstract Discussion</span>
          </div>
          <h3 className="text-lg sm:text-xl font-extrabold text-white mt-1">
            {currentSet.theme}
          </h3>
          <div className="flex items-center space-x-1 text-xs text-slate-400 mt-1">
            <Link2 className="w-3 h-3 text-indigo-400" />
            <span>Theme extension of Part 2 Cue Card: <strong className="text-slate-300">{currentSet.cueCardTopic}</strong></span>
          </div>
        </div>

        {/* Discussion Theme Switcher */}
        <div className="flex flex-wrap items-center gap-1.5 self-start sm:self-auto">
          {activeTopics.map((topic, idx) => (
            <button
              key={idx}
              onClick={() => onSelectTopic(idx)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                currentTopicIndex === idx
                  ? 'bg-indigo-600 border-indigo-500 text-white font-semibold shadow-sm shadow-indigo-600/30'
                  : 'bg-slate-800/80 border-slate-700/80 text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              {topic.cueCardTopic}
            </button>
          ))}
        </div>
      </div>

      {/* Official Examiner Script & Abstract Question List */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        
        {/* Examiner Official Protocol Script */}
        <div className="md:col-span-2 bg-slate-950/60 rounded-xl p-4 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center">
              <ShieldCheck className="w-3.5 h-3.5 text-indigo-400 mr-1.5" />
              Official Examiner Transition Script
            </span>
            <span className="text-[11px] text-slate-400 flex items-center">
              <Clock className="w-3 h-3 mr-1 text-indigo-400" />
              Duration: 4–5 min
            </span>
          </div>

          <p className="text-xs text-slate-300 italic border-l-2 border-indigo-500 pl-3 py-1">
            "We've been talking about {currentSet.cueCardTopic.toLowerCase()}, and now I'd like to discuss with you one or two more general questions related to this. Let's consider {currentSet.theme.toLowerCase()} in general."
          </p>

          <div className="space-y-2 pt-1">
            <span className="text-xs font-semibold text-slate-300">Abstract Discussion Questions:</span>
            <ul className="space-y-1.5">
              {currentSet.questions.map((q, idx) => (
                <li key={idx} className="flex items-start justify-between group text-xs text-slate-300 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 hover:border-indigo-500/50 transition-colors">
                  <span className="flex items-start space-x-2">
                    <span className="w-4 h-4 rounded-full bg-indigo-950 text-indigo-300 text-[10px] flex items-center justify-center font-mono border border-indigo-800 shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <span>{q}</span>
                  </span>
                  <button
                    onClick={() => onAskQuestion(q)}
                    className="opacity-0 group-hover:opacity-100 text-[10px] text-indigo-400 hover:text-indigo-300 bg-slate-800 px-2 py-0.5 rounded border border-slate-700 transition-opacity ml-2 shrink-0"
                  >
                    Practice This
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Candidate Strategy & Scoring Guide (AREA Method) */}
        <div className="bg-slate-950/40 rounded-xl p-4 border border-slate-800 flex flex-col justify-between space-y-3">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center mb-2">
              <Sparkles className="w-3.5 h-3.5 text-amber-400 mr-1.5" />
              Band 8.0 AREA Framework
            </span>

            <ul className="space-y-1.5 text-xs text-slate-300">
              <li className="flex items-start space-x-2">
                <span className="font-bold text-indigo-400 w-4">A:</span>
                <span><strong>Answer</strong> directly with a strong opinion.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="font-bold text-indigo-400 w-4">R:</span>
                <span><strong>Reason</strong> why ("This is primarily due to...").</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="font-bold text-indigo-400 w-4">E:</span>
                <span><strong>Example</strong> from society or global trends.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="font-bold text-indigo-400 w-4">A:</span>
                <span><strong>Alternative</strong> / Future speculation.</span>
              </li>
            </ul>
          </div>

          <div className="bg-indigo-950/30 p-2.5 rounded-lg border border-indigo-500/20 text-[11px] text-indigo-300">
            💡 <strong>Examiner Tip:</strong> Shift from personal "I like..." to societal "People generally tend to...".
          </div>
        </div>

      </div>

    </div>
  );
};
