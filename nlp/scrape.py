import yfinance as yf
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

alexPath = "/Users/alex/Desktop/Tulane/S24/Repos/NLPP/"
zachPath = ""
relativePath = "project-finance/nlp/app/research/"

def get_news_articles(ticker):
    articles_list = []
    stock = yf.Ticker(ticker)
    news_items = stock.news

    for item in news_items:
        url = item['link']
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, allow_redirects=True)
            final_url = response.url  # Capture the final URL after any redirects
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                article_content = soup.find('div', {'class': 'caas-body'}) or soup.find('article')
                if article_content:
                    articles_list.append({
                        'title': item['title'],
                        'url': final_url,
                        'content': article_content.text
                    })
                else:
                    articles_list.append({
                        'title': item['title'],
                        'url': final_url,
                        'content': "Content not found - page may use dynamic loading or have a different layout"
                    })
            else:
                articles_list.append({
                    'title': item['title'],
                    'url': final_url,
                    'content': f"Failed to fetch article: HTTP {response.status_code}"
                })
        except requests.exceptions.RequestException as e:
            articles_list.append({
                'title': item['title'],
                'url': url,
                'content': f"Error fetching the article: {str(e)}"
            })

    return articles_list

def save_to_json(data, path):
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

ticker = "AAPL"
news_articles = get_news_articles(ticker)
path = alexPath + relativePath + ticker + ".json"
save_to_json(news_articles, path) 

print("News articles saved to JSON.")
