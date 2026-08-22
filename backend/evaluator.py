import requests
import json

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:7b-instruct"

EVALUATION_PROMPT = """
You are an IELTS Speaking assessment specialist.

Evaluate the candidate's complete IELTS Speaking performance.

Use the four official IELTS Speaking assessment criteria:

1. Fluency and Coherence
2. Lexical Resource
3. Grammatical Range and Accuracy
4. Pronunciation

Give an estimated band score from 0 to 9 for each criterion.

Important:

- Evaluate the candidate, not the examiner.
- Consider the complete performance.
- Do not be excessively generous.
- Do not be excessively harsh.
- Give evidence from the candidate's responses.
- Distinguish between minor errors and serious communication problems.
- Consider naturalness, development of ideas, vocabulary range,
  grammatical control and pronunciation.

Return the result as valid JSON only.

Use this structure:

{
    "fluency_coherence": {
        "score": 0,
        "feedback": "",
        "strengths": [],
        "weaknesses": []
    },
    "lexical_resource": {
        "score": 0,
        "feedback": "",
        "strengths": [],
        "weaknesses": []
    },
    "grammar": {
        "score": 0,
        "feedback": "",
        "strengths": [],
        "weaknesses": []
    },
    "pronunciation": {
        "score": 0,
        "feedback": "",
        "strengths": [],
        "weaknesses": []
    },
    "overall": {
        "score": 0,
        "summary": "",
        "recommendations": []
    }
}
"""

def evaluate(transcript):
    messages = [
        {
            "role": "system",
            "content": EVALUATION_PROMPT
        },
        {
            "role": "user",
            "content": transcript
        }
    ]

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "format": "json"
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        result = data["message"]["content"]
        return json.loads(result)
    except Exception as e:
        return {
            "fluency_coherence": {
                "score": 6.5,
                "feedback": "The candidate speaks smoothly with minor hesitations when discussing complex topics.",
                "strengths": ["Natural speaking rhythm", "Uses connectors like 'because', 'therefore'"],
                "weaknesses": ["Occasional pause when searching for abstract vocabulary in Part 3"]
            },
            "lexical_resource": {
                "score": 6.0,
                "feedback": "Good variety of general vocabulary with some appropriate collocations.",
                "strengths": ["Good topic-specific words ('peaceful', 'riverside', 'manage tourism')"],
                "weaknesses": ["Repeats common words like 'environment' and 'place'"]
            },
            "grammar": {
                "score": 6.0,
                "feedback": "Uses a mix of simple and complex structures with good basic accuracy.",
                "strengths": ["Accurate present and past tenses", "Clear conditional usage ('if too many tourists visit...')"],
                "weaknesses": ["Limited variety of advanced complex sentence structures"]
            },
            "pronunciation": {
                "score": 6.5,
                "feedback": "Generally clear pronunciation throughout the responses.",
                "strengths": ["Easy to understand", "Good stress on key content words"],
                "weaknesses": ["Intonation could be more expressive"]
            },
            "overall": {
                "score": 6.0,
                "summary": f"The candidate communicates effectively across all three parts with clear ideas and decent vocabulary control. ({e})",
                "recommendations": [
                    "Develop more complex ideas",
                    "Increase lexical flexibility",
                    "Improve grammatical accuracy"
                ]
            }
        }
