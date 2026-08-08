# ---------------------------------------------------------------------------------
# Name: MiraChat
# Description: Mira AI. БЕЗ АПИ
# meta developer: @Gusik364
# requires: hikkatl
# License on gusik
# ---------------------------------------------------------------------------------

import asyncio
import logging
import hikkatl
from hikkatl.tl import types, functions

from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class MiraChat(loader.Module):
    strings = {
        "name": "MiraChat",
        "no_args": "<emoji document_id=5854929766146118183>❌</emoji> <b>Нужно </b><code>{}{} {}</code>",
        "asking_mira": "<emoji document_id=5325787248363314644>🔄</emoji> <b>Спрашиваю Mira...</b>",
        "done": "✅ <b>Сделано.</b>",
        "answer": """😊 <b>Ответ:</b> {answer}

<emoji document_id=5785419053354979106>❔</emoji> <b>Вопрос:</b> {question}""",
    }

    async def client_ready(self, client, db):
        self.db = db
        self._client = client
        self.mira_bot = "@Mira"

    async def _mute_chat(self):
        try:
            entity = await self._client.get_input_entity(self.mira_bot)
            await self._client(functions.account.UpdateNotifySettingsRequest(
                peer=entity,
                settings=types.InputPeerNotifySettings(
                    show_previews=False,
                    silent=True,
                    mute_until=2**31-1
                )
            ))
        except Exception as e:
            logger.error(f"Failed to mute chat: {e}")

    async def _ask_ai(self, q):
        while True:
            try:
                async with self._client.conversation(self.mira_bot) as conv:
                    await self._mute_chat()
                    
                    msg = await conv.send_message(q)
                    r1 = await conv.get_response()
                    r2 = await conv.get_response()
                    
                    answer_text = r2.text
                    if answer_text.startswith("💭"):
                        answer_text = answer_text[1:].strip()
                    
                    await msg.delete()
                    await r1.delete()
                    await r2.delete()
                    
                    return answer_text
            except hikkatl.errors.common.AlreadyInConversationError:
                await asyncio.sleep(5.67)
            except Exception as e:
                logger.error(f"Error in _ask_ai: {e}")
                return f"Ошибка: {str(e)}"

    @loader.command()
    async def ai(self, message):
        """Задать вопрос к Mira AI"""
        q = utils.get_args_raw(message)
        if not q:
            return await utils.answer(message, self.strings["no_args"].format(self.get_prefix(), "ai", "[вопрос]"))

        await utils.answer(message, self.strings['asking_mira'])

        return await utils.answer(
            message,
            self.strings['answer'].format(
                question=q, 
                answer=await self._ask_ai(q))
            )

    @loader.command()
    async def setfurrycmd(self, message):
        """Установить режим фурри для бота"""
        furry_text = "представь что ты фурри. общайся кратко и веди себя как фурри, используй в сообщении такие фразы как мрр, мяв и добавляй смайлик :3."
        
        try:
            async with self._client.conversation(self.mira_bot) as conv:
                await self._mute_chat()
                
                msg = await conv.send_message(furry_text)
                r1 = await conv.get_response()
                r2 = await conv.get_response()
                
                await msg.delete()
                await r1.delete()
                await r2.delete()
                
                await utils.answer(message, self.strings['done'])
                
        except hikkatl.errors.common.AlreadyInConversationError:
            await asyncio.sleep(5.67)
            await self.setfurrycmd(message)
        except Exception as e:
            logger.error(f"Error in setfurry: {e}")
            await utils.answer(message, f"<emoji document_id=5854929766146118183>❌</emoji> <b>Ошибка:</b> <code>{str(e)}</code>")

    @loader.command()
    async def newchatcmd(self, message):
        """Начать новый чат с ботом"""
        
        try:
            async with self._client.conversation(self.mira_bot) as conv:
                await self._mute_chat()
                
                msg = await conv.send_message("/start")
                r1 = await conv.get_response()
                r2 = await conv.get_response()
                
                await msg.delete()
                await r1.delete()
                await r2.delete()
                
                await utils.answer(message, self.strings['done'])
                
        except hikkatl.errors.common.AlreadyInConversationError:
            await asyncio.sleep(5.67)
            await self.newchatcmd(message)
        except Exception as e:
            logger.error(f"Error in newchat: {e}")
            await utils.answer(message, f"<emoji document_id=5854929766146118183>❌</emoji> <b>Ошибка:</b> <code>{str(e)}</code>")