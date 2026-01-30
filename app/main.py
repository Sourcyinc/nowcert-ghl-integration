"""
Aplicación principal FastAPI para integración NowCerts + GoHighLevel
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_router
from app.core.logger import logger

# Crear instancia de FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="Middleware para integración bidireccional entre NowCerts y GoHighLevel",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Incluir routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Eventos al iniciar la aplicación"""
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} iniciada")
    logger.info(f"Documentación disponible en /docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Eventos al cerrar la aplicación"""
    logger.info("Cerrando aplicación...")


@app.get("/")
async def root():
    """
    Endpoint raíz con información de la API
    """
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "webhooks": {
                "nowcerts": f"{settings.API_V1_PREFIX}/webhooks/nowcerts",
                "ghl": f"{settings.API_V1_PREFIX}/webhooks/ghl"
            },
            "sync": {
                "manual": f"{settings.API_V1_PREFIX}/sync/manual"
            }
        }
    }


@app.get("/health")
async def health_check():
    """
    Endpoint de health check
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

