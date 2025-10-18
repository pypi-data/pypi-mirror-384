# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------
import asyncio
import atexit
import os
import threading
import time
from typing import Dict, List

from ibm_watsonx_gov.clients.segment_client import SegmentClient
from ibm_watsonx_gov.utils.async_util import (gather_with_concurrency,
                                              run_in_event_loop)
from ibm_watsonx_gov.utils.gov_sdk_logger import GovSDKLogger

logger = GovSDKLogger.get_logger(__name__)

SEGMENT_BATCH_LIMIT = 10
SEGMENT_BATCH_INTERVAL = 5  # seconds


class SegmentBatchManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, api_client=None):
        """Ensure singleton instance across evaluators."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize(api_client)
            return cls._instance

    def _initialize(self, api_client=None):
        self.api_client = api_client
        self.queue: asyncio.Queue[Dict] | None = None
        self._stop_event = asyncio.Event()
        self._thread = None
        self._thread_loop: asyncio.AbstractEventLoop | None = None
        # Start a background worker thread
        self._start_background_worker()

        # Auto-stop on process exit
        atexit.register(self._shutdown)

    def _start_background_worker(self):
        """
        Start a background thread with its own event loop to batch and send events.
        This allows non-blocking event tracking from the other event tasks.
        """

        def runner():
            """
            Start a new event loop in a separate thread.
            """
            loop = asyncio.new_event_loop()
            self._thread_loop = loop
            asyncio.set_event_loop(loop)

            self.queue = asyncio.Queue()
            self._stop_event = asyncio.Event()

            # Run the worker until stopped
            loop.run_until_complete(self.worker())

        # Start the thread as a daemon
        self._thread = threading.Thread(target=runner, daemon=True)
        self._thread.start()

    async def track_event(self, event: Dict):
        """Add event to queue."""

        if os.getenv("WATSONX_SERVER") in ["WXO", "WXAI", "WXGOV"]:
            return

        if self.api_client is None:
            return

        if self.api_client.is_cpd:
            return

        if not hasattr(self.api_client, "wos_client"):
            return

        if not hasattr(self.api_client.wos_client, "service_instance_id"):
            return

        data = {
            "event": "API Call",
            "properties": {
                "productCodeType": "WWPC",
                "ut30": "30A5Q",
                "productTitle": "watsonx governance",
                "productCode": "WW0170",
                "custom.triggered_by": "watsonx gov sdk",
                "region": self.api_client.credentials.region or "us-south",
                "instanceID": self.api_client.wos_client.service_instance_id,
                "productPlan": self.api_client.wos_client.plan_name,
                **event
            },
            "integrations": {
                "Amplitude": {
                    "groups": {
                        "Instance": self.api_client.wos_client.service_instance_id
                    }
                }
            }
        }

        # Thread-safe submission to background loop
        if self._thread_loop and self.queue:
            fut = asyncio.run_coroutine_threadsafe(
                self.queue.put(data), self._thread_loop
            )
            await asyncio.wrap_future(fut)

    def _shutdown(self):
        """Stop worker at process exit."""
        if self._thread_loop and self._stop_event:
            self._thread_loop.call_soon_threadsafe(self._stop_event.set)

    async def worker(self):
        """Background loop: batch and send events."""
        buffer: List[Dict] = []
        last_flush = time.time()

        while True:
            # Exit when stop event set and queue empty
            if self._stop_event.is_set() and self.queue.empty():
                break

            try:
                event = await self.queue.get()
                buffer.append(event)
            except asyncio.TimeoutError:
                pass  # loop back and check stop_event

            if buffer and (
                len(buffer) >= SEGMENT_BATCH_LIMIT
                or time.time() - last_flush >= SEGMENT_BATCH_INTERVAL
            ):
                success = await self._flush_async(buffer)
                if success:
                    buffer.clear()
                    last_flush = time.time()

        if buffer:
            success = await self._flush_async(buffer)
            if success:
                buffer.clear()

    async def _flush_async(self, events: List[Dict]):
        if not events:
            return True
        logger.info(f"Flushing {len(events)} events")
        segment_client = SegmentClient(self.api_client.wos_client)
        return await segment_client.trigger_segment_endpoint(segment_data=events)
