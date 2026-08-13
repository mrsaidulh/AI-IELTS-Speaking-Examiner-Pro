import React, { useState, useEffect } from 'react';
import { CueCard } from '../types';
import { Play, Pause, RotateCcw, Clock, Sparkles, CheckCircle2 } from 'lucide-react';

interface CueCardViewerProps {
  cueCard: CueCard;
  onSelectNewCard?: () => void;
  onStartSpeech: () => void;
}

export const CueCardViewer: React.FC<CueCardViewerProps> = ({
  cueCard,
  onSelectNewCard,
  onStartSpeech,
}) => {
  const [prepSecondsLeft, setPrepSecondsLeft] = useState(cueCard.prepTimeSeconds);
  const [isPrepRunning, setIsPrepRunning] = useState(false);
  const [speakSecondsLeft, setSpeakSecondsLeft] = useState(cueCard.speakTimeSeconds);
  const [isSpeakRunning, setIsSpeakRunning] = useState(false);

  // Prep Countdown
  useEffect(() => {
    let timer: any = null;
    if (isPrepRunning && prepSecondsLeft > 0) {
      timer = setInterval(() => {
        setPrepSecondsLeft((prev) => prev - 1);
      }, 1000);
    } else if (prepSecondsLeft === 0 && isPrepRunning) {
      setIsPrepRunning(false);
      // Auto transition to speak mode
      setIsSpeakRunning(true);
      onStartSpeech();
    }
    return () => clearInterval(timer);
  }, [isPrepRunning, prepSecondsLeft, onStartSpeech]);

  // Speak Countdown
  useEffect(() => {
    let timer: any = null;
    if (isSpeakRunning && speakSecondsLeft > 0) {
      timer = setInterval(() => {
        setSpeakSecondsLeft((prev) => prev - 1);
      }, 1000);
    } else if (speakSecondsLeft === 0) {
      setIsSpeakRunning(false);
    }
    return () => clearInterval(timer);
  }, [isSpeakRunning, speakSecondsLeft]);

  const resetTimers = () => {
    setIsPrepRunning(false);
    setIsSpeakRunning(false);
    setPrepSecondsLeft(cueCard.prepTimeSeconds);
    setSpeakSecondsLeft(cueCard.speakTimeSeconds);
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-900/90 to-indigo-950/40 border border-indigo-500/30 rounded-2xl p-5 sm:p-6 shadow-xl mb-6 relative overflow-hidden">
      
      {/* Background Accent */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* Cue Card Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 mb-4 gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-1 text-xs font-bold rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              IELTS Speaking Part 2
            </span>
            <span className="text-xs text-slate-400">Individual Long Turn</span>
          </div>
          <h3 className="text-lg sm:text-xl font-extrabold text-white mt-1">{cueCard.topic}</h3>
        </div>

        {onSelectNewCard && (
          <button
            onClick={onSelectNewCard}
            className="self-start sm:self-auto text-xs text-indigo-400 hover:text-indigo-300 flex items-center space-x-1 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700/80 transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Switch Topic</span>
          </button>
        )}
      </div>

      {/* Cue Card Prompt & Bullet Points */}
      <div className="bg-slate-950/60 rounded-xl p-4 sm:p-5 border border-slate-800 mb-6 space-y-3">
        <p className="text-sm font-semibold text-slate-300">{cueCard.promptText}</p>
        <ul className="space-y-2">
          {cueCard.bulletPoints.map((pt, idx) => (
            <li key={idx} className="flex items-start space-x-2.5 text-sm text-slate-200">
              <CheckCircle2 className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
              <span>{pt}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Timers & Controls */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        
        {/* Prep Timer (60s) */}
        <div className={`p-4 rounded-xl border transition-all ${
          isPrepRunning ? 'bg-indigo-950/60 border-indigo-500 text-white' : 'bg-slate-800/40 border-slate-700/60'
        }`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center">
              <Clock className="w-3.5 h-3.5 mr-1 text-indigo-400" />
              Preparation Time (1 min)
            </span>
            <span className={`font-mono text-lg font-bold ${prepSecondsLeft < 10 ? 'text-amber-400 animate-pulse' : 'text-indigo-300'}`}>
              {formatTime(prepSecondsLeft)}
            </span>
          </div>

          <div className="w-full bg-slate-800 rounded-full h-2 mb-3 overflow-hidden">
            <div
              className="bg-indigo-500 h-2 rounded-full transition-all duration-1000"
              style={{ width: `${(prepSecondsLeft / cueCard.prepTimeSeconds) * 100}%` }}
            />
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsPrepRunning(!isPrepRunning)}
              className="flex-1 py-2 px-3 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg transition-all flex items-center justify-center space-x-1"
            >
              {isPrepRunning ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
              <span>{isPrepRunning ? 'Pause Prep' : 'Start 1-Min Prep'}</span>
            </button>
          </div>
        </div>

        {/* Speak Timer (120s) */}
        <div className={`p-4 rounded-xl border transition-all ${
          isSpeakRunning ? 'bg-emerald-950/60 border-emerald-500 text-white' : 'bg-slate-800/40 border-slate-700/60'
        }`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center">
              <Clock className="w-3.5 h-3.5 mr-1 text-emerald-400" />
              Speak Time (1-2 mins)
            </span>
            <span className={`font-mono text-lg font-bold ${speakSecondsLeft < 15 ? 'text-amber-400 animate-pulse' : 'text-emerald-300'}`}>
              {formatTime(speakSecondsLeft)}
            </span>
          </div>

          <div className="w-full bg-slate-800 rounded-full h-2 mb-3 overflow-hidden">
            <div
              className="bg-emerald-500 h-2 rounded-full transition-all duration-1000"
              style={{ width: `${(speakSecondsLeft / cueCard.speakTimeSeconds) * 100}%` }}
            />
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => {
                setIsSpeakRunning(!isSpeakRunning);
                if (!isSpeakRunning) onStartSpeech();
              }}
              className="flex-1 py-2 px-3 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-lg transition-all flex items-center justify-center space-x-1"
            >
              {isSpeakRunning ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
              <span>{isSpeakRunning ? 'Pause Speech' : 'Start Speaking'}</span>
            </button>

            <button
              onClick={resetTimers}
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700"
              title="Reset timers"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

      </div>

    </div>
  );
};
