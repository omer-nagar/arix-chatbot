# app/api_builder.py
from typing import Any, Callable, Dict, List
from fastapi import FastAPI

ALLOWED = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


def _normalize_methods(spec: Dict[str, Any]) -> List[str]:
    methods = spec.get("methods") or [spec.get("method", "GET")]
    methods = [m.upper() for m in (methods if isinstance(methods, (list, tuple)) else [methods])]
    for m in methods:
        if m not in ALLOWED:
            raise ValueError(f"Unsupported HTTP method: {m}")
    return methods


def build_app(routes: List[Dict[str, Any]], *, title: str = "Agent API") -> FastAPI:
    """
    routes = [
      {"method": "POST", "path": "/runs", "func": start_run},
      {"method": "GET",  "path": "/runs/{run_id}/state", "func": get_state},
      {"method": "POST", "path": "/runs/{run_id}/human", "func": inject_human},
      {"method": "POST", "path": "/runs/{run_id}/resume", "func": resume},
    ]
    """
    app = FastAPI(title=title)
    for spec in routes:
        path = spec["path"]
        func: Callable[..., Any] = spec["func"]
        for m in _normalize_methods(spec):
            if m == "GET":
                app.get(path)(func)
            elif m == "POST":
                app.post(path)(func)
            elif m == "PUT":
                app.put(path)(func)
            elif m == "PATCH":
                app.patch(path)(func)
            elif m == "DELETE":
                app.delete(path)(func)
            elif m == "HEAD":
                app.head(path)(func)
            elif m == "OPTIONS":
                app.options(path)(func)
    return app
