# run_demo.py
import asyncio
import threading
import httpx
import uvicorn
import time
import os
from typing import Any, Dict, List
INF_TIMEOUT = httpx.Timeout(connect=5000.0, read=5000.0, write=5000.0, pool=5000.0)

# -------- Optional helper (same wrapping UX you had) --------
import textwrap
def print_wrapped(text: str, width: int = 140) -> None:
    for line in text.splitlines() or [""]:
        print(textwrap.fill(line, width=width) if line.strip() else "")


# -------- Uvicorn server in a background thread ------------
def _serve():
    # NOTE: avoid --reload here for easier debugging & clean single process
    uvicorn.run("app.api:app", host="127.0.0.1", port=8000, log_level="info")


def start_server_in_background() -> threading.Thread:
    t = threading.Thread(target=_serve, daemon=True)
    t.start()
    # Give the server a moment to boot (or poll /health if you prefer)
    time.sleep(0.8)
    return t


# ------------------ HTTP client loop -----------------------
BASE = "http://127.0.0.1:8000"


async def run_client(initial_input: str = "Hello, world!", *, initial_agent: str | None = None) -> None:
    async with httpx.AsyncClient(base_url=BASE, timeout=60.0) as client:
        # Start a new run
        payload: Dict[str, Any] = {"input": initial_input}
        if initial_agent:
            payload["initial_agent"] = initial_agent  # optional, your API has a default

        r = await client.post("/v1/new", json=payload, timeout=INF_TIMEOUT)
        r.raise_for_status()
        new_resp = r.json()

        run_id = new_resp["run_id"]
        chat = new_resp.get("chat", None)

        # Conversation loop (WAIT_HUMAN)
        while chat is not None:
            print("============== AI ====================")
            msg = chat[-1].get("msg", "--")
            print_wrapped(msg)
            print("======================================")

            user_input = input(">> ")
            # Inject human input
            chat = {
                "type": "text",
                "msg": user_input,
                "from": "user"
            }
            r = await client.post(f"/v1/{run_id}/chat", json={"payload": {"chat": chat}}, timeout=INF_TIMEOUT)
            r.raise_for_status()
            chat = r.json()['chat']


        # Fetch updated state
        r = await client.get(f"/v1/{run_id}")
        r.raise_for_status()
        state = r.json()

        # Final output (mirrors your direct-pipeline prints)
        print_wrapped("============== FINAL OUTPUT ====================")
        ctx = state.get("agents_context", {}).get("intentRouter", {})
        print_wrapped(ctx.get("task_definition", ""))
        print_wrapped(ctx.get("data_type", ""))
        print_wrapped("Classes:")
        classes_str = ctx.get("classes", "[]")
        try:
            classes: List[Dict[str, Any]] = eval(classes_str) if isinstance(classes_str, str) else classes_str  # keep your original behavior
            for cls in classes or []:
                name = cls.get("name", "")
                definition = cls.get("definition", "")
                print_wrapped(f"{name}: {definition}")
        except Exception as e:
            print_wrapped(f"[warn] Could not parse classes: {e}")
            print_wrapped(str(classes_str))

# ---------------------- __main__ ---------------------------
if __name__ == "__main__":
    # 1) Start FastAPI (app.api:app) under Uvicorn in-process
    start_server_in_background()

    # 2) Optionally confirm server is healthy
    try:
        import requests
        requests.get(f"{BASE}/health", timeout=2)
    except Exception:
        # Not fatal—client will still try; you can add retries here if you want
        pass

    # 3) Run the async HTTP client flow
    asyncio.run(run_client(initial_input="Hello, world!"))
