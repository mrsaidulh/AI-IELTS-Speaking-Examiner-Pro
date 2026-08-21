import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Send, Volume2, Square, RefreshCw, AlertCircle } from 'lucide-react';
import { AudioWaveformVisualizer } from './AudioWaveformVisualizer';
import { createNormalizedAudioPipeline, NormalizedAudioPipeline } from '../audio/audioNormalizer';
import { TestMode } from '../types';

interface AudioRecorderControlsProps {
  onSendSpeech: (text: string) => void;
  isLoading: boolean;
  latestExaminerText?: string;
  onPlayExaminerVoice?: () => void;
  isSpeakingExaminer?: boolean;
  mode?: TestMode;
}

export const AudioRecorderControls: React.FC<AudioRecorderControlsProps> = ({
  onSendSpeech,
  isLoading,
  latestExaminerText,
  onPlayExaminerVoice,
  isSpeakingExaminer = false,
  mode = 'exam',
}) => {
  const [inputText, setInputText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const [audioLevel, setAudioLevel] = useState(0);
  const [analyserNode, setAnalyserNode] = useState<AnalyserNode | null>(null);
  
  const recognitionRef = useRef<any>(null);
  const isListeningRef = useRef<boolean>(false);
  const accumulatedRef = useRef<string>('');
  const pipelineRef = useRef<NormalizedAudioPipeline | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animRef = useRef<number | null>(null);

  // Initialize SpeechRecognition if available in browser
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = 'en-US';

      rec.onresult = (event: any) => {
        let interim = '';
        let currentFinal = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          if (result.isFinal) {
            currentFinal += result[0].transcript + ' ';
          } else {
            interim += result[0].transcript + ' ';
          }
        }
        if (currentFinal) {
          accumulatedRef.current = `${accumulatedRef.current} ${currentFinal}`.replace(/\s+/g, ' ').trim();
        }
        const fullTranscript = `${accumulatedRef.current} ${interim}`.replace(/\s+/g, ' ').trim();
        if (fullTranscript) {
          setInputText(fullTranscript);
        }
      };

      rec.onerror = (event: any) => {
        console.warn('Speech recognition notice:', event.error);
      };

      rec.onend = () => {
        if (isListeningRef.current) {
          try {
            rec.start();
          } catch (restartErr) {
            // Already started or active
          }
        } else {
          stopAudioGraph();
          setIsListening(false);
        }
      };

      recognitionRef.current = rec;
    } else {
      setSpeechSupported(false);
    }
  }, []);

  const stopAudioGraph = () => {
    if (animRef.current) {
      cancelAnimationFrame(animRef.current);
      animRef.current = null;
    }
    if (pipelineRef.current) {
      pipelineRef.current.cleanup();
      pipelineRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setAnalyserNode(null);
    setAudioLevel(0);
  };

  const startAudioGraph = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const pipeline = createNormalizedAudioPipeline(stream);
      pipelineRef.current = pipeline;

      const analyser = pipeline.analyserNode;
      setAnalyserNode(analyser);

      const data = new Uint8Array(analyser.fftSize);
      const loop = () => {
        if (!analyser) return;
        analyser.getByteTimeDomainData(data);
        let sum = 0;
        for (let i = 0; i < data.length; i++) {
          const val = (data[i] - 128) / 128;
          sum += val * val;
        }
        const rms = Math.sqrt(sum / data.length);
        setAudioLevel(Math.min(100, Math.round(rms * 500)));
        animRef.current = requestAnimationFrame(loop);
      };
      loop();
    } catch (e) {
      console.warn("Could not start visualizer audio graph:", e);
    }
  };

  const toggleListening = async () => {
    if (!recognitionRef.current) return;

    if (isListening) {
      isListeningRef.current = false;
      try {
        recognitionRef.current.stop();
      } catch (e) {}
      stopAudioGraph();
      setIsListening(false);
    } else {
      try {
        isListeningRef.current = true;
        accumulatedRef.current = inputText.trim();
        await startAudioGraph();
        recognitionRef.current.start();
        setIsListening(true);
      } catch (err) {
        console.error('Error starting speech rec:', err);
        isListeningRef.current = false;
      }
    }
  };

  const handleSend = () => {
    if (!inputText.trim() || isLoading) return;
    if (isListening && recognitionRef.current) {
      isListeningRef.current = false;
      try {
        recognitionRef.current.stop();
      } catch (e) {}
      stopAudioGraph();
      setIsListening(false);
    }
    accumulatedRef.current = '';
    onSendSpeech(inputText.trim());
    setInputText('');
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 sm:p-5 shadow-xl sticky bottom-4 z-20 backdrop-blur-lg space-y-3">
      
      {/* Latest Examiner Text Playback Banner */}
      {latestExaminerText && (
        <div className="flex items-center justify-between bg-indigo-950/40 border border-indigo-500/30 rounded-xl px-3.5 py-2.5 mb-2">
          <div className="flex items-center space-x-2 text-xs text-indigo-200 truncate pr-2">
            <Volume2 className={`w-4 h-4 text-indigo-400 shrink-0 ${isSpeakingExaminer ? 'animate-bounce' : ''}`} />
            <span className="font-medium text-slate-300 truncate">
              Examiner: "{latestExaminerText}"
            </span>
          </div>

          {onPlayExaminerVoice && (
            <div className="flex items-center space-x-2 shrink-0">
              {mode === 'training' && (
                <button
                  id="examiner-banner-retry-btn"
                  onClick={onPlayExaminerVoice}
                  className="flex items-center space-x-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 hover:border-slate-600 font-medium px-2.5 py-1 rounded-lg transition-colors"
                  title="Retry / Replay Examiner Audio (Training Mode only)"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isSpeakingExaminer ? 'animate-spin text-indigo-400' : 'text-slate-400'}`} />
                  <span>Retry</span>
                </button>
              )}
              <button
                id="examiner-banner-play-btn"
                onClick={onPlayExaminerVoice}
                className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-3 py-1 rounded-lg transition-colors"
              >
                {isSpeakingExaminer ? 'Speaking...' : 'Play Voice'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Real-time Waveform Visualizer when recording */}
      {isListening && (
        <AudioWaveformVisualizer
          analyserNode={analyserNode}
          isRecording={isListening}
          isVoiceDetected={audioLevel > 8}
          audioLevel={audioLevel}
          showDetails={true}
        />
      )}

      {/* Main Mic & Text Input Controls */}
      <div className="flex items-stretch space-x-3">
        
        {/* Mic Recording Button */}
        <button
          onClick={toggleListening}
          disabled={!speechSupported || isLoading}
          className={`px-4 sm:px-5 rounded-xl font-bold flex flex-col items-center justify-center transition-all ${
            isListening
              ? 'bg-rose-600 text-white animate-pulse ring-4 ring-rose-500/30 shadow-lg shadow-rose-600/30'
              : speechSupported
              ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20'
              : 'bg-slate-800 text-slate-500 cursor-not-allowed'
          }`}
          title={speechSupported ? (isListening ? 'Stop Recording' : 'Start Speech Recording') : 'Web Speech API not supported on browser'}
        >
          {isListening ? (
            <>
              <Square className="w-5 h-5 mb-0.5 fill-current" />
              <span className="text-[10px] uppercase font-bold">Stop</span>
            </>
          ) : (
            <>
              <Mic className="w-5 h-5 mb-0.5" />
              <span className="text-[10px] uppercase font-bold">Speak</span>
            </>
          )}
        </button>

        {/* Input Text Box / Speech Transcript Preview */}
        <div className="flex-1 relative">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={
              isListening
                ? 'Listening to your speech... (speak clearly into mic)'
                : 'Speak into microphone or type your IELTS candidate response here...'
            }
            rows={2}
            className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
          />

          {isListening && (
            <div className="absolute top-2 right-3 flex items-center space-x-1.5 text-rose-400 text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
              <span>Recording</span>
            </div>
          )}
        </div>

        {/* Send Button */}
        <button
          onClick={handleSend}
          disabled={!inputText.trim() || isLoading}
          className={`px-5 rounded-xl font-bold flex items-center justify-center transition-all ${
            inputText.trim() && !isLoading
              ? 'bg-gradient-to-r from-indigo-600 to-sky-500 hover:from-indigo-500 hover:to-sky-400 text-white shadow-md shadow-indigo-500/20'
              : 'bg-slate-800 text-slate-500 cursor-not-allowed'
          }`}
        >
          {isLoading ? (
            <RefreshCw className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>

      </div>

      {/* Helper Footer Bar */}
      <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2 px-1">
        <span className="flex items-center space-x-1">
          {!speechSupported && (
            <span className="text-amber-400 flex items-center mr-2">
              <AlertCircle className="w-3 h-3 mr-1" /> Mic auto-transcribe unavailable (use text box)
            </span>
          )}
          <span>Press <strong>Enter</strong> to submit answer • Practice natural pauses & clear articulation</span>
        </span>
        <span className="font-mono text-slate-500 hidden sm:inline">{inputText.length} chars</span>
      </div>

    </div>
  );
};
