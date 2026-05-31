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


def is_within_5_hours(endtime_str):
    try:
        end_dt = datetime.strptime(endtime_str, "%Y-%m-%d %H:%M:%S")
        return end_dt <= datetime.now() + timedelta(hours=5)
    except:
        return False


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
# ■ URL抽出（安定版）
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

for url in auction_urls[:10]:  # 負荷制御

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
        endtime = item.get("endtime", "")

        quantity = extract_quantity(title)

        # =====================================================
        # ■ フィルタ条件
        # =====================================================

        # 枚数が取れないものはスキップ（精度優先）
        if quantity is None:
            continue

        # 単価計算（重要）
        unit_price = price / quantity

        print("DEBUG:", title, price, quantity, unit_price)

        # 条件1：単価1500円以下
        if unit_price > 1500:
            continue

        # 条件2：10枚以下
        if quantity > 10:
            continue

        # 条件3：終了5時間以内
        if not is_within_5_hours(endtime):
            continue

        valid_items.append({
            "title": title,
            "price": price,
            "quantity": quantity,
            "unit_price": unit_price,
            "endtime": endtime,
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
            f"終了: {item['endtime']}\n"
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
