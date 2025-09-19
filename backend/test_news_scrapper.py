from aussie_news import ABCNewsScraper

if __name__ == '__main__':
  test_ABCNews = ABCNewsScraper()
  results = test_ABCNews.get_article_urls()
  for item in results:
    print(item)
    print("#" * 20)