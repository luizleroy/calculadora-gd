from fastapi import FastAPI

from app.routes.faturas import router as faturas_router


app = FastAPI(
    title="Cemig Calculadora",
    version="0.1.0",
)


app.include_router(faturas_router)