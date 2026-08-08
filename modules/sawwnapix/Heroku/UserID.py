#---------------------------------------------------------------------
#   __        __ __  __           _     
#   \ \      / /|  \/  | ___   __| |___ 
#    \ \ /\ / (_) |\/| |/ _ \ / _` / __|
#     \ V  V / _| |  | | (_) | (_| \__ \
#      \_/\_/ (_)_|  |_|\___/ \__,_|___/
#---------------------------------------------------------------------
# 🌐 Repository of Modules:https://github.com/sawwnapix/Heroku
# 👤 Developer: @zerixgod
# 🪧 Channel with modules: @wizardmodules/old channel @angellmodules
#---------------------------------------------------------------------
# 🔒 Licensed under GNU GPLv3
# 🧾 https://www.gnu.org/licenses/gpl-3.0.html#license-text
#--------------------------------------------------------------------- 
# Developer: @zerixgod
# Module Name: Userid
# Description: Выдаёт базовую информацию о пользователе/ gives basic information about the user 
# meta developer: @wizardmodules
#---------------------------------------------------------------------   


from telethon.errors import UserIdInvalidError, UsernameInvalidError
from .. import loader, utils

@loader.tds
class UserID(loader.Module):
    """Выдаёт базовую информацию о пользователе"""
    strings = {"name": "UserID"}

    @loader.command()
    async def getuser(self, message):
        """<id/username/reply>"""
        args = utils.get_args(message)
        reply = await message.get_reply_message()

        if reply and not args:
            entity = await message.client.get_entity(reply.sender_id)
        elif args:
            target = args[0]
            try:
                if target.isdigit():
                    entity = await message.client.get_entity(int(target))
                else:
                    entity = await message.client.get_entity(target)
            except (UserIdInvalidError, UsernameInvalidError):
                return await message.edit("Неверный id или username.")
        else:
            return await message.edit("Укажи id, username или сделай реплeй.")

        try:
            user_id = entity.id
            username = f"@{entity.username}" if entity.username else "None"
            forever_link = f"tg://openmessage?user_id={user_id}"

            result = (
                f"<blockquote><emoji document_id=6035084557378654059>👤</emoji> Вот информация о пользователе:</blockquote>\n"
                f"<blockquote><emoji document_id=5904650558127478452>🪪</emoji> ID: <code>{user_id}</code></blockquote>\n"
                f"<blockquote><emoji document_id=5776233299424843260>🌐</emoji> Username: {username}</blockquote>\n"
                f"<blockquote><emoji document_id=5960714428394507968>👁</emoji> Forever Link: <a href=\"{forever_link}\">Click</a></blockquote>"
            )
            await message.edit(result, parse_mode="html")

        except Exception as e:
            await message.edit(f"Ошибка: {e}")
