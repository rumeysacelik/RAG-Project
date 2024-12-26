from fastapi import FastAPI
from routes.api import router
# from routes.initial import initRouter
from config.middleware import setup_middlewares
from wsgi import create_app

# Uygulama oluşturulur
app = create_app()


# app = FastAPI()

setup_middlewares(app)

app.include_router(router)
# app.include_router(initRouter)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
