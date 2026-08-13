import React from 'react';
import { ChatMessage, TestMode } from '../types';
import { User, Volume2, Sparkles, CheckCircle, AlertTriangle, ArrowRight, BookOpen } from 'lucide-react';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  mode: TestMode;
  onPlayMessageVoice: (text: string) => void;
  isLoading: boolean;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  mode,
  onPlayMessageVoice,
  isLoading,
}) => {
  return (
    <div className="space-y-4 mb-6">
      {messages.length === 0 ? (
        <div className="text-center py-12 px-4 bg-slate-900/60 rounded-2xl border border-slate-800">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto mb-4">
            <User className="w-8 h-8" />
          </div>
          <h3 className="text-base font-bold text-white mb-1">Your IELTS Examiner is Ready</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Click "Speak" on the microphone or type below to introduce yourself. The examiner will guide you through Part 1, 2, and 3.
          </p>
        </div>
      ) : (
        messages.map((msg) => {
          const isExaminer = msg.sender === 'examiner';

          return (
            <div
              key={msg.id}
              className={`flex flex-col ${isExaminer ? 'items-start' : 'items-end'} space-y-2`}
            >
              
              {/* Sender Badge */}
              <div className="flex items-center space-x-2 px-1 text-xs text-slate-400">
                <span className="font-semibold text-slate-300">
                  {isExaminer ? 'IELTS Examiner' : 'Candidate'}
                </span>
                <span>•</span>
                <span className="text-[10px] text-slate-500">{msg.timestamp}</span>
              </div>

              {/* Message Speech Card */}
              <div
                className={`max-w-3xl rounded-2xl p-4 text-sm leading-relaxed shadow-sm relative ${
                  isExaminer
                    ? 'bg-slate-900 border border-slate-800 text-slate-100 rounded-tl-sm'
                    : 'bg-gradient-to-r from-indigo-700 to-indigo-800 text-white rounded-tr-sm shadow-md'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="whitespace-pre-wrap">{msg.text}</p>

                  {isExaminer && (
                    <button
                      onClick={() => onPlayMessageVoice(msg.text)}
                      className="text-slate-400 hover:text-indigo-400 p-1.5 rounded-lg hover:bg-slate-800 transition-colors shrink-0"
                      title="Play examiner voice audio"
                    >
                      <Volume2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>

              {/* Training Mode Feedback Card (for Candidate responses) */}
              {!isExaminer && msg.corrections && mode === 'training' && (
                <div className="max-w-3xl w-full bg-slate-950 border border-emerald-500/30 rounded-2xl p-4 text-xs space-y-3 mt-1 shadow-md">
                  
                  {/* Feedback Header */}
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <div className="flex items-center space-x-2 text-emerald-400 font-bold">
                      <Sparkles className="w-4 h-4 text-emerald-400" />
                      <span>Band 8.0+ Language Enhancements</span>
                    </div>
                    <span className="text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full font-semibold">
                      Training Feedback
                    </span>
                  </div>

                  {/* Corrected Sentence Version */}
                  {msg.corrections.correctedText && (
                    <div className="bg-emerald-950/40 p-3 rounded-xl border border-emerald-500/20">
                      <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                        Recommended Band 8.0 Paraphrase
                      </div>
                      <p className="text-slate-100 font-medium text-xs leading-relaxed flex items-start space-x-2">
                        <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                        <span>{msg.corrections.correctedText}</span>
                      </p>
                    </div>
                  )}

                  {/* Grammar Corrections */}
                  {msg.corrections.grammarIssues && msg.corrections.grammarIssues.length > 0 && (
                    <div className="space-y-1.5">
                      <div className="text-[10px] font-bold text-amber-400 uppercase tracking-wider flex items-center">
                        <AlertTriangle className="w-3 h-3 mr-1" /> Grammar Adjustments
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {msg.corrections.grammarIssues.map((g, idx) => (
                          <div key={idx} className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                            <div className="font-semibold text-rose-300 flex items-center text-[11px]">
                              <span>{g.issue}</span>
                              <ArrowRight className="w-3 h-3 mx-1 text-slate-500" />
                              <span className="text-emerald-300">{g.fix}</span>
                            </div>
                            <p className="text-[10px] text-slate-400 mt-1">{g.explanation}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Vocabulary Upgrades */}
                  {msg.corrections.vocabularyUpgrades && msg.corrections.vocabularyUpgrades.length > 0 && (
                    <div className="space-y-1.5">
                      <div className="text-[10px] font-bold text-sky-400 uppercase tracking-wider flex items-center">
                        <BookOpen className="w-3 h-3 mr-1" /> Lexical Resource Upgrades
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {msg.corrections.vocabularyUpgrades.map((v, idx) => (
                          <div key={idx} className="bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800 text-[11px] flex items-center space-x-2">
                            <span className="line-through text-slate-400">{v.original}</span>
                            <ArrowRight className="w-3 h-3 text-indigo-400" />
                            <span className="font-bold text-sky-300">{v.upgraded}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Band Boost Tip */}
                  {msg.corrections.bandBoostTip && (
                    <p className="text-[11px] text-slate-300 italic bg-indigo-950/30 p-2.5 rounded-lg border border-indigo-500/20">
                      💡 <strong>Examiner Tip:</strong> {msg.corrections.bandBoostTip}
                    </p>
                  )}

                </div>
              )}

            </div>
          );
        })
      )}

      {/* Loading Indicator */}
      {isLoading && (
        <div className="flex items-center space-x-3 bg-slate-900 border border-slate-800 rounded-2xl p-4 max-w-sm">
          <div className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-ping" />
          <span className="text-xs text-slate-300 font-medium">Examiner is listening & formulating question...</span>
        </div>
      )}
    </div>
  );
};
