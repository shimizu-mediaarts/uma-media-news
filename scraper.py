import json
import os
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
import requests

DATA_FILE = "articles.json"
QUERY = "宇都宮メディア・アーツ専門学校"


def fetch_google_news():
  """GoogleニュースRSSから最新記事を取得"""
  encoded_query = urllib.parse.quote(QUERY)
  rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ja&gl=JP&ceid=JP:ja"

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  try:
    response = requests.get(rss_url, headers=headers, timeout=10)
    if response.status_code != 200:
      print(f"Error fetching RSS: Status {response.status_code}")
      return []

    root = ET.fromstring(response.content)
    fetched_items = []

    for item in root.findall("./channel/item"):
      title = item.find("title").text if item.find("title") is not None else ""
      link = item.find("link").text if item.find("link") is not None else ""
      pub_date_raw = (
          item.find("pubDate").text if item.find("pubDate") is not None else ""
      )
      source_elem = item.find("source")
      source_name = (
          source_elem.text if source_elem is not None else "Webメディア"
      )

      try:
        pub_date = datetime.strptime(
            pub_date_raw, "%a, %d %b %Y %H:%M:%S %Z"
        ).strftime("%Y-%m-%d")
      except Exception:
        pub_date = datetime.now().strftime("%Y-%m-%d")

      clean_title = title.rsplit(" - ", 1)[0] if " - " in title else title

      fetched_items.append({
          "id": f"auto-{abs(hash(link))}",
          "title": clean_title,
          "media": source_name,
          "date": pub_date,
          "category": (
              "Webニュース"
              if "新聞" not in source_name
              else "新聞掲載"
          ),
          "importance": 4,
          "views": 0,
          "summary": f"{source_name}に掲載された『{QUERY}』に関する報道記事です。",
          "url": link,
          "tags": ["宇都宮メディア・アーツ", source_name, "自動取得"],
      })

    return fetched_items
  except Exception as e:
    print(f"Error: {e}")
    return []


def update_articles_json():
  existing_articles = []
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      try:
        existing_articles = json.load(f)
      except json.JSONDecodeError:
        existing_articles = []

  existing_urls = {item.get("url") for item in existing_articles}
  new_items = fetch_google_news()

  added_count = 0
  for item in new_items:
    if item["url"] not in existing_urls:
      existing_articles.insert(0, item)
      existing_urls.add(item["url"])
      added_count += 1

  if added_count > 0:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
      json.dump(existing_articles, f, ensure_ascii=False, indent=2)
    print(f"成功: {added_count} 件の新着記事を追加しました。")
  else:
    print("新着記事はありませんでした。")


if __name__ == "__main__":
  update_articles_json()
