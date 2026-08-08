# MIT License
# Copyright (c) 2025 zelenogoloviy
# ---------------------------------------------------------------------------------
# Name: AezaStatus
# Description: Модуль для проверки доступности аренды серверов Aeza.
# Author: @zelenogoloviy_m
# ---------------------------------------------------------------------------------
# meta developer: @zelenogoloviy_m
__version__ = (0, 1, 0)
from .. import loader, utils
import asyncio

@loader.tds
class AezaStatus(loader.Module):
    "Модуль для проверки доступности аренды серверов Aeza." 
    strings = {
        "name": "AezaStatus",
        "wait": "<emoji document_id=5328274090262275771>⏳</emoji>Секунду...",
        "no_response": "<emoji document_id=5210952531676504517>❌</emoji>Ошибка!",
        }
    strings_en = {
        "name": "AezaStatus",
        "wait": "<emoji document_id=5328274090262275771>⏳</emoji>Wait...",
        "no_response": "<emoji document_id=5210952531676504517>❌</emoji>Error",
        }
        
    @loader.command(
    en_doc="Check availability of Aeza servers for rent.",
    )
    async def statuscmd(self, message):
        """Проверить доступность аренды серверов на Aeza."""
        
        m = await utils.answer(message, self.strings["wait"])      
        try:
            async with self.client.conversation('@aezastatus_bot') as conv:
                await conv.send_message('/status')
                resp = await conv.get_response()
                await utils.answer(m, resp.text)
                await conv.mark_read()
                try:
                    await self.client.delete_messages('@aezastatus_bot', [resp.id, resp.id-1])                    
                except:
                    pass                 
        except asyncio.TimeoutError:
            await utils.answer(m, self.strings["no_response"])
