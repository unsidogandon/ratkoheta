# meta developer: @RostelecomNetworks

from herokutl.types import Message
from .. import loader, utils

@loader.tds
class ZOV(loader.Module):
    """ZV mode"""
    strings = {"name": "ZV"}
    strings_ru = {"name": "ZV", "switched": "ZV режим {}!!!!"}
    active = False

    @loader.command(
        ru_doc="Переключает (сообщения который начинаются с точки не изменяются)",
    )
    async def zv(self, message: Message):
        self.active = not self.active
        await utils.answer(
            message, 
            self.strings["switched"].format("активен" if self.active else "выключен")
        )

    @loader.watcher(out=True)
    async def watcher(self, message):
        if not self.active:
            return
    
        raw: str = message.text or (message.caption or "")
        if not raw or raw.startswith('.'):
            return

        new = (
            raw
            .replace("з", "Z").replace("с", "Z").replace("о", "O").replace("в", "V")
            .replace("и", "i").replace("З", "Z").replace("С", "Z").replace("О", "O")
            .replace("В", "V").replace("И", "i")
        )

        if new == raw:
            return

        await message.edit(new)
