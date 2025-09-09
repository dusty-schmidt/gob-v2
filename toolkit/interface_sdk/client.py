import asyncio
import json
import os
import uuid
from dataclasses import asdict
from typing import AsyncIterator

import websockets  # type: ignore

from toolkit.events import new_event, from_json


def _with_token(url: str, token: str | None) -> str:
    return f"{url}{'&' if '?' in url else '?'}token={token}" if token else url


class InterfaceClient:
    def __init__(self, interface_id: str | None = None, nexus_url: str | None = None, session_id: str | None = None, token: str | None = None):
        self.interface_id = interface_id or os.getenv("INTERFACE_ID", "nano")
        self.session_id = session_id or str(uuid.uuid4())
        self.nexus_url = nexus_url or os.getenv("NEXUS_URL", "ws://127.0.0.1:7000")
        self.token = token or os.getenv("NEXUS_TOKEN")
        self.ws: websockets.WebSocketClientProtocol | None = None

    async def connect(self):
        self.ws = await websockets.connect(_with_token(self.nexus_url, self.token))

    async def close(self):
        if self.ws:
            await self.ws.close()

    async def publish_input(self, text: str, topic: str = "chat.input"):
        assert self.ws is not None, "Not connected"
        ev = new_event(
            type="interface.input",
            source=f"interface:{self.interface_id}",
            topic=topic,
            payload={"text": text},
            meta={},
            session_id=self.session_id,
        )
        await self.ws.send(json.dumps(asdict(ev)))

    async def send_control(self, control: str, payload: dict | None = None):
        assert self.ws is not None, "Not connected"
        ev = new_event(
            type="interface.input",
            source=f"interface:{self.interface_id}",
            topic=f"control.{control}",
            payload=payload or {},
            meta={},
            session_id=self.session_id,
        )
        await self.ws.send(json.dumps(asdict(ev)))

    async def recv_outputs(self) -> AsyncIterator:
        assert self.ws is not None, "Not connected"
        async for raw in self.ws:
            try:
                ev = from_json(raw)
            except Exception:
                continue
            if ev.type == "interface.output" and ev.meta.get("session_id") == self.session_id:
                yield ev
