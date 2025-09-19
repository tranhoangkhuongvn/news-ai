# backend/app/scrapers/abc_scraper.py
from typing import List
from base_scraper import BaseScraper
from bs4 import BeautifulSoup

class ABCNewsScraper(BaseScraper):
    def __init__(self):
        super().__init__("ABC News", "https://www.abc.net.au")
    
    def get_article_urls(self) -> List[str]:
        response = self.session.get(f"{self.base_url}/news")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        urls = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/news/' in href and href.startswith('/'):
                full_url = self.base_url + href
                urls.append(full_url)
        
        return list(set(urls))[:20]  # Limit to 20 articles

# backend/app/scrapers/smh_scraper.py
class SMHScraper(BaseScraper):
    def __init__(self):
        super().__init__("Sydney Morning Herald", "https://www.smh.com.au")
    
    def get_article_urls(self) -> List[str]:
        response = self.session.get(self.base_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        urls = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('https://www.smh.com.au') and '/story/' in href:
                urls.append(href)
        
        return list(set(urls))[:20]

# Similar implementations for The Age, The Australian, etc.