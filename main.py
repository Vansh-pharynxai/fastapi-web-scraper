from fastapi import FastAPI
from dotenv import load_dotenv
import os
from routes import scrapper
from database import Base, engine
from config import pinecone_index, model  # Import from config.py

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize FastAPI
app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)

# Include router
app.include_router(scrapper.router)