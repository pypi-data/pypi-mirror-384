from fastapi import APIRouter
from fastapi.responses import JSONResponse


import os
import psutil
from typing import Dict, Union
uvicorn_router = APIRouter()


def get_uvicorn_worker_count() -> Dict[str, Union[int, str]]:
    """
    Detect the number of running Uvicorn workers and return a dict containing
    both the count and the source of information ("env", "psutil", or "fallback").

    Returns:
        Dict[str, Union[int, str]]: {
            "uvicorn_worker_count": <int>,
            "source": <str>
        }
    """
    # 1. Check environment variable
    if "UVICORN_WORKERS" in os.environ:
        return {
            "uvicorn_worker_count": int(os.environ["UVICORN_WORKERS"]),
            "source": "env",
        }

    # 2. Auto-detect via psutil
    try:
        current_pid = os.getpid()
        parent = psutil.Process(current_pid).parent()

        siblings = [
            p for p in parent.children(recursive=False)
            if "uvicorn" in " ".join(p.cmdline())
        ]
        return {
            "uvicorn_worker_count": max(1, len(siblings)),
            "source": "psutil",
        }
    except Exception as exc:
        # 3. Fallback to 1 if detection fails
        return {
            "uvicorn_worker_count": 1,
            "source": "fallback",
            "error": "Failed to detect Uvicorn workers",
            "exception": str(exc)
        }


@uvicorn_router.get("/uvicorn/workers", name="get_uvicorn_worker_count")
async def get_workers():
    """
    Return the current number of active Uvicorn workers
    along with the detection method used.
    """
    data = get_uvicorn_worker_count()
    return JSONResponse(content=data)