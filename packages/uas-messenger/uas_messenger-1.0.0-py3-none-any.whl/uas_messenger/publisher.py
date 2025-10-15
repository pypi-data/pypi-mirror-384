# src/uas_messenger/publisher.py
# version 1.0.0
# The Pennsylvania State University Unmanned Aerial Systems Club
# Theodore Tasman
# Created: 2025-10-14
# License: GPL-3.0

import asyncio
from typing import Optional
import zmq
import json

from uas_messenger.message import Message

class Publisher:
    def __init__(self, host: str, port: int, outbound_queue: Optional[asyncio.Queue] = None, wait_time: float = 0.1):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(f"tcp://{host}:{port}")
        self.running = False
        self.running_task = None
        self.outbound_queue = outbound_queue
        self.wait_time = wait_time

    def send(self, message: Message):
        try:
            topic = message.topic.encode("utf-8")
            header = json.dumps(message.header).encode("utf-8")

            if message.payload:
                # Binary message
                self.socket.send_multipart([topic, header, message.payload])
            else:
                # JSON-only message
                self.socket.send_multipart([topic, header])
        except Exception as e:
            print(f"[Publisher] Error sending message: {e}")

    async def close(self):
        self.running = False
        await self.running_task if self.running_task else None
        self.running_task = None
        self.socket.close()
        self.context.term()
    
    def start(self):
        if self.running_task:
            raise RuntimeError("Publisher is already running")
        self.running_task = asyncio.create_task(self.run())

    async def run(self):
        if self.outbound_queue is None:
            raise RuntimeError("No outbound queue provided")
        self.running = True
        while self.running:
            try:
                message = self.outbound_queue.get_nowait()
                self.send(message)
            except asyncio.QueueEmpty:
                await asyncio.sleep(self.wait_time)
