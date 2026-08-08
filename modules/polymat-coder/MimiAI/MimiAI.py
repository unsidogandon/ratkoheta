from .. import loader, utils
import asyncio
from telethon.tl.functions.channels import CreateChannelRequest, InviteToChannelRequest
from telethon.tl.types import InputPeerChannel, InputPeerUser
from telethon.tl.functions.messages import SetTypingRequest
from telethon.tl.types import SendMessageTypingAction
from telethon.errors import ChannelPrivateError

# meta developer: @dealdoxer
# meta banner: https://i.ibb.co/JwpB91Ht/image.jpg
__version__ = (1, 0, 2)

class MimiAI(loader.Module):
    """Модуль для общения с MimiAI."""
    strings = {"name": "MimiAI"}
    strings_ru = {"name": "MimiAI"}

    def __init__(self):
        self.pending_requests = {}
        self.typing_tasks = {}
        self.mimi_group_id = None
        self.mimi_bot_id = None

    async def client_ready(self, client, db):
        self._client = client
        self._db = db
        await self.create_mimi_group()

    async def create_mimi_group(self):
        try:
            group_id = self.get("mimi_group_id")
            bot_id = self.get("mimi_bot_id")

            if group_id and bot_id:
                try:
                    await self._client.get_entity(group_id)
                    self.mimi_group_id = group_id
                    self.mimi_bot_id = bot_id
                    return
                except (ChannelPrivateError, ValueError):
                    pass

            await self._create_new_mimi_group()
        except Exception as e:
            print(f"Error in create_mimi_group: {e}")
            await self._create_new_mimi_group()

    async def _create_new_mimi_group(self):
        try:
            group = await self._client(CreateChannelRequest(
                title="🦴 MimiTyph Чат",
                about="❤️ Группа для взаимодействие с ботом @MimiTyph_sBot",
                megagroup=True
            ))
            group_entity = group.chats[0]
            group_id = group_entity.id
            bot_entity = await self._client.get_entity("@MimiTyph_sBot")
            channel_input = InputPeerChannel(group_entity.id, group_entity.access_hash)
            bot_input = InputPeerUser(bot_entity.id, bot_entity.access_hash)
            await self._client(InviteToChannelRequest(channel_input, [bot_input]))

            await self._client.edit_folder(entity=group_entity, folder=1)

            self.set("mimi_group_id", group_id)
            self.set("mimi_bot_id", bot_entity.id)
            self.mimi_group_id = group_id
            self.mimi_bot_id = bot_entity.id
        except Exception as e:
            print(f"Error creating new Mimi group: {e}")
            raise

    async def keep_typing(self, chat_id, user_id, original_msg_id):
        try:
            while True:
                await self._client(SetTypingRequest(
                    peer=await self._client.get_input_entity(chat_id),
                    action=SendMessageTypingAction()
                ))
                await asyncio.sleep(5)
        except (asyncio.CancelledError, Exception):
            pass

    def format_response(self, request: str, response: str) -> str:
        return f"""<b>❤️ Запрос:</b>\n\t<code>{utils.escape_html(request)}</code>\n\n<b>🦴 Ответ:</b>\n\t<code>{utils.escape_html(response)}</code>""".strip()

    @loader.command(ru_doc="Общение с MimiAI")
    async def mimicmd(self, message):
        """Общение с MimiAI"""
        request = utils.get_args_raw(message)
        if not request:
            await utils.answer(message, "<b>😭 Пожалуйста, укажите запрос.</b>", parse_mode="HTML")
            return

        if not self.mimi_group_id:
            await self.create_mimi_group()
            if not self.mimi_group_id:
                await utils.answer(message, "<b>❌ Не удалось создать группу для Mimi</b>", parse_mode="HTML")
                return

        processing_msg = await utils.answer(
            message,
            f"<b>❤️ Запрос: </b><code>{utils.escape_html(request)}</code>\n\n<b>💤 Mimi обрабатывает ваш запрос...</b>",
            parse_mode="HTML"
        )

        typing_task = asyncio.create_task(
            self.keep_typing(message.chat.id, message.from_id, message.id)
        )

        try:
            last_bot_msg = await self.get_last_bot_message(self.mimi_group_id)

            if last_bot_msg:
                sent_msg = await self._client.send_message(
                    self.mimi_group_id,
                    request,
                    reply_to=last_bot_msg.id
                )
            else:
                await self._client.send_message(self.mimi_group_id, "/start")
                await asyncio.sleep(1)
                last_bot_msg = await self.get_last_bot_message(self.mimi_group_id)
                if last_bot_msg:
                    sent_msg = await self._client.send_message(
                        self.mimi_group_id,
                        request,
                        reply_to=last_bot_msg.id
                    )
                else:
                    sent_msg = await self._client.send_message(self.mimi_group_id, request)

            group_entity = await self._client.get_entity(self.mimi_group_id)
            await self._client.edit_folder(entity=group_entity, folder=1)

            self.pending_requests[sent_msg.id] = {
                "user_id": message.from_id,
                "chat_id": message.chat.id,
                "original_msg_id": message.id,
                "processing_msg_id": processing_msg.id,
                "typing_task": typing_task,
                "is_outgoing": message.out,
                "request_text": request
            }

            async def remove_pending(msg_id):
                await asyncio.sleep(60)
                if msg_id in self.pending_requests:
                    data = self.pending_requests.pop(msg_id)
                    data["typing_task"].cancel()
                    response = self.format_response(
                        data["request_text"],
                        "😪 Mimi не ответила в течение 60 секунд..."
                    )
                    if data["is_outgoing"]:
                        await self._client.edit_message(
                            data["chat_id"],
                            data["processing_msg_id"],
                            response,
                            parse_mode="HTML"
                        )
                    else:
                        await self._client.send_message(
                            data["chat_id"],
                            response,
                            reply_to=data["original_msg_id"],
                            parse_mode="HTML"
                        )

            asyncio.create_task(remove_pending(sent_msg.id))

        except (ChannelPrivateError, ValueError) as e:
            print(f"Channel error: {e}")
            await processing_msg.edit("<b>🔄 Группа недоступна, Mimi создает новую...</b>", parse_mode="HTML")
            await self._create_new_mimi_group()
            await self.mimicmd(message)
        except Exception as e:
            print(f"Error in mimicmd: {e}")
            await processing_msg.edit(f"<b>❌ Ошибка: </b><code>{str(e)}</code>", parse_mode="HTML")
            typing_task.cancel()

    async def get_last_bot_message(self, group_id):
        try:
            if not group_id or not self.mimi_bot_id:
                return None

            messages = await self._client.get_messages(
                group_id,
                from_user=self.mimi_bot_id,
                limit=1
            )
            return messages[0] if messages else None
        except (ChannelPrivateError, ValueError):
            await self._create_new_mimi_group()
            return None
        except Exception as e:
            print(f"Error in get_last_bot_message: {e}")
            return None

    @loader.watcher(only_messages=True, only_chats=True)
    async def watch_mimi_responses(self, message):
        try:
            if not message.reply_to or message.reply_to.reply_to_msg_id not in self.pending_requests:
                return

            request_data = self.pending_requests.pop(message.reply_to.reply_to_msg_id)
            request_data["typing_task"].cancel()

            formatted_response = self.format_response(
                request_data["request_text"],
                message.text
            )

            if request_data["is_outgoing"]:
                await self._client.edit_message(
                    request_data["chat_id"],
                    request_data["processing_msg_id"],
                    formatted_response,
                    parse_mode="HTML"
                )
            else:
                await self._client.send_message(
                    request_data["chat_id"],
                    formatted_response,
                    reply_to=request_data["original_msg_id"],
                    parse_mode="HTML"
                )

            try:
                group_entity = await self._client.get_entity(self.mimi_group_id)
                await self._client.edit_folder(entity=group_entity, folder=1)
            except:
                pass

        except Exception as e:
            print(f"Error in watch_mimi_responses: {e}")
