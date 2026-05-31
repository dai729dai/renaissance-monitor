import requests
import os
import re
import json
from datetime import datetime, timedelta

SEARCH_URL = "https://auctions.yahoo.co.jp/search/search?aq=-1&auccat=&ei=utf-8&fr=auc_top&oq=&p=%E3%83%AB%E3%83%8D%E3%82%B5%E3%83%B3%E3%82%B9%20%E6%A0%AA%E4%B8%BB%E5%84%AA%E5%BE%85&sc_i=&tab_ex=commerce"

headers = {
    "User-Agent": "Mozilla/5.0"
}

webhook = os.environ["DISCORD_WEBHOOK"]

# =========================================================
# ■ ユーティリティ
# =========================================================
def extract_quantity(text):
    match = re.search(r'(\d+)\s*枚', text)
    if match:
        return int(match.group(1))
    return None


def parse_endtime(endtime_str):
    try:
        return datetime.strptime(endtime_str, "%Y-%m-%d %H:%M:%S")
    except:
        return None


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

# =========================================================
# ■ URL抽出
# =========================================================
auction_urls = re.findall(
    r'https://auctions\.yahoo\.co\.jp/jp/auction/[a-zA-Z0-9]+',
    html
)

auction_urls = list(dict.fromkeys(auction_urls))

print("found urls:", len(auction_urls))

# =========================================================
# ■ 商品チェック
# =========================================================
valid_items = []

for url in auction_urls[:10]:

    try:
        r = requests.get(url, headers=headers, timeout=20)
        html = r.text

        match = re.search(
            r"var pageData = (.*?);</script>",
            html,
            re.DOTALL
        )

        if not match:
            continue

        data = json.loads(match.group(1))
        item = data["items"]

        title = item.get("productName", "")
        price = int(item.get("price", 0))
        endtime_str = item.get("endtime", "")

        quantity = extract_quantity(title)

        print("DEBUG:", title, price, quantity)

        # =====================================================
        # ■ 基本チェック
        # =====================================================
        if quantity is None:
            continue

        unit_price = price / quantity

        # =====================================================
        # ■ 条件①：単価1000円以下（変更済）
        # =====================================================
        if unit_price > 1000:
            continue

        # =====================================================
        # ■ 条件②：10枚以下
        # =====================================================
        if quantity > 10:
            continue

        # =====================================================
        # ■ 条件③：残り5時間以内（重要修正）
        # =====================================================
        end_dt = parse_endtime(endtime_str)

        if end_dt is None:
            continue

        now = datetime.now()
        remaining = end_dt - now

        if remaining.total_seconds() > 5 * 3600:
            continue

        if remaining.total_seconds() < 0:
            continue

        # =====================================================
        # ■ 合格
        # =====================================================
        valid_items.append({
            "title": title,
            "price": price,
            "quantity": quantity,
            "unit_price": unit_price,
            "endtime": endtime_str,
            "remaining_min": int(remaining.total_seconds() / 60),
            "url": url
        })

        print("MATCH:", title)

    except Exception as e:
        print("error:", e)

# =========================================================
# ■ Discord通知
# =========================================================
if valid_items:

    message = "🎯 条件一致アイテム発見\n\n"

    for item in valid_items:
        message += (
            f"{item['title']}\n"
            f"総額: {item['price']}円\n"
            f"枚数: {item['quantity']}\n"
            f"単価: {item['unit_price']:.0f}円/枚\n"
            f"残り: {item['remaining_min']}分\n"
            f"{item['url']}\n\n"
        )

    requests.post(
        webhook,
        json={"content": message[:1800]},
        timeout=30
    )

    print("Discord sent")

else:
    print("no matching items")

print("valid items:", len(valid_items))
