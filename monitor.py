import requests
import os
import re
import json

SEARCH_URL = "https://auctions.yahoo.co.jp/search/search?aq=-1&auccat=&ei=utf-8&fr=auc_top&oq=&p=%E3%83%AB%E3%83%8D%E3%82%B5%E3%83%B3%E3%82%B9%20%E6%A0%AA%E4%B8%BB%E5%84%AA%E5%BE%85&sc_i=&tab_ex=commerce"

headers = {
    "User-Agent": "Mozilla/5.0"
}

webhook = os.environ["DISCORD_WEBHOOK"]

# =========================================================
# ■ 検索ページ取得
# =========================================================
response = requests.get(
    SEARCH_URL,
    headers=headers,
    timeout=30
)

print("status:", response.status_code)

html = response.text

print("pageData =>", "pageData" in html)

# =========================================================
# ■ 検索 pageData 抽出
# =========================================================
search_data = None

match = re.search(
    r'var pageData = (.*?);</script>',
    html,
    re.DOTALL
)

if match:
    try:
        search_data = json.loads(match.group(1))
        print("SEARCH pageData FOUND")

        # ★ここに追加
        print(json.dumps(search_data, indent=2, ensure_ascii=False)[:3000])
    
    except Exception as e:
        print("search pageData parse error:", e)
else:
    print("search pageData NOT FOUND")

# =========================================================
# ■ 商品URL抽出（JSONのみ）
# =========================================================
items = []

if search_data:

    raw_items = search_data.get("items")

    if isinstance(raw_items, dict):
        raw_items = raw_items.get("items") or raw_items.get("list")

    if isinstance(raw_items, list):
        for it in raw_items:
            if not isinstance(it, dict):
                continue

            title = it.get("title") or it.get("productName")
            url = it.get("url") or it.get("itemUrl") or it.get("auctionUrl")

            if title and url:
                items.append({
                    "title": title,
                    "url": url
                })

print("item count:", len(items))

# =========================================================
# ■ Discord（検索結果）
# =========================================================
message = "Yahoo取得成功（検索）\n\n"

for item in items[:5]:
    message += f"{item['title']}\n{item['url']}\n\n"

requests.post(
    webhook,
    json={"content": message[:1800]},
    timeout=30
)

# =========================================================
# ■ 商品ページテスト
# =========================================================

auction_url = "https://auctions.yahoo.co.jp/jp/auction/s1231564200"

auction_response = requests.get(
    auction_url,
    headers=headers,
    timeout=30
)

print("auction status:", auction_response.status_code)

auction_html = auction_response.text

# =========================================================
# ■ 商品 pageData 抽出
# =========================================================
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
