import json
import os
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
import requests

DATA_FILE = "articles.json"

SEARCH_QUERIES = [
    "宇都宮メディア・アーツ専門学校",
    "宇都宮メディアアーツ専門学校",
    "学校法人宇都宮美術学院",
]

# 本校に関連する記事か確認するための必須キーワード
STRICT_KEYWORDS = [
    "宇都宮メディア・アーツ",
    "宇都宮メディアアーツ",
    "宇都宮美術学院",
    "media-arts.ac.jp",
]

# 除外したいネガティブワード・不適切なキーワードのリスト
NEGATIVE_KEYWORDS = [
    "事件",
    "事故",
    "逮捕",
    "容疑",
    "被害",
    "不祥事",
    "批判",
    "炎上",
    "不正",
    "処分",
    "違反",
    "訴訟",
    "疑惑",
    "倒産",
    "閉校",
]


def is_valid_uma_article(title, summary, url):
  """宇都宮メディア・アーツ専門学校に関する記事か判定"""
  text_to_check = f"{title} {summary} {url}".lower()
  if "media-arts.ac.jp" in url:
    return True
  for kw in STRICT_KEYWORDS:
    if kw.lower() in text_to_check:
      return True
  return False


def contains_negative_word(title, summary):
  """ネガティブキーワードが含まれているか判定"""
  text_to_check = f"{title} {summary}"
  for word in NEGATIVE_KEYWORDS:
    if word in text_to_check:
      return True
  return False


def fetch_google_news():
  fetched_items = []
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      )
  }

  for query in SEARCH_QUERIES:
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ja&gl=JP&ceid=JP:ja"

    try:
      response = requests.get(rss_url, headers=headers, timeout=10)
      if response.status_code != 200:
        continue

      root = ET.fromstring(response.content)

      for item in root.findall("./channel/item"):
        title = item.find("title").text if item.find("title") is not None else ""
        link = item.find("link").text if item.find("link") is not None else ""
        pub_date_raw = (
            item.find("pubDate").text
            if item.find("pubDate") is not None
            else ""
        )
        source_elem = item.find("source")
        source_name = (
            source_elem.text if source_elem is not None else "Webニュース"
        )

        # 本校に関係のない記事を除外
        if not is_valid_uma_article(title, "", link):
          continue

        # ネガティブワードが含まれている記事を自動除外
        if contains_negative_word(title, ""):
          print(f"ネガティブワード検知のため除外しました: {title}")
          continue

        try:
          pub_date = datetime.strptime(
              pub_date_raw, "%a, %d %b %Y %H:%M:%S %Z"
          ).strftime("%Y-%m-%d")
        except Exception:
          pub_date = datetime.now().strftime("%Y-%m-%d")

        clean_title = title.rsplit(" - ", 1)[0] if " - " in title else title

        category = "Webニュース"
        if "新聞" in source_name or "下野" in source_name:
          category = "新聞掲載"
        elif any(
            tv in source_name for tv in ["テレビ", "TV", "ラジオ", "NHK"]
        ):
          category = "TV/ラジオ"

        article_url = link if link else "https://media-arts.ac.jp/"

        fetched_items.append({
            "id": f"auto-{abs(hash(article_url))}",
            "title": clean_title,
            "media": source_name,
            "date": pub_date,
            "category": category,
            "importance": 4,
            "views": 0,
            "summary": (
                f"{source_name}に掲載された『{clean_title}』に関する報道記事です。"
            ),
            "url": article_url,
            "tags": ["宇都宮メディア・アーツ", source_name],
        })
    except Exception as e:
      print(f"Error: {e}")

  return fetched_items


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
    print(f"成功: {added_count} 件の記事を追加しました。")


if __name__ == "__main__":
  update_articles_json()
