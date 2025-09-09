import asyncio
import os
import random
from dataclasses import asdict
import websockets  # type: ignore
from pathlib import Path
import sys

def _add_root(marker="toolkit"):
    here=Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent/marker).exists() and str(parent) not in sys.path: sys.path.append(str(parent)); return
_add_root()

from toolkit.events import new_event
from toolkit.style import stylize

def _with_token(url, token):
    return f"{url}{'&' if '?' in url else '?'}token={token}" if token else url

async def main():
    url=os.getenv("NEXUS_URL","ws://127.0.0.1:7000"); token=os.getenv("NEXUS_TOKEN")
    tick_ms=int(os.getenv("GRID_TICK_MS","1000")); rng=random.Random(os.getenv("GRID_SEED")); n=0
    async with websockets.connect(_with_token(url, token)) as ws:
        print(stylize(f"Grid ticker online @ {tick_ms}ms", channel="grid"))
        while True:
            n+=1
            ev=new_event("grid.tick","grid:loop","tick",{"n":n,"rand":rng.random()}, meta={"grid":"main"})
            await ws.send(__import__("json").dumps(asdict(ev)))
            await asyncio.sleep(tick_ms/1000)

if __name__=="__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass
