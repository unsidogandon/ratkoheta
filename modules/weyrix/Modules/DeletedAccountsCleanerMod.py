__version__ = (1, 0, 0)
# meta developer: @weyrix
# requires: telethon

import asyncio
from telethon.tl.types import ChannelParticipantsKicked, ChatBannedRights
from telethon.tl.functions.channels import EditBannedRequest
from telethon.errors import UserAdminInvalidError
from .. import loader, utils

@loader.tds
class DeletedAccountsCleanerMod(loader.Module):
    """Модуль для очистки группы от удаленных аккаунтов ("призраков")."""
    
    strings = {
        "name": "DelAccsCleaner",
        "searching": "🔍 <b>Ищу удаленные аккаунты в чате...</b>",
        "no_admin": "❌ <b>У меня нет прав администратора (бан пользователей) в этом чате!</b>",
        "not_group": "❌ <b>Эта команда работает только в группах или супергруппах!</b>",
        "result": "✅ <b>Очистка завершена!</b>\nВсего проверено: <code>{}</code>\nУдалено аккаунтов: <code>{}</code>",
        "no_deleted": "🎉 <b>Удаленных аккаунтов в этом чате не найдено!</b>"
    }

    @loader.command(
        ru_doc="Удаляет все удаленные аккаунты (Deleted Accounts) из текущей группы."
    )
    async def delaccscmd(self, message):
        """Удалить удаленные аккаунты из группы."""
        if not message.is_group:
            await utils.answer(message, self.strings["not_group"])
            return

        await utils.answer(message, self.strings["searching"])
        
        chat = await message.get_chat()
        deleted_count = 0
        total_count = 0

        try:
            async for user in message.client.iter_participants(chat):
                total_count += 1
                if user.deleted:
                    try:
                        await message.client(EditBannedRequest(
                            channel=chat,
                            participant=user,
                            banned_rights=ChatBannedRights(until_date=None, view_messages=True)
                        ))
                        await message.client(EditBannedRequest(
                            channel=chat,
                            participant=user,
                            banned_rights=ChatBannedRights(until_date=None)
                        ))
                        deleted_count += 1
                        await asyncio.sleep(2)
                    except UserAdminInvalidError:
                        await utils.answer(message, self.strings["no_admin"])
                        return
                    except Exception:
                        continue
            
            if deleted_count > 0:
                await utils.answer(message, self.strings["result"].format(total_count, deleted_count))
            else:
                await utils.answer(message, self.strings["no_deleted"])

        except Exception as e:
            await utils.answer(message, f"❌ <b>Произошла ошибка:</b> <code>{str(e)}</code>")