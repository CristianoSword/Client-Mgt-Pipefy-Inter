from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClienteCreate(BaseModel):
    cliente_nome: str = Field(..., min_length=1)
    cliente_email: EmailStr
    tipo_solicitacao: str = Field(..., min_length=1)
    valor_patrimonio: Decimal = Field(..., ge=Decimal("0"))


class ClienteCreatedResponse(BaseModel):
    id: int
    cliente_nome: str
    cliente_email: EmailStr
    tipo_solicitacao: str
    valor_patrimonio: Decimal
    status: str
    prioridade: Optional[str] = None
    pipefy_payload: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class PipefyWebhookPayload(BaseModel):
    event_id: str = Field(..., min_length=1)
    card_id: str = Field(..., min_length=1)
    cliente_email: EmailStr
    timestamp: datetime


class PipefyWebhookResponse(BaseModel):
    event_id: str
    card_id: str
    cliente_email: EmailStr
    status: str
    prioridade: Optional[str] = None
    duplicate: bool
    pipefy_payload: Optional[Dict[str, Any]] = None

