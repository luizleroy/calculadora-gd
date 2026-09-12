from decimal import Decimal


class CalculoFaturaService:

    def calcular_total_sem_credito(
        self,
        fatura: dict,
    ) -> Decimal:
        """
        Calcula quanto seria cobrado pela Cemig caso todo o
        consumo de energia da fatura fosse fornecido pela Cemig,
        sem considerar créditos/compensações de energia.

        Fórmula:

            consumo_kwh
            × preço unitário faturado
            + CIP
            = total sem crédito

        O preço unitário utilizado é o do item "Energia Elétrica".

        Os itens:
            - Energia SCEE s/ ICMS
            - Energia compensada GD I

        não participam deste cálculo, pois representam energia
        compensada/créditos relacionados à geração distribuída.
        """

        consumo_kwh = self._decimal(
            fatura["consumo_kwh"]
        )

        iluminacao_publica = self._decimal(
            fatura["contribuicao_iluminacao_publica"]
        )

        preco_unitario = self._obter_preco_unitario_energia(
            fatura
        )

        valor_energia = (
            consumo_kwh * preco_unitario
        )

        return self._arredondar(
            valor_energia + iluminacao_publica
        )

    def _obter_preco_unitario_energia(
        self,
        fatura: dict,
    ) -> Decimal:

        for item in fatura["itens"]:

            if item["descricao"] == "Energia Elétrica":

                preco_unitario = item.get(
                    "preco_unitario"
                )

                if preco_unitario is None:
                    raise ValueError(
                        "Preço unitário da Energia Elétrica "
                        "não encontrado na fatura."
                    )

                return self._decimal(
                    preco_unitario
                )

        raise ValueError(
            "Item 'Energia Elétrica' não encontrado "
            "na fatura."
        )

    def _decimal(self, valor) -> Decimal:

        if isinstance(valor, Decimal):
            return valor

        return Decimal(str(valor))

    def _arredondar(self, valor: Decimal) -> Decimal:

        return valor.quantize(Decimal("0.01"))