import os
from fastapi import HTTPException, Query, Depends
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from database import get_db
from sqlalchemy.orm import Session
from models import Source, Text, Media, Recursive_Text
from sqlalchemy import text
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import pinecone_index, model
from typing import Dict, List, Any
from config import pinecone_index
from config import pinecone_index 
from openai import OpenAI
import ollama
from dotenv import load_dotenv


def get_all_links(url: str = Query(..., description="URL of the website"), db: Session = Depends(get_db)):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        links = set()
        for tag in soup.find_all('a', href=True):
            full_url = urljoin(url, tag['href'])  # type: ignore
            if full_url.startswith("http"):
                links.add(full_url)

        new_source = Source(
            base_url=url,
            type='html',
            page_content=response.content,
            internal_links=len(links),
            page_count=1
        )
        db.add(new_source)
        db.commit()  
        db.refresh(new_source)

        return {
            "source_id": new_source.source_id,
            "input_url": url,
            "total_links_found": len(links),
            "links": list(links)
        }
    except Exception as e:
        db.rollback()  # optional safety
        return {"error": str(e)}








def get_assets(url: str = Query(..., description="URL of the website"), db: Session = Depends(get_db)):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract images
        images = set()
        for img in soup.find_all("img", src=True):
            full_url = urljoin(url, img["src"])      #type:ignore
            if full_url.startswith("http"):
                images.add(full_url)

        # Extract PDFs and social links
        pdf_links = set()
        social_links = set()
        social_domains = ["facebook.com", "twitter.com", "instagram.com", "linkedin.com", "youtube.com"]

        for a in soup.find_all("a", href=True):
            full_url = urljoin(url, a["href"])      #type:ignore
            if full_url.lower().endswith(".pdf"):
                pdf_links.add(full_url)
            if any(domain in full_url for domain in social_domains):
                social_links.add(full_url)

        # Clean text
        for script in soup(["script", "style"]):
            script.extract()
        
        text = soup.get_text(separator=' ', strip=True)
        clean_text = " ".join(text.split())

        # Save to Source
        new_source = Source(
            base_url=url,
            type='html',
            page_content=clean_text[:2000],
            internal_links=list(social_links),
            page_count=1
        )
        db.add(new_source)
        db.commit()
        db.refresh(new_source)

        text_splitter=RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        chunks=text_splitter.split_text(clean_text)

        for chunk in chunks:
            new_chunk=Recursive_Text(
                # text_content=chunk,
                content=chunk,
                source_id=new_source.source_id
            )
            db.add(new_chunk)
        db.commit()
    
        new_text = Text(
            source_id=new_source.source_id,
            internal_link_url=list(social_links),
            text_content=clean_text[:2000]
            
        )

       
        db.add(new_text)
        db.commit()
        db.refresh(new_text)

        # ✅ Save Media with correct column name
        for media_url in images:
            db.add(Media(source_id=new_source.source_id, type='image', media_url=media_url, internal_link=False))
        for pdf_url in pdf_links:
            db.add(Media(source_id=new_source.source_id, type='pdf', media_url=pdf_url, internal_link=False))
        for social_url in social_links:
            db.add(Media(source_id=new_source.source_id, type='social', media_url=social_url, internal_link=False))
        

        # print (new_source.source_id)
        db.commit()

        return {
            "source_id": new_source.source_id,
            "input_url": url,
            "total_images": len(images),
            "total_pdfs": len(pdf_links),
            "total_social_links": len(social_links),
            "images": list(images),
            "pdfs": list(pdf_links),
            "social_links": list(social_links),
            "text_content": clean_text[:2000]
        }

    except Exception as e:
        return {"error": str(e)}






def delete_all(db:Session):
    db.query(Recursive_Text).delete()
    db.query(Text).delete()
    db.query(Media).delete()
    db.query(Source).delete()
    db.commit()

    db.execute(text("ALTER SEQUENCE source_source_id_seq RESTART WITH 1"))
    db.execute(text("ALTER SEQUENCE text_id_seq RESTART WITH 1"))
    db.execute(text("ALTER SEQUENCE media_id_seq RESTART WITH 1"))
    db.commit()

    return {"message": "All data and sequences reset successfully"}



def split_and_store_chunks(source_id:int, db:Session=Depends(get_db)):
    source=db.query(Source).filter(Source.source_id==source_id).first()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    splitter=RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50

    )

    chunks= splitter.split_text(source.page_content)

    for i, chunk in enumerate(chunks):
        new_text= Recursive_Text(
            source_id= source.source_id,
            content= chunk
        )

        db.add(new_text)
    
    db.commit()

    chunked_texts=db.query(Recursive_Text).filter(Recursive_Text.source_id == source_id).all()
    return{
        "source id": source_id,
        "total chunks": len(chunked_texts),
        "chunks": [chunk.content for chunk in chunked_texts]
    }












def generate_embedding(source_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    records = db.query(Recursive_Text).filter(Recursive_Text.source_id == source_id).all()

    if not records:
        raise HTTPException(status_code=404, detail="No chunks found for this source_id")

    vectors = []
    for record in records:
        if not record.embedding:  # Check if embedding needs to be generated
            embedding: List[float] = model.encode(record.content, convert_to_numpy=True).tolist()
            record.embedding = embedding  # Store in PostgreSQL (optional)
            db.add(record)
            vector_id = f"chunk_{record.id}"
            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    "source_id": record.source_id,
                    "content": record.content
                }
            })

    if vectors:
        try:
            pinecone_index.upsert(vectors=vectors)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upsert vectors: {str(e)}")

    db.commit()
    return {
        "message": "Embeddings generated and stored in Pinecone and PostgreSQL",
        "total_chunks": len(records)
    }











load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model_to_use = os.getenv("MODEL_TO_USE")

def search_similar_chunks(query: str, top_k: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    try:
        # Generate embedding for the query
        query_embedding: List[float] = model.encode(query, convert_to_numpy=True).tolist()

        # Check dependencies
        if pinecone_index is None:
            raise ValueError("Pinecone index is not initialized")
        if db is None:
            raise ValueError("Database session is not initialized")

        # Query Pinecone
        try:
            query_response = pinecone_index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )  # type: ignore
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Pinecone query failed: {str(e)}")

        # Convert response
        query_response_dict: Dict[str, Any] = (
            query_response.to_dict() if hasattr(query_response, "to_dict") else dict(query_response)  # type: ignore
        )

        # Parse matches
        matches = query_response_dict.get("matches", [])
        if not matches:
            raise HTTPException(status_code=404, detail="No similar chunks found")

        seen_contents = set()
        results_content = []
        for match in matches:
            content = match.get("metadata", {}).get("content", "")
            if content and content not in seen_contents:
                seen_contents.add(content)
                results_content.append(content)

        if not results_content:
            return {
                "model_used": model_to_use,
                "query": query,
                "summary": "No relevant information found",
                "total_results": 0
            }

        # Build prompt
        prompt = f"""You are an intelligent assistant. Based on the following content, extract only the information that directly answers the user's query.

User query: "{query}"

Content: "{' '.join(results_content)}"

Respond with only the relevant answer. Do not include extra details unless necessary for clarity."""

        # Summary generation
        try:
            if model_to_use == "openai":
                response = client.chat.completions.create(
                    model='gpt-4o-mini',
                    messages=[{'role': 'user', 'content': prompt}]
                )
                summary = response.choices[0].message.content

            elif model_to_use == "ollama":
                response = ollama.chat(
                    model='llama3',
                    messages=[{'role': 'user', 'content': prompt}]
                )
                summary = response['message']['content']

            else:
                raise HTTPException(status_code=400, detail=f"Invalid model specified: {model_to_use}")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

        return {
            "model_used": model_to_use,
            "query": query,
            "summary": summary,
            "total_results": len(results_content)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
