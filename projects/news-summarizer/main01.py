import os
import json
import openai
import requests
import time

import streamlit as st

from dotenv import  load_dotenv


load_dotenv()

news_api_key = os.environ.get("NEWS_API_KEY")
openai.api_key = os.environ.get("OPENAI_API_KEY")
client = openai.OpenAI()

model= "gpt-3.5-turbo"

def get_news(topic):
  final_news = []
  url = (
    f"https://newsapi.org/v2/everything?q={topic}&apiKey={news_api_key}&pageSize=1&page=1"
  )
  try:
    response = requests.get(url)
    if response.status_code == 200:
      news = json.dumps(response.json(), indent=4)
      news_json = json.loads(news)

      data = news_json

      # Access all the fields == loop through
      status = data['status']
      total_results = data['totalResults']
      articles = data['articles']
   
      
      # Loop through articles
      for article in articles:
        source_name = article['source']['name']
        author = article['author']
        title = article['title']
        description = article['description']
        url = article['url']
        content = article['content']
        tilte_description = f"""
Title: {title}
Author: {author},
Source: {source_name},
Description: {description},
URL: {url}
Content: {content}
"""
        final_news.append(tilte_description)   
  except requests.exceptions.RequestException as e:
    print("Error occured during API Request", e)
  return final_news

def main():
  news = get_news('bitcoin')
  if len(news) > 0:
    print(news)

if __name__ == '__main__':
  main()