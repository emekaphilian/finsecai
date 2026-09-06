import httpx
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.core.authorization import resolve_tenant_context
from app.db.models import Incident, User
from app.db.session import SessionLocal
from app.services import llm_providers

router = APIRouter(tags=["copilot"])


def _build_context(db: Session, tenant_id: str) -> str:
    incidents = (
        db.query(Incident)
        .filter(Incident.tenant_id == tenant_id)
        .order_by(Incident.risk_score.desc())
        .limit(15)
        .all()
    )
    lines = [
        f"- {i.id}: user {i.user_id}, ${i.amount:,.0f}, risk {i.risk_score:.2f}, "
        f"flags: {i.governance_flags or 'none'}"
        for i in incidents
    ]
    return "Top incidents for this tenant:\n" + "\n".join(lines) if lines else "No incidents loaded yet."


@router.get("/copilot/status")
async def copilot_status():
    if settings.cohere_api_key:
        available, detail = await llm_providers.readiness()
        if available:
            return {
                "provider": "Cohere",
                "mode": "live",
            }
        return {
            "provider": None,
            "mode": "unavailable",
            "detail": detail,
        }

    try:
        tags_url = settings.local_llm_url.replace(
            "/api/generate",
            "/api/tags",
        )

        async with httpx.AsyncClient(timeout=2) as client:
            resp = await client.get(tags_url)

            if resp.status_code == 200:
                return {
                    "provider": f"Ollama ({settings.local_llm_model})",
                    "mode": "live",
                }

    except Exception:
        pass

    return {
        "provider": None,
        "mode": "templated_fallback",
    }


@router.websocket("/ws/copilot")
async def copilot_ws(
    websocket: WebSocket,
    token: str = Query(...),
    tenant_id: str | None = Query(None),
):
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4401)
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == payload.get("sub")).first()
        if user is None or user.status != "ACTIVE":
            await websocket.close(code=4401)
            return
        context = resolve_tenant_context(db, user, tenant_id)
        if context.tenant_id is None:
            await websocket.close(code=4403)
            return
        await websocket.accept()
        while True:
            question = await websocket.receive_text()
            incident_context = _build_context(db, context.tenant_id)
            prompt = f"{incident_context}\n\nAnalyst question: {question}\n\nAnswer using only the data above."

            async for chunk in llm_providers.stream(prompt):
                await websocket.send_text(chunk)
            await websocket.send_text("[[END]]")
    except WebSocketDisconnect:
        pass
    finally:
        db.close()
