__version__ = (1, 3, 0)

# meta developer: @Mr4epTuk
# scope: hikka_only

import re
import logging
from .. import loader, utils
from herokutl import TelegramClient
from herokutl.extensions import html as tl_html
from herokutl.tl.functions.messages import EditMessageRequest as TLEditMessage
from herokutl.types import Message
from herokutl.tl.types import (
    MessageEntityCustomEmoji,
    MessageEntityTextUrl,
    MessageEntityPre,
    MessageEntityCode,
    UpdateEditMessage,
    UpdateEditChannelMessage,
    InputPeerSelf,
    InputPeerUser,
)

logger = logging.getLogger(__name__)

_EMOJI_TAG_RE = re.compile(
    r'<emoji\s+document_id=["\x27]?(\d+)["\x27]?[^>]*>([^<]*)</emoji>'
)
_TG_EMOJI_TAG_RE = re.compile(
    r'<tg-emoji\s+emoji-id=["\x27]?(\d+)["\x27]?[^>]*>([^<]*)</tg-emoji>'
)

_CODE_BLOCK_RE = re.compile(r"(<pre\b[^>]*>.*?</pre>)", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"(<code\b[^>]*>.*?</code>)", re.DOTALL)

_TOKEN_PREFIX = "EXEMOJI_BLK_"

_BOT_METHODS = (
    "send_message",
    "edit_message_text",
    "send_photo",
    "send_video",
    "send_document",
    "send_animation",
    "send_audio",
    "send_voice",
    "edit_message_caption",
    "edit_message_media",
    "send_media_group",
)

_TEXT_KEYS = ("text", "caption", "title")


@loader.tds
class ExteraEmojiMod(loader.Module):
    """Made for ExteraGram users without Telegram Premium.

    How it works: Replaces ALL outgoing premium emoji with links
    tg://emoji?id=... BEFORE they leave Userbot. ExteraGram users
    can see all the premium emoji that will be in Heroku even without
    a Premium subscription, and also supports modules."""

    strings = {
        "name": "ExteraEmoji",
        "cfg_enabled": "Enable replacement",
        "cfg_enabled_doc": "Enable/disable premium emoji → link conversion",
        "cfg_ignored": "Ignored chats",
        "cfg_ignored_doc": "Chat IDs where replacement is skipped (Saved Messages auto-ignored)",
        "_cls_doc": "Made for ExteraGram users without Telegram Premium.\n\nHow it works: Replaces ALL outgoing premium emoji with links tg://emoji?id=... BEFORE they leave Userbot. ExteraGram users can see all the premium emoji that will be in Heroku even without a Premium subscription, and also supports modules.",
        "toggled_on": "✅ <b>ExteraEmoji is now ON</b>\n\n<tg-emoji emoji-id=5463001519211161219>❤</tg-emoji><tg-emoji emoji-id=5463227726548707612>❤</tg-emoji><tg-emoji emoji-id=5463115636492217326>❤</tg-emoji><tg-emoji emoji-id=5463078158607591121>❤</tg-emoji> ← check",
        "toggled_off": "❌ <b>ExteraEmoji is now OFF</b>\n\n<tg-emoji emoji-id=5463001519211161219>❤</tg-emoji><tg-emoji emoji-id=5463227726548707612>❤</tg-emoji><tg-emoji emoji-id=5463115636492217326>❤</tg-emoji><tg-emoji emoji-id=5463078158607591121>❤</tg-emoji> ← check",
    }

    strings_ru = {
        "name": "ExteraEmoji",
        "cfg_enabled": "Включить замену",
        "cfg_enabled_doc": "Включить/выключить замену премиум-эмодзи на ссылки",
        "cfg_ignored": "Игнорируемые чаты",
        "cfg_ignored_doc": "ID чатов где замена не производится (Избранное авто-игнорируется)",
        "_cls_doc": "Сделано для пользователей ExteraGram без Telegram Premium.\n\nКак работает: Заменяет ВСЕ исходящие премиум-эмоджи на ссылки tg://emoji?id=... ДО того, как они покинут Userbot'а. Пользователи ExteraGram могут видеть все премиум эмодзи которые будут в Heroku даже без подписки Premium, а также поддерживает модули.",
        "toggled_on": "✅ <b>ExteraEmoji ВКЛЮЧЕН</b>\n\n<tg-emoji emoji-id=5463001519211161219>❤</tg-emoji><tg-emoji emoji-id=5463227726548707612>❤</tg-emoji><tg-emoji emoji-id=5463115636492217326>❤</tg-emoji><tg-emoji emoji-id=5463078158607591121>❤</tg-emoji> ← проверка",
        "toggled_off": "❌ <b>ExteraEmoji ВЫКЛЮЧЕН</b>\n\n<tg-emoji emoji-id=5463001519211161219>❤</tg-emoji><tg-emoji emoji-id=5463227726548707612>❤</tg-emoji><tg-emoji emoji-id=5463115636492217326>❤</tg-emoji><tg-emoji emoji-id=5463078158607591121>❤</tg-emoji> ← проверка",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "enabled",
                True,
                lambda: self.strings("cfg_enabled_doc"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "ignore_chats",
                [],
                lambda: self.strings("cfg_ignored_doc"),
                validator=loader.validators.Series(loader.validators.Integer()),
            ),
        )

    async def client_ready(self, client, db):
        self._client = client
        self._db = db
        self._processed = set()
        self._hooked_mtproto = False
        self._hooked_bot = False
        self._bot_orig = {}
        self._client_orig = {}
        self._bot_client = None

        await self._try_hook_mtproto()
        await self._try_hook_inline_bot()

    @loader.command(
        ru_doc="Включить/выключить замену премиум-эмодзи на ссылки (алиас: .ee)",
        en_doc="Toggle premium emoji → link replacement on/off (alias: .ee)",
        alias="ee",
    )
    async def exteraemojicmd(self, message: Message):
        """Toggle ExteraEmoji replacement on/off — alias: .ee"""
        current = self.config["enabled"]
        self.config["enabled"] = not current
        if current:
            await utils.answer(message, self.strings("toggled_off"))
        else:
            await utils.answer(message, self.strings("toggled_on"))

    def _replace_html(self, text: str) -> str:
        if not isinstance(text, str) or not text:
            return text

        if "<emoji" not in text and "<tg-emoji" not in text:
            return text

        blocks = []

        def _save(m):
            blocks.append(m.group(0))
            return f"{_TOKEN_PREFIX}{len(blocks) - 1}_END"

        text = _CODE_BLOCK_RE.sub(_save, text)
        text = _INLINE_CODE_RE.sub(_save, text)

        text = _EMOJI_TAG_RE.sub(
            lambda m: '<a href="tg://emoji?id={}">{}</a>'.format(m.group(1), m.group(2)),
            text,
        )
        text = _TG_EMOJI_TAG_RE.sub(
            lambda m: '<a href="tg://emoji?id={}">{}</a>'.format(m.group(1), m.group(2)),
            text,
        )

        for i, block in enumerate(blocks):
            text = text.replace(f"{_TOKEN_PREFIX}{i}_END", block)

        return text

    @staticmethod
    def _replace_html_bot(text: str) -> str:
        if not isinstance(text, str) or not text:
            return text

        if "<emoji" not in text and "<tg-emoji" not in text:
            return text

        text = _EMOJI_TAG_RE.sub(
            lambda m: '<a href="tg://emoji?id={}">{}</a>'.format(m.group(1), m.group(2)),
            text,
        )
        text = _TG_EMOJI_TAG_RE.sub(
            lambda m: '<a href="tg://emoji?id={}">{}</a>'.format(m.group(1), m.group(2)),
            text,
        )

        return text

    def _is_ignored_chat(self, chat_id: int) -> bool:
        if chat_id == self._tg_id:
            return True
        if chat_id in self.config["ignore_chats"]:
            return True
        return False

    def _convert_entities(self, entities: list) -> list:
        if not entities:
            return entities

        if not any(isinstance(e, MessageEntityCustomEmoji) for e in entities):
            return entities

        skip_ranges = []
        names_seen = set()

        for e in entities:
            name = type(e).__name__
            names_seen.add(name)

            hit = (
                hasattr(e, "language")
                or name == "MessageEntityPre"
                or name == "MessageEntityCode"
                or name.endswith("EntityPre")
                or name.endswith("EntityCode")
            )

            if hit:
                skip_ranges.append((e.offset, e.offset + e.length))

        skip_ranges.sort()

        logger.info(
            "ExteraEmoji: types=%s skip=%s",
            sorted(names_seen) if names_seen else "[]",
            skip_ranges,
        )

        # Динамически считаем сколько emoji можно конвертировать,
        # чтобы итоговый список не превысил 99 entities (лимит Telegram 100).
        # Blockquote-entity добавляется ПОСЛЕДНЕЙ в список парсером HTML,
        # поэтому при превышении 100 она первой выпадает.
        non_emoji_count = sum(
            1 for e in entities if not isinstance(e, MessageEntityCustomEmoji)
        )
        MAX_LINKS = max(0, min(48, 99 - non_emoji_count))
        changed = False
        result = []
        skipped = 0
        converted = 0

        for entity in entities:
            if isinstance(entity, MessageEntityCustomEmoji):
                s, e = entity.offset, entity.offset + entity.length
                if any(sk_s <= s and e <= sk_e for sk_s, sk_e in skip_ranges):
                    result.append(entity)
                    skipped += 1
                elif converted < MAX_LINKS:
                    result.append(
                        MessageEntityTextUrl(
                            offset=entity.offset,
                            length=entity.length,
                            url=f"tg://emoji?id={entity.document_id}",
                        )
                    )
                    converted += 1
                    changed = True
                else:
                    changed = True  # дропаем — реально уменьшаем общий счётчик
            else:
                result.append(entity)

        if skipped or converted >= MAX_LINKS:
            logger.info(
                "ExteraEmoji: skipped=%d converted=%d",
                skipped, converted,
            )

        return result if changed else entities

    def _process_tl_request(self, request, skip_owner_check=False):
        if not self.config["enabled"]:
            return request

        if not skip_owner_check:
            peer = getattr(request, "peer", None)
            if isinstance(peer, InputPeerSelf):
                return request
            if isinstance(peer, InputPeerUser) and peer.user_id == self._tg_id:
                return request

        name = type(request).__name__

        if name in ("SendMessageRequest", "EditMessageRequest", "SendMediaRequest"):
            entities = getattr(request, "entities", None)
            if entities:
                converted = self._convert_entities(entities)
                if converted is not entities:
                    request.entities = converted

        elif name == "SendMultiMediaRequest":
            for media in getattr(request, "multi_media", None) or []:
                ent = getattr(media, "entities", None)
                if ent:
                    converted = self._convert_entities(ent)
                    if converted is not ent:
                        media.entities = converted

        return request

    async def _try_hook_mtproto(self):
        module = self

        async def _patched_call(self_client, request, *args, **kwargs):
            is_bot = module._bot_client is not None and self_client is module._bot_client
            request = module._process_tl_request(request, skip_owner_check=is_bot)
            return await TelegramClient._prem_orig_call(
                self_client, request, *args, **kwargs
            )

        try:
            if not hasattr(TelegramClient, "_prem_orig_call"):
                TelegramClient._prem_orig_call = TelegramClient.__call__

            TelegramClient.__call__ = _patched_call

            self._hooked_mtproto = True
            logger.info("ExteraEmoji: MTProto __call__ hook active")
        except Exception as e:
            logger.info(
                "ExteraEmoji: MTProto hook blocked (%s), fallback active", e
            )
            self._hooked_mtproto = False

    async def _try_hook_inline_bot(self):
        module = self

        bot = None
        try:
            for attr in ("bot", "_bot"):
                bot = getattr(self.inline, attr, None)
                if bot is not None:
                    break
        except Exception:
            pass

        if bot is None:
            try:
                inline = getattr(self._client, "inline", None)
                if inline is not None:
                    for attr in ("bot", "_bot"):
                        bot = getattr(inline, attr, None)
                        if bot is not None:
                            break
            except Exception:
                pass

        if bot is None:
            logger.info("ExteraEmoji: inline bot not found, skipping aiogram hook")
            return

        self._bot_client = getattr(bot, "client", None)

        def _process_text_args(args, kwargs):
            new_args = list(args)
            new_kwargs = dict(kwargs)
            for i, arg in enumerate(new_args):
                if isinstance(arg, str):
                    new_args[i] = ExteraEmojiMod._replace_html_bot(arg)
            for key in _TEXT_KEYS:
                if key in new_kwargs and isinstance(new_kwargs[key], str):
                    new_kwargs[key] = ExteraEmojiMod._replace_html_bot(new_kwargs[key])
            for key in ("media",):
                val = new_kwargs.get(key)
                if val is None:
                    continue
                items = val if isinstance(val, list) else [val]
                for item in items:
                    if hasattr(item, "caption") and isinstance(item.caption, str):
                        item.caption = ExteraEmojiMod._replace_html_bot(item.caption)
            return new_args, new_kwargs

        def _make_patched(orig):
            async def _patched(*args, **kwargs):
                if not module.config["enabled"]:
                    return await orig(*args, **kwargs)
                new_args, new_kwargs = _process_text_args(args, kwargs)
                return await orig(*new_args, **new_kwargs)
            return _patched

        try:
            for method_name in _BOT_METHODS:
                orig = getattr(bot, method_name, None)
                if orig is None:
                    continue
                self._bot_orig[method_name] = orig
                setattr(bot, method_name, _make_patched(orig))

            self._hooked_bot = True
            logger.info("ExteraEmoji: aiogram bot hooks active")
        except Exception as e:
            logger.info("ExteraEmoji: bot hook blocked (%s)", e)
            self._hooked_bot = False

        if self._bot_client is not None:
            try:
                _client_methods = ("edit_message", "send_message", "send_file")
                for method_name in _client_methods:
                    orig = getattr(self._bot_client, method_name, None)
                    if orig is None:
                        continue
                    self._client_orig[method_name] = orig
                    setattr(self._bot_client, method_name, _make_patched(orig))
                logger.info("ExteraEmoji: bot client hooks active")
            except Exception as e:
                logger.info("ExteraEmoji: bot client hook blocked (%s)", e)

    async def _fallback_edit_message(self, message: Message):
        msg_key = (message.chat_id, message.id)
        if msg_key in self._processed:
            self._processed.discard(msg_key)
            return

        raw = getattr(message, "raw_text", None) or ""

        if raw and ("<emoji" in raw or "<tg-emoji" in raw):
            try:
                plain, html_entities = tl_html.parse(raw)
                modified = self._convert_entities(html_entities)
                if modified is not html_entities:
                    self._processed.add(msg_key)
                    peer = await message.get_input_chat()
                    await self._client(TLEditMessage(
                        peer=peer,
                        id=message.id,
                        message=plain,
                        entities=modified,
                        no_webpage=True,
                    ))
            except Exception:
                logger.debug("Fallback HTML edit failed", exc_info=True)
                self._processed.discard(msg_key)
            return

        # UpdateEditMessage присылает обрезанный список entities для больших сообщений.
        # Запрашиваем полное сообщение, чтобы получить ВСЕ entities (включая цитаты в конце).
        try:
            peer = await message.get_input_chat()
            full_msg = await self._client.get_messages(peer, ids=message.id)
            entities = getattr(full_msg, "entities", None) or message.entities or []
            text = getattr(full_msg, "message", None) or message.message or ""
        except Exception:
            peer = None
            entities = message.entities or []
            text = message.message or ""

        if any(isinstance(e, MessageEntityCustomEmoji) for e in entities):
            try:
                modified = self._convert_entities(entities)
                if modified is not entities:
                    self._processed.add(msg_key)
                    if peer is None:
                        peer = await message.get_input_chat()
                    await self._client(TLEditMessage(
                        peer=peer,
                        id=message.id,
                        message=text,
                        entities=modified,
                        no_webpage=True,
                    ))
            except Exception:
                logger.debug("Fallback entity edit failed", exc_info=True)
                self._processed.discard(msg_key)

    @loader.watcher(out=True, only_messages=True)
    async def emoji_replacer_watcher(self, message: Message):
        """Watcher for new outgoing messages"""
        if not self.config["enabled"]:
            return
        if message.sender_id in (777000, 489000):
            return
        if self._is_ignored_chat(message.chat_id):
            return
        entities = message.entities or []
        if not any(isinstance(e, MessageEntityCustomEmoji) for e in entities):
            return
        await self._fallback_edit_message(message)

    @loader.raw_handler(UpdateEditMessage, UpdateEditChannelMessage)
    async def emoji_replacer_edit_handler(self, event):
        """Handler for outgoing message edits"""
        if not self.config["enabled"]:
            return

        message = getattr(event, "message", None)
        if message is None:
            return
        if not getattr(message, "out", False):
            return
        if message.sender_id in (777000, 489000):
            return
        if self._is_ignored_chat(message.chat_id):
            return
        entities = message.entities or []
        if not any(isinstance(e, MessageEntityCustomEmoji) for e in entities):
            return
        await self._fallback_edit_message(message)

    async def on_unload(self):
        if self._hooked_mtproto:
            try:
                TelegramClient.__call__ = TelegramClient._prem_orig_call
                del TelegramClient._prem_orig_call
                logger.info("ExteraEmoji: MTProto hook restored")
            except Exception:
                logger.debug("ExteraEmoji: failed to restore MTProto hook", exc_info=True)

        if self._hooked_bot and self._bot_orig:
            bot = None
            try:
                for attr in ("bot", "_bot"):
                    bot = getattr(self.inline, attr, None)
                    if bot is not None:
                        break
            except Exception:
                pass
            if bot is None:
                try:
                    inline = getattr(self._client, "inline", None)
                    if inline is not None:
                        for attr in ("bot", "_bot"):
                            bot = getattr(inline, attr, None)
                            if bot is not None:
                                break
                except Exception:
                    pass
            if bot is not None:
                for method_name, orig in self._bot_orig.items():
                    try:
                        setattr(bot, method_name, orig)
                    except Exception:
                        pass
            logger.info("ExteraEmoji: bot hooks restored")

        if self._bot_client is not None and self._client_orig:
            for method_name, orig in self._client_orig.items():
                try:
                    setattr(self._bot_client, method_name, orig)
                except Exception:
                    pass
            logger.info("ExteraEmoji: bot client hooks restored")

        self._processed.clear()