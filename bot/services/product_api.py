import asyncio
import aiohttp
import random
import re
import logging
from bs4 import BeautifulSoup
from typing import Optional

log = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

STORES = [
    {
        "name": "1688",
        "search_url": "https://s.1688.com/selloffer/offer_search.htm?keywords={query}",
        "selectors": {
            "card": ".sm-offer-item, .offer-list-row, [data-offer]",
            "title": ".offer-title, .sm-offer-titleMod__title, h4",
            "price": ".sm-offer-priceNum, .price, [class*='price']",
            "image": "img",
            "link": "a[href*='detail']",
        },
    },
    {
        "name": "Taobao",
        "search_url": "https://s.taobao.com/search?q={query}&imgfile=&js=1&stats_click=search_radio_all%3A1",
        "selectors": {
            "card": ".Card--doubleCardWrapper--L2XFE75, .items .item, [class*='card']",
            "title": ".Title--title--jCOPvpf, [class*='title'] span, h3",
            "price": ".Price--priceInt--ZlsSi_M, [class*='price'] span",
            "image": "img",
            "link": "a[href*='item']",
        },
    },
    {
        "name": "JD",
        "search_url": "https://search.jd.com/Search?keyword={query}&enc=utf-8",
        "selectors": {
            "card": ".gl-item, .J_goodsList li, [class*='goods-item']",
            "title": ".p-name em, .p-name a, [class*='title']",
            "price": ".p-price strong i, .p-price span, [class*='price']",
            "image": "img",
            "link": "a[href*='item']",
        },
    },
    {
        "name": "DHgate",
        "search_url": "https://www.dhgate.com/wholesale/search.do?searchkey={query}",
        "selectors": {
            "card": ".product-list .product, .base-content .item, [class*='product']",
            "title": ".product-title, .prod-title, [class*='title']",
            "price": ".product-price, .prod-price, [class*='price']",
            "image": "img",
            "link": "a[href*='product']",
        },
    },
]


class ProductAPI:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    def _headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
        }

    def _extract_price(self, text: str) -> float:
        if not text:
            return 0.0
        cleaned = text.replace(",", "").replace(" ", "").replace("$", "").replace("¥", "").replace("￥", "")
        numbers = re.findall(r"[\d]+\.?[\d]*", cleaned)
        for n in numbers:
            try:
                val = float(n)
                if 0.01 < val < 500000:
                    return val
            except ValueError:
                continue
        return 0.0

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()[:150]

    async def _scrape_store(self, store: dict, query: str, max_results: int = 5) -> list:
        try:
            session = await self._get_session()
            url = store["search_url"].format(query=query.replace(" ", "+"))
            async with session.get(url, headers=self._headers(), timeout=aiohttp.ClientTimeout(total=15), ssl=False) as resp:
                if resp.status != 200:
                    return []
                html = await resp.text()

            soup = BeautifulSoup(html, "lxml")
            products = []
            sels = store["selectors"]

            cards = soup.select(sels["card"])[:max_results]
            if not cards:
                cards = soup.find_all("div", class_=re.compile(r"(item|card|product|offer)", re.I))[:max_results]

            for card in cards:
                try:
                    title = ""
                    for sel in sels["title"].split(", "):
                        el = card.select_one(sel.strip())
                        if el:
                            title = self._clean_text(el.get_text())
                            if title:
                                break

                    price = 0.0
                    for sel in sels["price"].split(", "):
                        el = card.select_one(sel.strip())
                        if el:
                            price = self._extract_price(el.get_text())
                            if price > 0:
                                break

                    image_url = ""
                    img = card.select_one("img")
                    if img:
                        image_url = img.get("src", "") or img.get("data-src", "") or img.get("data-lazy-img", "")
                        if image_url and not image_url.startswith("http"):
                            image_url = "https:" + image_url

                    product_url = ""
                    link = card.select_one("a")
                    if link:
                        href = link.get("href", "")
                        if href:
                            product_url = href if href.startswith("http") else f"https:{href}"

                    if title and price > 0:
                        products.append({
                            "title": title,
                            "price": int(price * 12800),
                            "original_price": int(price * 12800),
                            "image_url": image_url,
                            "product_url": product_url,
                            "source": store["name"],
                            "external_id": "",
                            "discount": 0,
                        })
                except Exception:
                    continue

            return products
        except Exception as e:
            log.warning("Scraping xatosi (%s): %s", store["name"], e)
            return []

    async def fetch_random_products(self, count: int = 3) -> list:
        from bot.config import USD_TO_UZS, CATEGORIES
        from bot.services.database import db

        markup_pct = 0
        try:
            markup_str = await db.get_setting("markup_percent")
            markup_pct = int(markup_str) if markup_str else 0
        except Exception:
            pass

        category = random.choice(CATEGORIES)
        log.info("Kategoriya: %s", category)

        tasks = [self._scrape_store(store, category, 5) for store in STORES]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_products = []
        for r in results:
            if isinstance(r, list):
                all_products.extend(r)

        if not all_products:
            log.warning("Scrapingdan mahsulot topilmadi, fallback ishlatiladi")
            all_products = self._get_fallback(category)

        if markup_pct > 0:
            for p in all_products:
                p["price"] = int(p["price"] * (1 + markup_pct / 100))

        random.shuffle(all_products)
        return all_products[:count]

    def _get_fallback(self, category: str = "") -> list:
        USD_TO_UZS = 12800
        products = [
            {
                "title": "Wireless Bluetooth TWS Quloqchin 5.3",
                "price": int(4.99 * USD_TO_UZS),
                "original_price": int(9.99 * USD_TO_UZS),
                "image_url": "https://images.unsplash.com/photo-1590658268037-6bf12f032f55?w=400",
                "product_url": "https://aliexpress.com",
                "source": "1688",
                "external_id": "",
                "discount": 50,
            },
            {
                "title": "Smart Watch Sport Band IP68",
                "price": int(8.50 * USD_TO_UZS),
                "original_price": int(15.00 * USD_TO_UZS),
                "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400",
                "product_url": "https://taobao.com",
                "source": "Taobao",
                "external_id": "",
                "discount": 43,
            },
            {
                "title": "USB-C Zaryadlash Simi 100W 2m",
                "price": int(1.50 * USD_TO_UZS),
                "original_price": int(3.00 * USD_TO_UZS),
                "image_url": "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=400",
                "product_url": "https://jd.com",
                "source": "JD",
                "external_id": "",
                "discount": 50,
            },
            {
                "title": "Mini Bluetooth Speaker 360 Sound",
                "price": int(5.99 * USD_TO_UZS),
                "original_price": int(12.00 * USD_TO_UZS),
                "image_url": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400",
                "product_url": "https://dhgate.com",
                "source": "DHgate",
                "external_id": "",
                "discount": 50,
            },
            {
                "title": "LED Stol Chirog'i USB Zaryad",
                "price": int(3.20 * USD_TO_UZS),
                "original_price": int(6.50 * USD_TO_UZS),
                "image_url": "https://images.unsplash.com/photo-1507473885765-e6ed057ab6fe?w=400",
                "product_url": "https://1688.com",
                "source": "1688",
                "external_id": "",
                "discount": 51,
            },
            {
                "title": "Telefon Uchun Magnit Ushtutkasi",
                "price": int(1.20 * USD_TO_UZS),
                "original_price": int(2.50 * USD_TO_UZS),
                "image_url": "https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?w=400",
                "product_url": "https://taobao.com",
                "source": "Taobao",
                "external_id": "",
                "discount": 52,
            },
            {
                "title": "Sport Sumka Crossbody Bag",
                "price": int(6.80 * USD_TO_UZS),
                "original_price": int(14.00 * USD_TO_UZS),
                "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400",
                "product_url": "https://dhgate.com",
                "source": "DHgate",
                "external_id": "",
                "discount": 51,
            },
            {
                "title": "Mekanik Bluetooth Klaviatura",
                "price": int(12.00 * USD_TO_UZS),
                "original_price": int(25.00 * USD_TO_UZS),
                "image_url": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=400",
                "product_url": "https://jd.com",
                "source": "JD",
                "external_id": "",
                "discount": 52,
            },
        ]
        random.shuffle(products)
        return products


product_api = ProductAPI()
