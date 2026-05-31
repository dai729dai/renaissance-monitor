import requests
from bs4 import BeautifulSoup
import os
import re
import json

SEARCH_URL = "https://auctions.yahoo.co.jp/search/search?aq=-1&auccat=&ei=utf-8&fr=auc_top&oq=&p=%E3%83%AB%E3%83%8D%E3%82%B5%E3%83%B3%E3%82%B9%20%E6%A0%AA%E4%B8%BB%E5%84%AA%E5%BE%85&sc_i=&tab_ex=commerce"

headers = {
    "User-Agent": "Mozilla/5.0"
}

# =========================
# 検索ページ取得
# =========================
response = requests.get(
    SEARCH_URL,
    headers=headers,
    timeout=30
)

print("status:", response.status_code)

html = response.text

print("pageData =>", "pageData" in html)
print("__NEXT_DATA__ =>", "__NEXT_DATA__" in html)
print("productName =>", "productName" in html)

# =========================
# とりあえず従来のHTML抽出（暫定）
# =========================
soup = BeautifulSoup(html, "lxml")

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

for item in items[:5]:
    print()
    print("TITLE:", item["title"])
    print("URL:", item["url"])

# =========================
# Discord通知（検索結果）
# =========================
webhook = os.environ["DISCORD_WEBHOOK"]

message = "Yahoo取得成功（検索）\n\n"

for item in items[:3]:
    message += (
        f"{item['title']}\n"
        f"{item['url']}\n\n"
    )

requests.post(
    webhook,
    json={"content": message[:1800]},
    timeout=30
)

# =========================
# デバッグ保存
# =========================
with open("debug.html", "w", encoding="utf-8") as f:
    f.write(html)

print("html saved")

# =========================================================
# ★ 商品ページ取得テスト（ここからが重要）
# =========================================================

auction_url = "https://auctions.yahoo.co.jp/jp/auction/s1231564200"

auction_response = requests.get(
    auction_url,
    headers=headers,
    timeout=30
)

print("auction status:", auction_response.status_code)

auction_html = auction_response.text

# =========================
# pageData 抽出（本命）
# =========================
match = re.search(
    r"var pageData = (.*?);</script>",
    auction_html,
    re.DOTALL
)

if match:
    try:
        page_data = json.loads(match.group(1))
        item = page_data["items"]

        print("\n=== ITEM INFO ===")
        print("TITLE:", item.get("productName"))
        print("PRICE:", item.get("price"))
        print("BIDS:", item.get("bids"))
        print("ENDTIME:", item.get("endtime"))

        # =========================
        # Discord通知（商品）
        # =========================
        message = (
            "Yahooオークション監視（商品）\n\n"
            f"タイトル: {item.get('productName')}\n"
            f"価格: {item.get('price')}円\n"
            f"入札数: {item.get('bids')}\n"
            f"終了: {item.get('endtime')}\n\n"
            f"{auction_url}"
        )

        requests.post(
            webhook,
            json={"content": message[:1800]},
            timeout=30
        )

    except Exception as e:
        print("pageData parse error:", e)

else:
    print("pageData not found in auction page")
