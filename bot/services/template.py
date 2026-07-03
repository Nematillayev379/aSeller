from datetime import datetime


class TemplateBuilder:

    def _parse_desc(self, desc: str) -> dict:
        result = {"old_price": 0, "sizes": "", "colors": ""}
        if not desc:
            return result
        for part in desc.split("|"):
            if part.startswith("old:"):
                try:
                    result["old_price"] = int(part[4:])
                except ValueError:
                    pass
            elif part.startswith("sizes:"):
                result["sizes"] = part[6:]
            elif part.startswith("colors:"):
                result["colors"] = part[7:]
        return result

    def build_manual_ad_text(self, ad: dict) -> str:
        title = ad.get("title", "Mahsulot")
        new_price = ad.get("price", 0)
        desc = self._parse_desc(ad.get("description", ""))
        old_price = desc.get("old_price", 0)
        sizes = desc.get("sizes", "")
        colors = desc.get("colors", "")

        lines = ["#PREMIUM", ""]
        lines.append(f"<b>{title}</b>")
        lines.append("")

        if colors:
            lines.append(f"Rang: {colors}")
        if sizes:
            lines.append(f"O'lcham: {sizes}")

        if old_price > 0 and old_price > new_price:
            lines.append("")
            lines.append(f"<s>{old_price:,} so'm</s>")
            lines.append(f"<b>{new_price:,} so'm</b> + 🚚 Kargo")
        else:
            lines.append("")
            lines.append(f"<b>{new_price:,} so'm</b> + 🚚 Kargo")

        lines.append("")
        lines.append("Buyurtma berish uchun tugmani bosing 👇")

        return "\n".join(lines)

    def build_ad_text(self, ad: dict) -> str:
        title = ad.get("title", "Noma'lum")
        price = ad.get("price", 0)
        desc_raw = ad.get("description", "")

        if desc_raw and "|" in desc_raw:
            return self.build_manual_ad_text(ad)

        lines = ["#PREMIUM", ""]
        lines.append(f"<b>{title}</b>")
        lines.append("")
        lines.append(f"Narx: <b>{price:,} so'm</b>")
        lines.append("")
        lines.append("Buyurtma berish uchun tugmani bosing 👇")

        return "\n".join(lines)

    def build_scraped_ad_text(self, product: dict) -> str:
        title = product.get("title", "Noma'lum mahsulot")
        price = product.get("price", 0)
        original_price = product.get("original_price", 0)
        discount = product.get("discount", 0)
        source = product.get("source", "")

        lines = ["#PREMIUM", ""]
        lines.append(f"<b>{title}</b>")
        lines.append("")

        if original_price > price and original_price > 0:
            lines.append(f"<s>{original_price:,} so'm</s>")
            lines.append(f"<b>{price:,} so'm</b> + 🚚 Kargo")
            if discount > 0:
                lines.append(f"Chegirma: -{discount}%")
        else:
            lines.append(f"<b>{price:,} so'm</b> + 🚚 Kargo")

        lines.append("")

        if source:
            lines.append(f"Manba: {source}")

        lines.append("")
        lines.append("Buyurtma berish uchun tugmani bosing 👇")

        return "\n".join(lines)

    def build_order_confirm(self, full_name: str, product_name: str,
                            price: int, prepay_percent: int, prepay_amount: int) -> str:
        return (
            "✅ Buyurtma qabul qilindi!\n\n"
            f"Ism: {full_name}\n"
            f"Mahsulot: {product_name}\n"
            f"Narx: {price:,} so'm\n"
            f"Oldindan to'lov: {prepay_percent}% = {prepay_amount:,} so'm\n\n"
            "Siz bilan tez orada bog'lanamiz!"
        )

    def build_order_notification(self, user_id: int, username: str, full_name: str,
                                  phone: str, address: str, product_name: str,
                                  price: int, prepay_percent: int, prepay_amount: int,
                                  comment: str, ad_id: int) -> str:
        text = (
            "🛒 <b>Yangi buyurtma!</b>\n\n"
            f"ID: #{ad_id}\n"
            f"Foydalanuvchi: {full_name} (@{username})\n"
            f"Telegram ID: <code>{user_id}</code>\n"
            f"Telefon: {phone}\n"
            f"Manzil: {address}\n"
            f"Mahsulot: {product_name}\n"
            f"Narx: {price:,} so'm\n"
            f"Oldindan to'lov: {prepay_percent}% = {prepay_amount:,} so'm\n"
        )
        if comment:
            text += f"Izoh: {comment}\n"
        return text

    def build_ads_list(self, ads: list) -> str:
        if not ads:
            return "📭 Reklamalar yo'q."
        text = "📦 <b>Reklamalar ro'yxati</b>\n\n"
        for ad in ads:
            status = "✅" if ad["is_posted"] else "⏳"
            text += (
                f"{status} #{ad['id']} | {ad['title'][:30]}\n"
                f"    💰 {ad['price']:,} so'm\n\n"
            )
        return text

    def build_channels_list(self, channels: list) -> str:
        if not channels:
            return "📢 Kanallar qo'shilmagan."
        text = "📢 <b>Kanallar</b>\n\n"
        for ch in channels:
            status = "✅" if ch["is_active"] else "❌"
            text += f"{status} {ch['channel_name']}\n"
        return text

    def build_stats_message(self, ad_stats: dict, order_stats: dict, channels: list) -> str:
        return (
            "📊 <b>Statistika</b>\n\n"
            f"📦 Reklamalar: {ad_stats['total']} ta\n"
            f"    ✅ Joylangan: {ad_stats['posted']}\n"
            f"    ⏳ Kutishda: {ad_stats['unposted']}\n\n"
            f"🛒 Buyurtmalar: {order_stats['total']} ta\n"
            f"    ⏳ Kutishda: {order_stats['pending']}\n"
            f"    ✅ Bajarilgan: {order_stats['completed']}\n\n"
            f"📢 Kanallar: {len(channels)} ta faol"
        )

    def build_orders_list(self, orders: list) -> str:
        if not orders:
            return "🛒 Buyurtmalar yo'q."
        text = "🛒 <b>So'nggi buyurtmalar</b>\n\n"
        for o in orders:
            status = "⏳" if o["status"] == "pending" else "✅" if o["status"] == "completed" else "❌"
            text += (
                f"{status} #{o['id']} | {o['full_name']}\n"
                f"    📱 {o['phone']}\n"
                f"    📦 {o['product_name'][:30]}\n"
                f"    💰 {o['product_price']:,} so'm ({o['prepay_percent']}%)\n\n"
            )
        return text

    def build_admin_users_list(self, users: list) -> str:
        if not users:
            return "👥 Admin foydalanuvchilar yo'q."
        text = "👥 <b>Admin foydalanuvchilar</b>\n\n"
        for u in users:
            text += f"• {u['full_name']} (<code>{u['user_id']}</code>)\n"
        return text


template_builder = TemplateBuilder()
