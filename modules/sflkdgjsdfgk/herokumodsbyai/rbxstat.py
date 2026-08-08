import httpx
import io
from herokutl.types import Message
from .. import loader, utils

# meta developer: @modsbyai

@loader.tds
class RobloxInfoMod(loader.Module):
    """Информация о пользователях Roblox. Можно искать по ID и юзернейму."""
    
    strings = {
        "name": "RobloxUser",
        "loading": "<b>[Roblox]</b> Чтение профиля... 🕵️‍♂️",
        "no_args": "<b>[Roblox]</b> Введите ID или имя игрока.",
        "not_found": "<b>[Roblox]</b> Игрок не найден. ❌",
        "user_card": (
            "<b>👤 Игрок:</b> <code>{name}</code> (<code>{display}</code>)\n"
            "<b>🆔 ID:</b> <code>{id}</code>\n"
            "<b>🛡 Статус:</b> {status}\n"
            "<b>💎 Premium:</b> {premium}\n"
            "<b>📅 Регистрация:</b> <code>{created}</code>\n"
            "<b>📝 О себе:</b>\n<i>{description}</i>\n\n"
            "<b>🔗 <a href='https://www.roblox.com/users/{id}/profile'>Профиль в Roblox</a></b>"
        ),
        "how_id": (
            "<b>❓ Как найти ID:</b>\n"
            "В ссылке <code>roblox.com/users/12345/profile</code> число <b>12345</b> — это ваш ID."
        )
    }

    async def fetch(self, url, method="GET", json_data=None):
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            try:
                r = await (client.post(url, json=json_data) if method == "POST" else client.get(url))
                return r.json() if r.status_code == 200 else None
            except: return None

    @loader.command(ru_doc="Информация об игроке")
    async def ruser(self, message: Message):
        """<id/имя> - Инфо об игроке"""
        args = utils.get_args_raw(message)
        if not args: return await utils.answer(message, self.strings["no_args"])
        await utils.answer(message, self.strings["loading"])

        u_id = args
        if not args.isdigit():
            res = await self.fetch("https://users.roblox.com/v1/usernames/users", "POST", {"usernames": [args]})
            if not res or not res['data']: return await utils.answer(message, self.strings["not_found"])
            u_id = res['data'][0]['id']

        data = await self.fetch(f"https://users.roblox.com/v1/users/{u_id}")
        if not data: return await utils.answer(message, self.strings["not_found"])

        # Данные
        membership = "✅ Активен" if data.get("isPremium") else "❌ Нет"
        is_banned = "🔴 Забанен" if data.get("isBanned") else "🟢 Активен"
        
        # Аватарка 720x720 (максимум для API)
        thumb = await self.fetch(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={u_id}&size=720x720&format=Png")
        img_url = thumb['data'][0]['imageUrl'] if thumb and thumb.get('data') else None

        txt = self.strings["user_card"].format(
            name=data.get("name"),
            display=data.get("displayName"),
            id=u_id,
            status=is_banned,
            premium=membership,
            created=data.get("created")[:10],
            description=data.get("description") or "Не указано"
        )
        
        if img_url:
            async with httpx.AsyncClient() as client:
                resp = await client.get(img_url)
                if resp.status_code == 200:
                    img_data = io.BytesIO(resp.content)
                    img_data.name = f"roblox_{u_id}.png"
                    await message.delete()
                    return await message.client.send_file(message.chat_id, img_data, caption=txt, force_document=True)
        
        await utils.answer(message, txt)

    @loader.command(ru_doc="Инструкция по ID")
    async def rid(self, message: Message):
        """Инструкция по ID"""
        await utils.answer(message, self.strings["how_id"])

