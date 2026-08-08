# MIT License
# Copyright (c) 2025 zelenogoloviy
# ---------------------------------------------------------------------------------
# Name: StringStreamMod
# Description: Модуль для построчного вывода текста с задержкой в инлайн-режиме.
# Author: @zelenogoloviy_m
# ---------------------------------------------------------------------------------
# meta developer: @zelenogoloviy_m
__version__ = (0, 1, 0)
from .. import loader, utils
import asyncio
from ..types import InlineCall
from hikkatl.types import Message

@loader.tds
class StringStreamMod(loader.Module):
    """Автоматический построчный вывод текста с задержкой в инлайн-режиме."""
    strings = {
        "name": "StringStream",
        "no_args": "Нет Аргументов",
    }
    strings_en = {
        "name": "StringStream",
        "no_args": "<emoji document_id=5210952531676504517>❌</emoji>No Args",
    }

    async def client_ready(self):
        self._stream_tasks = {}
        
    @loader.command(
    en_doc="Start automatic line-by-line output.",
    )
    async def strcmd(self, message):
        """Начать автоматический построчный вывод."""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["no_args"].format(self.get_prefix()))
            return

        lines = args.split('\n')
        if not lines:
            return

        message = await self.inline.form(
            text=lines[0],
            message=message,
            
        )

        stream_id = id(message)
        self._stream_tasks[stream_id] = asyncio.create_task(
            self._auto_stream(message, lines, stream_id)
        )

    async def _auto_stream(self, message, lines, stream_id):
        try:
            for i in range(1, len(lines)):
                await asyncio.sleep(2)  
                if stream_id not in self._stream_tasks:
                    break
                current_text = "\n".join(lines[:i+1])
                await message.edit(
                    text=current_text,
                )
        finally:
            self._stream_tasks.pop(stream_id, None)
