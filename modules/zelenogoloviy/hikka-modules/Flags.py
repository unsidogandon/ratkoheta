# MIT License
# Copyright (c) 2025 zelenogoloviy
# ---------------------------------------------------------------------------------
# Name: Flags
# Description: Модуль для получения флага страны по её двухбуквенному коду
# Author: @zelenogoloviy_m
# ---------------------------------------------------------------------------------
# meta developer: @zelenogoloviy_m
__version__ = (0, 0, 1)
from .. import loader, utils

@loader.tds
class FlagMod(loader.Module):
    """Модуль для получения флага страны по её двухбуквенному коду."""
    strings = {
        "name": "Флаги",
        "no_args": "<emoji document_id=5210952531676504517>❌</emoji>Нет Аргументов",
    }
    strings_en = {
        "name": "Flags",
        "no_args": "<emoji document_id=5210952531676504517>❌</emoji>No Args",
    }

    @loader.command(
    en_doc="Get flag for two-letters code of the country",
    )
    async def fl(self, message):
        """Получить флаг страны по двухбуквенному коду"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["no_args"])
            return
        flag = utils.get_lang_flag(args)
        await utils.answer(message, flag)

        