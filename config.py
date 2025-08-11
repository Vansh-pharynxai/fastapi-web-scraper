# config.py
import pinecone
from pinecone import ServerlessSpec
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not PINECONE_API_KEY:
    logger.error("PINECONE_API_KEY is not set in the .env file")
    raise ValueError("PINECONE_API_KEY is required")

# Initialize Pinecone
try:
    pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
    logger.info("Pinecone client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Pinecone client: {str(e)}")
    raise

# Explicitly set index_name to chatbot2
index_name = "chatbot2"  

# Verify index exists or create it
try:
    indexes = pc.list_indexes().names()
    logger.info(f"Available indexes: {indexes}")
    if index_name not in indexes:
        logger.info(f"Creating index: {index_name}")
        pc.create_index(
            name=index_name,
            dimension=384,  
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        logger.info(f"Index {index_name} created successfully")
except Exception as e:
    logger.error(f"Failed to create or list index: {str(e)}")
    raise

# Initialize index
try:
    pinecone_index = pc.Index(index_name)
    if pinecone_index is None:
        logger.error(f"Failed to initialize index: {index_name}")
        raise ValueError(f"Index {index_name} could not be initialized")
    logger.info(f"Index {index_name} initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize index {index_name}: {str(e)}")
    raise

model = SentenceTransformer('all-MiniLM-L6-v2')