from fastapi import Query
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin




def get_all_links(url: str = Query(..., description="URL of the website")):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        links = set()
        for tag in soup.find_all('a', href=True):
            full_url = urljoin(url, tag['href']) # type: ignore
            if full_url.startswith("http"):
                links.add(full_url)

        return {
            "input_url": url,
            "total_links_found": len(links),
            "links": list(links)
        }
    except Exception as e:
        return {"error": str(e)}
    






def get_assets(url: str = Query(..., description="URL of the website")):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        images = set()
        for img in soup.find_all("img", src=True):
            full_url = urljoin(url, img["src"]) # type: ignore
            if full_url.startswith("http"):
                images.add(full_url)

        pdf_links = set()
        social_links = set()
        social_domains = ["facebook.com", "twitter.com", "instagram.com", "linkedin.com", "youtube.com"]

        for a in soup.find_all("a", href=True):
            full_url = urljoin(url, a["href"]) # type: ignore
            if full_url.lower().endswith(".pdf"):
                pdf_links.add(full_url)
            if any(domain in full_url for domain in social_domains):
                social_links.add(full_url)

        return {
            "input_url": url,
            "total_images": len(images),
            "total_pdfs": len(pdf_links),
            "total_social_links": len(social_links),
            "images": list(images),
            "pdfs": list(pdf_links),
            "social_links": list(social_links)
        }

    except Exception as e:
        return {"error": str(e)}