# src/uas_messenger/subscriber.py
# version 1.0.0
# The Pennsylvania State University Unmanned Aerial Systems Club
# Theodore Tasman
# Created: 2025-10-14
# License: GPL-3.0

import asyncio
import zmq
import json
from uas_messenger.message import Message
from typing import Callable, List, Optional

class Subscriber:
    def __init__(self, host: str, port: int, topics: List[str] = [], callback: Optional[Callable[[Message], None]] = None, wait_time: float = 0.1):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(f"tcp://{host}:{port}")
        if len(topics) == 0:
            self.socket.setsockopt_string(zmq.SUBSCRIBE, "")
        else:
            for topic in topics:
                self.socket.setsockopt_string(zmq.SUBSCRIBE, topic)
        self.running = False
        self.callback = callback
        self.wait_time = wait_time
        self.running_task = None

    def recv(self) -> Optional[Message]:
        try:
            parts = self.socket.recv_multipart(zmq.NOBLOCK)
            topic = parts[0].decode("utf-8")

            if len(parts) == 2:
                # JSON-only message (header-only)
                header = json.loads(parts[1].decode("utf-8"))
                payload = b""
            elif len(parts) == 3:
                # Binary message (header + payload)
                header = json.loads(parts[1].decode("utf-8"))
                payload = parts[2]
            else:
                print(f"[Subscriber] Warning: unexpected message format ({len(parts)} parts)")
                return None
            
            return Message(topic=topic, header=header, payload=payload)
        
        except zmq.Again:
            return None
        
        except Exception as e:
            print(f"[Subscriber] Error receiving message: {e}") 
            return None
    
    async def close(self):
        self.running = False
        await self.running_task if self.running_task else None
        self.running_task = None
        self.socket.close()
        self.context.term()

    def start(self):
        self.running_task = asyncio.create_task(self.run())
    
    async def run(self):
        self.running = True
        while self.running:
            message = self.recv()
            if message and self.callback:
                self.callback(message)
            await asyncio.sleep(self.wait_time)
