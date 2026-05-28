from decimal import Decimal
from typing import Any, Dict


PIPEFY_PIPE_ID = "mundo_invest_clientes"
FIELD_CLIENTE_NOME = "cliente_nome"
FIELD_CLIENTE_EMAIL = "cliente_email"
FIELD_TIPO_SOLICITACAO = "tipo_solicitacao"
FIELD_VALOR_PATRIMONIO = "valor_patrimonio"
FIELD_STATUS = "status"
FIELD_PRIORIDADE = "prioridade"

CREATE_CARD_MUTATION = """
mutation CreateMundoInvestClientCard(
  $pipeId: ID!
  $title: String!
  $fieldsAttributes: [FieldValueInput]
) {
  createCard(input: {
    pipe_id: $pipeId
    title: $title
    fields_attributes: $fieldsAttributes
  }) {
    card {
      id
      title
    }
  }
}
""".strip()

UPDATE_CARD_FIELDS_MUTATION = """
mutation UpdateMundoInvestCardFields(
  $cardId: ID!
  $statusFieldId: ID!
  $statusValue: [UndefinedInput]
  $priorityFieldId: ID!
  $priorityValue: [UndefinedInput]
) {
  updateStatus: updateCardField(input: {
    card_id: $cardId
    field_id: $statusFieldId
    new_value: $statusValue
  }) {
    success
  }
  updatePriority: updateCardField(input: {
    card_id: $cardId
    field_id: $priorityFieldId
    new_value: $priorityValue
  }) {
    success
  }
}
""".strip()


class PipefyClient:
    """Builds Pipefy GraphQL requests without sending them to Pipefy."""

    def build_create_card_payload(
        self,
        *,
        cliente_nome: str,
        cliente_email: str,
        tipo_solicitacao: str,
        valor_patrimonio: Decimal,
    ) -> Dict[str, Any]:
        return {
            "operationName": "CreateMundoInvestClientCard",
            "query": CREATE_CARD_MUTATION,
            "variables": {
                "pipeId": PIPEFY_PIPE_ID,
                "title": cliente_nome,
                "fieldsAttributes": [
                    {"field_id": FIELD_CLIENTE_NOME, "field_value": cliente_nome},
                    {"field_id": FIELD_CLIENTE_EMAIL, "field_value": cliente_email},
                    {"field_id": FIELD_TIPO_SOLICITACAO, "field_value": tipo_solicitacao},
                    {
                        "field_id": FIELD_VALOR_PATRIMONIO,
                        "field_value": str(valor_patrimonio),
                    },
                ],
            },
        }

    def build_update_card_fields_payload(
        self,
        *,
        card_id: str,
        status: str,
        prioridade: str,
    ) -> Dict[str, Any]:
        return {
            "operationName": "UpdateMundoInvestCardFields",
            "query": UPDATE_CARD_FIELDS_MUTATION,
            "variables": {
                "cardId": card_id,
                "statusFieldId": FIELD_STATUS,
                "statusValue": [status],
                "priorityFieldId": FIELD_PRIORIDADE,
                "priorityValue": [prioridade],
            },
        }


pipefy_client = PipefyClient()

