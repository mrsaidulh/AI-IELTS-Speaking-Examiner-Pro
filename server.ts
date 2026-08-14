import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI, Type } from "@google/genai";

const PORT = 3000;

async function startServer() {
  const app = express();
  app.use(express.json({ limit: "10mb" }));

  // Initialize Gemini AI
  const getAiClient = () => {
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      console.warn("GEMINI_API_KEY is missing from environment. Using fallback modes.");
      return null;
    }
    return new GoogleGenAI({
      apiKey,
      httpOptions: {
        headers: {
          "User-Agent": "aistudio-build",
        },
      },
    });
  };

  // API Route: Health check & System Diagnostics
  app.get(["/api/health", "/api/system/status"], async (req, res) => {
    try {
      const resp = await fetch("http://localhost:8000/api/system/status");
      if (resp.ok) {
        const data = await resp.json();
        return res.json(data);
      }
    } catch (err) {
      // FastAPI backend unreachable fallback
    }

    res.json({
      status: "degraded",
      timestamp: new Date().toISOString(),
      all_systems_ready: false,
      components: {
        fastapi: {
          status: "offline",
          port: 8000,
          version: "1.3",
          message: "FastAPI server is not running on port 8000. Run `PYTHONPATH=backend python3 backend/voice_api.py`"
        },
        ollama: {
          status: "unknown",
          model: "qwen2.5:7b-instruct",
          url: "http://localhost:11434",
          available_models: [],
          message: "Start FastAPI backend to inspect Ollama status"
        },
        whisper: {
          status: "unknown",
          backend: "faster_whisper",
          model_size: "small",
          device: "cpu/cuda",
          compute_type: "int8",
          message: "Start FastAPI backend to inspect Whisper status"
        },
        kokoro: {
          status: "unknown",
          voice: "af_heart",
          sample_rate: 24000,
          message: "Start FastAPI backend to inspect Kokoro status"
        },
        gpu: {
          status: "unknown",
          cuda_available: false,
          device_name: "GPU",
          vram_total_mb: 0,
          vram_allocated_mb: 0,
          cuda_version: null
        },
        database: {
          status: "online",
          engine: "SQLite",
          message: "Frontend API proxy active"
        }
      }
    });
  });

  // API Route: Examiner Response Generation
  app.post("/api/examiner/respond", async (req, res) => {
    try {
      const { testPart, mode, messages, userSpeech, cueCardTopic, accent } = req.body;
      const ai = getAiClient();

      if (!ai) {
        // Fallback examiner responses if API key is not present
        return res.json({
          examinerResponse: "Thank you for that response. Could you elaborate a bit more on why you feel that way?",
          corrections: mode === "training" ? {
            originalText: userSpeech || "",
            correctedText: userSpeech ? `In my opinion, ${userSpeech.toLowerCase()}` : "",
            grammarIssues: [{ issue: "Sentence structure", fix: "Add transition connector", explanation: "IELTS examiners look for complex cohesive devices." }],
            vocabularyUpgrades: [{ original: "good", upgraded: "beneficial / exceptional", context: "Enhances lexical score" }],
            bandBoostTip: "Use varied sentence structures like conditional clauses to reach Band 7.0+."
          } : null
        });
      }

      const promptSystem = `
You are an official IELTS Speaking Examiner.
Accent / Tone: ${accent || 'British'} English.
Test Part: ${testPart || 'part1'}.
Mode: ${mode || 'exam'}.
Cue Card Topic (if Part 2/3): ${cueCardTopic || 'N/A'}.

RULES:
1. Act strictly like an authentic IELTS Speaking examiner.
2. Ask only ONE natural, clear, official-style IELTS question at a time.
3. Do not break character or give commentary inside your examiner spoken question.
4. Part 1: Keep questions personal, concise, and focused on everyday life (hometown, study, hobbies, work).
5. Part 2: Focus on encouraging candidate to speak for 1-2 minutes on the cue card.
6. Part 3: Ask abstract, analytical, and opinion-based follow-up questions extending the Part 2 topic.
7. Maintain candidate conversation flow based on history provided.
8. IF mode is "training", also evaluate the candidate's sentence grammar & vocabulary in a JSON field "corrections". IF mode is "exam", leave "corrections" as null.

Format your output strictly as a JSON object with this structure:
{
  "examinerResponse": "Next question or examiner statement",
  "corrections": ${mode === "training" ? `{
    "originalText": "candidate input text",
    "correctedText": "grammatically natural Band 8+ version",
    "grammarIssues": [{"issue": "short label", "fix": "correction", "explanation": "why"}],
    "vocabularyUpgrades": [{"original": "simple word", "upgraded": "advanced collocation", "context": "usage tip"}],
    "bandBoostTip": "specific advice to boost score"
  }` : "null"}
}
`;

      const formattedHistory = (messages || []).slice(-6).map((m: any) => `${m.sender.toUpperCase()}: ${m.text}`).join("\n");
      const userPrompt = `Conversation History:\n${formattedHistory}\n\nCANDIDATE SPOKE: "${userSpeech || 'Hello examiner, I am ready.'}"\n\nProvide the examiner's response in JSON.`;

      const response = await ai.models.generateContent({
        model: "gemini-3.6-flash",
        contents: userPrompt,
        config: {
          systemInstruction: promptSystem,
          responseMimeType: "application/json",
          temperature: 0.7,
        },
      });

      const responseText = response.text || "{}";
      let parsedData;
      try {
        parsedData = JSON.parse(responseText);
      } catch (err) {
        parsedData = {
          examinerResponse: responseText.replace(/```json|```/g, "").trim(),
          corrections: null,
        };
      }

      res.json(parsedData);
    } catch (error: any) {
      console.error("Examiner respond error:", error);
      res.status(500).json({
        examinerResponse: "Thank you. Let's move on to the next question. Could you share your thoughts on this topic?",
        corrections: null,
        error: error.message,
      });
    }
  });

  // API Route: Full IELTS Band Evaluation & Diagnostic Report
  app.post("/api/examiner/evaluate", async (req, res) => {
    try {
      const { candidateName, fullTranscript, targetBand = 7.5 } = req.body;
      const ai = getAiClient();

      if (!ai) {
        // High quality fallback report
        return res.json({
          candidateName: candidateName || "Candidate",
          testDate: new Date().toLocaleDateString("en-US", { year: 'numeric', month: 'long', day: 'numeric' }),
          targetBand,
          overallBand: 6.5,
          scores: {
            fluencyScore: 6.5,
            lexicalScore: 6.5,
            grammarScore: 6.0,
            pronunciationScore: 7.0,
            overallBand: 6.5,
            fluencyFeedback: "Good willingness to speak at length with reasonable coherence.",
            lexicalFeedback: "Used adequate vocabulary range with occasional repetition.",
            grammarFeedback: "Demonstrated mix of simple and complex structures with minor tense errors.",
            pronunciationFeedback: "Clear speech with generally good intonation.",
          },
          keyStrengths: [
            "Responded directly and relevantly to all examiner prompts",
            "Maintained continuous speech without long unnaturally silence",
            "Good clear pronunciation with natural sentence stress"
          ],
          priorityImprovements: [
            "Reduce hesitation gaps when organizing complex arguments",
            "Incorporate more Band 7.0+ idiomatic expressions and topic collocations",
            "Double-check subject-verb agreement and article precision"
          ],
          detailedErrors: [
            { quote: "I am living here since 5 years", correction: "I have been living here for 5 years", category: "Grammar", impact: "Tense accuracy" },
            { quote: "It was a very good experience", correction: "It was a remarkably rewarding experience", category: "Vocabulary", impact: "Lexical precision" }
          ],
          studyPlan: [
            { day: 1, title: "Fluency & Connectors", focus: "Cohesive devices", exercise: "Practice using 'In spite of', 'Conversely', and 'Furthermore'." },
            { day: 2, title: "Cue Card Structure", focus: "PPF Technique", exercise: "Structure 2-minute answers with Past, Present, Future context." },
            { day: 3, title: "Grammar Precision", focus: "Complex Tenses", exercise: "Drill Present Perfect Continuous in personal answers." },
            { day: 4, title: "Lexical Booster", focus: "Topic Collocations", exercise: "Learn 15 advanced collocations for Environment and Technology." },
            { day: 5, title: "Part 3 Abstract Analysis", focus: "Expressing Opinions", exercise: "Answer 3 analytical questions using 'It is widely argued that...'." },
            { day: 6, title: "Timed Mock Drill", focus: "Full Test Simulation", exercise: "Complete a full 15-minute mock test with continuous speech." },
            { day: 7, title: "Diagnostic Review", focus: "Self-recording analysis", exercise: "Record yourself, transcribe speech, and fix article errors." }
          ],
          examinerNotes: "Overall solid performance with strong potential to reach Band 7.5+ with targeted grammar accuracy drills."
        });
      }

      const formattedTranscript = (fullTranscript || []).map((t: any) => `${t.sender.toUpperCase()}: ${t.text}`).join("\n");

      const systemPrompt = `
You are a Senior Official IELTS Examiner evaluating a candidate's complete Speaking Test.
Evaluate strictly based on official IELTS 9-band criteria:
1. Fluency & Coherence
2. Lexical Resource
3. Grammatical Range & Accuracy
4. Pronunciation

Return a detailed JSON evaluation report.
Format strictly matching this JSON schema:
{
  "candidateName": "${candidateName || 'Candidate'}",
  "testDate": "${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}",
  "targetBand": ${targetBand},
  "overallBand": number (e.g. 6.5, 7.0, 7.5),
  "scores": {
    "fluencyScore": number,
    "lexicalScore": number,
    "grammarScore": number,
    "pronunciationScore": number,
    "overallBand": number,
    "fluencyFeedback": "detailed sentence",
    "lexicalFeedback": "detailed sentence",
    "grammarFeedback": "detailed sentence",
    "pronunciationFeedback": "detailed sentence"
  },
  "keyStrengths": ["strength 1", "strength 2", "strength 3"],
  "priorityImprovements": ["improvement 1", "improvement 2", "improvement 3"],
  "detailedErrors": [
    {
      "quote": "exact candidate mistake",
      "correction": "Band 8+ replacement",
      "category": "Grammar" | "Vocabulary" | "Fluency/Fillers" | "Pronunciation",
      "impact": "brief explanation"
    }
  ],
  "studyPlan": [
    { "day": 1, "title": "string", "focus": "string", "exercise": "string" },
    { "day": 2, "title": "string", "focus": "string", "exercise": "string" },
    { "day": 3, "title": "string", "focus": "string", "exercise": "string" },
    { "day": 4, "title": "string", "focus": "string", "exercise": "string" },
    { "day": 5, "title": "string", "focus": "string", "exercise": "string" },
    { "day": 6, "title": "string", "focus": "string", "exercise": "string" },
    { "day": 7, "title": "string", "focus": "string", "exercise": "string" }
  ],
  "examinerNotes": "Professional summary paragraph"
}
`;

      const userContent = `Candidate Transcript:\n\n${formattedTranscript}\n\nEvaluate and generate official report in JSON.`;

      const response = await ai.models.generateContent({
        model: "gemini-3.6-flash",
        contents: userContent,
        config: {
          systemInstruction: systemPrompt,
          responseMimeType: "application/json",
          temperature: 0.3,
        },
      });

      const reportJson = JSON.parse(response.text || "{}");
      res.json(reportJson);
    } catch (error: any) {
      console.error("Evaluation error:", error);
      res.status(500).json({ error: error.message });
    }
  });

  // API Route: Kokoro TTS Audio Stream Proxy
  app.post(["/api/examiner/voice", "/api/tts"], async (req, res) => {
    try {
      const { text = "Where are you from?", voice = "af_heart" } = req.body;
      
      // 1. Try FastAPI Kokoro on port 8000
      try {
        const fastApiResponse = await fetch("http://127.0.0.1:8000/tts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text, voice }),
        });
        if (fastApiResponse.ok) {
          const audioBuffer = await fastApiResponse.arrayBuffer();
          res.setHeader("Content-Type", "audio/mpeg");
          return res.send(Buffer.from(audioBuffer));
        }
      } catch (fastApiErr) {
        // FastAPI unavailable, try Kokoro container
      }

      // 2. Try Kokoro OpenAI-compatible Docker container on port 8880
      try {
        const kokoroContainerResp = await fetch("http://127.0.0.1:8880/v1/audio/speech", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            model: "kokoro",
            input: text,
            voice: voice === "british" ? "bf_emma" : "af_heart",
            response_format: "mp3"
          }),
        });
        if (kokoroContainerResp.ok) {
          const audioBuffer = await kokoroContainerResp.arrayBuffer();
          res.setHeader("Content-Type", "audio/mpeg");
          return res.send(Buffer.from(audioBuffer));
        }
      } catch (containerErr) {
        // Continue to fallback
      }

      res.status(404).json({ error: "Local Kokoro TTS not reachable on port 8000 or 8880" });
    } catch (err: any) {
      console.error("TTS Proxy error:", err);
      res.status(500).json({ error: err.message });
    }
  });

  // Vite middleware setup for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`IELTS Speaking AI Server listening on http://0.0.0.0:${PORT}`);
  });
}

startServer();
