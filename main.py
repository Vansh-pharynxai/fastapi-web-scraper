from fastapi import FastAPI
from routes import scrapper



app = FastAPI()

app.include_router(scrapper.router)
