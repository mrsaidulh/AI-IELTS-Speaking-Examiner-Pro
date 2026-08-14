import { QuestionBank, Part1Topic, CueCard, Part3Topic } from '../types';
import { OFFICIAL_CUE_CARDS, PART1_TOPICS, PART3_TOPICS } from '../data/topics';

const STORAGE_KEY = 'ielts_active_question_bank';
const CUSTOM_BANKS_KEY = 'ielts_custom_question_banks';

export interface BankPreset {
  id: string;
  name: string;
  url: string;
  badge: string;
  description: string;
}

export const OFFICIAL_PRESETS: BankPreset[] = [
  {
    id: 'cambridge-standard-2026',
    name: 'Cambridge Official IELTS 2026 (Standard)',
    url: '/data/question_bank.json',
    badge: 'Standard 2026',
    description: 'High-frequency core topics: Journeys, Mentors, Daily Tech & Environment'
  },
  {
    id: 'cambridge-19-academic',
    name: 'Cambridge IELTS 19 Academic Test Pack',
    url: '/data/question_bank_cambridge19.json',
    badge: 'Cambridge 19',
    description: 'Academic focus: Heritage Sites, Decision Making & Outdoor Recreation'
  }
];

// Fallback Default Bank
export const DEFAULT_FALLBACK_BANK: QuestionBank = {
  id: 'cambridge-standard-2026',
  title: 'Cambridge Official IELTS Speaking Bank (Standard Edition)',
  version: '2026.1',
  description: 'Standard authentic Cambridge IELTS test bank covering Part 1, Part 2, and Part 3.',
  author: 'Cambridge IELTS Assessment Framework',
  lastUpdated: '2026-08-14',
  part1Topics: PART1_TOPICS,
  part2CueCards: OFFICIAL_CUE_CARDS,
  part3Topics: PART3_TOPICS
};

/**
 * Validates whether a given parsed object matches the QuestionBank schema.
 */
export function validateQuestionBank(data: any): { valid: boolean; error?: string } {
  if (!data || typeof data !== 'object') {
    return { valid: false, error: 'Question bank JSON must be a valid object.' };
  }

  if (!data.id || typeof data.id !== 'string') {
    return { valid: false, error: 'Question bank is missing a required "id" string.' };
  }

  if (!data.title || typeof data.title !== 'string') {
    return { valid: false, error: 'Question bank is missing a required "title" string.' };
  }

  if (!Array.isArray(data.part1Topics) || data.part1Topics.length === 0) {
    return { valid: false, error: 'Question bank must include at least one Part 1 topic in "part1Topics".' };
  }

  if (!Array.isArray(data.part2CueCards) || data.part2CueCards.length === 0) {
    return { valid: false, error: 'Question bank must include at least one Part 2 Cue Card in "part2CueCards".' };
  }

  if (!Array.isArray(data.part3Topics) || data.part3Topics.length === 0) {
    return { valid: false, error: 'Question bank must include at least one Part 3 topic in "part3Topics".' };
  }

  // Validate Cue Card structure
  for (const card of data.part2CueCards) {
    if (!card.topic || !Array.isArray(card.bulletPoints) || card.bulletPoints.length === 0) {
      return { valid: false, error: `Invalid Cue Card format in Part 2: ${card.topic || 'Unknown'}` };
    }
  }

  return { valid: true };
}

/**
 * Fetches a Question Bank from a JSON file URL or endpoint.
 */
export async function fetchQuestionBankFromUrl(url: string): Promise<QuestionBank> {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP Error ${response.status}: Failed to fetch ${url}`);
    }
    const data = await response.json();
    const validation = validateQuestionBank(data);
    if (!validation.valid) {
      throw new Error(validation.error);
    }
    return data as QuestionBank;
  } catch (err: any) {
    console.warn(`Failed to fetch from ${url}, using fallback:`, err);
    throw err;
  }
}

/**
 * Loads the active Question Bank from LocalStorage or default URL.
 */
export async function loadActiveQuestionBank(): Promise<QuestionBank> {
  try {
    // Check if user set a cached bank in LocalStorage
    const cached = localStorage.getItem(STORAGE_KEY);
    if (cached) {
      const parsed = JSON.parse(cached);
      const val = validateQuestionBank(parsed);
      if (val.valid) {
        return parsed;
      }
    }

    // Try fetching from the default JSON endpoint
    const fetched = await fetchQuestionBankFromUrl('/data/question_bank.json');
    return fetched;
  } catch (e) {
    console.warn('Falling back to built-in fallback bank', e);
    return DEFAULT_FALLBACK_BANK;
  }
}

/**
 * Saves a Question Bank as the active active question bank in LocalStorage.
 */
export function setActiveQuestionBank(bank: QuestionBank): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(bank));
}

/**
 * Parses and imports a JSON string as a new Question Bank.
 */
export function parseAndImportQuestionBankJSON(jsonString: string): QuestionBank {
  const data = JSON.parse(jsonString);
  const val = validateQuestionBank(data);
  if (!val.valid) {
    throw new Error(val.error || 'Invalid Question Bank JSON.');
  }
  setActiveQuestionBank(data as QuestionBank);
  return data as QuestionBank;
}

/**
 * Resets back to the default factory Cambridge bank.
 */
export function resetQuestionBankToDefault(): QuestionBank {
  localStorage.removeItem(STORAGE_KEY);
  return DEFAULT_FALLBACK_BANK;
}
