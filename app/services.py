from decimal import Decimal
from typing import Tuple

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Cliente, ProcessedPipefyEvent
from app.pipefy_client import pipefy_client
from app.schemas import ClienteCreate, PipefyWebhookPayload


STATUS_AGUARDANDO_ANALISE = "Aguardando Análise"
STATUS_PROCESSADO = "Processado"
PRIORIDADE_ALTA = "prioridade_alta"
PRIORIDADE_NORMAL = "prioridade_normal"
PATRIMONIO_PRIORIDADE_ALTA = Decimal("200000")


def create_cliente(db: Session, payload: ClienteCreate) -> Tuple[Cliente, dict]:
    existing = db.scalar(
        select(Cliente).where(Cliente.cliente_email == str(payload.cliente_email))
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cliente ja cadastrado para este e-mail.",
        )

    cliente = Cliente(
        cliente_nome=payload.cliente_nome,
        cliente_email=str(payload.cliente_email),
        tipo_solicitacao=payload.tipo_solicitacao,
        valor_patrimonio=payload.valor_patrimonio,
        status=STATUS_AGUARDANDO_ANALISE,
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)

    pipefy_payload = pipefy_client.build_create_card_payload(
        cliente_nome=cliente.cliente_nome,
        cliente_email=cliente.cliente_email,
        tipo_solicitacao=cliente.tipo_solicitacao,
        valor_patrimonio=Decimal(cliente.valor_patrimonio),
    )
    return cliente, pipefy_payload


def process_pipefy_card_updated(db: Session, payload: PipefyWebhookPayload) -> dict:
    existing_event = db.get(ProcessedPipefyEvent, payload.event_id)
    if existing_event:
        cliente = db.scalar(
            select(Cliente).where(Cliente.cliente_email == str(payload.cliente_email))
        )
        return {
            "event_id": payload.event_id,
            "card_id": payload.card_id,
            "cliente_email": str(payload.cliente_email),
            "status": cliente.status if cliente else STATUS_PROCESSADO,
            "prioridade": cliente.prioridade if cliente else None,
            "duplicate": True,
            "pipefy_payload": None,
        }

    cliente = db.scalar(
        select(Cliente).where(Cliente.cliente_email == str(payload.cliente_email))
    )
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente nao encontrado para o e-mail informado.",
        )

    prioridade = calculate_prioridade(Decimal(cliente.valor_patrimonio))
    pipefy_payload = pipefy_client.build_update_card_fields_payload(
        card_id=payload.card_id,
        status=STATUS_PROCESSADO,
        prioridade=prioridade,
    )

    cliente.status = STATUS_PROCESSADO
    cliente.prioridade = prioridade
    cliente.pipefy_card_id = payload.card_id
    db.add(
        ProcessedPipefyEvent(
            event_id=payload.event_id,
            card_id=payload.card_id,
            cliente_email=str(payload.cliente_email),
            event_timestamp=payload.timestamp,
        )
    )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return process_pipefy_card_updated(db, payload)

    db.refresh(cliente)
    return {
        "event_id": payload.event_id,
        "card_id": payload.card_id,
        "cliente_email": cliente.cliente_email,
        "status": cliente.status,
        "prioridade": cliente.prioridade,
        "duplicate": False,
        "pipefy_payload": pipefy_payload,
    }


def calculate_prioridade(valor_patrimonio: Decimal) -> str:
    if valor_patrimonio >= PATRIMONIO_PRIORIDADE_ALTA:
        return PRIORIDADE_ALTA
    return PRIORIDADE_NORMAL
