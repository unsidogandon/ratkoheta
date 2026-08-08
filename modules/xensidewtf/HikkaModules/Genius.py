import random
import re
from telethon import types
from .. import loader, utils

#
# ░█░█░█▀▀░█▀█░█▀▀░▀█▀░█▀▄░█▀▀
# ░▄▀▄░█▀▀░█░█░▀▀█░░█░░█░█░█▀▀
# ░▀░▀░▀▀▀░▀░▀░▀▀▀░▀▀▀░▀▀░░▀▀▀
#
# 🔒 Licensed under All Rights Reserved.
# meta developer: @XenSideMOD
#

@loader.tds
class GeniusMod(loader.Module):
    strings = {
        "name": "Гениус",
        "pref": "<b>[Гениус]</b> ",
        "need_arg": "{}Нужен аргумент",
        "status": "{}Шанс ответа теперь 1 к {}",
        "on": "{}Гений в этом чате включён",
        "off": "{}Гений в этом чате выключен",
    }
    _db_name = "Genius"

    async def client_ready(self, client, db):
        self.db = db
        self.client = client
        self.me = (await client.get_me()).id

    @staticmethod
    def str2bool(v: str) -> bool:
        return v.lower() in (
            "yes", "y", "ye", "yea", "true", "t", "1",
            "on", "enable", "start", "run", "go", "да",
        )

    async def geniuscmd(self, m: types.Message):
        ".genius <on/off> - Включить/выключить режим гения в чате."
        args = utils.get_args_raw(m)
        if not m.is_private:
            chat_id = m.chat_id
            chats = self.db.get(self._db_name, "chats", [])
            if self.str2bool(args):
                if chat_id not in chats:
                    chats.append(chat_id)
                    self.db.set(self._db_name, "chats", chats)
                await utils.answer(m, self.strings("on").format(self.strings("pref")))
            else:
                if chat_id in chats:
                    chats.remove(chat_id)
                    self.db.set(self._db_name, "chats", chats)
                await utils.answer(m, self.strings("off").format(self.strings("pref")))

    async def geniuschancecmd(self, m: types.Message):
        ".geniuschance <число> - Установить шанс ответа 1 к N (0 - всегда)."
        args = utils.get_args_raw(m)
        if args and args.isdigit():
            chance = int(args)
            self.db.set(self._db_name, "chance", chance)
            await utils.answer(m, self.strings("status").format(self.strings("pref"), chance))
        else:
            await utils.answer(m, self.strings("need_arg").format(self.strings("pref")))

    async def watcher(self, m: types.Message):
        if not isinstance(m, types.Message) or not m.chat or m.sender_id == self.me:
            return

        if m.chat_id not in self.db.get(self._db_name, "chats", []):
            return

        chance = self.db.get(self._db_name, "chance", 0)
        if chance != 0 and random.randint(0, chance) != 0:
            return
        
        try:
            text = m.raw_text
            valid_words = list(filter(lambda x: len(x) >= 3, text.split()))
            if not valid_words:
                return

            words = {random.choice(valid_words) for _ in ".." if valid_words}
            
            msgs = []
            for word in words:
                async for message in self.client.iter_messages(m.chat_id, search=word, limit=200):
                    if message.replies and message.replies.max_id:
                        msgs.append(message)
            
            if not msgs:
                return

            replier = random.choice(msgs)
            sid = replier.id
            eid = replier.replies.max_id
            
            reply_msgs = [
                msg
                async for msg in self.client.iter_messages(m.chat_id, ids=list(range(sid + 1, eid + 1)))
                if msg and msg.reply_to and msg.reply_to.reply_to_msg_id == sid and msg.text
            ]

            if not reply_msgs:
                return
            
            message_to_send = random.choice(reply_msgs)

            original_text = message_to_send.text
            entities = message_to_send.entities or []
            
            link_spans = []
            for entity in entities:
                if isinstance(entity, types.MessageEntityTextUrl):
                    start = entity.offset
                    end = entity.offset + entity.length
                    link_spans.append((start, end))

            if link_spans:
                link_spans.sort()
                text_without_hyperlinks = ""
                last_pos = 0
                for start, end in link_spans:
                    text_without_hyperlinks += original_text[last_pos:start]
                    last_pos = end
                text_without_hyperlinks += original_text[last_pos:]
            else:
                text_without_hyperlinks = original_text
            
            url_pattern = r'(https?://\S+|www\.\S+|t\.me/\S+|@\w+|\b\w+\.\w+\b)'
            cleaned_text = re.sub(url_pattern, '', text_without_hyperlinks).strip()

            if cleaned_text:
                await m.reply(cleaned_text)

        except Exception:
            return