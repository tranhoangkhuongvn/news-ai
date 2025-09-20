from src.scrapers.aussie_news import ABCNewsScraper
from pprint import pprint

if __name__ == '__main__':
  test_ABCNews = ABCNewsScraper()
  results = test_ABCNews.get_article_urls()
  for item in results:
    print("#" * 20)
    print("scraping...: ", item)
    article = test_ABCNews.scrape_article(item)
    pprint(article)