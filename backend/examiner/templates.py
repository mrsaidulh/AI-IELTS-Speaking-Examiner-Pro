QUESTION_TEMPLATES = {
    "cause": [
        "Why do you think {topic} has become so significant recently?",
        "What are the main underlying causes for this trend in {topic}?"
    ],
    "effect": [
        "What impact does {topic} have on society as a whole?",
        "How does {topic} affect people's daily choices and habits?"
    ],
    "comparison": [
        "How is {topic} different today compared to how it was in the past?",
        "Do you think people view {topic} differently across different generations?"
    ],
    "future": [
        "How might {topic} evolve over the next twenty years?",
        "What changes do you anticipate regarding {topic} in the future?"
    ],
    "advantage": [
        "What are the primary benefits associated with {topic}?",
        "Why do many people view {topic} as a positive development?"
    ],
    "disadvantage": [
        "What drawbacks or challenges are associated with {topic}?",
        "In what ways could {topic} lead to negative consequences?"
    ],
    "solution": [
        "What measures could be taken to address challenges related to {topic}?",
        "How can governments or institutions improve {topic} for everyone?"
    ]
}

TRANSITIONS = {
    "general": ["cause", "opinion", "comparison", "advantage"],
    "cause": ["effect", "solution", "opinion"],
    "effect": ["solution", "comparison", "disadvantage"],
    "comparison": ["future", "opinion", "advantage"],
    "advantage": ["disadvantage", "comparison", "future"],
    "disadvantage": ["solution", "comparison"],
    "solution": ["future", "opinion"],
    "future": ["opinion", "comparison"]
}
