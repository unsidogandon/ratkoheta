# name: KeyBoardSwitcher
# meta developer: @hp_modules
# author: @haloperidolpills
__version__ = 1,0,1
from .. import loader, utils

class KeyBoardSwitcher(loader.Module):
    
    strings = {"name": "KeyBoardSwitcher"}

    async def kbscmd(self, message):
        """Используй .kbs (реплай или текст), чтобы сменить раскладку"""
        reply = await message.get_reply_message()
        args = utils.get_args_raw(message)
        client = message.client
        me = await client.get_me()

        if args:
            target_text = args
            target_msg = message
        elif reply:
            target_text = reply.raw_text
            if reply.sender_id == me.id:
                target_msg = reply
                await message.delete()
            else:
                target_msg = message
        else:
            return

        en_layout = "`~qwertyuiop[]asdfghjkl;'zxcvbnm,./QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>?@#$^&"
        ru_layout = "ёЁйцукенгшщзхъфывапролджэячсмитьбю.ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,№?;:?"

        en_to_ru = str.maketrans(en_layout, ru_layout)
        ru_to_en = str.maketrans(ru_layout, en_layout)

        converted_text = ""
        for char in target_text:
            if char in en_layout:
                converted_text += char.translate(en_to_ru)
            elif char in ru_layout:
                converted_text += char.translate(ru_to_en)
            else:
                converted_text += char

        if target_msg.id == message.id:
            await message.edit(converted_text)
        else:
            await target_msg.edit(converted_text)
