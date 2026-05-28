from sqlalchemy import Column, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cliente_nome = Column(String(160), nullable=False)
    cliente_email = Column(String(255), nullable=False, unique=True, index=True)
    tipo_solicitacao = Column(String(160), nullable=False)
    valor_patrimonio = Column(Numeric(14, 2), nullable=False)
    status = Column(String(80), nullable=False, default="Aguardando Análise")
    prioridade = Column(String(80), nullable=True)
    pipefy_card_id = Column(String(80), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ProcessedPipefyEvent(Base):
    __tablename__ = "processed_pipefy_events"

    event_id = Column(String(120), primary_key=True, index=True)
    card_id = Column(String(120), nullable=False)
    cliente_email = Column(String(255), nullable=False, index=True)
    event_timestamp = Column(DateTime(timezone=True), nullable=False)
    processed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
