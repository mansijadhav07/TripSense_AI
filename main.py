"""Root-level app entry point for uvicorn.

This keeps the documented command `python3 -m uvicorn main:app ...` working even
when the user launches it from the repository root instead of `apps/api`.
"""

from apps.api.main import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
