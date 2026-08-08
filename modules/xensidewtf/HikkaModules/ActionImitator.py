# -*- coding: utf-8 -*-
from asyncio import sleep, create_task
from telethon import functions, types
from .. import loader, utils
import random

__version__ = (1, 0, 3)

#░█░█░█▀▀░█▀█░█▀▀░▀█▀░█▀▄░█▀▀
#░▄▀▄░█▀▀░█░█░▀▀█░░█░░█░█░█▀▀
#░▀░▀░▀▀▀░▀░▀░▀▀▀░▀▀▀░▀▀▀░▀▀░░▀▀▀

# 🔒 Licensed under All Rights Reserved.
# meta developer: @XenSideMOD

@loader.tds
class ImitateMod(loader.Module):
    """Имитирует активность в чате """

    strings = {
        "name": "Imitate",
        "imitate_started": "<blockquote>✅ Имитация '{}' в этом чате запущена</blockquote>",
        "imitate_stopped": "<blockquote>🛑 Имитация в этом чате остановлена</blockquote>",
        "imitate_invalid": "<blockquote>⚠️ Укажи тип действия. Пример: .imitate typing</blockquote>",
        "imitate_already": "<blockquote>⚠️ В этом чате уже запущена имитация. Остановите её командой .simit</blockquote>",
        "imitate_unknown": "<blockquote>⚠️ Неизвестный тип действия. Доступные: {}</blockquote>"
    }

    def __init__(self):
        self.tasks = {}
        self.actions = [
            "typing", "voice", "game", "video", "photo", 
            "document", "location", "record-video", "record-audio", 
            "record-round", "scrn", "mixed"
        ]

    async def imitatecmd(self, message):
        """Типы: typing, voice, game, video, photo, document, location, record-video, record-audio, record-round, scrn, mixed"""
        args = utils.get_args(message)
        if not args:
            await utils.answer(message, self.strings["imitate_invalid"])
            return

        action = args[0].lower()
        chat_id = message.chat_id
        if chat_id in self.tasks and not self.tasks[chat_id].done():
            await utils.answer(message, self.strings["imitate_already"])
            return

        if action not in self.actions:
            await utils.answer(message, self.strings["imitate_unknown"].format(", ".join(self.actions)))
            return

        if action == "scrn":
            await message.client(functions.messages.SendScreenshotNotificationRequest(
                peer=message.to_id,
                reply_to=types.InputReplyToMessage(reply_to_msg_id=message.id)
            ))
            await message.delete()
            return

        async def run_single_action():
            try:
                while True:
                    async with message.client.action(chat_id, action):
                        await sleep(1)
            except:
                return

        async def run_mixed_action():
            try:
                mixed_actions = [a for a in self.actions if a not in ["mixed", "scrn"]]
                while True:
                    current_action = random.choice(mixed_actions)
                    async with message.client.action(chat_id, current_action):
                        await sleep(1)
            except:
                return

        if action == "mixed":
            task = create_task(run_mixed_action())
        else:
            task = create_task(run_single_action())
        self.tasks[chat_id] = task
        
        await utils.answer(message, self.strings["imitate_started"].format(action))

    async def simitcmd(self, message):
        """Остановить СВО"""
        chat_id = message.chat_id
        if chat_id in self.tasks and not self.tasks[chat_id].done():
            self.tasks[chat_id].cancel()
            del self.tasks[chat_id]
            await utils.answer(message, self.strings["imitate_stopped"])
        else:
            await message.delete()