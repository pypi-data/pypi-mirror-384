# src/uas_messenger/message.py
# version 1.0.0
# The Pennsylvania State University Unmanned Aerial Systems Club
# Theodore Tasman
# Created: 2025-10-14
# License: GPL-3.0

from pydantic import BaseModel

class Message(BaseModel):
    topic: str
    header: dict
    payload: bytes = b""