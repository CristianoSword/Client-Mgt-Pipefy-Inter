# Mundo Invest - Client Management & Pipefy Integration

API em Python/FastAPI para cadastrar clientes, persistir dados localmente em SQLite e simular os payloads GraphQL que seriam enviados ao Pipefy.

## Stack

- Python 3.9+ (CPython)
- FastAPI
- SQLAlchemy
- SQLite
- Pytest

## Execucao local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

No Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Se `python` apontar para uma instalacao MSYS/MinGW no Windows, prefira o launcher `py`, como no exemplo acima.

A API sobe em `http://127.0.0.1:8000` e cria o arquivo `mundo_invest.db` automaticamente.

## Testes

```bash
pytest -q
```

Os testes cobrem:

- criacao de cliente valido e persistencia no banco;
- processamento do webhook com prioridade baseada no patrimonio;
- bloqueio de reprocessamento quando o `event_id` ja existe.

## Exemplos de requisicao

Criar cliente:

```bash
curl -X POST "http://127.0.0.1:8000/clientes" \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_nome": "João Silva",
    "cliente_email": "joao.silva@example.com",
    "tipo_solicitacao": "Atualização cadastral",
    "valor_patrimonio": 250000
  }'
```

Simular webhook do Pipefy:

```bash
curl -X POST "http://127.0.0.1:8000/webhooks/pipefy/card-updated" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_123",
    "card_id": "card_456",
    "cliente_email": "joao.silva@example.com",
    "timestamp": "2026-05-18T12:00:00Z"
  }'
```

## Mapeamento Pipefy

A camada `app/pipefy_client.py` nao chama a API real do Pipefy. Ela monta o payload que seria enviado via GraphQL.

Para criacao de card, o codigo usa a mutation `createCard` com `pipe_id`, `title` e `fields_attributes`, seguindo a estrutura documentada em:

- [Pipefy - Cards / createCard](https://developers.pipefy.com/reference/cards)
- [Pipefy - CreateCardInput](https://api-docs.pipefy.com/reference/inputObjects/CreateCardInput)
- [Pipefy - FieldValueInput](https://api-docs.pipefy.com/reference/inputObjects/FieldValueInput)

Para atualizacao, o codigo usa duas chamadas `updateCardField` com aliases na mesma operacao GraphQL, uma para `status` e outra para `prioridade`, seguindo:

- [Pipefy - Fields / updateCardField](https://developers.pipefy.com/reference/fields)
- [Pipefy - UpdateCardFieldInput](https://api-docs.pipefy.com/reference/inputObjects/UpdateCardFieldInput/)

## Visao de producao na AWS

Uma evolucao natural seria expor os endpoints por API Gateway e processa-los com AWS Lambda. Para dados transacionais e consultas relacionais, RDS PostgreSQL funcionaria bem. Para um fluxo mais orientado a eventos e idempotencia simples por chave, DynamoDB tambem seria uma boa opcao, usando `event_id` como chave unica da tabela de eventos processados.

Para webhooks, API Gateway receberia o evento do Pipefy e publicaria em SQS. Uma Lambda consumidora processaria a fila, calcularia a prioridade, atualizaria o cliente e gravaria o `event_id` de forma condicional para garantir idempotencia. Secrets Manager guardaria tokens do Pipefy, CloudWatch centralizaria logs/metricas e DLQ armazenaria eventos com falha para reprocessamento seguro.
