from fastapi import APIRouter, Query
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import controllers

router=APIRouter()

@router.get("/get-links")
def get_all_links_route(url: str = Query(..., description="URL of the website")):
    return controllers.get_all_links(url)

@router.get("/get-assets")
def get_assets_route(url: str = Query(..., description="URL of the website")):
    return controllers.get_assets(url)