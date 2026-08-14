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
      'Where is your hometown located and what is it like?',
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
    category: 'Leisure & Daily Life',
    questions: [
      'What do you enjoy doing in your free time?',
      'Did you have different hobbies when you were younger?',
      'Do you prefer indoor activities or outdoor sports?',
      'How important is relaxation to maintain a good work-life balance?'
    ]
  }
];

export const PART3_TOPICS = [
  {
    topicId: 'cue-1',
    cueCardTopic: 'Travel & Journeys',
    theme: 'Tourism, Cultural Exchange & Transportation',
    questions: [
      'How has modern technology transformed the way people travel and experience foreign cultures?',
      'Do you think international tourism does more to preserve or dilute local cultural traditions?',
      'Why do some people prefer adventurous solo travel while others prefer guided group tours?',
      'How might the travel and tourism industry evolve over the next twenty years?'
    ]
  },
  {
    topicId: 'cue-2',
    cueCardTopic: 'Inspiring People & Mentorship',
    theme: 'Leadership, Role Models & Modern Influence',
    questions: [
      'What qualities do you believe are essential for a person to be considered a true role model in today’s society?',
      'How has the rise of social media influencers changed young people’s perception of success and leadership?',
      'Do you think public figures and celebrities have a moral responsibility to set a good example for the youth?',
      'In what ways can mentors and teachers motivate students more effectively than parents?'
    ]
  },
  {
    topicId: 'cue-3',
    cueCardTopic: 'Technology & Everyday Devices',
    theme: 'Digital Transformation, Artificial Intelligence & Privacy',
    questions: [
      'In what ways has the widespread use of smart devices impacted human interpersonal communication?',
      'Do you think society is becoming overly dependent on automated algorithms and artificial intelligence?',
      'What measures should governments take to protect personal privacy in an increasingly digitized world?',
      'Will future technological breakthroughs eliminate the distinction between work and personal life?'
    ]
  },
  {
    topicId: 'cue-4',
    cueCardTopic: 'Environment & Sustainable Habits',
    theme: 'Global Climate Action, Corporate Responsibility & Conservation',
    questions: [
      'Who do you think bears greater responsibility for environmental conservation: individual citizens or multinational corporations?',
      'How can schools and educational institutions foster genuine environmental awareness in the younger generation?',
      'Do you believe economic development and environmental sustainability can realistically coexist without conflict?',
      'What role should international treaties and global cooperation play in addressing climate emergencies?'
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
