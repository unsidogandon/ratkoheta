# Name: lesenkascanner
# Description: ищет лесенки в чате
# version: 1.0.0
# meta developer: @latexmods
# meta banner: https://github.com/neistv/mods/raw/main/assets/LesenkaScanner.png

import time

from herokutl.types import Message

from .. import loader, utils



@loader.tds
class LesenkaScannerMod(loader.Module):
    """Сканирует чат на наличие лесенок"""

    strings = {
        "name": "lesenkaScanner",
        "no_messages": (
            "<emoji document_id=5219672809936006424>❄️</emoji> "
            "<b>Недостаточно сообщений для анализа.</b>"
        ),
        "no_ladders": (
            "<emoji document_id=5219672809936006424>❄️</emoji> "
            "<b>В последних {} сообщениях лесенок не обнаружено.</b>"
        ),
        "ladder_found": (
            "<tg-emoji emoji-id=5220070652756635426>👀</tg-emoji> "
            "<b>Обнаружены лесенки</b> <i>(минимум {} подряд):</i>\n\n"
            "{}"
        ),
        "ladder_item": (
            "<tg-emoji emoji-id=5258212320282168974>🎈</tg-emoji> "
            "<b>{}</b> — {} сообщ. • <a href='{}'>перейти</a>"
        ),
        "scan_start": (
            "<tg-emoji emoji-id=5258396243666681152>🔎</tg-emoji> "
            "<b>Сканирую {} сообщений...</b>"
        ),
        "err_scan_depth": (
            "<emoji document_id=5219672809936006424>❄️</emoji> "
            "<b>Укажи глубину от 10 до 10000.</b>"
        ),
        "config_min_ladder": "Минимальное количество сообщений подряд для лесенки",
        "config_scan_depth": "Глубина сканирования (кол-во сообщений)",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "min_ladder",
                6,
                lambda: self.strings["config_min_ladder"],
                validator=loader.validators.Integer(minimum=1, maximum=15),
            ),
            loader.ConfigValue(
                "scan_depth",
                100,
                lambda: self.strings["config_scan_depth"],
                validator=loader.validators.Integer(minimum=10, maximum=10000),
            ),
        )
        self.message_history = {}

    async def client_ready(self, client, db):
        self.client = client
        self._db = db

    async def _get_messages(self, chat_id: int, limit: int):
        now = time.time()
        cache = self.message_history.get(chat_id, {})
        if cache.get("time", 0) > now - 60 and len(cache.get("messages", [])) >= limit:
            return cache["messages"][-limit:]

        messages = []
        async for msg in self.client.iter_messages(chat_id, limit=limit):
            if msg.sender_id:
                messages.append(msg)

        self.message_history[chat_id] = {"messages": messages, "time": now}
        return messages

    @loader.command(
        ru_doc="[глубина] — поиск лесенок в чате",
        alias="ls",
    )
    async def lesenkacmd(self, message: Message):
        """[глубина] — поиск лесенок в чате"""
        args = utils.get_args_raw(message)
        scan_depth = self.config["scan_depth"]

        if args and args.isdigit():
            scan_depth = int(args)
            if not (10 <= scan_depth <= 10000):
                await utils.answer(message, self.strings["err_scan_depth"])
                return

        min_ladder = self.config["min_ladder"]
        chat_id = utils.get_chat_id(message)
        await utils.answer(message, self.strings["scan_start"].format(scan_depth))

        messages = await self._get_messages(chat_id, scan_depth)
        if len(messages) < min_ladder:
            await utils.answer(message, self.strings["no_messages"])
            return

        ladders = {}
        current_user, current_chain = None, []

        for msg in reversed(messages):
            if msg.sender_id == current_user:
                current_chain.append(msg)
            else:
                if len(current_chain) >= min_ladder:
                    ladders[current_user] = {
                        "chain": current_chain,
                        "first_msg": current_chain[0],
                    }
                current_user, current_chain = msg.sender_id, [msg]

        if len(current_chain) >= min_ladder:
            ladders[current_user] = {
                "chain": current_chain,
                "first_msg": current_chain[0],
            }

        if not ladders:
            await utils.answer(message, self.strings["no_ladders"].format(scan_depth))
            return

        results = []
        for user_id, data in ladders.items():
            try:
                user = await self.client.get_entity(user_id)
                user_name = getattr(user, "first_name", "User")
            except Exception:
                user_name = str(user_id)

            try:
                msg_id = data["first_msg"].id
                chat = await message.get_chat()
                if getattr(chat, "username", None):
                    link = f"https://t.me/{chat.username}/{msg_id}"
                else:
                    link = f"https://t.me/c/{str(chat_id).replace('-100', '')}/{msg_id}"
            except Exception:
                link = "#"

            results.append(
                self.strings["ladder_item"].format(
                    utils.escape_html(user_name),
                    len(data["chain"]),
                    link,
                )
            )

        await utils.answer(
            message,
            self.strings["ladder_found"].format(min_ladder, "\n".join(results)),
        )
