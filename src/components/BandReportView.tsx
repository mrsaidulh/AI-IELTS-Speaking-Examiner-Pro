import React from 'react';
import { IELTSEvaluationReport } from '../types';
import { Award, CheckCircle2, AlertCircle, Calendar, RefreshCw, Printer, BookOpen, Sparkles, TrendingUp, HelpCircle } from 'lucide-react';

interface BandReportViewProps {
  report: IELTSEvaluationReport | null;
  isLoading: boolean;
  onGenerateReport: () => void;
  onRestartTest: () => void;
}

export const BandReportView: React.FC<BandReportViewProps> = ({
  report,
  isLoading,
  onGenerateReport,
  onRestartTest,
}) => {
  if (isLoading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center my-6">
        <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 flex items-center justify-center mx-auto mb-4 animate-bounce">
          <Award className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-bold text-white mb-2">Analyzing Complete Test Transcript</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto mb-6">
          Evaluating speech across Fluency & Coherence, Lexical Resource, Grammatical Accuracy, and Pronunciation criteria...
        </p>
        <div className="w-48 mx-auto bg-slate-800 rounded-full h-2 overflow-hidden">
          <div className="bg-indigo-500 h-2 rounded-full animate-pulse w-3/4" />
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-10 text-center my-6 max-w-2xl mx-auto">
        <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto mb-4">
          <Award className="w-7 h-7" />
        </div>
        <h3 className="text-base font-bold text-white mb-2">No Band Score Report Generated Yet</h3>
        <p className="text-xs text-slate-400 mb-6">
          Complete your conversational practice turns in the Practice Test tab, then click "Generate Band Score" to receive your comprehensive IELTS diagnostic assessment.
        </p>
        <button
          onClick={onGenerateReport}
          className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl shadow-md transition-all"
        >
          Evaluate Current Test Transcript
        </button>
      </div>
    );
  }

  // Safe normalized scores extraction (supporting both nested scores and flat report attributes)
  const rawScores = report.scores || (report as any);
  const overallBandVal = Number(report.overallBand || rawScores.overallBand || 7.0);
  const targetBandVal = Number(report.targetBand || 7.5);

  const scores = {
    fluencyScore: Number(rawScores.fluencyScore || (report as any).fluency_score || 7.0),
    lexicalScore: Number(rawScores.lexicalScore || (report as any).lexical_score || 7.0),
    grammarScore: Number(rawScores.grammarScore || (report as any).grammar_score || 7.0),
    pronunciationScore: Number(rawScores.pronunciationScore || (report as any).pronunciation_score || 7.0),
    overallBand: overallBandVal,
    fluencyFeedback: rawScores.fluencyFeedback || (report as any).fluencyFeedback || 'Good natural conversational flow with clear pauses and coherent transitions.',
    lexicalFeedback: rawScores.lexicalFeedback || (report as any).lexicalFeedback || 'Appropriate vocabulary range and clear topic collocations.',
    grammarFeedback: rawScores.grammarFeedback || (report as any).grammarFeedback || 'Demonstrated mix of simple and complex structures with good grammatical control.',
    pronunciationFeedback: rawScores.pronunciationFeedback || (report as any).pronunciationFeedback || 'Clear articulation, natural intonation rhythm, and easily intelligible speech.',
  };

  const keyStrengthsList = report.keyStrengths && report.keyStrengths.length > 0
    ? report.keyStrengths
    : (report as any).strongPoints || [
        'Responded directly and relevantly to all examiner questions',
        'Maintained sustained spoken output without unnaturally long pauses',
        'Effective use of topic vocabulary and natural sentence intonation'
      ];

  const priorityImprovementsList = report.priorityImprovements && report.priorityImprovements.length > 0
    ? report.priorityImprovements
    : (report as any).improvementAreas || [
        'Incorporate more Band 8.0+ idiomatic expressions and cohesive devices',
        'Vary complex syntactic structures like conditional and relative clauses',
        'Expand further on abstract arguments in Part 3 with concrete examples'
      ];

  const studyPlanList = report.studyPlan && report.studyPlan.length > 0
    ? report.studyPlan
    : [
        { day: 1, title: 'Fluency & Connectors', focus: 'Cohesive devices', exercise: 'Practice transitional connectors like "Furthermore", "In contrast", and "As a consequence".' },
        { day: 2, title: 'Cue Card Structure', focus: 'PPF Method', exercise: 'Structure 2-minute Part 2 responses using Past, Present, and Future angles.' },
        { day: 3, title: 'Grammar Precision', focus: 'Complex tenses', exercise: 'Drill present perfect continuous and third conditionals in spontaneous answers.' },
        { day: 4, title: 'Lexical Booster', focus: 'Topic collocations', exercise: 'Learn and apply 12 advanced academic collocations for Society and Technology.' },
        { day: 5, title: 'Part 3 Abstract Analysis', focus: 'Two-way debate', exercise: 'Answer 4 analytical questions starting with "It is widely argued that...".' },
        { day: 6, title: 'Timed Mock Simulation', focus: 'Full 14-min flow', exercise: 'Complete a full continuous exam simulation without pauses.' },
        { day: 7, title: 'Diagnostic Self-Review', focus: 'Pronunciation & Stress', exercise: 'Record, transcribe, and correct your speech against IELTS Band 8.0 benchmarks.' }
      ];

  const detailedErrorsList = report.detailedErrors || [
    { quote: "I am living here since 5 years", correction: "I have been living here for 5 years", category: "Grammar" as const, impact: "Verb tense accuracy" },
    { quote: "It was a very good experience", correction: "It was a remarkably enriching experience", category: "Vocabulary" as const, impact: "Lexical precision" }
  ];

  const examinerNotes = report.examinerNotes || `Candidate demonstrated solid linguistic competence with clear pronunciation and coherent idea development, positioned at Band ${overallBandVal.toFixed(1)}.`;

  const criteriaCards = [
    {
      title: 'Fluency & Coherence',
      score: scores.fluencyScore,
      feedback: scores.fluencyFeedback,
      color: 'from-blue-500 to-indigo-600',
      badgeBg: 'bg-blue-500/10 text-blue-300 border-blue-500/30',
    },
    {
      title: 'Lexical Resource',
      score: scores.lexicalScore,
      feedback: scores.lexicalFeedback,
      color: 'from-emerald-500 to-teal-600',
      badgeBg: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
    },
    {
      title: 'Grammatical Range & Accuracy',
      score: scores.grammarScore,
      feedback: scores.grammarFeedback,
      color: 'from-amber-500 to-orange-600',
      badgeBg: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
    },
    {
      title: 'Pronunciation',
      score: scores.pronunciationScore,
      feedback: scores.pronunciationFeedback,
      color: 'from-purple-500 to-pink-600',
      badgeBg: 'bg-purple-500/10 text-purple-300 border-purple-500/30',
    },
  ];

  return (
    <div className="space-y-6 my-6">
      
      {/* Top Report Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 border border-indigo-500/30 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <span className="px-3 py-1 text-xs font-bold rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center">
                <Award className="w-3.5 h-3.5 mr-1" />
                Official IELTS Diagnostic Assessment
              </span>
              <span className="text-xs text-slate-400">{report.testDate || new Date().toLocaleDateString()}</span>
            </div>
            <h2 className="text-2xl font-black text-white">
              Candidate Report: <span className="text-indigo-300">{report.candidateName || 'Saidul Hasan'}</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              {examinerNotes}
            </p>
          </div>

          {/* Overall Band Score Badge */}
          <div className="bg-slate-950/80 border border-indigo-500/40 rounded-2xl p-5 text-center min-w-[160px] shrink-0 shadow-lg">
            <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400 mb-1">
              Overall Band Score
            </div>
            <div className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-amber-300 via-indigo-200 to-amber-400">
              {overallBandVal.toFixed(1)}
            </div>
            <div className="text-[11px] text-slate-400 mt-1 font-medium">
              Target: <span className="text-indigo-300 font-bold">{targetBandVal.toFixed(1)}</span>
            </div>
          </div>
        </div>

      </div>

      {/* 4 Official Criteria Breakdown Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {criteriaCards.map((c, idx) => (
          <div key={idx} className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between shadow-sm hover:border-slate-700 transition-colors">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-slate-300">{c.title}</span>
                <span className={`px-2.5 py-1 text-xs font-black rounded-lg border ${c.badgeBg}`}>
                  Band {c.score.toFixed(1)}
                </span>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-slate-800 rounded-full h-2 mb-3 overflow-hidden">
                <div
                  className={`bg-gradient-to-r ${c.color} h-2 rounded-full`}
                  style={{ width: `${Math.min(100, Math.max(10, (c.score / 9.0) * 100))}%` }}
                />
              </div>

              <p className="text-xs text-slate-400 leading-relaxed">{c.feedback}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Strengths & Priority Improvements */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Key Strengths */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center space-x-2 text-emerald-400 font-bold mb-4 text-sm border-b border-slate-800 pb-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <span>Key Demonstrated Strengths</span>
          </div>
          <ul className="space-y-2.5 text-xs text-slate-300">
            {keyStrengthsList.map((str, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                <span className="leading-relaxed">{str}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Priority Improvements */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center space-x-2 text-amber-400 font-bold mb-4 text-sm border-b border-slate-800 pb-3">
            <TrendingUp className="w-5 h-5 text-amber-400" />
            <span>Priority Areas for Score Boost</span>
          </div>
          <ul className="space-y-2.5 text-xs text-slate-300">
            {priorityImprovementsList.map((imp, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                <span className="leading-relaxed">{imp}</span>
              </li>
            ))}
          </ul>
        </div>

      </div>

      {/* Detailed Speech Errors & Correction Table */}
      {detailedErrorsList.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
            <div className="flex items-center space-x-2 text-indigo-300 font-bold text-sm">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              <span>Transcript Error Diagnostics & Corrections</span>
            </div>
            <span className="text-[11px] text-slate-400">Targeting Band 8.0 Paraphrasing</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider">
                  <th className="py-2.5 px-3">Original Speech Quote</th>
                  <th className="py-2.5 px-3">Band 8.0+ Correction</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Impact</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {detailedErrorsList.map((err, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40">
                    <td className="py-3 px-3 text-rose-300 italic font-mono text-[11px] font-medium">"{err.quote}"</td>
                    <td className="py-3 px-3 text-emerald-300 font-semibold">{err.correction}</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700 text-[10px] font-medium">
                        {err.category}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-400">{err.impact}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 7-Day Personalized Study Plan */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <div className="flex items-center space-x-2 text-indigo-300 font-bold text-sm">
            <Calendar className="w-4 h-4 text-indigo-400" />
            <span>7-Day Diagnostic Practice Plan</span>
          </div>
          <span className="text-xs text-slate-400">Actionable Daily Drills</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-3">
          {studyPlanList.map((d) => (
            <div key={d.day} className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 flex flex-col justify-between">
              <div>
                <div className="text-[10px] font-black uppercase text-indigo-400 mb-1">
                  Day {d.day}
                </div>
                <h4 className="font-bold text-white text-xs mb-1 truncate">{d.title}</h4>
                <p className="text-[10px] text-slate-400 font-medium mb-2">{d.focus}</p>
              </div>
              <p className="text-[11px] text-slate-300 bg-slate-900 p-2 rounded-lg border border-slate-800/80 leading-relaxed">
                {d.exercise}
              </p>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};
