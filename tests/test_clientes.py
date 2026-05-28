from decimal import Decimal

from sqlalchemy import func, select

from app.models import Cliente, ProcessedPipefyEvent


def cliente_payload(valor_patrimonio=250000):
    return {
        "cliente_nome": "Joao Silva",
        "cliente_email": "joao.silva@example.com",
        "tipo_solicitacao": "Atualizacao cadastral",
        "valor_patrimonio": valor_patrimonio,
    }


def webhook_payload(event_id="evt_123", email="joao.silva@example.com"):
    return {
        "event_id": event_id,
        "card_id": "card_456",
        "cliente_email": email,
        "timestamp": "2026-05-18T12:00:00Z",
    }


def test_cria_cliente_com_payload_valido_e_salva_no_banco(client, session_factory):
    response = client.post("/clientes", json=cliente_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "Aguardando Análise"
    assert body["prioridade"] is None
    assert "createCard" in body["pipefy_payload"]["query"]
    assert body["pipefy_payload"]["variables"]["fieldsAttributes"][0] == {
        "field_id": "cliente_nome",
        "field_value": "Joao Silva",
    }

    with session_factory() as db:
        cliente = db.scalar(
            select(Cliente).where(Cliente.cliente_email == "joao.silva@example.com")
        )

    assert cliente is not None
    assert cliente.cliente_nome == "Joao Silva"
    assert cliente.status == "Aguardando Análise"
    assert Decimal(cliente.valor_patrimonio) == Decimal("250000.00")


def test_processa_webhook_e_aplica_prioridade_alta(client, session_factory):
    client.post("/clientes", json=cliente_payload(valor_patrimonio=250000))

    response = client.post("/webhooks/pipefy/card-updated", json=webhook_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["duplicate"] is False
    assert body["status"] == "Processado"
    assert body["prioridade"] == "prioridade_alta"
    assert "updateCardField" in body["pipefy_payload"]["query"]
    assert body["pipefy_payload"]["variables"]["statusValue"] == ["Processado"]
    assert body["pipefy_payload"]["variables"]["priorityValue"] == ["prioridade_alta"]

    with session_factory() as db:
        cliente = db.scalar(
            select(Cliente).where(Cliente.cliente_email == "joao.silva@example.com")
        )

    assert cliente.status == "Processado"
    assert cliente.prioridade == "prioridade_alta"
    assert cliente.pipefy_card_id == "card_456"


def test_bloqueia_processamento_de_event_id_duplicado(client, session_factory):
    client.post("/clientes", json=cliente_payload(valor_patrimonio=150000))
    first_response = client.post("/webhooks/pipefy/card-updated", json=webhook_payload())
    second_response = client.post("/webhooks/pipefy/card-updated", json=webhook_payload())

    assert first_response.status_code == 200
    assert first_response.json()["prioridade"] == "prioridade_normal"
    assert second_response.status_code == 200
    assert second_response.json()["duplicate"] is True
    assert second_response.json()["pipefy_payload"] is None

    with session_factory() as db:
        event_count = db.scalar(select(func.count(ProcessedPipefyEvent.event_id)))
        cliente = db.scalar(
            select(Cliente).where(Cliente.cliente_email == "joao.silva@example.com")
        )

    assert event_count == 1
    assert cliente.status == "Processado"
    assert cliente.prioridade == "prioridade_normal"
