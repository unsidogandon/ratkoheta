# meta developer: @coddan
from .. import loader, utils
import aiohttp
import urllib.parse
import logging

logger = logging.getLogger(__name__)

@loader.tds
class CityTimeMod(loader.Module):
    """Показывает текущее время в указанном городе"""
    
    strings = {
        "name": "CityTime",
        "no_city": "🌍 <b>Пожалуйста, укажите город!</b>\n<i>Пример:</i> <code>.time Москва</code>",
        "loading": "⏳ <b>Получение времени...</b>",
        "not_found": "❌ <b>Город не найден!</b>",
        "api_error": "❌ <b>Ошибка при получении данных от API!</b>",
        "error": "❌ <b>Произошла ошибка:</b> <code>{}</code>",
        "result": (
            "🌍 <b>Локация:</b> <code>{location}</code>\n"
            "🕒 <b>Время:</b> <code>{time}</code>\n"
            "📅 <b>Дата:</b> <code>{date}</code>\n"
            "🌐 <b>Часовой пояс:</b> <code>{timezone}</code>"
        )
    }

    @loader.command()
    async def timecmd(self, message):
        """<город> - Узнать текущее время в указанном городе"""
        city = utils.get_args_raw(message)
        if not city:
            return await utils.answer(message, self.strings("no_city"))

        message = await utils.answer(message, self.strings("loading"))

        try:
            async with aiohttp.ClientSession() as session:
                # 1. Geocoding via Nominatim (OpenStreetMap)
                geo_url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(city)}&format=json&limit=1&accept-language=ru"
                headers = {"User-Agent": "HikkaUserbot/CityTimeModule"}
                
                async with session.get(geo_url, headers=headers) as geo_resp:
                    if geo_resp.status != 200:
                        return await utils.answer(message, self.strings("api_error"))
                    
                    geo_data = await geo_resp.json()
                    if not geo_data:
                        return await utils.answer(message, self.strings("not_found"))
                    
                    lat = geo_data[0]['lat']
                    lon = geo_data[0]['lon']
                    display_name = geo_data[0]['display_name']

                # 2. Getting time via TimeAPI
                time_url = f"https://timeapi.io/api/Time/current/coordinate?latitude={lat}&longitude={lon}"
                
                async with session.get(time_url) as time_resp:
                    if time_resp.status != 200:
                        return await utils.answer(message, self.strings("api_error"))
                    
                    time_data = await time_resp.json()
                    
                    current_time = time_data.get("time", "Неизвестно")
                    date = time_data.get("date", "Неизвестно")
                    timezone = time_data.get("timeZone", "Неизвестно")

                    text = self.strings("result").format(
                        location=display_name,
                        time=current_time,
                        date=date,
                        timezone=timezone
                    )
                    
                    await utils.answer(message, text)

        except Exception as e:
            logger.error("CityTime error", exc_info=True)
            await utils.answer(message, self.strings("error").format(str(e)))
