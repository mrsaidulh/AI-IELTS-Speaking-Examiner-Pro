import React, { useEffect, useRef, useState } from 'react';
import { Activity, Mic, Volume2, Sparkles, Sliders, AlertTriangle, CheckCircle2, Radio } from 'lucide-react';

export type VisualizerMode = 'wave' | 'bars' | 'dual';

interface AudioWaveformVisualizerProps {
  analyserNode: AnalyserNode | null;
  isRecording: boolean;
  isVoiceDetected: boolean;
  audioLevel: number; // 0 to 100
  silenceProgress?: number; // 0 to 1
  accentColor?: string;
  showDetails?: boolean;
}

export const AudioWaveformVisualizer: React.FC<AudioWaveformVisualizerProps> = ({
  analyserNode,
  isRecording,
  isVoiceDetected,
  audioLevel,
  silenceProgress = 0,
  accentColor = '#10b981',
  showDetails = true,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const [mode, setMode] = useState<VisualizerMode>('dual');
  const [peakLevel, setPeakLevel] = useState<number>(0);
  const [decibels, setDecibels] = useState<number>(-60);

  // Track peak level with decay
  useEffect(() => {
    if (audioLevel > peakLevel) {
      setPeakLevel(audioLevel);
    } else {
      const decayTimer = setTimeout(() => {
        setPeakLevel((prev) => Math.max(0, prev - 2));
      }, 50);
      return () => clearTimeout(decayTimer);
    }
  }, [audioLevel, peakLevel]);

  // Determine speech quality status
  const getQualityStatus = () => {
    if (!isRecording) {
      return {
        label: 'Standby',
        badgeColor: 'bg-slate-800 text-slate-400 border-slate-700',
        icon: Radio,
        hint: 'Click Start Answer to begin speaking',
      };
    }
    if (!isVoiceDetected || audioLevel < 8) {
      const remainingSeconds = Math.max(0, 1.5 * (1 - silenceProgress)).toFixed(1);
      return {
        label: silenceProgress > 0 ? `Silence (${remainingSeconds}s)` : 'Low Signal / Quiet',
        badgeColor: silenceProgress > 0.4 ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' : 'bg-slate-800/80 text-slate-300 border-slate-700',
        icon: AlertTriangle,
        hint: 'Speak clearly toward your microphone',
      };
    }
    if (audioLevel >= 85) {
      return {
        label: 'Peak Input / High Gain',
        badgeColor: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
        icon: AlertTriangle,
        hint: 'Audio is loud; move slightly back from mic',
      };
    }
    return {
      label: 'Optimal Speech Level',
      badgeColor: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 animate-pulse',
      icon: CheckCircle2,
      hint: 'Crystal clear input for AI Speech Recognition',
    };
  };

  const quality = getQualityStatus();

  // Canvas visualizer loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Handle high-DPI crisp rendering
    const updateCanvasSize = () => {
      if (!containerRef.current || !canvas) return;
      const rect = containerRef.current.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    };

    updateCanvasSize();
    const resizeObserver = new ResizeObserver(updateCanvasSize);
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    let timeDomainBuffer: Uint8Array;
    let frequencyBuffer: Uint8Array;

    if (analyserNode) {
      timeDomainBuffer = new Uint8Array(analyserNode.fftSize);
      frequencyBuffer = new Uint8Array(analyserNode.frequencyBinCount);
    }

    let phase = 0;
    const barPeaks: number[] = new Array(36).fill(0);

    const render = () => {
      if (!canvas || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const width = rect.width;
      const height = rect.height;

      ctx.clearRect(0, 0, width, height);

      // Background subtle grid
      ctx.lineWidth = 1;
      ctx.strokeStyle = 'rgba(30, 41, 59, 0.4)';
      const midY = height / 2;

      // Draw center baseline
      ctx.beginPath();
      ctx.setLineDash([4, 4]);
      ctx.moveTo(0, midY);
      ctx.lineTo(width, midY);
      ctx.stroke();
      ctx.setLineDash([]);

      // If analyserNode is connected, extract live audio data
      if (analyserNode && isRecording) {
        analyserNode.getByteTimeDomainData(timeDomainBuffer);
        analyserNode.getByteFrequencyData(frequencyBuffer);

        // Compute dBFS approximation
        let sum = 0;
        for (let i = 0; i < timeDomainBuffer.length; i++) {
          const val = (timeDomainBuffer[i] - 128) / 128;
          sum += val * val;
        }
        const rms = Math.sqrt(sum / timeDomainBuffer.length);
        const db = rms > 0.0001 ? Math.max(-60, Math.round(20 * Math.log10(rms))) : -60;
        setDecibels(db);

        // --- MODE: BARS or DUAL (Frequency Spectrum) ---
        if (mode === 'bars' || mode === 'dual') {
          const barCount = 36;
          const barWidth = (width / barCount) * 0.7;
          const barSpacing = (width / barCount) * 0.3;
          const binStep = Math.max(1, Math.floor(frequencyBuffer.length / (barCount * 1.6)));

          for (let i = 0; i < barCount; i++) {
            const binIdx = Math.min(frequencyBuffer.length - 1, i * binStep);
            const rawVal = frequencyBuffer[binIdx] / 255;
            const barHeight = Math.max(4, rawVal * (height * 0.82));
            
            // Peak cap decay
            if (barHeight > barPeaks[i]) {
              barPeaks[i] = barHeight;
            } else {
              barPeaks[i] = Math.max(4, barPeaks[i] - 1.2);
            }

            const x = i * (barWidth + barSpacing) + barSpacing / 2;
            const y = midY - barHeight / 2;

            // Bar Gradient
            const barGrad = ctx.createLinearGradient(0, midY - barHeight / 2, 0, midY + barHeight / 2);
            if (isVoiceDetected) {
              if (rawVal > 0.75) {
                barGrad.addColorStop(0, 'rgba(244, 63, 94, 0.9)'); // Rose peak
                barGrad.addColorStop(0.5, 'rgba(245, 158, 11, 0.85)'); // Amber
                barGrad.addColorStop(1, 'rgba(16, 185, 129, 0.6)'); // Emerald
              } else {
                barGrad.addColorStop(0, 'rgba(14, 165, 233, 0.85)'); // Cyan
                barGrad.addColorStop(0.5, 'rgba(16, 185, 129, 0.8)'); // Emerald
                barGrad.addColorStop(1, 'rgba(99, 102, 241, 0.5)'); // Indigo
              }
            } else {
              barGrad.addColorStop(0, 'rgba(71, 85, 105, 0.5)');
              barGrad.addColorStop(1, 'rgba(51, 65, 85, 0.3)');
            }

            // Draw rounded bar
            ctx.fillStyle = barGrad;
            const radius = Math.min(barWidth / 2, 3);
            ctx.beginPath();
            ctx.roundRect(x, y, barWidth, barHeight, radius);
            ctx.fill();

            // Draw peak marker cap
            if (barPeaks[i] > 6) {
              ctx.fillStyle = isVoiceDetected ? 'rgba(56, 189, 248, 0.95)' : 'rgba(148, 163, 184, 0.6)';
              ctx.beginPath();
              ctx.roundRect(x, midY - barPeaks[i] / 2 - 2, barWidth, 2, 1);
              ctx.fill();
            }
          }
        }

        // --- MODE: WAVE or DUAL (Fluid Oscilloscope Sine Curve) ---
        if (mode === 'wave' || mode === 'dual') {
          const sliceWidth = width / (timeDomainBuffer.length / 4);
          
          // Layer 1: Glow Halo / Area Fill
          ctx.save();
          ctx.beginPath();
          ctx.moveTo(0, midY);

          for (let i = 0; i < timeDomainBuffer.length; i += 4) {
            const v = (timeDomainBuffer[i] - 128) / 128;
            const y = midY + v * (height * (mode === 'dual' ? 0.45 : 0.85));
            const x = (i / 4) * sliceWidth;

            if (i === 0) {
              ctx.moveTo(x, y);
            } else {
              ctx.lineTo(x, y);
            }
          }

          ctx.lineTo(width, midY);
          const areaGrad = ctx.createLinearGradient(0, 0, 0, height);
          if (isVoiceDetected) {
            areaGrad.addColorStop(0, 'rgba(16, 185, 129, 0.15)');
            areaGrad.addColorStop(0.5, 'rgba(6, 182, 212, 0.08)');
            areaGrad.addColorStop(1, 'rgba(99, 102, 241, 0.0)');
          } else {
            areaGrad.addColorStop(0, 'rgba(51, 65, 85, 0.1)');
            areaGrad.addColorStop(1, 'rgba(30, 41, 59, 0.0)');
          }
          ctx.fillStyle = areaGrad;
          ctx.fill();
          ctx.restore();

          // Layer 2: Sharp Crisp Stroke Curve
          ctx.save();
          ctx.beginPath();
          ctx.lineWidth = mode === 'dual' ? 2 : 2.5;

          const strokeGrad = ctx.createLinearGradient(0, 0, width, 0);
          if (isVoiceDetected) {
            strokeGrad.addColorStop(0, '#10b981'); // Emerald
            strokeGrad.addColorStop(0.35, '#06b6d4'); // Cyan
            strokeGrad.addColorStop(0.7, '#6366f1'); // Indigo
            strokeGrad.addColorStop(1, '#a855f7'); // Purple
          } else {
            strokeGrad.addColorStop(0, '#475569');
            strokeGrad.addColorStop(1, '#64748b');
          }

          ctx.strokeStyle = strokeGrad;
          ctx.shadowColor = isVoiceDetected ? 'rgba(16, 185, 129, 0.6)' : 'rgba(71, 85, 105, 0.2)';
          ctx.shadowBlur = isVoiceDetected ? 8 : 2;

          for (let i = 0; i < timeDomainBuffer.length; i += 4) {
            const v = (timeDomainBuffer[i] - 128) / 128;
            const y = midY + v * (height * (mode === 'dual' ? 0.45 : 0.85));
            const x = (i / 4) * sliceWidth;

            if (i === 0) {
              ctx.moveTo(x, y);
            } else {
              ctx.lineTo(x, y);
            }
          }

          ctx.stroke();
          ctx.restore();
        }
      } else {
        // Standby animated wave when idle or initializing
        phase += 0.04;
        ctx.save();
        ctx.beginPath();
        ctx.lineWidth = 2;
        ctx.strokeStyle = 'rgba(71, 85, 105, 0.5)';
        ctx.moveTo(0, midY);

        for (let x = 0; x < width; x += 4) {
          const y = midY + Math.sin(x * 0.02 + phase) * 4 * Math.sin(x * 0.005 + phase * 0.5);
          ctx.lineTo(x, y);
        }

        ctx.stroke();
        ctx.restore();
      }

      animationFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animationFrameRef.current !== null) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      resizeObserver.disconnect();
    };
  }, [analyserNode, isRecording, isVoiceDetected, mode]);

  const StatusIcon = quality.icon;

  return (
    <div className="w-full bg-slate-950/90 border border-slate-800/90 rounded-xl p-3 sm:p-4 shadow-inner backdrop-blur space-y-2.5">
      
      {/* Top Bar: Input Metrics & Status Badges */}
      {showDetails && (
        <div className="flex items-center justify-between flex-wrap gap-2 text-xs">
          
          {/* Live Audio Status Badge */}
          <div className="flex items-center space-x-2">
            <span className={`px-2.5 py-1 rounded-md font-semibold border flex items-center space-x-1.5 transition-all ${quality.badgeColor}`}>
              <StatusIcon className="w-3.5 h-3.5 shrink-0" />
              <span>{quality.label}</span>
            </span>

            {isRecording && (
              <span className="text-[11px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                {decibels > -60 ? `${decibels} dBFS` : 'Noise floor'}
              </span>
            )}
          </div>

          {/* Mode Switcher Buttons */}
          <div className="flex items-center space-x-1 bg-slate-900 p-0.5 rounded-lg border border-slate-800">
            <button
              onClick={() => setMode('dual')}
              title="Dual Wave + Spectrum View"
              className={`px-2 py-0.5 rounded text-[11px] font-medium transition-all ${
                mode === 'dual'
                  ? 'bg-indigo-600 text-white shadow-sm font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Dual
            </button>
            <button
              onClick={() => setMode('wave')}
              title="Oscilloscope Waveform View"
              className={`px-2 py-0.5 rounded text-[11px] font-medium transition-all ${
                mode === 'wave'
                  ? 'bg-indigo-600 text-white shadow-sm font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Wave
            </button>
            <button
              onClick={() => setMode('bars')}
              title="Frequency Equalizer Spectrum View"
              className={`px-2 py-0.5 rounded text-[11px] font-medium transition-all ${
                mode === 'bars'
                  ? 'bg-indigo-600 text-white shadow-sm font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Bars
            </button>
          </div>
        </div>
      )}

      {/* Main Canvas Waveform Display Container */}
      <div 
        ref={containerRef} 
        className="w-full h-20 sm:h-24 bg-gradient-to-b from-slate-950 to-slate-900/90 rounded-lg relative overflow-hidden border border-slate-800/80 flex items-center justify-center"
      >
        <canvas ref={canvasRef} className="w-full h-full block" />

        {/* Overlay Target Range Guidelines */}
        {isRecording && (
          <div className="absolute inset-y-0 left-0 right-0 pointer-events-none flex flex-col justify-between p-1.5 opacity-30 text-[9px] font-mono text-slate-500">
            <div className="flex justify-between border-b border-slate-700/40 pb-0.5">
              <span>PEAK ZONE (+0 dB)</span>
              <span>8.0 kHz</span>
            </div>
            <div className="flex justify-between border-t border-slate-700/40 pt-0.5">
              <span>TARGET SPEECH ZONE (-18 dB)</span>
              <span>100 Hz</span>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Meter: Multi-Segment Audio Strength & Silence Countdown */}
      <div className="space-y-1.5">
        
        {/* Dynamic Multicolored Audio Level Bar with Peak Indicator */}
        <div className="relative w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800 flex items-center">
          
          {/* Active Audio Level Fill */}
          <div 
            className={`h-full transition-all duration-75 ${
              audioLevel > 85 
                ? 'bg-gradient-to-r from-amber-500 to-rose-500' 
                : isVoiceDetected 
                ? 'bg-gradient-to-r from-teal-500 via-emerald-400 to-cyan-400' 
                : 'bg-slate-700'
            }`}
            style={{ width: `${Math.max(2, Math.min(100, audioLevel))}%` }}
          />

          {/* Peak Hold Marker Line */}
          {peakLevel > 0 && (
            <div 
              className="absolute top-0 bottom-0 w-1 bg-white/90 shadow-sm"
              style={{ left: `${Math.min(99, Math.max(1, peakLevel))}%` }}
            />
          )}

          {/* Optimal Target Zone Marker */}
          <div className="absolute left-[20%] right-[35%] top-0 bottom-0 border-x border-emerald-500/40 bg-emerald-500/5 pointer-events-none" />
        </div>

        {/* Silence Timeout Progress Bar (When candidate is silent) */}
        {isRecording && silenceProgress > 0 && (
          <div className="flex items-center space-x-2 text-[10px] text-amber-400/90 pt-0.5 font-medium animate-pulse">
            <AlertTriangle className="w-3 h-3 shrink-0 text-amber-400" />
            <div className="flex-1 bg-slate-900 rounded-full h-1.5 overflow-hidden border border-slate-800">
              <div 
                className="h-full bg-gradient-to-r from-amber-400 to-rose-500 transition-all duration-100"
                style={{ width: `${Math.min(100, silenceProgress * 100)}%` }}
              />
            </div>
            <span className="font-mono">{(Math.max(0, 1.5 * (1 - silenceProgress))).toFixed(1)}s to auto-stop</span>
          </div>
        )}

        {/* Quality Hint */}
        {showDetails && (
          <div className="flex items-center justify-between text-[11px] text-slate-400 pt-0.5">
            <span className="truncate pr-2">{quality.hint}</span>
            <span className="font-mono text-slate-500 shrink-0">Level: {audioLevel}%</span>
          </div>
        )}
      </div>

    </div>
  );
};
