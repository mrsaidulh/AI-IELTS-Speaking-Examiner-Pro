import React, { useState, useEffect } from 'react';
import { 
  Server, Bot, Mic, Volume2, Cpu, Database, RefreshCw, 
  CheckCircle2, XCircle, AlertTriangle, Terminal, X, ShieldCheck, Zap
} from 'lucide-react';
import { SystemStatusData } from '../types';

interface ServerStatusModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ServerStatusModal: React.FC<ServerStatusModalProps> = ({ isOpen, onClose }) => {
  const [statusData, setStatusData] = useState<SystemStatusData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [lastChecked, setLastChecked] = useState<string>('');

  const fetchStatus = async () => {
    setLoading(true);
    try {
      // Try direct FastAPI backend first, then fallback to relative API proxy
      let res: Response | null = null;
      try {
        res = await fetch('http://localhost:8000/api/system/status', { cache: 'no-store' });
      } catch (e) {
        res = await fetch('/api/system/status', { cache: 'no-store' });
      }

      if (res && res.ok) {
        const data: SystemStatusData = await res.json();
        setStatusData(data);
      } else {
        throw new Error('Non-200 response');
      }
    } catch (err) {
      // Unreachable fallback
      setStatusData({
        status: 'degraded',
        timestamp: new Date().toISOString(),
        all_systems_ready: false,
        components: {
          fastapi: {
            status: 'offline',
            port: 8000,
            version: '1.3',
            message: 'FastAPI Backend server is offline on http://localhost:8000'
          },
          ollama: {
            status: 'unknown',
            model: 'qwen2.5:7b-instruct',
            url: 'http://localhost:11434',
            available_models: [],
            message: 'Start FastAPI backend to check Ollama LLM'
          },
          whisper: {
            status: 'unknown',
            backend: 'faster_whisper',
            model_size: 'small',
            device: 'cpu/cuda',
            compute_type: 'int8',
            message: 'Start FastAPI backend to check Whisper STT'
          },
          kokoro: {
            status: 'unknown',
            voice: 'af_heart',
            sample_rate: 24000,
            message: 'Start FastAPI backend to check Kokoro TTS'
          },
          gpu: {
            status: 'unknown',
            cuda_available: false,
            device_name: 'GPU',
            vram_total_mb: 0,
            vram_allocated_mb: 0,
            cuda_version: null
          },
          database: {
            status: 'online',
            engine: 'SQLite',
            message: 'Web client active'
          }
        }
      });
    } finally {
      setLoading(false);
      setLastChecked(new Date().toLocaleTimeString());
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchStatus();
      const interval = setInterval(fetchStatus, 8000);
      return () => clearInterval(interval);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'online':
      case 'ok':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            <span>Online</span>
          </span>
        );
      case 'fallback':
      case 'cpu_only':
      case 'degraded':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
            <AlertTriangle className="w-3 h-3 text-amber-400" />
            <span className="capitalize">{status.replace('_', ' ')}</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30">
            <XCircle className="w-3 h-3 text-rose-400" />
            <span>Offline</span>
          </span>
        );
    }
  };

  const c = statusData?.components;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in">
      <div className="relative w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl text-slate-100 overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/80">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-indigo-600/20 text-indigo-400 rounded-xl border border-indigo-500/30">
              <Server className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-bold text-white">System & Server Status</h3>
                <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  Port 8000 & 11434
                </span>
              </div>
              <p className="text-xs text-slate-400">Real-time health monitor for local AI pipeline engines</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={fetchStatus}
              disabled={loading}
              className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
              <span>Refresh</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Status Summary Banner */}
        <div className="px-6 py-3 bg-slate-950/60 border-b border-slate-800/80 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-2">
            <span className="text-slate-400">System Readiness:</span>
            {statusData?.all_systems_ready ? (
              <span className="font-semibold text-emerald-400 flex items-center space-x-1">
                <ShieldCheck className="w-4 h-4" />
                <span>All Core AI Components Online</span>
              </span>
            ) : (
              <span className="font-semibold text-amber-400 flex items-center space-x-1">
                <AlertTriangle className="w-4 h-4" />
                <span>Partial / Offline Services Detected</span>
              </span>
            )}
          </div>
          <div className="text-slate-500">
            Last checked: {lastChecked || 'Just now'}
          </div>
        </div>

        {/* Components Grid */}
        <div className="p-6 overflow-y-auto space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

            {/* 1. FastAPI Backend Server */}
            <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/80 hover:border-slate-600 transition-all">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2.5">
                  <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                    <Server className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm text-white">FastAPI Voice Server</h4>
                    <span className="text-[11px] text-slate-400">HTTP & WebSocket API (Port 8000)</span>
                  </div>
                </div>
                {getStatusBadge(c?.fastapi?.status || 'offline')}
              </div>

              <div className="mt-3 pt-3 border-t border-slate-700/50 text-xs space-y-1 text-slate-300">
                <div className="flex justify-between text-slate-400">
                  <span>Version / Host:</span>
                  <span className="font-mono text-slate-200">v{c?.fastapi?.version || '1.3'} (localhost:8000)</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1">{c?.fastapi?.message}</p>
              </div>

              {c?.fastapi?.status === 'offline' && (
                <div className="mt-3 p-2 rounded bg-slate-900 border border-rose-500/30 text-[11px] font-mono text-rose-300">
                  Start command: <span className="text-white">PYTHONPATH=backend python3 backend/voice_api.py</span>
                </div>
              )}
            </div>

            {/* 2. Ollama LLM Engine */}
            <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/80 hover:border-slate-600 transition-all">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2.5">
                  <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                    <Bot className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm text-white">Ollama LLM (Qwen2.5)</h4>
                    <span className="text-[11px] text-slate-400">Examiner Brain (Port 11434)</span>
                  </div>
                </div>
                {getStatusBadge(c?.ollama?.status || 'offline')}
              </div>

              <div className="mt-3 pt-3 border-t border-slate-700/50 text-xs space-y-1 text-slate-300">
                <div className="flex justify-between text-slate-400">
                  <span>Target Model:</span>
                  <span className="font-mono text-purple-300 font-medium">{c?.ollama?.model || 'qwen2.5:7b-instruct'}</span>
                </div>
                {c?.ollama?.available_models && c.ollama.available_models.length > 0 && (
                  <div className="flex justify-between text-slate-400">
                    <span>Installed Models:</span>
                    <span className="font-mono text-emerald-300">{c.ollama.available_models.join(', ')}</span>
                  </div>
                )}
                <p className="text-[11px] text-slate-400 mt-1">{c?.ollama?.message}</p>
              </div>

              {c?.ollama?.status === 'offline' && (
                <div className="mt-3 p-2 rounded bg-slate-900 border border-amber-500/30 text-[11px] text-amber-200">
                  💡 Launch Ollama in Windows or run: <code className="text-amber-100 bg-slate-800 px-1 rounded">ollama serve</code>
                </div>
              )}
            </div>

            {/* 3. Whisper STT Model */}
            <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/80 hover:border-slate-600 transition-all">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2.5">
                  <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
                    <Mic className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm text-white">Whisper Speech-to-Text</h4>
                    <span className="text-[11px] text-slate-400">Candidate Audio Transcriber</span>
                  </div>
                </div>
                {getStatusBadge(c?.whisper?.status || 'offline')}
              </div>

              <div className="mt-3 pt-3 border-t border-slate-700/50 text-xs space-y-1 text-slate-300">
                <div className="grid grid-cols-2 gap-x-2 text-[11px]">
                  <div><span className="text-slate-400">Engine:</span> <span className="font-mono text-slate-200">{c?.whisper?.backend || 'faster_whisper'}</span></div>
                  <div><span className="text-slate-400">Size:</span> <span className="font-mono text-slate-200">{c?.whisper?.model_size || 'small'}</span></div>
                  <div><span className="text-slate-400">Device:</span> <span className="font-mono text-sky-300 font-semibold">{c?.whisper?.device?.toUpperCase() || 'CPU'}</span></div>
                  <div><span className="text-slate-400">Compute:</span> <span className="font-mono text-slate-200">{c?.whisper?.compute_type || 'int8'}</span></div>
                </div>
                <p className="text-[11px] text-slate-400 mt-1.5">{c?.whisper?.message}</p>
              </div>
            </div>

            {/* 4. Kokoro TTS Engine */}
            <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/80 hover:border-slate-600 transition-all">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2.5">
                  <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <Volume2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm text-white">Kokoro Voice Synthesis</h4>
                    <span className="text-[11px] text-slate-400">Examiner Speech Generator</span>
                  </div>
                </div>
                {getStatusBadge(c?.kokoro?.status || 'offline')}
              </div>

              <div className="mt-3 pt-3 border-t border-slate-700/50 text-xs space-y-1 text-slate-300">
                <div className="flex justify-between text-slate-400">
                  <span>Voice Model / Voice:</span>
                  <span className="font-mono text-emerald-300">Kokoro-82M ({c?.kokoro?.voice || 'af_heart'})</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Sample Rate:</span>
                  <span className="font-mono text-slate-200">24,000 Hz PCM</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1">{c?.kokoro?.message}</p>
              </div>
            </div>

            {/* 5. GPU Acceleration */}
            <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/80 hover:border-slate-600 transition-all">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2.5">
                  <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    <Zap className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm text-white">NVIDIA GPU Acceleration</h4>
                    <span className="text-[11px] text-slate-400">PyTorch CUDA Hardware</span>
                  </div>
                </div>
                {getStatusBadge(c?.gpu?.status || 'cpu_only')}
              </div>

              <div className="mt-3 pt-3 border-t border-slate-700/50 text-xs space-y-1 text-slate-300">
                <div className="flex justify-between text-slate-400">
                  <span>GPU Card:</span>
                  <span className="font-semibold text-amber-300">{c?.gpu?.device_name || 'NVIDIA GPU'}</span>
                </div>
                {c?.gpu?.vram_total_mb ? (
                  <div className="flex justify-between text-slate-400">
                    <span>VRAM Usage:</span>
                    <span className="font-mono text-slate-200">{c.gpu.vram_allocated_mb} MiB / {c.gpu.vram_total_mb} MiB</span>
                  </div>
                ) : null}
                {c?.gpu?.cuda_version && (
                  <div className="flex justify-between text-slate-400">
                    <span>CUDA Runtime:</span>
                    <span className="font-mono text-slate-200">CUDA {c.gpu.cuda_version}</span>
                  </div>
                )}
              </div>
            </div>

            {/* 6. SQLite Database */}
            <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/80 hover:border-slate-600 transition-all">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2.5">
                  <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    <Database className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm text-white">Database Store</h4>
                    <span className="text-[11px] text-slate-400">Sessions & Score Reports</span>
                  </div>
                </div>
                {getStatusBadge(c?.database?.status || 'online')}
              </div>

              <div className="mt-3 pt-3 border-t border-slate-700/50 text-xs space-y-1 text-slate-300">
                <div className="flex justify-between text-slate-400">
                  <span>Storage Engine:</span>
                  <span className="font-mono text-blue-300">SQLite (local.db)</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1">{c?.database?.message}</p>
              </div>
            </div>

          </div>
        </div>

        {/* Quick Launch Terminal Command Guide */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-indigo-400" />
            <span>Quick Start Terminal Command:</span>
            <code className="px-2 py-1 bg-slate-900 border border-slate-700 rounded font-mono text-indigo-300 text-[11px]">
              PYTHONPATH=backend python3 backend/voice_api.py
            </code>
          </div>

          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition-colors"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
};
