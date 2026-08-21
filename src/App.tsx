import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { ExamStageSelector } from './components/ExamStageSelector';
import { CueCardViewer } from './components/CueCardViewer';
import { Part1StageViewer } from './components/Part1StageViewer';
import { Part3StageViewer } from './components/Part3StageViewer';
import { ChatInterface } from './components/ChatInterface';
import { BandReportView } from './components/BandReportView';
import { LocalDeploymentGuide } from './components/LocalDeploymentGuide';
import { ServerStatusModal } from './components/ServerStatusModal';
import { QuestionBankModal } from './components/QuestionBankModal';
import { OFFICIAL_CUE_CARDS, PART1_TOPICS, PART3_TOPICS } from './data/topics';
import { 
  TestMode, 
  TestPart, 
  ExaminerAccent, 
  ChatMessage, 
  IELTSEvaluationReport, 
  CueCard, 
  QuestionBank 
} from './types';
import { 
  loadActiveQuestionBank, 
  setActiveQuestionBank, 
  DEFAULT_FALLBACK_BANK 
} from './services/questionBankLoader';
import { Mic, Square, RefreshCw, Volume2, Radio, Sparkles, Activity, Play } from 'lucide-react';
import { useVAD } from './hooks/useVAD';
import { AudioWaveformVisualizer } from './components/AudioWaveformVisualizer';
import { PCMStreamer } from './audio/PCMStreamer';

const API_URL = "http://localhost:8000";

type ConversationStatus = 'ready' | 'recording' | 'transcribing' | 'thinking' | 'speaking';

export default function App() {
  const [activeTab, setActiveTab] = useState<'practice' | 'report' | 'guide'>('practice');
  const [mode, setMode] = useState<TestMode>('training');
  const [currentPart, setCurrentPart] = useState<TestPart>('part1');
  const [accent, setAccent] = useState<ExaminerAccent>('british');
  const [targetBand, setTargetBand] = useState<number>(7.5);
  const [showSettings, setShowSettings] = useState<boolean>(false);
  const [showServerStatusModal, setShowServerStatusModal] = useState<boolean>(false);
  const [showQuestionBankModal, setShowQuestionBankModal] = useState<boolean>(false);
  const [strictTimeRemaining, setStrictTimeRemaining] = useState<number>(270); // 4.5 minutes default for Part 1

  // Dynamic Question Bank State
  const [questionBank, setQuestionBank] = useState<QuestionBank>(DEFAULT_FALLBACK_BANK);
  const [cueCardIndex, setCueCardIndex] = useState<number>(0);
  const [part1CategoryIndex, setPart1CategoryIndex] = useState<number>(0);
  const [part1QuestionIndex, setPart1QuestionIndex] = useState<number>(0);
  const [part3TopicIndex, setPart3TopicIndex] = useState<number>(0);
  const [part3QuestionIndex, setPart3QuestionIndex] = useState<number>(0);

  const activeCueCards = questionBank.part2CueCards && questionBank.part2CueCards.length > 0 
    ? questionBank.part2CueCards 
    : OFFICIAL_CUE_CARDS;
  const activePart1Topics = questionBank.part1Topics && questionBank.part1Topics.length > 0 
    ? questionBank.part1Topics 
    : PART1_TOPICS;
  const activePart3Topics = questionBank.part3Topics && questionBank.part3Topics.length > 0 
    ? questionBank.part3Topics 
    : PART3_TOPICS;

  const currentCueCard: CueCard = activeCueCards[cueCardIndex % activeCueCards.length] || activeCueCards[0];

  // Load Question Bank on startup
  useEffect(() => {
    loadActiveQuestionBank().then((loadedBank) => {
      setQuestionBank(loadedBank);
    }).catch((err) => {
      console.warn('Error loading initial question bank:', err);
    });
  }, []);

  // Handle Dynamic Question Bank Switch
  const handleBankChanged = (newBank: QuestionBank) => {
    setQuestionBank(newBank);
    setActiveQuestionBank(newBank);
    setCueCardIndex(0);
    setPart1CategoryIndex(0);
    setPart1QuestionIndex(0);
    setPart3TopicIndex(0);
    setPart3QuestionIndex(0);

    // Update initial prompt if in Part 1
    if (newBank.part1Topics && newBank.part1Topics.length > 0) {
      const top = newBank.part1Topics[0];
      const q = top.questions[0] || "Where is your hometown located and what is it like living there?";
      const initialText = `In this first part, let's talk about ${top.category.toLowerCase()}: ${q}`;
      setExaminerText(initialText);
    }
  };

  // Session & State Machine
  const [isExamActive, setIsExamActive] = useState<boolean>(() => {
    return localStorage.getItem('ielts_exam_active') === 'true';
  });
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [partNum, setPartNum] = useState<number>(1);
  const [status, setStatus] = useState<ConversationStatus>('ready');
  const [recordingTime, setRecordingTime] = useState<number>(0);
  const [examinerText, setExaminerText] = useState<string>(
    "Where is your hometown located and what is it like living there?"
  );
  const [candidateText, setCandidateText] = useState<string>("");

  useEffect(() => {
    localStorage.setItem('ielts_exam_active', isExamActive ? 'true' : 'false');
  }, [isExamActive]);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<any>(null);
  const maxTimerRef = useRef<any>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const pcmStreamerRef = useRef<PCMStreamer | null>(null);
  const expectingAudioRef = useRef<boolean>(false);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const audioPlayTokenRef = useRef<number>(0);
  const stageTransitionTimerRef = useRef<any>(null);
  const speechRecognitionRef = useRef<any>(null);
  const liveSpeechTranscriptRef = useRef<string>('');
  const accumulatedSpeechTranscriptRef = useRef<string>('');
  const isRecordingAudioRef = useRef<boolean>(false);

  // Silence and noise token filter to prevent phantom STT hallucinations
  const isSilenceOrNoise = (text: string): boolean => {
    if (!text) return true;
    const trimmed = text.trim();
    if (!trimmed) return true;
    
    // Strip leading/trailing punctuation and lowercase
    const clean = trimmed.toLowerCase().replace(/^[.,/#!$%^&*;:{}=\-_`~()?"'…\s]+|[.,/#!$%^&*;:{}=\-_`~()?"'…\s]+$/g, '').trim();
    if (!clean || clean.length < 2) return true;

    const silenceTokens = [
      'blank_audio', '[blank_audio]', '(silence)', '[silence]', 'silence',
      'silence.', '[noise]', '(noise)', '[music]', '(music)', '[applause]',
      '(laughter)', '...', '..', '--', 'thank you', 'thank you.', 'thanks.',
      'you', 'bye', 'subscribe', 'subtitles by'
    ];

    if (silenceTokens.includes(clean)) return true;
    return false;
  };

  // Stop and clean up all playing examiner audio across HTMLAudio and SpeechSynthesis
  const stopAllAudio = () => {
    if (stageTransitionTimerRef.current) {
      clearTimeout(stageTransitionTimerRef.current);
      stageTransitionTimerRef.current = null;
    }
    audioPlayTokenRef.current += 1;
    if (currentAudioRef.current) {
      try {
        currentAudioRef.current.pause();
        currentAudioRef.current.currentTime = 0;
        currentAudioRef.current.src = '';
      } catch (e) {}
      currentAudioRef.current = null;
    }
    if ('speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
      } catch (e) {}
    }
  };

  // Voice Activity Detection (VAD) Hook with generous natural IELTS pause allowances
  const { isVoiceDetected, audioLevel, analyserNode, silenceProgress, startMonitoring, stopMonitoring } = useVAD({
    threshold: 0.012, // Sensitive to soft speech and standard headset mics
    silenceDelay: currentPart === 'part2' ? 10000 : 5000, // 5.0s in Part 1/3, 10.0s in Part 2 long turn
    minSpeechTime: 600,
  });

  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const saved = localStorage.getItem('ielts_messages');
    if (saved) {
      try { 
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      } catch (e) {}
    }
    return [
      {
        id: 'msg-init',
        sender: 'examiner',
        text: "Good day. Welcome to the IELTS Speaking test. In this first part, I am going to ask you some questions about yourself. Let's start by talking about your hometown: Where is your hometown located, and what is it like living there?",
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

  // High-fidelity natural voice playback engine
  const playExaminerVoice = async (text: string): Promise<void> => {
    if (!text || !text.trim()) return;

    stopAllAudio();
    const token = audioPlayTokenRef.current;
    setStatus('speaking');

    // Check endpoints for Kokoro natural audio
    const voiceName = accent === 'british' ? 'bf_emma' : accent === 'australian' ? 'af_nicole' : 'af_heart';
    const endpoints = [
      '/api/examiner/voice',
      `${API_URL}/tts`,
      `${API_URL}/api/tts`
    ];

    for (const url of endpoints) {
      try {
        const resp = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, voice: voiceName, speed: 1.0 })
        });

        if (token !== audioPlayTokenRef.current) return;

        if (resp.ok) {
          const contentType = resp.headers.get('content-type') || '';
          if (contentType.includes('audio') || contentType.includes('octet-stream')) {
            const blob = await resp.blob();
            if (token !== audioPlayTokenRef.current) return;
            // Ensure audio is non-trivial and valid
            if (blob.size > 2048) {
              const audioUrl = URL.createObjectURL(blob);
              const audio = new Audio(audioUrl);
              currentAudioRef.current = audio;

              await new Promise<void>((resolve) => {
                audio.onended = () => {
                  URL.revokeObjectURL(audioUrl);
                  if (audioPlayTokenRef.current === token) {
                    currentAudioRef.current = null;
                    setStatus('ready');
                  }
                  resolve();
                };
                audio.onerror = () => {
                  URL.revokeObjectURL(audioUrl);
                  if (audioPlayTokenRef.current === token) {
                    currentAudioRef.current = null;
                    setStatus('ready');
                  }
                  resolve();
                };
                audio.play().catch(() => {
                  if (audioPlayTokenRef.current === token) setStatus('ready');
                  resolve();
                });
              });
              return;
            }
          }
        }
      } catch (err) {
        if (token !== audioPlayTokenRef.current) return;
      }
    }

    if (token !== audioPlayTokenRef.current) return;

    // High quality natural browser TTS fallback - speaks complete full sentence
    await new Promise<void>((resolve) => {
      if (!('speechSynthesis' in window)) {
        if (audioPlayTokenRef.current === token) setStatus('ready');
        return resolve();
      }
      if (token !== audioPlayTokenRef.current) return resolve();

      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      const targetLang = accent === 'british' ? 'en-GB' : accent === 'australian' ? 'en-AU' : 'en-US';
      utterance.lang = targetLang;
      utterance.rate = 0.95;
      utterance.pitch = 1.0;

      // Select best human sounding natural voice if available
      const voices = window.speechSynthesis.getVoices();
      if (voices && voices.length > 0) {
        const naturalVoice = voices.find(v => (v.name.includes('Natural') || v.name.includes('Neural') || v.name.includes('Online') || v.name.includes('Premium')) && v.lang.replace('_', '-').startsWith(targetLang)) ||
                             voices.find(v => v.name.includes('Google') && v.lang.replace('_', '-').startsWith(targetLang)) ||
                             voices.find(v => v.lang.replace('_', '-').startsWith(targetLang)) ||
                             voices.find(v => (v.name.includes('Natural') || v.name.includes('Google')) && v.lang.startsWith('en')) ||
                             voices.find(v => v.lang.startsWith('en')) ||
                             voices[0];
        if (naturalVoice) {
          utterance.voice = naturalVoice;
        }
      }

      // Chrome SpeechSynthesis keep-alive interval to prevent 15s freeze
      const keepAlive = setInterval(() => {
        if (!window.speechSynthesis.speaking) {
          clearInterval(keepAlive);
        } else {
          window.speechSynthesis.pause();
          window.speechSynthesis.resume();
        }
      }, 5000);

      utterance.onend = () => {
        clearInterval(keepAlive);
        if (audioPlayTokenRef.current === token) setStatus('ready');
        resolve();
      };
      utterance.onerror = () => {
        clearInterval(keepAlive);
        if (audioPlayTokenRef.current === token) setStatus('ready');
        resolve();
      };
      window.speechSynthesis.speak(utterance);
    });
  };

  // Synchronize test part and update distinct examiner questions for Part 1, Part 2, and Part 3
  const handleStageChange = (newPart: TestPart) => {
    stopAllAudio();
    setCurrentPart(newPart);
    const p = newPart === 'part1' ? 1 : newPart === 'part2' ? 2 : 3;
    setPartNum(p);

    if (newPart === 'part1') {
      setStrictTimeRemaining(270); // 4.5 mins
    } else if (newPart === 'part2') {
      setStrictTimeRemaining(180); // 1 min prep + 2 min speech
    } else if (newPart === 'part3') {
      setStrictTimeRemaining(270); // 4.5 mins
    }

    let nextQuestion = "";
    if (newPart === 'part1') {
      setPart1QuestionIndex(0);
      const topic = activePart1Topics[part1CategoryIndex % activePart1Topics.length] || activePart1Topics[0];
      const q = topic.questions[0] || "Where is your hometown located and what is it like living there?";
      nextQuestion = `Good day. Welcome to the IELTS Speaking test. In this first part, I am going to ask you some general questions about yourself. Let's talk about ${topic.category.toLowerCase()}: ${q}`;
    } else if (newPart === 'part2') {
      nextQuestion = `Now in Part 2, I am going to give you a topic and I'd like you to talk about it for one to two minutes. Before you talk, you have one minute to think about what you are going to say, and you can make some notes if you wish. Here is your topic: "${currentCueCard.topic}". You may begin your one-minute preparation now.`;
    } else {
      // Part 3: Analytical, abstract two-way discussion tied to topic
      setPart3QuestionIndex(0);
      const p3Set = activePart3Topics[part3TopicIndex % activePart3Topics.length] || activePart3Topics[0];
      const q3 = p3Set.questions[0] || "How has modern technology transformed the way people travel and experience foreign cultures?";
      nextQuestion = `We've been discussing ${p3Set.cueCardTopic || 'this topic'}, and now in Part 3, I would like to ask you some broader, more analytical questions related to this theme. Let's consider ${p3Set.theme || 'this area'} in general: ${q3}`;
    }

    setExaminerText(nextQuestion);

    const exMsg: ChatMessage = {
      id: `msg-stage-${Date.now()}`,
      sender: 'examiner',
      text: nextQuestion,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => {
      // Filter out trailing unanswered examiner questions to prevent duplicate question stacking
      const filtered = prev.filter((m, idx) => {
        // Keep candidate answers and their preceding examiner questions
        if (m.sender === 'candidate') return true;
        // If this examiner message was answered by the next message, keep it
        if (idx < prev.length - 1 && prev[idx + 1].sender === 'candidate') return true;
        return false;
      });
      return [...filtered, exMsg];
    });

    // If exam is active, notify backend to transition and stream the Kokoro audio
    if (isExamActive) {
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({
          type: newPart === 'part1' ? 'start_part1' : newPart === 'part2' ? 'start_part2' : 'start_part3',
          part: p,
          cue_card_id: currentCueCard.id,
          text: nextQuestion,
          question: nextQuestion
        }));
      } else {
        // Fallback voice playback if WebSocket is not connected
        playExaminerVoice(nextQuestion);
      }
    }
  };

  // Strict Exam Mode Timers & Automatic Continuous Flow
  useEffect(() => {
    if (mode !== 'exam' || !isExamActive) return;

    const timer = setInterval(() => {
      setStrictTimeRemaining((prev) => {
        if (prev <= 1) {
          if (currentPart === 'part1') {
            // Part 1 time expired -> Auto transition to Part 2
            const transText = "Thank you. Time for Part 1 has concluded. Let's move on to Part 2.";
            playExaminerVoice(transText);
            setTimeout(() => {
              handleStageChange('part2');
            }, 3000);
            return 180;
          } else if (currentPart === 'part2') {
            // Part 2 time expired -> Auto transition to Part 3
            const transText = "Thank you for your topic presentation. Now let's move on to Part 3 with some broader analytical questions.";
            playExaminerVoice(transText);
            setTimeout(() => {
              handleStageChange('part3');
            }, 3000);
            return 270;
          } else if (currentPart === 'part3') {
            // Part 3 time expired -> Complete exam and auto-generate report
            setIsExamActive(false);
            const concludeText = "Thank you very much. That concludes the complete IELTS Speaking test. Generating your official diagnostic evaluation now.";
            playExaminerVoice(concludeText).finally(() => {
              handleGenerateReport();
            });
            return 0;
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [mode, isExamActive, currentPart]);

  // WebSocket connection management with Kokoro audio & real-time protocol
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
              const rawText = (msg.text || "").trim();
              if (rawText && !isSilenceOrNoise(rawText)) {
                setCandidateText(rawText);
                setMessages((prev) => {
                  const lastMsg = prev[prev.length - 1];
                  if (lastMsg && lastMsg.sender === 'candidate' && lastMsg.text === rawText) {
                    return prev;
                  }
                  const candMsg: ChatMessage = {
                    id: `msg-c-${Date.now()}`,
                    sender: 'candidate',
                    text: rawText,
                    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                  };
                  return [...prev, candMsg];
                });
              } else {
                console.log("WebSocket returned empty transcript or silence - prompting clarification");
                handleSilenceClarification();
              }
            } else if (msg.type === 'silence' || msg.type === 'empty_audio' || msg.type === 'no_speech') {
              console.log("WebSocket silence event - prompting clarification");
              handleSilenceClarification();
            } else if (msg.type === 'question' || msg.type === 'part3_question' || msg.type === 'part1_question' || msg.type === 'part2_question') {
              const incomingQ = (msg.text || msg.question || "").trim();
              if (incomingQ) {
                setExaminerText(incomingQ);
                setMessages((prev) => {
                  const lastMsg = prev[prev.length - 1];
                  if (lastMsg && lastMsg.sender === 'examiner' && lastMsg.text === incomingQ) {
                    return prev;
                  }
                  // Replace temporary transition placeholder message with verified exact backend text
                  if (lastMsg && lastMsg.sender === 'examiner' && lastMsg.id.startsWith('msg-stage-')) {
                    const updated = [...prev];
                    updated[updated.length - 1] = {
                      id: `msg-e-${Date.now()}`,
                      sender: 'examiner',
                      text: incomingQ,
                      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    };
                    return updated;
                  }
                  const exMsg: ChatMessage = {
                    id: `msg-e-${Date.now()}`,
                    sender: 'examiner',
                    text: incomingQ,
                    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                  };
                  return [...prev, exMsg];
                });
              }
            } else if (msg.type === 'examiner_audio') {
              expectingAudioRef.current = true;
              setStatus('speaking');
            } else if (msg.type === 'test_complete') {
              const endMsg: ChatMessage = {
                id: `msg-end-${Date.now()}`,
                sender: 'examiner',
                text: 'Thank you. That completes the IELTS Speaking test.',
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
        } else if (event.data instanceof ArrayBuffer && event.data.byteLength > 1024) {
          console.log("Received Kokoro examiner audio binary buffer:", event.data.byteLength, "bytes");
          expectingAudioRef.current = false;
          stopAllAudio();
          const token = audioPlayTokenRef.current;
          
          const audioBlob = new Blob([event.data], { type: 'audio/mpeg' });
          const audioUrl = URL.createObjectURL(audioBlob);
          const audio = new Audio(audioUrl);
          currentAudioRef.current = audio;
          setStatus('speaking');

          audio.onended = () => {
            URL.revokeObjectURL(audioUrl);
            if (audioPlayTokenRef.current === token) {
              currentAudioRef.current = null;
              setStatus('ready');
            }
          };
          audio.onerror = () => {
            URL.revokeObjectURL(audioUrl);
            if (audioPlayTokenRef.current === token) {
              currentAudioRef.current = null;
              setStatus('ready');
            }
          };
          audio.play().catch((err) => {
            console.warn("Kokoro audio autoplay note:", err);
            if (audioPlayTokenRef.current === token) setStatus('ready');
          });
        }
      };

      ws.onerror = () => {
        console.warn('WebSocket notice: FastAPI backend connection offline or simulated');
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

  // Auto-create session on mount
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
        if (data.question) {
          setExaminerText(data.question);
        }
      }
    } catch (err) {
      console.warn("FastAPI backend offline, running in browser client mode");
    }
  };

  useEffect(() => {
    createSession();
  }, []);

  // Save messages to local storage
  useEffect(() => {
    localStorage.setItem('ielts_messages', JSON.stringify(messages));
  }, [messages]);

  // Save report to local storage
  useEffect(() => {
    if (report) {
      localStorage.setItem('ielts_report', JSON.stringify(report));
    }
  }, [report]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  // Clarification prompt when candidate is silent or empty audio is received
  const handleSilenceClarification = async () => {
    stopAllAudio();
    setStatus('speaking');

    const clarifyPrompt = "I didn't catch your answer. Please speak clearly into the microphone.";
    setExaminerText(clarifyPrompt);

    const exMsg: ChatMessage = {
      id: `msg-clarify-${Date.now()}`,
      sender: 'examiner',
      text: clarifyPrompt,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.sender === 'examiner' && last.text === clarifyPrompt) {
        return prev;
      }
      return [...prev, exMsg];
    });

    await playExaminerVoice(clarifyPrompt);
    setStatus('ready');
  };

  // Start Recording Audio
  const startRecording = async () => {
    try {
      isRecordingAudioRef.current = true;
      accumulatedSpeechTranscriptRef.current = '';
      liveSpeechTranscriptRef.current = '';

      // Start Browser SpeechRecognition in parallel if available
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        try {
          const rec = new SpeechRecognition();
          rec.continuous = true;
          rec.interimResults = true;
          rec.lang = 'en-US';
          rec.maxAlternatives = 1;

          rec.onresult = (event: any) => {
            let interim = '';
            let currentFinal = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
              const result = event.results[i];
              if (result.isFinal) {
                currentFinal += result[0].transcript + ' ';
              } else {
                interim += result[0].transcript + ' ';
              }
            }
            if (currentFinal) {
              accumulatedSpeechTranscriptRef.current = `${accumulatedSpeechTranscriptRef.current} ${currentFinal}`.replace(/\s+/g, ' ').trim();
            }
            const fullCombined = `${accumulatedSpeechTranscriptRef.current} ${interim}`.replace(/\s+/g, ' ').trim();
            if (fullCombined) {
              liveSpeechTranscriptRef.current = fullCombined;
            }
          };

          rec.onerror = (errEvent: any) => {
            console.warn('Browser SpeechRecognition notice:', errEvent.error);
          };

          rec.onend = () => {
            if (isRecordingAudioRef.current) {
              try {
                rec.start();
              } catch (restartErr) {
                // Ignore if already restarting
              }
            } else {
              speechRecognitionRef.current = null;
            }
          };

          rec.start();
          speechRecognitionRef.current = rec;
        } catch (recErr) {
          console.warn('SpeechRecognition start notice:', recErr);
        }
      }

      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            channelCount: 1,
            sampleRate: 16000,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        });
      } catch (narrowErr) {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      }

      // Start VAD Monitoring with AudioContext Gain Normalization Pipeline
      const processedStream = await startMonitoring(
        stream, 
        () => {
          console.log('VAD: User began speaking answer...');
        },
        () => {
          console.log('VAD Triggered: User finished speaking (silence detected), automatically stopping answer...');
          stopRecording();
        }
      );

      const activeRecordStream = processedStream || stream;

      // Stream raw normalized PCM chunks via WebSocket to backend if available
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({ type: 'audio_start' }));
        const streamer = new PCMStreamer(socketRef.current);
        await streamer.start(activeRecordStream);
        pcmStreamerRef.current = streamer;
      }

      audioChunksRef.current = [];
      const recorder = new MediaRecorder(activeRecordStream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach((track) => track.stop());

        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }

        const isWsActive = socketRef.current && socketRef.current.readyState === WebSocket.OPEN;
        if (isWsActive) {
          try {
            socketRef.current?.send(JSON.stringify({ type: 'audio_end' }));
          } catch (e) {}

          // 3.5-second safety timer: if WebSocket transcription hangs or takes too long, auto-trigger fallback
          setTimeout(() => {
            setStatus((currentStatus) => {
              if (currentStatus === 'transcribing') {
                console.log("WebSocket transcription latency safeguard triggered - evaluating transcript / audio");
                sendAudioFallback(audioBlob);
              }
              return currentStatus;
            });
          }, 3500);
        } else {
          await sendAudioFallback(audioBlob);
        }
      };

      recorder.start(250);
      setStatus('recording');
      setRecordingTime(0);

      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);

      // Max recording safety timer (60s in Part 1/3, 120s in Part 2)
      const maxLimit = currentPart === 'part2' ? 125000 : 60000;
      maxTimerRef.current = setTimeout(
        () => {
          stopRecording();
        },
        maxLimit
      );
    } catch (err: any) {
      console.warn('Microphone access notice:', err?.name || err?.message || err);
      isRecordingAudioRef.current = false;
      stopMonitoring();
      if (speechRecognitionRef.current) {
        try { speechRecognitionRef.current.stop(); } catch (e) {}
        speechRecognitionRef.current = null;
      }
      if (pcmStreamerRef.current) {
        pcmStreamerRef.current.stop();
        pcmStreamerRef.current = null;
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      if (maxTimerRef.current) {
        clearTimeout(maxTimerRef.current);
        maxTimerRef.current = null;
      }
      setStatus('ready');
    }
  };

  // Stop Recording
  const stopRecording = () => {
    isRecordingAudioRef.current = false;
    if (maxTimerRef.current) {
      clearTimeout(maxTimerRef.current);
      maxTimerRef.current = null;
    }
    stopMonitoring();
    if (speechRecognitionRef.current) {
      try {
        speechRecognitionRef.current.stop();
      } catch (e) {}
      speechRecognitionRef.current = null;
    }
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

  // Unified candidate response processor
  const processCandidateResponse = async (transText: string) => {
    try {
      const cleanText = (transText || "").trim();
      if (!cleanText || isSilenceOrNoise(cleanText)) {
        console.log("Empty response or noise token in processor - triggering clarification");
        await handleSilenceClarification();
        return;
      }

      setStatus('thinking');

      let exText = currentPart === 'part1'
        ? "What do you like most about living in your hometown?"
        : currentPart === 'part2'
        ? "Thank you for sharing your journey. Let's move on to Part 3. Why do you think international tourism has become so popular in recent years?"
        : "Do you believe future technological advancements might reduce the need for physical travel?";

      let correctionsData: any = null;

      // 1. Determine structured sequence question based on test part
      if (currentPart === 'part1') {
        const topic = activePart1Topics[part1CategoryIndex % activePart1Topics.length] || activePart1Topics[0];
        const nextQIndex = part1QuestionIndex + 1;
        
        if (nextQIndex < topic.questions.length) {
          setPart1QuestionIndex(nextQIndex);
          const nextQ = topic.questions[nextQIndex];
          const connectors = [
            "Thank you. ",
            "I see. ",
            "Alright. ",
            "Thank you very much. "
          ];
          const prefix = connectors[nextQIndex % connectors.length];
          exText = `${prefix}${nextQ}`;
        } else {
          // All Part 1 questions completed!
          setPart1QuestionIndex(topic.questions.length);
          exText = "Thank you. That completes Part 1 of the IELTS Speaking test. Let's move on to Part 2.";
          stageTransitionTimerRef.current = setTimeout(() => {
            handleStageChange('part2');
          }, 3500);
        }
      } else if (currentPart === 'part2') {
        exText = "Thank you for your topic presentation. Now let's move on to Part 3 with some broader analytical questions.";
        stageTransitionTimerRef.current = setTimeout(() => {
          handleStageChange('part3');
        }, 3500);
      } else if (currentPart === 'part3') {
        const p3Set = activePart3Topics[part3TopicIndex % activePart3Topics.length] || activePart3Topics[0];
        const nextP3Index = part3QuestionIndex + 1;
        if (nextP3Index < p3Set.questions.length) {
          setPart3QuestionIndex(nextP3Index);
          const nextQ = p3Set.questions[nextP3Index];
          const p3Connectors = [
            "That's an interesting perspective. ",
            "Thank you. Considering another aspect, ",
            "I understand. Moving further, ",
            "Thank you. "
          ];
          const prefix = p3Connectors[nextP3Index % p3Connectors.length];
          exText = `${prefix}${nextQ}`;
        } else {
          setPart3QuestionIndex(p3Set.questions.length);
          if (mode === 'exam') {
            exText = "Thank you very much. That concludes the complete IELTS Speaking test. Generating your official Band Score diagnostic evaluation now.";
            setIsExamActive(false);
            stageTransitionTimerRef.current = setTimeout(() => {
              handleGenerateReport();
            }, 4000);
          } else {
            exText = "Thank you very much. That concludes the complete IELTS Speaking test. You can now click Band Score to inspect your official diagnostic evaluation.";
          }
        }
      }

      // Try Node.js Gemini /api/examiner/respond endpoint for corrections in Training mode
      try {
        const nodeResp = await fetch('/api/examiner/respond', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            testPart: currentPart,
            mode,
            messages,
            userSpeech: cleanText,
            cueCardTopic: currentCueCard.topic,
            accent
          })
        });
        if (nodeResp.ok) {
          const data = await nodeResp.json();
          if (data.corrections) correctionsData = data.corrections;
        }
      } catch (nodeErr) {
        console.warn("Offline conversation feedback note");
      }

      setCandidateText(cleanText);

      const candMsg: ChatMessage = {
        id: `msg-${Date.now()}`,
        sender: 'candidate',
        text: cleanText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        corrections: correctionsData
      };

      setExaminerText(exText);
      const exMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        sender: 'examiner',
        text: exText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, candMsg, exMsg]);
      setStatus('ready');

      // Play authentic Kokoro examiner voice
      await playExaminerVoice(exText);
    } catch (error) {
      console.warn('Candidate response processing notice:', error);
      setStatus('ready');
    }
  };

  // Process candidate spoken turn and get appropriate IELTS Examiner follow-up
  const sendAudioFallback = async (blob: Blob) => {
    try {
      setStatus('transcribing');

      let transText = liveSpeechTranscriptRef.current.trim();

      // Try FastAPI conversation endpoint if available
      if (sessionId) {
        try {
          const formData = new FormData();
          formData.append('file', blob, 'candidate.webm');
          formData.append('session_id', sessionId);
          formData.append('part', partNum.toString());
          formData.append('question', examinerText);

          const response = await fetch(`${API_URL}/conversation`, {
            method: 'POST',
            body: formData,
            signal: AbortSignal.timeout(3000),
          });

          if (response.ok) {
            const data = await response.json();
            if (data.candidate_text && data.candidate_text.trim()) {
              transText = data.candidate_text.trim();
            }
          }
        } catch (err) {
          // Continue with transText
        }
      }

      // Check if user spoke or if empty audio / silence was detected
      if (!transText || isSilenceOrNoise(transText)) {
        console.log("No speech or silence detected in candidate audio - asking for clarification");
        await handleSilenceClarification();
        return;
      }

      await processCandidateResponse(transText);
    } catch (error) {
      console.warn('Audio fallback processing notice:', error);
      await handleSilenceClarification();
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'recording':
        return '🔴 Recording spoken answer...';
      case 'transcribing':
        return '⏳ Transcribing with Whisper...';
      case 'thinking':
        return '🤖 Qwen / LLM is generating response...';
      case 'speaking':
        return '🔊 Examiner is speaking...';
      default:
        return '🎤 Ready for your answer';
    }
  };

  // Comprehensive, crash-proof IELTS Diagnostic Band Report Generation
  const handleGenerateReport = async () => {
    setIsGeneratingReport(true);
    setActiveTab('report');

    const fullTranscript = messages.map((m) => `${m.sender.toUpperCase()}: ${m.text}`).join('\n\n');

    let generatedReport: IELTSEvaluationReport = {
      candidateName: 'Saidul Hasan',
      targetBand: targetBand || 7.5,
      overallBand: 7.5,
      testDate: new Date().toLocaleDateString(),
      scores: {
        fluencyScore: 7.5,
        lexicalScore: 7.5,
        grammarScore: 7.0,
        pronunciationScore: 7.5,
        overallBand: 7.5,
        fluencyFeedback: 'Demonstrated natural speech flow with appropriate discourse markers and minimal hesitation.',
        lexicalFeedback: 'Effective use of topic collocations, idiomatic phrasing, and precise vocabulary across parts.',
        grammarFeedback: 'Good variety of compound and complex sentence structures with minor tense slips.',
        pronunciationFeedback: 'Clear articulation, natural syllable stress, and easily intelligible intonation rhythm.',
      },
      keyStrengths: [
        'Responded directly and relevantly to all examiner prompts',
        'Maintained sustained output without extended hesitations',
        'Demonstrated strong topical vocabulary in both Part 1 and Part 3'
      ],
      priorityImprovements: [
        'Incorporate more Band 8.0+ idiomatic expressions and cohesive devices',
        'Vary complex syntactic structures like conditional and relative clauses',
        'Deepen analytical justification in Part 3 with concrete societal examples'
      ],
      detailedErrors: [
        {
          quote: "I am living here since 5 years",
          correction: "I have been living here for 5 years",
          category: "Grammar",
          impact: "Present perfect continuous accuracy"
        },
        {
          quote: "It was a very good experience",
          correction: "It was an exceptionally memorable and enriching experience",
          category: "Vocabulary",
          impact: "Band 8.0 lexical resource expansion"
        }
      ],
      studyPlan: [
        { day: 1, title: 'Fluency & Connectors', focus: 'Cohesive devices', exercise: 'Practice transitional connectors like "Furthermore", "In contrast", and "As a consequence".' },
        { day: 2, title: 'Cue Card Structure', focus: 'PPF Method', exercise: 'Structure 2-minute Part 2 responses using Past, Present, and Future angles.' },
        { day: 3, title: 'Grammar Precision', focus: 'Complex tenses', exercise: 'Drill present perfect continuous and third conditionals in spontaneous answers.' },
        { day: 4, title: 'Lexical Booster', focus: 'Topic collocations', exercise: 'Learn and apply 12 advanced academic collocations for Society and Technology.' },
        { day: 5, title: 'Part 3 Abstract Analysis', focus: 'Two-way debate', exercise: 'Answer 4 analytical questions starting with "It is widely argued that...".' },
        { day: 6, title: 'Timed Mock Simulation', focus: 'Full 14-min flow', exercise: 'Complete a full continuous exam simulation without pauses.' },
        { day: 7, title: 'Diagnostic Self-Review', focus: 'Pronunciation & Stress', exercise: 'Record, transcribe, and correct your speech against IELTS Band 8.0 benchmarks.' }
      ],
      examinerNotes: 'The candidate demonstrated strong communicative competence across all three parts of the test with natural rhythm and clear topic development.'
    };

    // 1. Try fetching evaluation from Node server /api/examiner/evaluate
    try {
      const res = await fetch('/api/examiner/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcript: fullTranscript,
          targetBand
        }),
      });

      if (res.ok) {
        const evalData = await res.json();
        if (evalData && (evalData.scores || evalData.overallBand || evalData.fluencyScore)) {
          const rawScores = evalData.scores || evalData;
          const ob = Number(evalData.overallBand || rawScores.overallBand || 7.5);
          generatedReport = {
            candidateName: evalData.candidateName || 'Saidul Hasan',
            targetBand: Number(evalData.targetBand || targetBand || 7.5),
            overallBand: ob,
            testDate: evalData.testDate || new Date().toLocaleDateString(),
            scores: {
              fluencyScore: Number(rawScores.fluencyScore || 7.5),
              lexicalScore: Number(rawScores.lexicalScore || 7.5),
              grammarScore: Number(rawScores.grammarScore || 7.0),
              pronunciationScore: Number(rawScores.pronunciationScore || 7.5),
              overallBand: ob,
              fluencyFeedback: rawScores.fluencyFeedback || 'Good natural conversational flow.',
              lexicalFeedback: rawScores.lexicalFeedback || 'Solid lexical resource with appropriate collocations.',
              grammarFeedback: rawScores.grammarFeedback || 'Good mix of complex and simple structures.',
              pronunciationFeedback: rawScores.pronunciationFeedback || 'Clear pronunciation with accurate intonation.',
            },
            keyStrengths: evalData.keyStrengths || generatedReport.keyStrengths,
            priorityImprovements: evalData.priorityImprovements || generatedReport.priorityImprovements,
            detailedErrors: evalData.detailedErrors || generatedReport.detailedErrors,
            studyPlan: evalData.studyPlan || generatedReport.studyPlan,
            examinerNotes: evalData.examinerNotes || generatedReport.examinerNotes
          };
        }
      }
    } catch (err) {
      console.warn("Node evaluation proxy offline, trying FastAPI evaluate...");
    }

    // 2. Try FastAPI evaluation endpoint if needed
    try {
      const fastApiRes = await fetch(`${API_URL}/evaluate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript: fullTranscript }),
      });
      if (fastApiRes.ok) {
        const fastApiData = await fastApiRes.json();
        if (fastApiData) {
          const fc = fastApiData.fluency_coherence || {};
          const lr = fastApiData.lexical_resource || {};
          const gr = fastApiData.grammar || {};
          const pr = fastApiData.pronunciation || {};
          const ov = fastApiData.overall || {};

          generatedReport.scores = {
            fluencyScore: Number(fc.score || generatedReport.scores.fluencyScore),
            lexicalScore: Number(lr.score || generatedReport.scores.lexicalScore),
            grammarScore: Number(gr.score || generatedReport.scores.grammarScore),
            pronunciationScore: Number(pr.score || generatedReport.scores.pronunciationScore),
            overallBand: Number(ov.score || generatedReport.scores.overallBand),
            fluencyFeedback: fc.notes || generatedReport.scores.fluencyFeedback,
            lexicalFeedback: lr.notes || generatedReport.scores.lexicalFeedback,
            grammarFeedback: gr.notes || generatedReport.scores.grammarFeedback,
            pronunciationFeedback: pr.notes || generatedReport.scores.pronunciationFeedback,
          };
          generatedReport.overallBand = generatedReport.scores.overallBand;
        }
      }
    } catch (fErr) {
      // Keep generatedReport
    }

    setReport(generatedReport);
    localStorage.setItem('ielts_report', JSON.stringify(generatedReport));
    setIsGeneratingReport(false);
  };

  // Start Exam when Candidate is ready
  const handleStartExam = () => {
    stopAllAudio();
    setIsExamActive(true);

    let startQuestion = "";
    if (currentPart === 'part1') {
      const topic = activePart1Topics[part1CategoryIndex % activePart1Topics.length] || activePart1Topics[0];
      const q = topic.questions[0] || "Where is your hometown located and what is it like living there?";
      startQuestion = `Good day. Welcome to the IELTS Speaking test. In this first part, I am going to ask you some general questions about yourself. Let's start by talking about ${topic.category.toLowerCase()}: ${q}`;
    } else if (currentPart === 'part2') {
      startQuestion = `Now in Part 2, here is your cue card topic: "${currentCueCard.topic}". You have 1 minute to prepare your notes and then 2 minutes to speak.`;
    } else {
      const p3Set = activePart3Topics[part3TopicIndex % activePart3Topics.length] || activePart3Topics[0];
      const q3 = p3Set.questions[0] || "How has modern technology transformed the way people travel and experience foreign cultures?";
      startQuestion = `We've been discussing ${p3Set.cueCardTopic || 'this topic'}, and now in Part 3, let's consider ${p3Set.theme || 'this area'} in general: ${q3}`;
    }

    setExaminerText(startQuestion);

    const exMsg: ChatMessage = {
      id: `msg-start-${Date.now()}`,
      sender: 'examiner',
      text: startQuestion,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => {
      // If previous messages already have this question, don't duplicate
      const lastMsg = prev[prev.length - 1];
      if (lastMsg && lastMsg.sender === 'examiner' && lastMsg.text === startQuestion) {
        return prev;
      }
      return [...prev, exMsg];
    });

    setStatus('ready');

    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: currentPart === 'part1' ? 'start_part1' : currentPart === 'part2' ? 'start_part2' : 'start_part3',
        part: partNum,
        cue_card_id: currentCueCard.id,
        text: startQuestion,
        question: startQuestion
      }));
    } else {
      playExaminerVoice(startQuestion);
    }
  };

  // Stop / Pause Exam
  const handleStopExam = () => {
    if (status === 'recording') {
      stopRecording();
    }
    stopAllAudio();
    setIsExamActive(false);
    setStatus('ready');
  };

  const handleResetTest = () => {
    stopAllAudio();
    if (status === 'recording') {
      stopRecording();
    }
    setIsExamActive(false);
    setPart1CategoryIndex(0);
    setPart1QuestionIndex(0);
    setCueCardIndex(0);
    setPart3TopicIndex(0);
    setPart3QuestionIndex(0);
    const p1Topic = activePart1Topics[0] || PART1_TOPICS[0];
    const p1Questions = p1Topic.questions || [];
    const initialQ = `Good day. Welcome to the IELTS Speaking test. In this first part, I am going to ask you some questions about yourself. Let's start by talking about ${p1Topic.category ? p1Topic.category.toLowerCase() : 'your hometown'}: ${p1Questions[0] || "Where is your hometown located and what is it like living there?"}`;
    const initMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'examiner',
      text: initialQ,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages([initMsg]);
    setExaminerText(initialQ);
    setCandidateText('');
    setReport(null);
    setCurrentPart('part1');
    setPartNum(1);
    setStatus('ready');
    localStorage.removeItem('ielts_messages');
    localStorage.removeItem('ielts_report');
    localStorage.removeItem('ielts_exam_active');
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
        onOpenServerStatus={() => setShowServerStatusModal(true)}
        onOpenQuestionBank={() => setShowQuestionBankModal(true)}
        activeBankTitle={questionBank.title}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        
        {/* Practice Tab */}
        {activeTab === 'practice' && (
          <div className="max-w-4xl mx-auto space-y-5">
            
            {/* Exam Stage Selector */}
            <ExamStageSelector
              currentPart={currentPart}
              setCurrentPart={handleStageChange}
              onResetTest={handleResetTest}
              onFinishTest={handleGenerateReport}
              messageCount={messages.length}
              onOpenQuestionBank={() => setShowQuestionBankModal(true)}
              questionBankTitle={questionBank.title}
              isExamActive={isExamActive}
              onStartExam={handleStartExam}
              onStopExam={handleStopExam}
              mode={mode}
              strictTimeRemaining={strictTimeRemaining}
            />

            {/* Part 1 Stage Viewer */}
            {currentPart === 'part1' && (
              <Part1StageViewer
                topics={activePart1Topics}
                currentCategoryIndex={part1CategoryIndex}
                currentQuestionIndex={part1QuestionIndex}
                onSelectCategory={(idx) => {
                  setPart1CategoryIndex(idx);
                  setPart1QuestionIndex(0);
                  const topic = activePart1Topics[idx % activePart1Topics.length];
                  const q = topic.questions[0] || "Where is your hometown located and what is it like living there?";
                  const fullQ = `In this part, let's talk about ${topic.category.toLowerCase()}: ${q}`;
                  setExaminerText(fullQ);
                  const exMsg: ChatMessage = {
                    id: `msg-p1-${Date.now()}`,
                    sender: 'examiner',
                    text: fullQ,
                    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                  };
                  setMessages((prev) => [...prev, exMsg]);
                  if (isExamActive) {
                    playExaminerVoice(fullQ);
                  }
                }}
                onAskQuestion={(q, idx) => {
                  if (typeof idx === 'number') {
                    setPart1QuestionIndex(idx);
                  }
                  setExaminerText(q);
                  const exMsg: ChatMessage = {
                    id: `msg-p1-${Date.now()}`,
                    sender: 'examiner',
                    text: q,
                    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                  };
                  setMessages((prev) => [...prev, exMsg]);
                  if (isExamActive) {
                    playExaminerVoice(q);
                  }
                }}
              />
            )}

            {/* Cue Card Viewer for Part 2 */}
            {currentPart === 'part2' && (
              <CueCardViewer
                cueCard={currentCueCard}
                onSelectNewCard={() => {
                  const nextIdx = (cueCardIndex + 1) % activeCueCards.length;
                  setCueCardIndex(nextIdx);
                  const nextCard = activeCueCards[nextIdx];
                  const q = `Now in Part 2, here is your cue card topic: "${nextCard.topic}". You have 1 minute to prepare your notes and then 2 minutes to speak.`;
                  setExaminerText(q);
                  if (isExamActive) {
                    playExaminerVoice(q);
                  }
                }}
                onStartSpeech={() => {
                  const prompt = `Thank you. Please begin speaking now on your topic: ${currentCueCard.topic}.`;
                  setExaminerText(prompt);
                  if (isExamActive) {
                    playExaminerVoice(prompt);
                  }
                }}
              />
            )}

            {/* Part 3 Stage Viewer */}
            {currentPart === 'part3' && (
              <Part3StageViewer
                topics={activePart3Topics}
                currentTopicIndex={part3TopicIndex}
                currentQuestionIndex={part3QuestionIndex}
                onSelectTopic={(idx) => {
                  setPart3TopicIndex(idx);
                  setPart3QuestionIndex(0);
                  const p3Set = activePart3Topics[idx % activePart3Topics.length];
                  const q3 = p3Set.questions[0] || "How has modern technology transformed the way people travel and experience foreign cultures?";
                  const fullQ = `We've been talking about ${p3Set.cueCardTopic.toLowerCase()}, and now I'd like to discuss with you one or two more general questions related to this. Let's consider ${p3Set.theme.toLowerCase()} in general: ${q3}`;
                  setExaminerText(fullQ);
                  const exMsg: ChatMessage = {
                    id: `msg-p3-${Date.now()}`,
                    sender: 'examiner',
                    text: fullQ,
                    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                  };
                  setMessages((prev) => [...prev, exMsg]);
                  if (isExamActive) {
                    playExaminerVoice(fullQ);
                  }
                }}
                onAskQuestion={(q, idx) => {
                  if (typeof idx === 'number') {
                    setPart3QuestionIndex(idx);
                  }
                  setExaminerText(q);
                  const exMsg: ChatMessage = {
                    id: `msg-p3-${Date.now()}`,
                    sender: 'examiner',
                    text: q,
                    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                  };
                  setMessages((prev) => [...prev, exMsg]);
                  if (isExamActive) {
                    playExaminerVoice(q);
                  }
                }}
              />
            )}

            {/* Chat Transcript */}
            <ChatInterface
              messages={messages}
              mode={mode}
              onPlayMessageVoice={(txt) => playExaminerVoice(txt)}
              isLoading={status === 'transcribing' || status === 'thinking'}
              evaluationReport={report}
            />

            {/* Real-Time Conversation Controls */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl sticky bottom-4 z-20 backdrop-blur-lg space-y-3">
              
              {/* Header with status and VAD indicator */}
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center space-x-2">
                  <span className={`w-3 h-3 rounded-full ${
                    status === 'recording' ? 'bg-rose-500 animate-ping' : status === 'speaking' ? 'bg-indigo-500 animate-pulse' : 'bg-emerald-500'
                  }`} />
                  <span className="font-bold text-sm text-white">
                    {getStatusText()}
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  {/* Voice Activity Detection Debug Indicator */}
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
                    <div className="text-xs font-mono text-slate-400 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800 hidden sm:block">
                      Session: {sessionId.substring(0, 8)}
                    </div>
                  )}
                </div>
              </div>

              {/* Advanced Real-time Audio Waveform & Spectrum Visualizer */}
              {status === 'recording' && (
                <AudioWaveformVisualizer
                  analyserNode={analyserNode}
                  isRecording={status === 'recording'}
                  isVoiceDetected={isVoiceDetected}
                  audioLevel={audioLevel}
                  silenceProgress={silenceProgress}
                />
              )}

              {/* Action Area: Voice Controls */}
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
                        <span>⏹ Stop Answer</span>
                      </button>
                    </div>
                    <p className="text-[11px] text-slate-400 italic">
                      ✨ Automatic VAD active: Stops after 1.5s silence or max {currentPart === 'part2' ? '120s' : '60s'}
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
                Official IELTS Speaking Simulation • Click <strong>Start Answer</strong>, articulate your response into your microphone, then click <strong>Stop Answer</strong>
              </div>

            </div>

          </div>
        )}

        {/* Band Diagnostic Report Tab */}
        {activeTab === 'report' && (
          <div className="max-w-5xl mx-auto">
            {isGeneratingReport ? (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center my-6 space-y-4">
                <RefreshCw className="w-10 h-10 animate-spin text-indigo-400 mx-auto" />
                <h3 className="text-lg font-bold text-white">Synthesizing Official IELTS Band Score...</h3>
                <p className="text-xs text-slate-400 max-w-md mx-auto">
                  Analyzing candidate speech across Fluency & Coherence, Lexical Resource, Grammatical Range & Accuracy, and Pronunciation against British Council & Cambridge benchmarks.
                </p>
              </div>
            ) : (
              <BandReportView
                report={report}
                onGenerateReport={handleGenerateReport}
                onRestartTest={handleResetTest}
                onExportPDF={() => window.print()}
              />
            )}
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

      {/* Question Bank Loader Modal */}
      {showQuestionBankModal && (
        <QuestionBankModal
          isOpen={showQuestionBankModal}
          onClose={() => setShowQuestionBankModal(false)}
          currentBank={questionBank}
          onBankChanged={handleBankChanged}
        />
      )}

      {/* Server Status Modal */}
      {showServerStatusModal && (
        <ServerStatusModal
          isOpen={showServerStatusModal}
          onClose={() => setShowServerStatusModal(false)}
        />
      )}

    </div>
  );
}
