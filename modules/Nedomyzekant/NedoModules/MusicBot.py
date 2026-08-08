__version__ = (5, 4, 1)
# meta developer: @Nedo_Modules

import asyncio
from .. import loader, utils
from telethon.tl import types
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest, DeleteHistoryRequest

@loader.tds
class MusicBot(loader.Module):
    """Поиск музыки через @mus_vir_bot. Есть баги на версиях Heroku 2.x.x"""
    
    strings = {
        "name": "MusicBot",
        "no_query": "❌ <b>Введите запрос!</b>",
        "searching": "🔍 <b>Ищу:</b> <code>{}</code>",
        "no_results": "❌ <b>Результаты не найдены.</b>",
        "downloading": "📥 <b>Скачиваю...</b>",
        "uploading": "📤 <b>Отправляю...</b>",
        "error": "❌ <b>Ошибка:</b> {}",
        "wait_page": "⏳ <b>Загружаю страницу...</b>",
    }

    def __init__(self):
        self.bot = "@mus_vir_bot"

    async def client_ready(self, client, db):
        self.client = client

    async def _clean_bot_chat(self):
        try:
            peer = await self.client.get_input_entity(self.bot)
            await self.client(DeleteHistoryRequest(peer=peer, max_id=0, just_clear=False, revoke=True))
        except:
            async for msg in self.client.iter_messages(self.bot, limit=100):
                await msg.delete()

    def _generate_hikka_buttons(self, bot_msg, chat_id, reply_id):
        hikka_buttons = []
        if not bot_msg or not bot_msg.buttons:
            return None

        for row in bot_msg.buttons:
            btn_row = []
            for btn in row:
                text = btn.text
                if "/" in text and any(char.isdigit() for char in text):
                    btn_row.append({"text": text, "callback": self.empty_callback})
                elif any(x in text for x in ["❮", "❯", "«", "»"]):
                    btn_row.append({
                        "text": text,
                        "callback": self.navigate_callback,
                        "args": (bot_msg.id, btn.button.data, chat_id, reply_id)
                    })
                elif hasattr(btn.button, 'data'):
                    btn_row.append({
                        "text": text,
                        "callback": self.press_and_get,
                        "args": (bot_msg.id, btn.button.data, chat_id, reply_id)
                    })
            if btn_row:
                hikka_buttons.append(btn_row)
        
        hikka_buttons.append([{"text": "🚫 Закрыть", "action": "close"}])
        return hikka_buttons

    @loader.command()
    async def mus(self, message):
        """[запрос] - Поиск музыки"""
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, self.strings["no_query"])

        chat_id = message.chat_id
        reply_id = message.reply_to_msg_id or message.id

        await self._clean_bot_chat()
        
        status = await utils.answer(message, self.strings["searching"].format(args))
        await self.client.send_message(self.bot, args)
        
        bot_msg = None
        for _ in range(15):
            await asyncio.sleep(1)
            async for msg in self.client.iter_messages(self.bot, limit=3):
                if not msg.out and msg.buttons:
                    bot_msg = msg
                    break
            if bot_msg: break
            
        if not bot_msg:
            return await utils.answer(status, self.strings["no_results"])

        buttons = self._generate_hikka_buttons(bot_msg, chat_id, reply_id)
        await self.inline.form(
            text=f"🎵 <b>Результаты для:</b> <code>{args}</code>",
            message=status,
            reply_markup=buttons
        )

    async def empty_callback(self, call):
        await call.answer("Это номер страницы", show_alert=False)

    async def navigate_callback(self, call, bot_msg_id, data, chat_id, reply_id):
        try:
            await call.edit(self.strings["wait_page"])
            await self.client(GetBotCallbackAnswerRequest(peer=self.bot, msg_id=bot_msg_id, data=data))

            updated_msg = None
            for _ in range(14): 
                await asyncio.sleep(0.5)
                m = await self.client.get_messages(self.bot, ids=bot_msg_id)
                if m and m.buttons:
                    updated_msg = m
                    break
            
            if not updated_msg:
                return await call.answer("❌ Ошибка обновления", show_alert=True)

            new_buttons = self._generate_hikka_buttons(updated_msg, chat_id, reply_id)
            await call.edit(text=f"🎵 <b>Страница обновлена</b>", reply_markup=new_buttons)
        except Exception as e:
            await call.edit(self.strings["error"].format(str(e)))

    async def press_and_get(self, call, msg_id, data, chat_id, reply_id):
        try:
            await call.edit(self.strings["downloading"])
            
            msgs = await self.client.get_messages(self.bot, limit=1)
            last_id = msgs[0].id if msgs else 0

            await self.client(GetBotCallbackAnswerRequest(peer=self.bot, msg_id=msg_id, data=data))

            audio_msg = None
            for _ in range(30):
                await asyncio.sleep(0.5)
                async for m in self.client.iter_messages(self.bot, min_id=last_id, limit=3):
                    if m.audio or m.voice or m.document:
                        audio_msg = m
                        break
                if audio_msg: break
            
            if not audio_msg:
                return await call.answer("❌ Файл не получен", show_alert=True)

            await call.edit(self.strings["uploading"])
            
            await self.client.send_file(
                chat_id,
                audio_msg.media,
                caption="",
                reply_to=reply_id
            )
            
            await self._clean_bot_chat()
            await call.delete()

        except Exception as e:
            await call.edit(self.strings["error"].format(str(e)))