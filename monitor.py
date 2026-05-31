import requests
from bs4 import BeautifulSoup
import os

SEARCH_URL = "https://auctions.yahoo.co.jp/search/search?aq=-1&auccat=&ei=utf-8&fr=auc_top&oq=&p=%E3%83%AB%E3%83%8D%E3%82%B5%E3%83%B3%E3%82%B9%20%E6%A0%AA%E4%B8%BB%E5%84%AA%E5%BE%85&sc_i=&tab_ex=commerce"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(
    SEARCH_URL,
    headers=headers,
    timeout=30
)

print("status:", response.status_code)

print(response.text[:10000])

soup = BeautifulSoup(response.text, "lxml")

items = []

for a in soup.find_all("a", href=True):

    href = a["href"]
    text = a.get_text(strip=True)

    if (
        "auction" in href.lower()
        and len(text) > 10
    ):
        items.append({
            "title": text,
            "url": href
        })

print("item count:", len(items))

for item in items[:10]:

    print()
    print("TITLE:", item["title"])
    print("URL:", item["url"])

webhook = os.environ["DISCORD_WEBHOOK"]

message = "Yahoo取得成功\n\n"

for item in items[:3]:

    message += (
        f"{item['title']}\n"
        f"{item['url']}\n\n"
    )

requests.post(
    webhook,
    json={
        "content": message[:1800]
    },
    timeout=30
)

with open("debug.html", "w", encoding="utf-8") as f:
    f.write(response.text)

print("html saved")

# =========================
# 商品ページ取得テスト
# =========================

auction_url = "https://auctions.yahoo.co.jp/jp/auction/s1231564200"

auction_response = requests.get(
    auction_url,
    headers=headers,
    timeout=30
)

print("auction status:", auction_response.status_code)

print(auction_response.text[:5000])
