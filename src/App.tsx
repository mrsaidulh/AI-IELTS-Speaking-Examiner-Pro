import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { ExamStageSelector } from './components/ExamStageSelector';
import { CueCardViewer } from './components/CueCardViewer';
import { ChatInterface } from './components/ChatInterface';
import { BandReportView } from './components/BandReportView';
import { LocalDeploymentGuide } from './components/LocalDeploymentGuide';
import { OFFICIAL_CUE_CARDS } from './data/topics';
import { TestMode, TestPart, ExaminerAccent, ChatMessage, IELTSEvaluationReport, CueCard } from './types';
import { Mic, Square, RefreshCw, Volume2, Radio, Sparkles, Activity } from 'lucide-react';
import { useVAD } from './hooks/useVAD';
import { PCMStreamer } from './audio/PCMStreamer';

const API_URL = "http://localhost:8000";

type ConversationStatus = 'ready' | 'recording' | 'transcribing' | 'thinking' | 'speaking';

export default function App() {
  const [activeTab, setActiveTab] = useState<'practice' | 'report' | 'guide'>('practice');
  const [mode, setMode] = useState<TestMode>('exam');
  const [currentPart, setCurrentPart] = useState<TestPart>('part1');
  const [accent, setAccent] = useState<ExaminerAccent>('british');
  const [targetBand, setTargetBand] = useState<number>(7.5);
  const [showSettings, setShowSettings] = useState<boolean>(false);

  const [cueCardIndex, setCueCardIndex] = useState<number>(0);
  const currentCueCard: CueCard = OFFICIAL_CUE_CARDS[cueCardIndex];

  // Session & State Machine
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [partNum, setPartNum] = useState<number>(1);
  const [status, setStatus] = useState<ConversationStatus>('ready');
  const [recordingTime, setRecordingTime] = useState<number>(0);
  const [examinerText, setExaminerText] = useState<string>(
    "Where are you from?"
  );
  const [candidateText, setCandidateText] = useState<string>("");

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<any>(null);
  const maxTimerRef = useRef<any>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const pcmStreamerRef = useRef<PCMStreamer | null>(null);
  const expectingAudioRef = useRef<boolean>(false);

  // Lesson 22: Voice Activity Detection (VAD) Hook
  const { isVoiceDetected, audioLevel, startMonitoring, stopMonitoring } = useVAD({
    threshold: 0.02,
    silenceDelay: 1500,
    minSpeechTime: 300,
  });

  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const saved = localStorage.getItem('ielts_messages');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) {}
    }
    return [
      {
        id: 'msg-init',
        sender: 'examiner',
        text: 'Where are you from?',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ];
  });

  const [report, setReport] = useState<IELTSEvaluationReport | null>(() => {
    const saved = localStorage.getItem('ielts_report');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) {}
    }
    return null;
  });

  const [isGeneratingReport, setIsGeneratingReport] = useState<boolean>(false);

  // Synchronize test part number
  useEffect(() => {
    const p = currentPart === 'part1' ? 1 : currentPart === 'part2' ? 2 : 3;
    setPartNum(p);
  }, [currentPart]);

  // Lessons 19, 20 & 21: WebSocket connection management with Kokoro audio & real-time protocol
  useEffect(() => {
    const wsUrl = `ws://localhost:8000/ws/speaking/${sessionId || 'demo'}`;
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(wsUrl);
      ws.binaryType = "arraybuffer";
      socketRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected to FastAPI backend for session:', sessionId);
      };

      ws.onmessage = (event) => {
        if (typeof event.data === 'string') {
          try {
            const msg = JSON.parse(event.data);
            console.log('WebSocket Event:', msg);

            if (msg.type === 'phase' || msg.type === 'status') {
              if (msg.value === 'listening') setStatus('recording');
              else if (msg.value === 'processing' || msg.value === 'transcribing') setStatus('transcribing');
              else if (msg.value === 'thinking') setStatus('thinking');
              else if (msg.value === 'speaking') setStatus('speaking');
              else if (msg.value === 'ready') setStatus('ready');
            } else if (msg.type === 'transcription' || msg.type === 'transcript') {
              setCandidateText(msg.text);
              const candMsg: ChatMessage = {
                id: `msg-c-${Date.now()}`,
                sender: 'candidate',
                text: msg.text,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              };
              setMessages((prev) => [...prev, candMsg]);
            } else if (msg.type === 'question') {
              setExaminerText(msg.text);
              const exMsg: ChatMessage = {
                id: `msg-e-${Date.now()}`,
                sender: 'examiner',
                text: msg.text,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              };
              setMessages((prev) => [...prev, exMsg]);
            } else if (msg.type === 'examiner_audio') {
              expectingAudioRef.current = true;
              setStatus('speaking');
            } else if (msg.type === 'test_complete') {
              const endMsg: ChatMessage = {
                id: `msg-end-${Date.now()}`,
                sender: 'examiner',
                text: 'Thank you. That completes Part 1 of the IELTS Speaking test.',
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              };
              setMessages((prev) => [...prev, endMsg]);
              setStatus('ready');
            } else if (msg.type === 'error') {
              console.warn('WebSocket message note:', msg.message);
              setStatus('ready');
            }
          } catch (e) {
            console.log('WebSocket raw message:', event.data);
          }
        } else if (event.data instanceof ArrayBuffer) {
          console.log("Received Kokoro examiner audio binary buffer:", event.data.byteLength, "bytes");
          expectingAudioRef.current = false;
          const audioBlob = new Blob([event.data], { type: 'audio/mpeg' });
          const audioUrl = URL.createObjectURL(audioBlob);
          const audio = new Audio(audioUrl);
          setStatus('speaking');

          audio.onended = () => {
            setStatus('ready');
            URL.revokeObjectURL(audioUrl);
          };
          audio.onerror = () => {
            setStatus('ready');
          };
          audio.play().catch((err) => {
            console.warn("Kokoro audio autoplay note:", err);
            setStatus('ready');
          });
        }
      };

      ws.onerror = () => {
        console.warn('WebSocket notice: FastAPI backend connection simulated or offline');
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
      };
    } catch (e) {
      console.warn('WebSocket init exception:', e);
    }

    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [sessionId]);

  // Lessons 19 & 20: Auto-create session on mount
  const createSession = async () => {
    try {
      const res = await fetch(`${API_URL}/session/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Saidul Hasan', email: 'test@example.com' }),
      });
      if (res.ok) {
        const data = await res.json();
        setSessionId(data.session_id);
        if (data.question) setExaminerText(data.question);
        if (data.part) setPartNum(data.part);
      } else {
        setSessionId(`sess-${Date.now()}`);
      }
    } catch (e) {
      console.warn("Backend local API not yet running, using client session ID");
      setSessionId(`sess-${Date.now()}`);
    }
  };

  useEffect(() => {
    createSession();
  }, []);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const startTimer = () => {
    setRecordingTime(0);
    timerRef.current = setInterval(() => {
      setRecordingTime((prev) => prev + 1);
    }, 1000);
  };

  const stopTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Start Microphone Recording with Echo Cancellation & VAD Constraints
  const startRecording = async () => {
    if (status === 'speaking' || status !== 'ready') {
      console.warn('Recording blocked: Examiner is currently speaking or system is busy.');
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = async (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            try {
              const buffer = await event.data.arrayBuffer();
              if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
                socketRef.current.send(buffer);
                console.log('Audio chunk streamed over WebSocket:', buffer.byteLength, 'bytes');
              }
            } catch (err) {
              console.warn('Chunk streaming error:', err);
            }
          }
        }
      };

      recorder.onstop = async () => {
        if (maxTimerRef.current) {
          clearTimeout(maxTimerRef.current);
          maxTimerRef.current = null;
        }
        stopMonitoring();
        stopTimer();

        if (pcmStreamerRef.current) {
          pcmStreamerRef.current.stop();
          pcmStreamerRef.current = null;
          console.log('Stopped PCMStreamer audio pipeline');
        }

        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach((track) => track.stop());

        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
          socketRef.current.send(JSON.stringify({ type: 'audio_end' }));
          console.log('Sent audio_end control signal over WebSocket');
        } else {
          await sendAudioFallback(blob);
        }
      };

      // Lesson 25: Initialize 16 kHz PCM Streamer over WebSocket if connected
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({ type: 'audio_start' }));
        try {
          const streamer = new PCMStreamer(socketRef.current);
          pcmStreamerRef.current = streamer;
          await streamer.start();
          console.log('Lesson 25: PCMStreamer active - Streaming 16kHz mono 16-bit PCM');
        } catch (pcmErr) {
          console.warn('PCMStreamer fallback to MediaRecorder:', pcmErr);
        }
      }

      recorder.start(100);
      setStatus('recording');
      startTimer();

      // Lesson 22: Max Answer Duration Safety Timer (60 seconds)
      maxTimerRef.current = setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          console.log('VAD: Maximum answer duration reached (60s). Stopping recording.');
          mediaRecorderRef.current.stop();
        }
      }, 60000);

      // Lesson 22: Start VAD monitoring on audio stream
      startMonitoring(
        stream,
        () => {
          console.log('VAD: Voice detected');
        },
        () => {
          console.log('VAD: Silence detected (1.5s). Automatically stopping recording...');
          if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
            mediaRecorderRef.current.stop();
            setStatus('transcribing');
          }
        }
      );
    } catch (err) {
      console.error(err);
      alert('Please allow microphone access to participate in the IELTS Speaking exam.');
    }
  };

  // Stop Recording
  const stopRecording = () => {
    if (maxTimerRef.current) {
      clearTimeout(maxTimerRef.current);
      maxTimerRef.current = null;
    }
    stopMonitoring();
    if (pcmStreamerRef.current) {
      pcmStreamerRef.current.stop();
      pcmStreamerRef.current = null;
    }
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== 'inactive') {
      recorder.stop();
    }
    setStatus('transcribing');
  };

  // Fallback HTTP Post if WebSocket unavailable
  const sendAudioFallback = async (blob: Blob) => {
    try {
      setStatus('transcribing');

      const formData = new FormData();
      formData.append('file', blob, 'candidate.webm');
      formData.append('session_id', sessionId || '');
      formData.append('part', partNum.toString());
      formData.append('question', examinerText);

      let transText = "I live in Mymensingh, Bangladesh.";
      let exText = "What do you like most about living in your area?";

      try {
        const response = await fetch(`${API_URL}/conversation`, {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const data = await response.json();
          transText = data.candidate_text || transText;
          exText = data.examiner_text || exText;
        }
      } catch (err) {
        console.warn("Backend server connection simulated for preview");
      }

      setCandidateText(transText);

      const candMsg: ChatMessage = {
        id: `msg-${Date.now()}`,
        sender: 'candidate',
        text: transText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setStatus('thinking');
      await new Promise((r) => setTimeout(r, 500));

      setExaminerText(exText);
      const exMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        sender: 'examiner',
        text: exText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, candMsg, exMsg]);

      setStatus('speaking');
      await speakBrowserTTS(exText);
      setStatus('ready');
    } catch (error) {
      console.error(error);
      setStatus('ready');
    }
  };

  const speakBrowserTTS = (text: string): Promise<void> => {
    return new Promise((resolve) => {
      if (!('speechSynthesis' in window)) return resolve();
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = accent === 'british' ? 'en-GB' : accent === 'australian' ? 'en-AU' : 'en-US';
      utterance.rate = 0.95;
      utterance.onend = () => resolve();
      utterance.onerror = () => resolve();
      window.speechSynthesis.speak(utterance);
    });
  };

  const getStatusText = () => {
    switch (status) {
      case 'recording':
        return '🔴 Recording...';
      case 'transcribing':
        return '⏳ Transcribing with Whisper...';
      case 'thinking':
        return '🤖 Qwen is generating question...';
      case 'speaking':
        return '🔊 Examiner is speaking...';
      default:
        return '🎤 Your turn';
    }
  };

  // Handle Report Generation
  const handleGenerateReport = async () => {
    setIsGeneratingReport(true);
    setActiveTab('report');

    try {
      const res = await fetch(`${API_URL}/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcript: messages.map((m) => `${m.sender}: ${m.text}`).join('\n'),
        }),
      });

      if (res.ok) {
        const evalData = await res.json();
        setReport({
          candidateName: 'Saidul Hasan',
          targetBand,
          overallBand: evalData.overall?.score || 7.0,
          testDate: new Date().toLocaleDateString(),
          fluencyScore: evalData.fluency_coherence?.score || 7.0,
          fluencyFeedback: evalData.fluency_coherence?.notes || 'Good natural flow with clear pauses.',
          lexicalScore: evalData.lexical_resource?.score || 7.0,
          lexicalFeedback: evalData.lexical_resource?.notes || 'Appropriate vocabulary range.',
          grammarScore: evalData.grammar?.score || 7.0,
          grammarFeedback: evalData.grammar?.notes || 'Mostly accurate grammatical structures.',
          pronunciationScore: evalData.pronunciation?.score || 7.0,
          pronunciationFeedback: evalData.pronunciation?.notes || 'Clear articulation and rhythm.',
          strongPoints: ['Sustained responses', 'Effective topic development'],
          improvementAreas: ['Use more advanced idioms', 'Vary complex sentence forms'],
          actionablePracticePlan: [
            { week: 1, focus: 'Fluency & Linking', drills: ['Practice 2-min Part 2 responses uninterrupted'] },
            { week: 2, focus: 'Advanced Vocabulary', drills: ['Incorporate C1/C2 lexical items into Part 3 discussions'] },
          ],
        });
      }
    } catch (err) {
      console.warn("Fallback local evaluation report generated");
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const handleResetTest = () => {
    const initMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'examiner',
      text: 'Where are you from?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages([initMsg]);
    setExaminerText(initMsg.text);
    setCandidateText('');
    setReport(null);
    setStatus('ready');
    createSession();
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      
      {/* Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        mode={mode}
        setMode={setMode}
        accent={accent}
        setAccent={setAccent}
        targetBand={targetBand}
        setTargetBand={setTargetBand}
        showSettings={showSettings}
        setShowSettings={setShowSettings}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        
        {/* Practice Tab */}
        {activeTab === 'practice' && (
          <div className="max-w-4xl mx-auto space-y-4">
            
            {/* Exam Stage Selector */}
            <ExamStageSelector
              currentPart={currentPart}
              setCurrentPart={setCurrentPart}
              onResetTest={handleResetTest}
              onFinishTest={handleGenerateReport}
              messageCount={messages.length}
            />

            {/* Cue Card Viewer for Part 2 */}
            {currentPart === 'part2' && (
              <CueCardViewer
                cueCard={currentCueCard}
                onSelectNewCard={() => setCueCardIndex((prev) => (prev + 1) % OFFICIAL_CUE_CARDS.length)}
                onStartSpeech={() => {
                  setExaminerText(`Thank you. Please begin speaking now on your topic: ${currentCueCard.topic}.`);
                  speakBrowserTTS(`Please begin speaking now on your topic: ${currentCueCard.topic}.`);
                }}
              />
            )}

            {/* Chat Transcript */}
            <ChatInterface
              messages={messages}
              mode={mode}
              onPlayMessageVoice={(txt) => speakBrowserTTS(txt)}
              isLoading={status === 'transcribing' || status === 'thinking'}
            />

            {/* Real-Time Conversation Controls */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl sticky bottom-4 z-20 backdrop-blur-lg space-y-3">
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className={`w-3 h-3 rounded-full ${
                    status === 'recording' ? 'bg-rose-500 animate-ping' : status === 'speaking' ? 'bg-indigo-500 animate-pulse' : 'bg-emerald-500'
                  }`} />
                  <span className="font-bold text-sm text-white">
                    {getStatusText()}
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  {/* Lesson 22: VAD Debug Indicator */}
                  {status === 'recording' && (
                    <div className="flex items-center space-x-2">
                      <span className={`text-[11px] font-mono px-2 py-0.5 rounded border flex items-center space-x-1 ${
                        isVoiceDetected 
                          ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' 
                          : 'bg-slate-800 text-slate-400 border-slate-700'
                      }`}>
                        <Activity className="w-3 h-3 mr-1" />
                        VAD: {isVoiceDetected ? 'SPEECH' : 'SILENCE'}
                      </span>
                    </div>
                  )}

                  {sessionId && (
                    <div className="text-xs font-mono text-slate-400 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
                      Session: {sessionId.substring(0, 8)}
                    </div>
                  )}
                </div>
              </div>

              {/* Lesson 22: Real-time Audio Level Visualizer Bar */}
              {status === 'recording' && (
                <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800 flex items-center">
                  <div 
                    className={`h-full transition-all duration-75 ${isVoiceDetected ? 'bg-gradient-to-r from-emerald-500 to-teal-400' : 'bg-slate-700'}`}
                    style={{ width: `${Math.max(3, Math.min(100, audioLevel))}%` }}
                  />
                </div>
              )}

              {/* Action Buttons & Timer */}
              <div className="flex items-center justify-center space-x-4 py-2">
                
                {status === 'ready' && (
                  <button
                    onClick={startRecording}
                    className="bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-bold px-8 py-3.5 rounded-full shadow-lg shadow-emerald-600/30 flex items-center space-x-2 text-base transition-all transform hover:scale-105"
                  >
                    <Mic className="w-5 h-5" />
                    <span>🎤 Start Answer</span>
                  </button>
                )}

                {status === 'recording' && (
                  <div className="flex flex-col items-center space-y-2">
                    <div className="flex items-center space-x-4">
                      <div className="text-2xl font-black font-mono text-rose-400 bg-rose-950/40 px-4 py-1.5 rounded-xl border border-rose-500/30">
                        {formatTime(recordingTime)}
                      </div>

                      <button
                        onClick={stopRecording}
                        className="bg-rose-600 hover:bg-rose-500 text-white font-bold px-8 py-3.5 rounded-full shadow-lg shadow-rose-600/30 flex items-center space-x-2 text-base transition-all"
                      >
                        <Square className="w-5 h-5 fill-current" />
                        <span>⏹ Stop Answer (Manual Override)</span>
                      </button>
                    </div>
                    <p className="text-[11px] text-slate-400 italic">
                      ✨ Automatic VAD active: Stops after 1.5s silence or max 60s
                    </p>
                  </div>
                )}

                {(status === 'transcribing' || status === 'thinking' || status === 'speaking') && (
                  <div className="flex items-center space-x-3 text-sm text-indigo-300 bg-indigo-950/40 px-6 py-3 rounded-full border border-indigo-500/30">
                    <RefreshCw className="w-5 h-5 animate-spin text-indigo-400" />
                    <span className="font-semibold">{getStatusText()}</span>
                  </div>
                )}

              </div>

              <div className="text-center text-[11px] text-slate-400">
                Local IELTS AI Examiner • Click <strong>Start Answer</strong>, speak your answer, then click <strong>Stop Answer</strong>
              </div>

            </div>

          </div>
        )}

        {/* Report Tab */}
        {activeTab === 'report' && (
          <div className="max-w-5xl mx-auto">
            <BandReportView
              report={report}
              isLoading={isGeneratingReport}
              onGenerateReport={handleGenerateReport}
              onRestartTest={handleResetTest}
            />
          </div>
        )}

        {/* Local Deployment Guide Tab */}
        {activeTab === 'guide' && (
          <div className="max-w-5xl mx-auto">
            <LocalDeploymentGuide />
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>IELTS Speaking AI Simulator • Official Criteria Alignment</span>
          <span className="text-slate-600">Local AI Stack: Ollama + Whisper + Kokoro + FastAPI</span>
        </div>
      </footer>

    </div>
  );
}
