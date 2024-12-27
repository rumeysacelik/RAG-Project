from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import search
from routes.history import router as history_router



def create_app() -> FastAPI:

    app = FastAPI(
        title='Drug Search API',
        description='An API for searching and retrieving drug information.'
    )
    init_routers(app)
    configure_middlewares(app)
    return app


def init_routers(app: FastAPI) -> None:
    app.include_router(search.router)  
    app.include_router(history_router)  # History router'ı dahil et



def configure_middlewares(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )


# FastAPI uygulamasını başlatır
app = create_app()
