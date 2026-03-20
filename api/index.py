import sys
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Add the project root to Python path so we can import from backend/
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import_error = None

try:
    from backend.server import app
except Exception as e:
    import traceback
    import_error = f"{str(e)}\n\n{traceback.format_exc()}"
    app = FastAPI()

    @app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
    async def error_handler(path: str):
        return JSONResponse(
            status_code=500,
            content={"status": "import_error", "error": import_error, "path": path}
        )

# Health check endpoint (works in both success and error cases)
@app.get("/api/health")
async def health_check():
    if import_error:
        return JSONResponse(status_code=500, content={"status": "error", "error": import_error})
    return {"status": "ok", "message": "API is running"}

handler = app
