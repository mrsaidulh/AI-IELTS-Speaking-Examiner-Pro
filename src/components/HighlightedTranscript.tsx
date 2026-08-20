import React, { useState } from 'react';
import { CorrectionData, DetailedErrorItem, IELTSEvaluationReport } from '../types';
import { AlertTriangle, BookOpen, CheckCircle, Sparkles, HelpCircle, ArrowRight, MessageSquare } from 'lucide-react';

interface FlaggedToken {
  target: string;
  startIndex: number;
  endIndex: number;
  category: 'Grammar' | 'Vocabulary' | 'Fluency' | 'Pronunciation' | 'Feedback';
  correction: string;
  explanation: string;
}

interface HighlightedTranscriptProps {
  text: string;
  corrections?: CorrectionData;
  evaluationReport?: IELTSEvaluationReport | null;
  isCandidate?: boolean;
}

export const HighlightedTranscript: React.FC<HighlightedTranscriptProps> = ({
  text,
  corrections,
  evaluationReport,
  isCandidate = false,
}) => {
  const [activeTooltipIndex, setActiveTooltipIndex] = useState<number | null>(null);

  if (!isCandidate || (!corrections && !evaluationReport?.detailedErrors?.length)) {
    return <div className="whitespace-pre-wrap leading-relaxed">{text}</div>;
  }

  // 1. Gather all candidate flagged target items
  const flaggedItems: {
    target: string;
    category: 'Grammar' | 'Vocabulary' | 'Fluency' | 'Pronunciation' | 'Feedback';
    correction: string;
    explanation: string;
  }[] = [];

  // Grammar issues from Training Mode feedback
  if (corrections?.grammarIssues) {
    corrections.grammarIssues.forEach((g) => {
      if (g.issue && g.issue.trim()) {
        flaggedItems.push({
          target: g.issue.trim(),
          category: 'Grammar',
          correction: g.fix,
          explanation: g.explanation || 'Grammatical accuracy adjustment',
        });
      }
    });
  }

  // Vocabulary upgrades from Training Mode feedback
  if (corrections?.vocabularyUpgrades) {
    corrections.vocabularyUpgrades.forEach((v) => {
      if (v.original && v.original.trim()) {
        flaggedItems.push({
          target: v.original.trim(),
          category: 'Vocabulary',
          correction: v.upgraded,
          explanation: v.context || 'Band 8.0+ Lexical Resource upgrade',
        });
      }
    });
  }

  // Detailed errors from full diagnostic Band Evaluation report
  if (evaluationReport?.detailedErrors) {
    evaluationReport.detailedErrors.forEach((err: DetailedErrorItem) => {
      if (err.quote && err.quote.trim()) {
        const cat =
          err.category === 'Grammar'
            ? 'Grammar'
            : err.category === 'Vocabulary'
            ? 'Vocabulary'
            : err.category === 'Fluency/Fillers'
            ? 'Fluency'
            : 'Pronunciation';
        flaggedItems.push({
          target: err.quote.trim(),
          category: cat,
          correction: err.correction,
          explanation: err.impact || 'Examiner diagnostic feedback',
        });
      }
    });
  }

  if (flaggedItems.length === 0) {
    return <div className="whitespace-pre-wrap leading-relaxed">{text}</div>;
  }

  // 2. Locate match intervals in the transcript text
  const rawTextLower = text.toLowerCase();
  const tokens: FlaggedToken[] = [];

  flaggedItems.forEach((item) => {
    const searchTarget = item.target.toLowerCase();
    let searchStart = 0;

    // Direct substring match
    while (searchStart < rawTextLower.length) {
      const foundIdx = rawTextLower.indexOf(searchTarget, searchStart);
      if (foundIdx === -1) break;

      tokens.push({
        target: text.substring(foundIdx, foundIdx + item.target.length),
        startIndex: foundIdx,
        endIndex: foundIdx + item.target.length,
        category: item.category,
        correction: item.correction,
        explanation: item.explanation,
      });

      searchStart = foundIdx + item.target.length;
    }

    // Fallback: If target was an entire clause, also attempt word-by-word key token match if not found directly
    if (tokens.length === 0 && searchTarget.includes(' ')) {
      const words = searchTarget.split(' ').filter((w) => w.length > 3);
      for (const word of words) {
        const wordIdx = rawTextLower.indexOf(word);
        if (wordIdx !== -1) {
          tokens.push({
            target: text.substring(wordIdx, wordIdx + word.length),
            startIndex: wordIdx,
            endIndex: wordIdx + word.length,
            category: item.category,
            correction: item.correction,
            explanation: item.explanation,
          });
          break;
        }
      }
    }
  });

  if (tokens.length === 0) {
    return <p className="whitespace-pre-wrap leading-relaxed">{text}</p>;
  }

  // 3. Resolve overlapping intervals (prioritize earlier start and longer span)
  tokens.sort((a, b) => a.startIndex - b.startIndex || (b.endIndex - b.startIndex) - (a.endIndex - a.startIndex));

  const nonOverlappingTokens: FlaggedToken[] = [];
  let lastEnd = 0;

  for (const token of tokens) {
    if (token.startIndex >= lastEnd) {
      nonOverlappingTokens.push(token);
      lastEnd = token.endIndex;
    }
  }

  // 4. Construct parsed segments
  const segments: React.ReactNode[] = [];
  let cursor = 0;

  nonOverlappingTokens.forEach((token, index) => {
    // Unflagged text prior to match
    if (token.startIndex > cursor) {
      segments.push(
        <span key={`plain-${cursor}`}>{text.substring(cursor, token.startIndex)}</span>
      );
    }

    const isHovered = activeTooltipIndex === index;

    // Distinct category color themes
    const categoryStyles = {
      Grammar: {
        bg: 'bg-rose-500/25 hover:bg-rose-500/35 border-b-2 border-rose-400 text-rose-100',
        badge: 'bg-rose-950/80 text-rose-300 border border-rose-500/30',
        icon: AlertTriangle,
        label: 'Grammar Issue',
      },
      Vocabulary: {
        bg: 'bg-sky-500/25 hover:bg-sky-500/35 border-b-2 border-sky-400 text-sky-100',
        badge: 'bg-sky-950/80 text-sky-300 border border-sky-500/30',
        icon: BookOpen,
        label: 'Band 8.0+ Lexical Upgrade',
      },
      Fluency: {
        bg: 'bg-amber-500/25 hover:bg-amber-500/35 border-b-2 border-amber-400 text-amber-100',
        badge: 'bg-amber-950/80 text-amber-300 border border-amber-500/30',
        icon: Sparkles,
        label: 'Fluency & Filler',
      },
      Pronunciation: {
        bg: 'bg-purple-500/25 hover:bg-purple-500/35 border-b-2 border-purple-400 text-purple-100',
        badge: 'bg-purple-950/80 text-purple-300 border border-purple-500/30',
        icon: MessageSquare,
        label: 'Pronunciation Stress',
      },
      Feedback: {
        bg: 'bg-indigo-500/25 hover:bg-indigo-500/35 border-b-2 border-indigo-400 text-indigo-100',
        badge: 'bg-indigo-950/80 text-indigo-300 border border-indigo-500/30',
        icon: HelpCircle,
        label: 'Examiner Flag',
      },
    };

    const style = categoryStyles[token.category] || categoryStyles.Feedback;
    const Icon = style.icon;

    segments.push(
      <span
        key={`flagged-${token.startIndex}-${index}`}
        className="relative inline-block"
        onMouseEnter={() => setActiveTooltipIndex(index)}
        onMouseLeave={() => setActiveTooltipIndex(null)}
        onClick={() => setActiveTooltipIndex(isHovered ? null : index)}
      >
        <mark
          className={`px-1 py-0.5 rounded cursor-pointer transition-all duration-150 font-medium ${style.bg}`}
          title={`Click or hover to view correction: ${token.correction}`}
        >
          {text.substring(token.startIndex, token.endIndex)}
        </mark>

        {/* Interactive Self-Correction Tooltip Popover */}
        {isHovered && (
          <span
            className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 z-30 w-64 p-3 bg-slate-950 text-slate-100 rounded-xl shadow-2xl border border-slate-700 text-xs text-left animate-in fade-in zoom-in-95 pointer-events-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Popover Header */}
            <div className="flex items-center justify-between mb-1.5 pb-1 border-b border-slate-800">
              <span className={`flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] font-bold ${style.badge}`}>
                <Icon className="w-3 h-3 mr-0.5" />
                {style.label}
              </span>
              <span className="text-[10px] text-slate-400 font-mono">Self-Correction</span>
            </div>

            {/* Original vs Suggested comparison */}
            <div className="bg-slate-900/90 rounded-lg p-2 mb-2 border border-slate-800 space-y-1">
              <div className="flex items-center space-x-1.5 text-[11px]">
                <span className="text-slate-400 line-through truncate max-w-[90px]">{token.target}</span>
                <ArrowRight className="w-3 h-3 text-slate-500 shrink-0" />
                <span className="text-emerald-400 font-bold truncate">{token.correction}</span>
              </div>
            </div>

            {/* Explanation Note */}
            <span className="block text-[10px] text-slate-300 leading-tight">
              {token.explanation}
            </span>

            {/* Arrow pointer */}
            <span className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-px border-4 border-transparent border-t-slate-950" />
          </span>
        )}
      </span>
    );

    cursor = token.endIndex;
  });

  // Remaining text
  if (cursor < text.length) {
    segments.push(
      <span key={`plain-tail-${cursor}`}>{text.substring(cursor)}</span>
    );
  }

  return (
    <div className="space-y-1.5">
      <div className="whitespace-pre-wrap leading-relaxed">{segments}</div>
      
      {/* Targeted self-correction hint pill */}
      <div className="flex items-center space-x-1.5 text-[10px] text-indigo-200/90 bg-indigo-950/40 border border-indigo-500/20 px-2 py-0.5 rounded-full w-fit">
        <Sparkles className="w-3 h-3 text-indigo-300" />
        <span>
          {nonOverlappingTokens.length} {nonOverlappingTokens.length === 1 ? 'phrase' : 'phrases'} flagged for self-correction (hover highlighted text)
        </span>
      </div>
    </div>
  );
};
