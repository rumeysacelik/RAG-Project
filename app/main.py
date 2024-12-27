from fastapi import FastAPI
from routes.search import router
from config.middleware import setup_middlewares
from wsgi import create_app

app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
