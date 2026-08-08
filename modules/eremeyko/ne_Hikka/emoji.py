__version__ = (1, 0, 5)
# meta developer: @eremod
#
#
# 	.----..----. .----..-.   .-. .----. .----.
# 	| {_  | {}  }| {_  |  `.'  |/  {}  \| {}  \
# 	| {__ | .-. \| {__ | |\ /| |\      /|     /
# 	`----'`-' `-'`----'`-' ` `-' `----' `----'
#
#              	© Copyright 2025
#          	https://t.me/eremod
#
# 🔒      Licensed under the GNU GPLv3
# 🌐 https://www.gnu.org/licenses/gpl-3.0.html
# Original repository: https://github.com/eremeyko/ne_Hikka

from herokutl.types import Message
from .. import loader, utils


@loader.tds
class EmojiCipher(loader.Module):
    """Энкодер/декодер с эмодзи"""

    strings = {
        "name": "EmojiCipher",
        "encode_doc": "Encode text to emoji",
        "decode_doc": "Decode text from emoji",
        "no_text": "❗ Nothing to encode. \n\nType text after the command or reply to a message.",
    }

    strings_ru = {
        "encode_doc": "Зашифровать текст эмодзи",
        "decode_doc": "Расшифровать текст из эмодзи",
        "no_text": "❗ Нечего шифровать. \n\nНапишите текст после команды или ответьте на сообщение.",
    }

    # Базовый алфавит: латиница, кириллица, цифры и пробел
    _UPPER_PREFIX = "🔼"

    _CHART = {
        # латиница, только нижний регистр (верхний будет приводиться к нижнему)
        "a": "😀",
        "b": "😁",
        "c": "😂",
        "d": "🤣",
        "e": "😃",
        "f": "😄",
        "g": "😅",
        "h": "😆",
        "i": "😉",
        "j": "😊",
        "k": "😋",
        "l": "😎",
        "m": "😍",
        "n": "😘",
        "o": "🥰",
        "p": "😗",
        "q": "😙",
        "r": "😚",
        "s": "🙂",
        "t": "🤗",
        "u": "🤩",
        "v": "🤔",
        "w": "🤨",
        "x": "😐",
        "y": "😑",
        "z": "😶",
        # кириллица (нижний регистр)
        "а": "🐶",
        "б": "🐱",
        "в": "🐭",
        "г": "🐹",
        "д": "🐰",
        "е": "🦊",
        "ё": "🐻",
        "ж": "🐼",
        "з": "🐨",
        "и": "🐯",
        "й": "🦁",
        "к": "🐮",
        "л": "🐷",
        "м": "🐸",
        "н": "🐵",
        "о": "🐔",
        "п": "🐧",
        "р": "🐦",
        "с": "🐤",
        "т": "🐣",
        "у": "🐺",
        "ф": "🦆",
        "х": "🦅",
        "ц": "🦉",
        "ч": "🦇",
        "ш": "🐗",
        "щ": "🐴",
        "ъ": "🦄",
        "ы": "🐝",
        "ь": "🪲",
        "э": "🦋",
        "ю": "🐞",
        "я": "🐙",
        # цифры
        "0": "0️⃣",
        "1": "1️⃣",
        "2": "2️⃣",
        "3": "3️⃣",
        "4": "4️⃣",
        "5": "5️⃣",
        "6": "6️⃣",
        "7": "7️⃣",
        "8": "8️⃣",
        "9": "9️⃣",
        # пробел
        " ": "⬜",
    }

    _REV_CHART = {v: k for k, v in _CHART.items()}
    _REV_KEYS = sorted(_REV_CHART, key=len, reverse=True)
    _MAX_KEY_LEN = len(_REV_KEYS[0]) if _REV_KEYS else 1
    _PREFIX_LEN = len(_UPPER_PREFIX)

    def _encode(self, text: str) -> str:
        """Внутренний метод шифрования."""
        out = []
        for ch in text:
            base = ch.lower()
            mapped = self._CHART.get(base)
            if mapped is None:
                out.append(ch)
                continue

            if ch != base:
                out.append(f"{self._UPPER_PREFIX}{mapped}")
            else:
                out.append(mapped)
        return "".join(out)

    def _decode(self, glyphs: str) -> str:
        """Внутренний метод дешифрования (учёт многосимвольных эмодзи)."""
        out = []
        i = 0
        keys = self._REV_KEYS
        max_len = self._MAX_KEY_LEN
        prefix = self._UPPER_PREFIX
        len_prefix = self._PREFIX_LEN
        while i < len(glyphs):
            matched = False

            is_upper = glyphs.startswith(prefix, i)
            start_idx = i + len_prefix if is_upper else i

            if is_upper and start_idx >= len(glyphs):
                out.append(prefix)
                i += len_prefix
                continue

            for L in range(max_len, 0, -1):
                tok = glyphs[start_idx : start_idx + L]
                if tok in self._REV_CHART:
                    char = self._REV_CHART[tok]
                    out.append(char.upper() if is_upper else char)
                    i = start_idx + L
                    matched = True
                    break

            if is_upper and matched:
                continue

            if not matched:
                out.append(glyphs[i])
                i += 1
        return "".join(out)

    async def _get_target_text(
        self, message: Message
    ) -> tuple[str | None, Message | None]:
        """
        Возвращает текст и сообщение:
        1) есть аргументы команды → шифрует их, редактируем/отвечаем на команду;
        2) нет аргументов, но есть реплай → шифрует текст реплая и редактируем его;
        3) ничего нет → возвращаем (None, None).
        """
        args = utils.get_args_raw(message)
        if args:
            return args, message

        reply = await message.get_reply_message()
        if reply and reply.text:
            return reply.text, message

        return None, None

    async def _handle(self, message: Message, func):
        text, target = await self._get_target_text(message)
        if text is None:
            await utils.answer(message, self.strings["no_text"])
            return
        result = func(text)
        if target is message:
            await utils.answer(message, result)
        else:
            await target.edit(result)

    @loader.command(
        ru_doc="Зашифровать текст эмодзи. "
        "Если есть аргументы — шифрует их. "
        "Если нет — шифрует текст сообщения, на которое сделан ответ.",
        alias="enc",
    )
    async def encode(self, message: Message):
        """Encode text to emoji."""
        await self._handle(message, self._encode)

    @loader.command(
        ru_doc="Расшифровать текст из эмодзи. "
        "Если есть аргументы — расшифровывает их. "
        "Если нет — расшифровывает текст сообщения, на которое сделан ответ.",
        alias="dec",
    )
    async def decode(self, message: Message):
        """Decode text from emoji."""
        await self._handle(message, self._decode)
