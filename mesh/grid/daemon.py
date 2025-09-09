# File: mesh/grid/daemon.py
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from .registry import get_agent

app = FastAPI(title="Agent Core Service")

class AgentMessage(BaseModel):
    agent_id: str
    timestamp: str
    state: dict = {}
    action: dict
    feedback: dict = {}

@app.post("/act")
def act(message: AgentMessage):
    # Look up the right agent by ID or role
    agent = get_agent(message.agent_id)
    response_action = agent.decide(message)
    return AgentMessage(
        agent_id=message.agent_id,
        timestamp=datetime.utcnow().isoformat(),
        state=message.state,
        action=response_action,
        feedback={}
    )
