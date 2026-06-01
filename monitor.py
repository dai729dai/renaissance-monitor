import requests
import os
import re
import json
from datetime import datetime, timedelta

SEARCH_URL = "https://auctions.yahoo.co.jp/search/search?aq=-1&auccat=&ei=utf-8&fr=auc_top&oq=&p=%E3%83%AB%E3%83%8D%E3%82%B5%E3%83%B3%E3%82%B9%20%E6%A0%AA%E4%B8%BB%E5%84%AA%E5%BE%85"

headers = {"User-Agent": "Mozilla/5.0"}

webhook = os.environ["DISCORD_WEBHOOK"]

# -------------------------
# 枚数抽出（安定版）
# -------------------------
def extract_quantity(text):
    if not text:
        return 1

    text = text.replace("２","2").replace("３","3").replace("４","4").replace("５","5")

    m = re.search(r'(\d+)\s*枚', text)
    if m:
        return int(m.group(1))

    return 1


# -------------------------
# 時間（安全版）
# -------------------------
def parse_endtime(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except:
        return None


# -------------------------
# 検索
# -------------------------
r = requests.get(SEARCH_URL, headers=headers, timeout=30)
html = r.text

auction_urls = re.findall(
    r'https://auctions\.yahoo\.co\.jp/jp/auction/[a-zA-Z0-9]+',
    html
)

auction_urls = list(dict.fromkeys(auction_urls))

print("urls:", len(auction_urls))

valid_items = []

# -------------------------
# 商品ループ
# -------------------------
for url in auction_urls[:10]:

    try:
        r = requests.get(url, headers=headers, timeout=20)
        html = r.text

        match = re.search(r"var pageData = (.*?);</script>", html, re.DOTALL)
        if not match:
            continue

        data = json.loads(match.group(1))
        item = data["items"]

        title = item.get("productName","")
        price = int(item.get("price",0))
        endtime = item.get("endtime","")

        qty = extract_quantity(title)

        unit = price / qty

        print("DEBUG:", title, price, qty, unit)

        # ★ 条件（まずはゆるく）
        if unit > 1500:
            continue

        if qty > 10:
            continue

        end_dt = parse_endtime(endtime)

print("ENDTIME:", endtime)

if end_dt:

    remaining = end_dt - datetime.now()

    print(
        "REMAINING HOURS:",
        remaining.total_seconds() / 3600
    )

    if remaining.total_seconds() > 5 * 3600:
        print("SKIP: more than 5 hours remaining")
        continue

    if remaining.total_seconds() < 0:
        print("SKIP: already ended")
        continue
        
        valid_items.append((title, price, qty, unit, url))

    except Exception as e:
        print("error:", e)


# -------------------------
# Discord
# -------------------------
print("VALID:", len(valid_items))

if valid_items:

    msg = "🔥 ヒット\n\n"

    for v in valid_items:
        msg += f"{v[0]}\n{v[1]}円 / {v[2]}枚 / {v[3]:.0f}円\n{v[4]}\n\n"

    requests.post(webhook, json={"content": msg[:1800]})

else:
    print("NO MATCH → relax conditions or debug filters")

print("TEST WEBHOOK")

r = requests.post(
    webhook,
    json={"content": "Webhookテスト"},
    timeout=30
)

print("WEBHOOK STATUS:", r.status_code)
print("WEBHOOK RESPONSE:", r.text)
