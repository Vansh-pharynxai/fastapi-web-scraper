from fastapi import APIRouter, Query,Depends
from openai import BaseModel
import controllers
from database import get_db
from sqlalchemy.orm import Session

router=APIRouter()


class SearchQuery(BaseModel):
    query:str
    top_k:int=5


@router.get("/get-links")
def get_all_links_route(url: str = Query(..., description="URL of the website"), db:Session=Depends(get_db)):
    return controllers.get_all_links(url,db)

@router.get("/get-assets")
def get_assets_route(url: str = Query(..., description="URL of the website"),db:Session=Depends(get_db)):
    return controllers.get_assets(url,db)


@router.delete("/delete_all")
def delete_all_route(db:Session=Depends(get_db)):
    return controllers.delete_all(db)



@router.post("/split_text/{source_id}")
def split_and_store_text_route(source_id:int, db:Session=Depends(get_db)):
    return controllers.split_and_store_chunks(source_id,db)


@router.post("/generate_embedding/{source_id}")
def generate_embedding_route(source_id:int, db:Session=Depends(get_db)):
    return controllers.generate_embedding(source_id,db)



@router.post("/search")
def search_route(search_query:SearchQuery,db:Session=Depends(get_db)):
    return controllers.search_similar_chunks(search_query.query, search_query.top_k,db)