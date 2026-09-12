import re
from decimal import Decimal
from pathlib import Path

from pypdf import PdfReader

from app.models.fatura import Fatura
from app.models.fatura import ItemFaturado
from app.models.fatura import Tributo


class LeituraFaturaService:

    def ler(self, caminho: Path) -> dict:
        texto = self._extrair_texto(caminho)

        fatura = Fatura(
            referencia=self._extrair_referencia(texto),
            consumo_kwh=self._extrair_consumo(texto),
            bandeira=self._extrair_bandeira(texto),
        )

        fatura.itens = self._extrair_itens(texto)
        fatura.tributos = self._extrair_tributos(texto)

        fatura.contribuicao_iluminacao_publica = (
            self._extrair_iluminacao_publica(texto)
        )

        fatura.total = self._extrair_total(texto)

        return fatura.to_dict()

    # ---------------------------------------------------------
    # Leitura do PDF
    # ---------------------------------------------------------

    def _extrair_texto(self, caminho: Path) -> str:
        reader = PdfReader(caminho)

        texto = "\n".join(
            pagina.extract_text() or ""
            for pagina in reader.pages
        )

        if not texto.strip():
            raise ValueError(
                "Não foi possível extrair texto do PDF."
            )

        return texto

    # ---------------------------------------------------------
    # Referência
    # ---------------------------------------------------------

    def _extrair_referencia(self, texto: str) -> str:
        texto_normalizado = self._normalizar_espacos(texto)

        resultado = re.search(
            r"Referente a Vencimento Valor a pagar \(R\$\)\s+"
            r"([A-Z]{3}/\d{4})",
            texto_normalizado,
            re.IGNORECASE,
        )

        if not resultado:
            raise ValueError(
                "Referência da fatura não encontrada."
            )

        return resultado.group(1).upper()

    # ---------------------------------------------------------
    # Consumo
    # ---------------------------------------------------------

    def _extrair_consumo(self, texto: str) -> Decimal:
        texto_normalizado = self._normalizar_espacos(texto)

        resultado = re.search(
            r"Energia\s+kWh\s+\S+\s+"
            r"[\d.]+\s+"
            r"[\d.]+\s+"
            r"\d+\s+"
            r"(\d+)",
            texto_normalizado,
            re.IGNORECASE,
        )

        if not resultado:
            raise ValueError(
                "Consumo da fatura não encontrado."
            )

        return Decimal(resultado.group(1))

    # ---------------------------------------------------------
    # Bandeira
    # ---------------------------------------------------------

    def _extrair_bandeira(self, texto: str) -> str:
        texto_normalizado = self._normalizar_espacos(texto)

        resultado = re.search(
            r"Band\.\s+"
            r"(Verde|Amarela|Vermelha\s+1|Vermelha\s+2)",
            texto_normalizado,
            re.IGNORECASE,
        )

        if not resultado:
            raise ValueError(
                "Bandeira tarifária não encontrada."
            )

        return resultado.group(1).lower()

    # ---------------------------------------------------------
    # Itens faturados
    # ---------------------------------------------------------

    def _extrair_itens(self, texto: str) -> list[ItemFaturado]:
        itens = []

        descricoes = (
            "Energia Elétrica",
            "Energia SCEE s/ ICMS",
            "Energia compensada GD I",
        )

        for descricao in descricoes:
            linha = self._extrair_linha_item(
                texto,
                descricao,
            )

            itens.append(
                self._parse_item_energia(
                    linha,
                    descricao,
                )
            )

        linha = self._extrair_linha_item(
            texto,
            "Bônus ITAIPU",
        )

        itens.append(
            ItemFaturado(
                descricao="Bônus ITAIPU",
                valor=self._extrair_primeiro_valor_negativo(
                    linha
                ),
            )
        )

        return itens

    def _extrair_linha_item(
        self,
        texto: str,
        descricao: str,
    ) -> str:

        texto_normalizado = self._normalizar_espacos(texto)

        padrao = (
            re.escape(descricao)
            + r"\s+"
            + r".*?"
            + r"(?=\s+(?:Energia Elétrica|"
            r"Energia SCEE s/ ICMS|"
            r"Energia compensada GD I|"
            r"Bônus ITAIPU|"
            r"Contrib Ilum Publica Municipal|"
            r"TOTAL)\b)"
        )

        resultado = re.search(
            padrao,
            texto_normalizado,
            re.IGNORECASE,
        )

        if not resultado:
            print( f"Item não encontrado: {descricao}")
            return None

        return resultado.group(0)

    def _parse_item_energia(
        self,
        linha: str,
        descricao: str,
    ) -> ItemFaturado:

        valores = re.findall(
            r"-?\d+(?:,\d+)?",
            linha,
        )

        if len(valores) < 6:
            raise ValueError(
                f"Valores insuficientes para o item: {descricao}"
            )

        return ItemFaturado(
            descricao=descricao,
            unidade="kWh",
            quantidade=Decimal(valores[0]),
            preco_unitario=self._decimal(
                valores[1]
            ),
            valor=self._decimal(
                valores[2]
            ),
            tarifa_unitaria=self._decimal(
                valores[-1]
            ),
        )

    # ---------------------------------------------------------
    # Tributos
    # ---------------------------------------------------------

    def _extrair_tributos(
        self,
        texto: str,
    ) -> list[Tributo]:

        texto_normalizado = self._normalizar_espacos(texto)

        tributos = []

        for nome in ("ICMS", "PASEP", "COFINS"):

            resultado = re.search(
                rf"\b{nome}\s+"
                r"(-?\d+,\d+)\s+"
                r"(\d+,\d+)\s+"
                r"(-?\d+,\d+)",
                texto_normalizado,
                re.IGNORECASE,
            )

            if not resultado:
                raise ValueError(
                    f"Tributo não encontrado: {nome}"
                )

            tributos.append(
                Tributo(
                    nome=nome,
                    base_calculo=self._decimal(
                        resultado.group(1)
                    ),
                    aliquota=self._decimal(
                        resultado.group(2)
                    ),
                    valor=self._decimal(
                        resultado.group(3)
                    ),
                )
            )

        return tributos

    # ---------------------------------------------------------
    # Iluminação pública
    # ---------------------------------------------------------

    def _extrair_iluminacao_publica(
        self,
        texto: str,
    ) -> Decimal:

        texto_normalizado = self._normalizar_espacos(texto)

        resultado = re.search(
            r"Contrib Ilum Publica Municipal\s+"
            r"(-?\d+,\d+)",
            texto_normalizado,
            re.IGNORECASE,
        )

        if not resultado:
            raise ValueError(
                "Contribuição de iluminação pública "
                "não encontrada."
            )

        return self._decimal(resultado.group(1))

    # ---------------------------------------------------------
    # Total
    # ---------------------------------------------------------

    def _extrair_total(self, texto: str) -> Decimal:
        texto_normalizado = self._normalizar_espacos(texto)

        resultado = re.search(
            r"\bTOTAL\s+"
            r"(-?\d+,\d+)",
            texto_normalizado,
            re.IGNORECASE,
        )

        if not resultado:
            raise ValueError(
                "Total da fatura não encontrado."
            )

        return self._decimal(resultado.group(1))

    # ---------------------------------------------------------
    # Utilitários
    # ---------------------------------------------------------

    def _extrair_primeiro_valor_negativo(
        self,
        texto: str,
    ) -> Decimal:

        if texto is None:
            print("Texto não encontrado.")
            return None

        resultado = re.search(
            r"-\d+(?:,\d+)?",
            texto,
        )

        if not resultado:
            raise ValueError(
                "Valor negativo não encontrado."
            )

        return self._decimal(resultado.group(0))

    def _normalizar_espacos(self, texto: str) -> str:
        return re.sub(r"\s+", " ", texto).strip()

    def _decimal(self, valor: str) -> Decimal:
        return Decimal(
            valor.replace(".", "").replace(",", ".")
        )