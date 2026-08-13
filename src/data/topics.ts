import { CueCard } from '../types';

export const OFFICIAL_CUE_CARDS: CueCard[] = [
  {
    id: 'cue-1',
    topic: 'Describe a memorable journey you went on',
    promptText: 'You should say:',
    bulletPoints: [
      'Where you went and how you traveled there',
      'Who you went with and why you took this trip',
      'What you saw or experienced during the journey',
      'And explain why this journey was so memorable to you'
    ],
    prepTimeSeconds: 60,
    speakTimeSeconds: 120
  },
  {
    id: 'cue-2',
    topic: 'Describe a person who has greatly inspired you',
    promptText: 'You should say:',
    bulletPoints: [
      'Who this person is and how you know them',
      'What achievements or qualities make them special',
      'How they have influenced your life or decisions',
      'And explain why you feel inspired by this person'
    ],
    prepTimeSeconds: 60,
    speakTimeSeconds: 120
  },
  {
    id: 'cue-3',
    topic: 'Describe a piece of technology you use every day',
    promptText: 'You should say:',
    bulletPoints: [
      'What technology or device it is',
      'When and where you acquired it',
      'How often and what tasks you use it for',
      'And explain how your daily life would change without it'
    ],
    prepTimeSeconds: 60,
    speakTimeSeconds: 120
  },
  {
    id: 'cue-4',
    topic: 'Describe an environmental rule or habit you practice',
    promptText: 'You should say:',
    bulletPoints: [
      'What the rule or habit is',
      'When you started following it',
      'Why you think it is important for the planet',
      'And explain what impact it has had on your lifestyle'
    ],
    prepTimeSeconds: 60,
    speakTimeSeconds: 120
  }
];

export const PART1_TOPICS = [
  {
    category: 'Hometown & Living',
    questions: [
      'Where is your hometown located?',
      'What do you like most about living in your city or town?',
      'Has your hometown changed much over the past few years?',
      'Would you recommend visitors to spend time in your hometown?'
    ]
  },
  {
    category: 'Work or Study',
    questions: [
      'Do you work or are you currently a student?',
      'What subject or field do you specialize in?',
      'What made you choose this career or academic path?',
      'What is a typical day like for you at work or university?'
    ]
  },
  {
    category: 'Leisure & Hobbies',
    questions: [
      'What do you enjoy doing in your free time?',
      'Did you have different hobbies when you were younger?',
      'Do you prefer indoor activities or outdoor sports?',
      'How important is relaxation to maintain work-life balance?'
    ]
  }
];

export const HARDWARE_PRESETS = [
  {
    name: 'Standard Laptop / Entry Rig',
    vramGb: 8,
    ramGb: 16,
    cpuCores: 8,
    llmModel: 'Qwen 3 (8B) / Llama 3.1 (8B)',
    sttModel: 'faster-whisper (small.en / base)',
    ttsModel: 'Kokoro v1.0 (CPU / CUDA)',
    supportedUsers: 1,
    status: 'Minimum' as const
  },
  {
    name: 'Dedicated AI Workstation',
    vramGb: 16,
    ramGb: 32,
    cpuCores: 12,
    llmModel: 'Qwen 3 (14B) / Gemma 2 (9B)',
    sttModel: 'faster-whisper (medium.en)',
    ttsModel: 'Kokoro v1.0 (FP16 Batch)',
    supportedUsers: 3,
    status: 'Recommended' as const
  },
  {
    name: 'High-Performance Local Server',
    vramGb: 24,
    ramGb: 64,
    cpuCores: 24,
    llmModel: 'Qwen 3 (32B) / Mixtral 8x7B',
    sttModel: 'faster-whisper (large-v3)',
    ttsModel: 'Kokoro v1.0 (Streaming CUDA)',
    supportedUsers: 10,
    status: 'High Performance' as const
  }
];
