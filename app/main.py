from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, status
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.schemas import (
    ClienteCreate,
    ClienteCreatedResponse,
    PipefyWebhookPayload,
    PipefyWebhookResponse,
)
from app.services import create_cliente, process_pipefy_card_updated


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Mundo Invest - Client Management",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.post(
    "/clientes",
    response_model=ClienteCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_cliente(payload: ClienteCreate, db: Session = Depends(get_db)) -> dict:
    cliente, pipefy_payload = create_cliente(db, payload)
    return {
        "id": cliente.id,
        "cliente_nome": cliente.cliente_nome,
        "cliente_email": cliente.cliente_email,
        "tipo_solicitacao": cliente.tipo_solicitacao,
        "valor_patrimonio": cliente.valor_patrimonio,
        "status": cliente.status,
        "prioridade": cliente.prioridade,
        "pipefy_payload": pipefy_payload,
    }


@app.post(
    "/webhooks/pipefy/card-updated",
    response_model=PipefyWebhookResponse,
)
def post_pipefy_card_updated(
    payload: PipefyWebhookPayload,
    db: Session = Depends(get_db),
) -> dict:
    return process_pipefy_card_updated(db, payload)

