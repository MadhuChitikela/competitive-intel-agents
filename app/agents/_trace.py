"""Direct bridge to P1's trace DB.

We bypass P1's Tracer decorator here because LangGraph nodes take a
state dict, not a user_input string. Instead, each node calls
log_agent_run() at the end so P1's MCP tools can query these runs.
"""
from datetime import datetime, timezone
import json
import subprocess
import uuid

from app.config import settings
import app.db
app.db.DB_PATH = settings.db_path
from app.db import get_db, init_db  # P1's DB layer

# Ensure tables exist in target database
try:
    init_db()
except Exception:
    pass


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return ""


def log_agent_run(
    agent_id: str,
    input_str: str,
    output_str: str,
    tool_calls: list[dict] | None = None,
    latency_ms: int = 0,
) -> str:
    """Write a trace to P1's DB. Returns trace_id."""
    trace_id = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            "INSERT INTO traces VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                trace_id,
                agent_id,
                input_str,
                output_str,
                json.dumps(tool_calls or []),
                latency_ms,
                0.0,
                _git_sha(),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
    return trace_id
