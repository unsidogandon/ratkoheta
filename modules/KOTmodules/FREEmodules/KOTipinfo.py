#meta developer: @kotcheat

import logging
import aiohttp
import asyncio
from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class KOTipinfoMod(loader.Module):
    """Анализатор IP-адресов (by @kotcheat)"""

    strings = {
        "name": "KOTipinfo",
        "no_ip": "<emoji document_id=5220197908342648622>❗️</emoji>️ Укажите IP-адрес: <code>.ip 1.1.1.1</code>",
        "invalid_ip": "<emoji document_id=5220053623211305785>❓</emoji> Некорректный IP-адрес",
        "analyzing": "<emoji document_id=5220070652756635426>👀</emoji> <b>Анализирую IP...</b>",
        "error": "<emoji document_id=5220053623211305785>❓</emoji> <b>Ошибка:</b> <code>{}</code>",
    }

    async def ipcmd(self, message):
        """🔍 Получает информацию об IP-адресе"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["no_ip"])
            return

        ip = args.strip()
        try:
            import ipaddress
            ipaddress.ip_address(ip)
        except ValueError:
            await utils.answer(message, self.strings["invalid_ip"])
            return

        msg = await utils.answer(message, self.strings["analyzing"])
        await asyncio.sleep(1)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://ip-api.com/json/{ip}?fields=status,message,country,city,org,lat,lon,timezone,hosting,proxy,vpn,mobile,countryCode"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data["status"] == "success":
                            result = f"<blockquote><b><emoji document_id=5257987903945986017>🐈</emoji> IP:</b> <code>{ip}</code></blockquote>\n\n"
                            
                            if data.get("country"):
                                country_code = f" ({data.get('countryCode')})" if data.get("countryCode") else ""
                                result += f"<blockquote><emoji document_id=5258079378159453410>✈️</emoji> <b>Страна:</b> {data['country']}{country_code}\n"
                            
                            if data.get("city"):
                                result += f"<emoji document_id=5258396243666681152>🔎</emoji> <b>Город:</b> {data['city']}\n"
                            
                            if data.get("timezone"):
                                result += f"<emoji document_id=5453900977432188793>⭐️</emoji> <b>Часовой пояс:</b> {data['timezone']}\n"
                            
                            if data.get("org"):
                                result += f"<emoji document_id=5235588635885054955>🎲</emoji> <b>Провайдер:</b> <code>{data['org']}</code></blockquote>\n"
                            
                            result += "\n"
                            
                            is_host = data.get("hosting", False)
                            result += f"<blockquote><emoji document_id=5258196742435787040>👾</emoji> <b>Хостинг:</b> {'Да' if is_host else 'Нет'}\n"
                            
                            mobile = data.get("mobile", False)
                            result += f"<emoji document_id=5453965363286925977>📞</emoji> <b>Мобильный:</b> {'Да' if mobile else 'Нет'}\n"
                            
                            vpn = data.get("vpn", False)
                            result += f"<emoji document_id=5260424249914435335>♨️</emoji> <b>VPN:</b> {'Обнаружен' if vpn else 'Не обнаружен'}\n"
                            
                            proxy = data.get("proxy", False)
                            result += f"<emoji document_id=5341492148468465410>📂</emoji> <b>Прокси:</b> {'Обнаружен' if proxy else 'Не обнаружен'}</blockquote>\n"
                            
                            latitude = data.get("lat")
                            longitude = data.get("lon")
                            if latitude and longitude:
                                google_maps_link = f"https://www.google.com/maps/place/{latitude},{longitude}"
                                result += f"\n<blockquote><emoji document_id=5397730656400714154>🏳️</emoji>️ <a href='{google_maps_link}'>Открыть на карте</a></blockquote>"
                            
                            await utils.answer(msg, result)
                        else:
                            await utils.answer(msg, self.strings["error"].format(data.get("message", "Unknown")))
                    else:
                        await utils.answer(msg, self.strings["error"].format(f"HTTP {response.status}"))
        except Exception as e:
            await utils.answer(msg, self.strings["error"].format(str(e)))
            logger.error(f"IP Info error: {str(e)}")

    async def on_dlmod(self):
        try:
            import aiohttp
        except ImportError:
            await self.download_lib("aiohttp")

    async def download_lib(self, lib_name):
        try:
            await utils.run_sync(lambda: __import__("pip").main(["install", lib_name]))
            return True
        except Exception:
            return False
