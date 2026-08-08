__version__ = (1, 0, 0)
# meta developer: @weyrix & @RooniRN
from .. import loader, utils
import aiohttp

@loader.tds
class RNHostStatusMod(loader.Module):
    """Модуль для проверки статуса нод status.rnhost.ru"""
    strings = {"name": "RNHostStatus"}

    @loader.command(ru_doc="Узнать статус нод и панелей с rnhost")
    async def rnstatuscmd(self, message):
        """Выводит информацию о состоянии нод"""
        await utils.answer(message, "<b>🔄 Запрашиваю актуальные данные со status.rnhost.ru...</b>")
        
        api_info_url = "https://status.rnhost.ru/api/status-page/rnhost"
        api_heartbeat_url = "https://status.rnhost.ru/api/status-page/heartbeat/rnhost"
        
        try:
            async with aiohttp.ClientSession() as session:
                # 1. Структура
                async with session.get(api_info_url) as resp_info:
                    if resp_info.status != 200:
                        return await utils.answer(message, f"<b>❌ Ошибка получения структуры: код {resp_info.status}</b>")
                    data_info = await resp_info.json()
                
                # 2. Статистика
                async with session.get(api_heartbeat_url) as resp_heartbeat:
                    if resp_heartbeat.status != 200:
                        return await utils.answer(message, f"<b>❌ Ошибка получения статистики: код {resp_heartbeat.status}</b>")
                    data_heartbeat = await resp_heartbeat.json()
            
            result_text = "<b>📊 Статус серверов RNHost:</b>\n\n"
            
            groups = data_info.get("publicGroupList", [])
            uptime_list = data_heartbeat.get("uptimeList", {})
            heartbeat_list = data_heartbeat.get("heartbeatList", {})
            
            if not groups:
                return await utils.answer(message, "<b>⚠️ Не удалось получить список групп из API.</b>")

            for group in groups:
                group_name = group.get("name", "Неизвестная группа")
                
                # Создаем временную переменную для сбора текста ВСЕЙ группы
                group_text = f"<b>🌐 {group_name}</b>\n"
                
                monitors = group.get("monitorList", [])
                for monitor in monitors:
                    monitor_id = str(monitor.get("id"))
                    name = monitor.get("name", "Неизвестная нода")
                    
                    uptime_val = uptime_list.get(f"{monitor_id}_24")
                    
                    current_status = 1 
                    monitor_beats = heartbeat_list.get(monitor_id, [])
                    if monitor_beats:
                        current_status = monitor_beats[-1].get("status", 1)

                    if uptime_val is not None:
                        uptime_percent = uptime_val * 100
                        if uptime_percent >= 99.99:
                            status_text = "100%"
                        else:
                            status_text = f"{uptime_percent:.2f}%"
                    else:
                        status_text = "100%"

                    if current_status == 1:
                        emoji = "🟢"
                    elif current_status == 0:
                        emoji = "🔴"
                    elif current_status == 2:
                        emoji = "🟡"
                    elif current_status == 3:
                        emoji = "🔧"
                    else:
                        emoji = "🔵"
                        
                    group_text += f"{emoji} {name} — <b>{status_text}</b>\n"
                
                # Оборачиваем собранный текст группы в ОДНУ общую цитату
                result_text += f"<blockquote>{group_text.strip()}</blockquote>\n\n"
                
            result_text += "<i>Данные получены напрямую из API</i>"
            
            await utils.answer(message, result_text)

        except Exception as e:
            await utils.answer(message, f"<b>❌ Произошла ошибка при запросе к API:</b>\n<code>{e}</code>")
