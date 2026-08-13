from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from api.core.constants import TEMPLATES_DIR
from api.core.security import issue_token

router = APIRouter()
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    """A fresh token per page render — the page is the only way to get one."""
    return templates.TemplateResponse(
        request, "index.html", {"chat_token": issue_token()}
    )
