export type TestMode = 'exam' | 'training';
export type TestPart = 'intro' | 'part1' | 'part2' | 'part3' | 'evaluation';
export type ExaminerAccent = 'british' | 'australian' | 'american';

export interface CorrectionData {
  originalText: string;
  correctedText: string;
  grammarIssues: { issue: string; fix: string; explanation: string }[];
  vocabularyUpgrades: { original: string; upgraded: string; context: string }[];
  bandBoostTip: string;
}

export interface ChatMessage {
  id: string;
  sender: 'examiner' | 'candidate' | 'system';
  text: string;
  timestamp: string;
  audioBlobUrl?: string;
  corrections?: CorrectionData;
}

export interface CueCard {
  id: string;
  topic: string;
  promptText: string;
  bulletPoints: string[];
  prepTimeSeconds: number;
  speakTimeSeconds: number;
}

export interface BandCriteriaScores {
  fluencyScore: number; // 0-9
  lexicalScore: number;
  grammarScore: number;
  pronunciationScore: number;
  overallBand: number;
  fluencyFeedback: string;
  lexicalFeedback: string;
  grammarFeedback: string;
  pronunciationFeedback: string;
}

export interface DetailedErrorItem {
  quote: string;
  correction: string;
  category: 'Grammar' | 'Vocabulary' | 'Fluency/Fillers' | 'Pronunciation';
  impact: string;
}

export interface StudyPlanDay {
  day: number;
  title: string;
  focus: string;
  exercise: string;
}

export interface IELTSEvaluationReport {
  candidateName: string;
  testDate: string;
  targetBand: number;
  overallBand: number;
  scores: BandCriteriaScores;
  keyStrengths: string[];
  priorityImprovements: string[];
  detailedErrors: DetailedErrorItem[];
  studyPlan: StudyPlanDay[];
  examinerNotes: string;
}

export interface LocalStackComponent {
  name: string;
  technology: string;
  purpose: string;
  dockerImage?: string;
  status: string;
}

export interface HardwarePreset {
  name: string;
  vramGb: number;
  ramGb: number;
  cpuCores: number;
  llmModel: string;
  sttModel: string;
  ttsModel: string;
  supportedUsers: number;
  status: 'Recommended' | 'Minimum' | 'High Performance';
}
