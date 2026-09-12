from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter
from fastapi import File
from fastapi import HTTPException
from fastapi import UploadFile

from app.services.calculo_fatura_service import (
    CalculoFaturaService,
)
from app.services.leitura_fatura_service import (
    LeituraFaturaService,
)


router = APIRouter(
    prefix="/faturas",
    tags=["Faturas"],
)


@router.post("/ler")
async def ler_fatura(
    arquivo: UploadFile = File(
        ...,
        description="Arquivo PDF da fatura de energia elétrica",
    ),
):
    if not arquivo.filename:
        raise HTTPException(
            status_code=400,
            detail="Nenhum arquivo foi informado.",
        )

    if not arquivo.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="O arquivo deve ser um PDF.",
        )

    arquivo_temporario = None

    try:
        with NamedTemporaryFile(
            suffix=".pdf",
            delete=False,
        ) as temp:

            arquivo_temporario = Path(temp.name)

            conteudo = await arquivo.read()

            temp.write(conteudo)

        # -----------------------------------------------------
        # 1. Leitura e parse da fatura
        # -----------------------------------------------------

        leitura_service = LeituraFaturaService()

        fatura = leitura_service.ler(
            arquivo_temporario
        )

        # -----------------------------------------------------
        # 2. Cálculo do valor sem crédito/compensação
        # -----------------------------------------------------

        calculo_service = CalculoFaturaService()

        fatura["total_sem_gd"] = (
            calculo_service.calcular_total_sem_credito(
                fatura
            )
        )

        return fatura

    except ValueError as exc:

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar a fatura: {exc}",
        )

    finally:

        if (
            arquivo_temporario
            and arquivo_temporario.exists()
        ):
            arquivo_temporario.unlink()

        await arquivo.close()