from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class ItemFaturado:
    descricao: str
    unidade: str | None = None
    quantidade: Decimal | None = None
    preco_unitario: Decimal | None = None
    valor: Decimal | None = None
    tarifa_unitaria: Decimal | None = None


@dataclass
class Tributo:
    nome: str
    base_calculo: Decimal
    aliquota: Decimal
    valor: Decimal


@dataclass
class Fatura:
    referencia: str
    consumo_kwh: Decimal
    bandeira: str

    itens: list[ItemFaturado] = field(default_factory=list)
    tributos: list[Tributo] = field(default_factory=list)

    contribuicao_iluminacao_publica: Decimal = Decimal("0")
    total: Decimal = Decimal("0")

    def to_dict(self) -> dict:
        return {
            "referencia": self.referencia,
            "consumo_kwh": str(self.consumo_kwh),
            "bandeira": self.bandeira,
            "itens": [
                {
                    "descricao": item.descricao,
                    "unidade": item.unidade,
                    "quantidade": (
                        str(item.quantidade)
                        if item.quantidade is not None
                        else None
                    ),
                    "preco_unitario": (
                        str(item.preco_unitario)
                        if item.preco_unitario is not None
                        else None
                    ),
                    "valor": (
                        str(item.valor)
                        if item.valor is not None
                        else None
                    ),
                    "tarifa_unitaria": (
                        str(item.tarifa_unitaria)
                        if item.tarifa_unitaria is not None
                        else None
                    ),
                }
                for item in self.itens
            ],
            "tributos": [
                {
                    "nome": tributo.nome,
                    "base_calculo": str(tributo.base_calculo),
                    "aliquota": str(tributo.aliquota),
                    "valor": str(tributo.valor),
                }
                for tributo in self.tributos
            ],
            "contribuicao_iluminacao_publica": str(
                self.contribuicao_iluminacao_publica
            ),
            "total": str(self.total),
        }