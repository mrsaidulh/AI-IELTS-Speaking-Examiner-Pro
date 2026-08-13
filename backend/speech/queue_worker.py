import asyncio
import logging
from typing import Dict, Any, Callable, Optional
from speech.metrics import PipelineLatencyTracker

logger = logging.getLogger("speech_queue_worker")


class RealtimeVoiceQueueWorker:
    """
    Asynchronous queue worker for non-blocking real-time voice processing pipeline.
    Prevents WebSocket stream blockage while Whisper, Qwen, and Kokoro process audio.
    """
    def __init__(self, max_queue_size: int = 10):
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.worker_task: Optional[asyncio.Task] = None
        self.is_running = False

    def start(self, process_callback: Callable[[Dict[str, Any]], Any]):
        if not self.is_running:
            self.is_running = True
            self.worker_task = asyncio.create_task(self._worker_loop(process_callback))
            logger.info("RealtimeVoiceQueueWorker started.")

    async def stop(self):
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
            self.worker_task = None
            logger.info("RealtimeVoiceQueueWorker stopped.")

    async def enqueue_utterance(self, session_id: str, pcm_data: bytes, metadata: Dict[str, Any]) -> bool:
        """Puts a finalized utterance task into the async queue with capacity check."""
        if self.queue.full():
            logger.warning(f"Audio queue full! Dropping utterance for session {session_id}")
            return False
        
        await self.queue.put({
            "session_id": session_id,
            "pcm_data": pcm_data,
            "metadata": metadata
        })
        return True

    async def _worker_loop(self, process_callback: Callable[[Dict[str, Any]], Any]):
        while self.is_running:
            try:
                item = await self.queue.get()
                tracker = PipelineLatencyTracker()
                tracker.start_stage("total")
                
                try:
                    await process_callback(item, tracker)
                except Exception as e:
                    logger.error(f"Error processing audio utterance task: {e}", exc_info=True)
                finally:
                    tracker.end_stage("total")
                    logger.info(tracker.log_summary())
                    self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue worker error: {e}")
