__version__ = (1, 0, 7)
#ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ© Copyright 2024
#ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤhttps://t.me/unnic
# 🔒ㅤㅤㅤㅤㅤLicensed under the GNU AGPLv3
# 🌐ㅤㅤhttps://www.gnu.org/licenses/agpl-3.0.html
#┏┓━┏┓━━┏┓━━┏┓━━┏━━━━┓━━━━━┏┓━━━━━━━━━━━━
#┃┃━┃┃━━┃┃━━┃┃━━┃┏┓┏┓┃━━━━┏┛┗┓━━━━━━━━━━━
#┃┗━┛┃┏┓┃┃┏┓┃┃┏┓┗┛┃┃┗┛┏┓┏┓┗┓┏┛┏━━┓┏━┓━━━━
#┃┏━┓┃┣┫┃┗┛┛┃┗┛┛━━┃┃━━┃┃┃┃━┃┃━┃┏┓┃┃┏┛━━━━
#┃┃━┃┃┃┃┃┏┓┓┃┏┓┓━┏┛┗┓━┃┗┛┃━┃┗┓┃┗┛┃┃┃━━━━━
#┗┛━┗┛┗┛┗┛┗┛┗┛┗┛━┗━━┛━┗━━┛━┗━┛┗━━┛┗┛━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# load from: t.me:HikkTutor 
# meta developer:@HikkTutor 
# author: @unnic
# name: TextStyler
#██╗░░░██╗███╗░░██╗███╗░░██╗██╗░█████╗░
#██║░░░██║████╗░██║████╗░██║██║██╔══██╗
#██║░░░██║██╔██╗██║██╔██╗██║██║██║░░╚═╝
#██║░░░██║██║╚████║██║╚████║██║██║░░██╗
#╚██████╔╝██║░╚███║██║░╚███║██║╚█████╔╝
#░╚═════╝░╚═╝░░╚══╝╚═╝░░╚══╝╚═╝░╚════╝
from telethon import events
from telethon.tl.types import Message
from .. import loader # type: ignore

@loader.tds
class TextStylerMod(loader.Module):
    """Модуль для форматирования текста в чате"""

    strings = {
        "name": "TextStyler"
    }

    def __init__(self):
        super().__init__()
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "ignore_char",
                ".",
                lambda: "Префикс, указывающий на игнорирование сообщения.",
                validator=loader.validators.String(min_len=1, max_len=1)
            ),
            loader.ConfigValue(
                "enable_bold",
                False,
                lambda: "Вкл/выкл автоматическое жирное форматирование текста.",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "enable_italic",
                False,
                lambda: "Вкл/выкл автоматическое курсивное форматирование текста.",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "enable_strikethrough",
                False,
                lambda: "Вкл/выкл автозачеркивание текста.",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "enable_underlined",
                False,
                lambda: "Вкл/выкл автоматическое подчеркивание текста.",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "enable_spoiler",
                False,
                lambda: "Вкл/выкл автоматический скрытый текст.",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "enable_mono",
                False,
                lambda: "Вкл/выкл автоматический моноширинный текст.",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "enable_quoted",
                False,
                lambda: "Вкл/выкл автоматический цитируемый текст.",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "enable_code_block",
                False,
                lambda: "Вкл/выкл автоматический блок кода.",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "ignore_formatting",
                False,
                lambda: "Игнорировать форматирование текста для сообщений в канале.",
                validator=loader.validators.Boolean()
            )
        )

    async def client_ready(self, client, db):
        self._client = client
        client.add_event_handler(self.message_handler, events.NewMessage())

    async def is_premium(self, user_id: int) -> bool:
        try:
            user = await self._client.get_entity(user_id)
            if hasattr(user, 'premium') and user.premium:
                return True
            return False
        except Exception:
            return False
        
    def get_emojis(self, is_premium: bool):
        if is_premium:
            return {
                "common0": "<tg-emoji emoji-id=5875462364110787088>🗂</tg-emoji>",
                "common1": "<tg-emoji emoji-id=5807557921843715576>⬇️</tg-emoji>",
                "common2": "<tg-emoji emoji-id=5778335621491723621>📷</tg-emoji>",
                "common3": "<tg-emoji emoji-id=5988023995125993550>🛠</tg-emoji>",
                "common4": "<tg-emoji emoji-id=5879770735999717115>👤</tg-emoji>"
            }
        else:
            return {
                "common0": "📋",
                "common1": "⬇️",
                "common2": "◽️",
                "common3": "🛠",
                "common4": "👤"
            }

    def format_text(self, text):
        if self.config["enable_bold"]:
            text = f"<b>{text}</b>"
        if self.config["enable_italic"]:
            text = f"<i>{text}</i>"
        if self.config["enable_underlined"]:
            text = f"<u>{text}</u>"
        if self.config["enable_strikethrough"]:
            text = f"<s>{text}</s>"
        if self.config["enable_spoiler"]:
            text = f"<tg-spoiler>{text}</tg-spoiler>"
        if self.config["enable_mono"]:
            text = f"<code>{text}</code>"
        if self.config["enable_quoted"]:
            text = f"<blockquote>{text}</blockquote>"
        if self.config["enable_code_block"]:
            text = f"<pre>{text}</pre>"
        return text

    async def message_handler(self, event):
        try:
            if not hasattr(self, 'config'):
                return

            original_message = event.raw_text

            if event.message.media:
                return

            if original_message.startswith(self.config["ignore_char"]):
                return

            if (event.is_channel and self.config["ignore_formatting"]) and not (event.is_group or event.is_private):
                return

            formatted_message = self.format_text(original_message)

            if formatted_message and formatted_message != original_message:
                await event.edit(formatted_message, parse_mode='html')

        except Exception as e:
            print(f"Error in message_handler: {e}")
  
    async def tshelpcmd(self, message: Message):
        """Инструкция по модулю"""
        is_premium_user = await self.is_premium(message.sender_id)
        emojis = self.get_emojis(is_premium_user)
        
        instruction = (
            f"<blockquote><b>{emojis['common0']} Справка по модулю:</b> {emojis['common1']}</blockquote>\n"
            f"<blockquote><b>{emojis['common2']} Все исходящие сообщения автоматически форматируются, если включен тот или инной формат.</b>\n\n"
            f"{emojis['common2']} Если сообщение начинается с символа игнорирования, сообщение <b>не будет изменено.</b>\n\n"
            f"{emojis['common2']} Модуль не изменяет текст, содержащий только эмодзи, стикеры, GIF и медиафайлы.\n\n"
            f"{emojis['common2']} Модуль не действует в каналах, если <b>включить игнор</b>, ниже настройка.\n\n"
            f"{emojis['common2']} Hikka не поддерживает форматирование: <code>«𝗕𝗹𝗼𝗰𝗸𝗾𝘂𝗼𝘁𝗲»</code>\n\n"
            f"{emojis['common2']} Эмодзи и стикеры в тексте останутся без изменений, <b>если выключены все форматы.</b></blockquote>\n\n"
            f"<blockquote>{emojis['common0']} <b>Информация и настройка:</b> {emojis['common1']}</blockquote>\n"
            f"<blockquote>{emojis['common2']} Символ игнорирования по умолчанию: «<code>.</code>».\n"
            f"{emojis['common3']} <b>Настройка:</b> <code>.cfg TextStyler ignore_char</code>\n\n"
            f"{emojis['common2']} Ты можешь включить/выключить <b>игнор для каналов.</b>\n"
            f"{emojis['common3']} <b>Настройка:</b> <code>.cfg TextStyler ignore_formatting</code>\n\n"
            f"{emojis['common2']} <b>Для новчиков:</b> Флаг «True» - <b>вкл</b>, флаг «False» - <b>выкл.</b>.</blockquote>\n\n"
            f"<blockquote>{emojis['common4']} <b>Разработчик: @unnic</b></blockquote>"
        )
        await message.edit(instruction, parse_mode='html')
