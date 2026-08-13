"""Routing only: paths and methods onto the code that handles them, plus the
dependencies each route needs. Anything a request *does* belongs in a service.
"""
from fastapi import APIRouter, Depends, Response

from api.core.schemas import ChatRequest
from api.core.security import verify_token
from api.services.chat import respond

router = APIRouter(prefix="/api")


@router.post("/chat", dependencies=[Depends(verify_token)])
async def chat(request: ChatRequest) -> Response:
    return await respond(request)
