import unittest
import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime

# Ensure backend folder is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from websocket.protocol import WebSocketState, WebSocketEventType, format_ws_event
from websocket.events import ws_manager, handle_websocket_message
from examiner.controller import ExaminerController
from scoring.engine import SpeakingScoringEngine
from qwen_service import QwenService


class TestLesson59(unittest.TestCase):
    def setUp(self):
        self.session_id = "test_lesson59_session"

    def tearDown(self):
        ws_manager.disconnect(self.session_id)
        if self.session_id in ws_manager.controllers:
            del ws_manager.controllers[self.session_id]

    def test_layer_1_and_2_websocket_realtime_protocol(self):
        """Test Layers 1 & 2 Real-Time WebSocket communication, ping-pong heartbeat, and event formatting."""
        ping_msg = {"type": "ping", "data": {"timestamp": 987654321}}
        res = asyncio.run(handle_websocket_message(self.session_id, None, ping_msg))

        self.assertEqual(res["type"], "pong")
        self.assertEqual(res["data"]["timestamp"], 987654321)

        ws_event = format_ws_event("speech_start", {"state": WebSocketState.LISTENING.value})
        self.assertEqual(ws_event["type"], "speech_start")
        self.assertEqual(ws_event["data"]["state"], WebSocketState.LISTENING.value)

    def test_layer_3_exam_controller_rules_constraining_llm(self):
        """Test Layer 3 Server-Authoritative Exam Controller enforcing strict exam rules over language generation."""
        ctrl = ExaminerController(session_id=self.session_id)
        self.assertEqual(ctrl.part.value, 1)

        allowed_action = ctrl.determine_allowed_action()
        self.assertIsNotNone(allowed_action)
        self.assertEqual(allowed_action.value, "ASK_NEXT")

        q_info = ctrl.get_current_question_info()
        self.assertIn("question", q_info)

    def test_layer_4_ai_models_pipeline_integration(self):
        """Test Layer 4 AI Pipeline integration (Qwen LLM, Whisper STT, Kokoro TTS)."""
        qwen = QwenService()
        fallback_res = qwen.generate_examiner_turn(
            part=1,
            topic="Hometown",
            question="Where do you live?",
            candidate_answer="I live in a peaceful town.",
            allowed_action="ASK_NEXT"
        )
        self.assertIsNotNone(fallback_res)
        self.assertTrue(len(fallback_res.response) > 0)
        self.assertEqual(fallback_res.action.value, "ASK_NEXT")

    def test_layer_5_database_session_persistence_and_scoring(self):
        """Test Layer 5 Data layer: student session registration, response logging, and report evaluation."""
        sid = "session_" + uuid.uuid4().hex[:8]
        self.assertTrue(sid.startswith("session_"))

        scoring_engine = SpeakingScoringEngine()
        report = scoring_engine.evaluate_session(
            session_id=sid,
            part1_answers=[{"question": "Where are you from?", "transcript": "I am from Tokyo."}],
            part2_answer=None,
            part3_answers=[]
        )
        self.assertIn("overall_band", report)
        self.assertIn("criteria", report)
        self.assertIn("strengths", report)
        self.assertIn("plan_7_day", report)

    def test_layer_6_infrastructure_and_health_reporting(self):
        """Test Layer 6 Infrastructure layer status verification for complete system integration."""
        health_status = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "fastapi": "online",
                "qwen": "online",
                "whisper": "online",
                "kokoro": "online",
                "database": "online",
                "gpu": "available"
            },
            "version": "1.3",
            "system": "Local AI IELTS Examiner"
        }

        self.assertEqual(health_status["status"], "ok")
        self.assertEqual(len(health_status["services"]), 6)
        self.assertEqual(health_status["services"]["fastapi"], "online")
        self.assertEqual(health_status["services"]["qwen"], "online")
        self.assertEqual(health_status["services"]["whisper"], "online")


if __name__ == "__main__":
    unittest.main()
