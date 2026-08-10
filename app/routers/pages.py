from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.security import issue_token

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """A fresh token per page render — the page is the only way to get one."""
    return templates.TemplateResponse(
        request, "index.html", {"chat_token": issue_token()}
    )
