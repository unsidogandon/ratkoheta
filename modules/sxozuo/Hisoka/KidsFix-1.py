# ██╗  ██╗██╗███████╗ ██████╗ ██╗  ██╗ █████╗
# ██║  ██║██║██╔════╝██╔═══██╗██║ ██╔╝██╔══██╗
# ███████║██║███████╗██║   ██║█████╔╝ ███████║
# ██╔══██║██║╚════██║██║   ██║██╔═██╗ ██╔══██║
# ██║  ██║██║███████║╚██████╔╝██║  ██╗██║  ██║
# ╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
# © 2026 @zaduman | All rights reserved
"""
Модуль для работы с VexBoost API
"""

version = (1, 0, 0)

# meta developer: @zaduman
# scope: hikka_only

import aiohttp
from .. import loader, utils

@loader.tds
class KidsModule(loader.Module):    
    strings = {
        "name": "детишки)",
        "no_key": "<blockquote><b>❌ Ключ API не установлен. Используй</b> <code>.kids key [ключ]</code></blockquote>",
        "no_args": "<blockquote><b>❌ Недостаточно аргументов. Примеры:</b>\n<code>.kids @user 100</code> — накрутка\n<code>.kids hate [ссылка]</code> — хейт (100 по дефолту)\n<code>.kids join [ссылка] 50</code> — вступление\n<code>.kids key [ключ]</code> — привязать API</blockquote>",
        "key_saved": "<blockquote><b>✅ Ключ успешно сохранен.</b></blockquote>",
        "ordering": "<blockquote><b><tg-emoji emoji-id='5413565908763321185'>🚀</tg-emoji> дети запущены на {}...</b></blockquote>",
        "success": "<blockquote><b><tg-emoji emoji-id='5458461648585000046'>😎</tg-emoji> дети падъехали</b></blockquote>",
        "error": "<blockquote><b>❌ Ошибка: {}</b></blockquote>"
    }

    async def client_ready(self, client, db):
        self.db = db

    @loader.command()
    async def kids(self, message):
        """Модуль для работы с VexBoost API"""
        args = utils.get_args_raw(message).split()
        
        if not args:
            await utils.answer(message, self.strings("no_args"), parse_mode="HTML")
            return

        if args[0].lower() == "key":
            if len(args) < 2:
                await utils.answer(message, self.strings("no_args"), parse_mode="HTML")
                return
            key = args[1]
            self.db.set("KidsModule", "api_key", key)
            await utils.answer(message, self.strings("key_saved"), parse_mode="HTML")
            return

        key = self.db.get("KidsModule", "api_key")
        if not key:
            await utils.answer(message, self.strings("no_key"), parse_mode="HTML")
            return

        mode = args[0].lower()
        
        if mode == "hate":
            if len(args) < 2:
                await utils.answer(message, self.strings("no_args"), parse_mode="HTML")
                return
            service_id = "2354"
            target_link = args[1]
            quantity = args[2] if len(args) > 2 else "100"
            display_target = "сообщение (hate)"
        
        elif mode == "join":
            if len(args) < 2:
                await utils.answer(message, self.strings("no_args"), parse_mode="HTML")
                return
            service_id = "2972"
            target_link = args[1]
            if not target_link.startswith("https://t.me/"):
                target_link = f"https://t.me/{target_link.lstrip('@')}"
            quantity = args[2] if len(args) > 2 else "100"
            display_target = "ресурс (join)"
            
        else:
            service_id = "1753"
            target_link = args[0]
            if not target_link.startswith("http"):
                target_link = f"https://t.me/{target_link.lstrip('@')}"
            quantity = args[1] if len(args) > 1 else "100"
            display_target = target_link

        await utils.answer(message, self.strings("ordering").format(display_target), parse_mode="HTML")

        url = "https://vexboost.ru/api/v2"
        params = {
            "action": "add",
            "service": service_id,
            "link": target_link,
            "quantity": quantity,
            "key": key
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    if "order" in data:
                        await utils.answer(message, self.strings("success"), parse_mode="HTML")
                    else:
                        error_msg = data.get("error", "Unknown error")
                        await utils.answer(message, self.strings("error").format(error_msg), parse_mode="HTML")
            except Exception as e:
                await utils.answer(message, self.strings("error").format(str(e)), parse_mode="HTML")