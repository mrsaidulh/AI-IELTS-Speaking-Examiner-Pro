from examiner.questions import PART_1_QUESTIONS
from examiner.cue_cards import CUE_CARDS
from examiner.part3_topics import PART3_TOPICS
import random


class QuestionManager:

    def __init__(self, questions=None, cue_cards=None, part3_topics=None):
        self.questions = questions if questions is not None else PART_1_QUESTIONS
        self.cue_cards = cue_cards if cue_cards is not None else CUE_CARDS
        self.part3_topics = part3_topics if part3_topics is not None else PART3_TOPICS
        self.topic_index = 0
        self.question_index = 0
        self.used_cue_cards = set()

    def get_part3_question(self, topic_key="education"):
        topic_info = self.part3_topics.get(topic_key, self.part3_topics.get("education"))
        if topic_info and "questions" in topic_info:
            return topic_info["questions"][0]
        return {"type": "general", "question": "Why is this topic considered important in society today?"}

    def get_cue_card(self):
        available = [c for c in self.cue_cards if c["id"] not in self.used_cue_cards]
        if not available:
            self.used_cue_cards.clear()
            available = self.cue_cards
        card = random.choice(available)
        self.used_cue_cards.add(card["id"])
        return card

    def get_next_question(self):
        if self.topic_index >= len(self.questions):
            return None

        item = self.questions[self.topic_index]

        # Case 1: Item is a topic group with a "questions" list
        if isinstance(item, dict) and "questions" in item and isinstance(item["questions"], list):
            questions_list = item["questions"]
            if self.question_index >= len(questions_list):
                self.topic_index += 1
                self.question_index = 0
                return self.get_next_question()

            question_text = questions_list[self.question_index]
            self.question_index += 1
            return {
                "topic": item.get("topic", "general"),
                "question": question_text
            }

        # Case 2: Item is a flat question object (e.g. {"id": ..., "topic": ..., "question": ...})
        elif isinstance(item, dict) and "question" in item:
            self.topic_index += 1
            return {
                "topic": item.get("topic", "general"),
                "question": item.get("question")
            }

        # Case 3: Item is a plain string
        elif isinstance(item, str):
            self.topic_index += 1
            return {
                "topic": "general",
                "question": item
            }

        self.topic_index += 1
        return None

    def reset(self):
        self.topic_index = 0
        self.question_index = 0
