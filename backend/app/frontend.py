from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles


FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


class ImmutableStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response


def mount_frontend(app: FastAPI) -> None:
    app.mount(
        "/assets",
        ImmutableStaticFiles(directory=FRONTEND_DIST / "assets", check_dir=False),
        name="frontend-assets",
    )

    async def frontend_shell(full_path: str = ""):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")

        requested_file = FRONTEND_DIST / full_path
        if full_path and requested_file.is_file() and requested_file.parent == FRONTEND_DIST:
            return FileResponse(requested_file)

        index_file = FRONTEND_DIST / "index.html"
        if not index_file.is_file():
            raise HTTPException(status_code=503, detail="Frontend build is unavailable")
        return FileResponse(
            index_file,
            media_type="text/html",
            headers={"Cache-Control": "no-cache"},
        )

    app.add_api_route("/", frontend_shell, include_in_schema=False)
    app.add_api_route("/{full_path:path}", frontend_shell, include_in_schema=False)
