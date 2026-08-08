# meta developer: @CoderHoly - @YouRooni
# meta banner: https://yufic.ru/api/hc/?a=SourceTrigger&b=Ответ%20медиа%20по%20триггеру
# meta name: SourceTriggerFork
# meta version: 2.0.0
# Hi Rooni , I've improved your module a bit
# Paid by @exetans
# The fork was done — @CoderHoly
"""
⣿⣿⡻⠿⣳⠸⢿⡇⢇⣿⡧⢹⠿⣿⣿⣿⣿⣾⣿⡇⣿⣿⣿⣿⡿⡐⣯⠁ ⠄⠄
⠟⣛⣽⡳⠼⠄⠈⣷⡾⣥⣱⠃⠣⣿⣿⣿⣯⣭⠽⡇⣿⣿⣿⣿⣟⢢⠏⠄ ⠄
⢠⡿⠶⣮⣝⣿⠄⠄⠈⡥⢭⣥⠅⢌⣽⣿⣻⢶⣭⡿⠿⠜⢿⣿⣿⡿⠁⠄⠄
⠄⣼⣧⠤⢌⣭⡇⠄⠄⠄⠭⠭⠭⠯⠴⣚⣉⣛⡢⠭⠵⢶⣾⣦⡍⠁⠄⠄⠄⠄
⠄⣿⣷⣯⣭⡷⠄⠄⢀⣀⠩⠍⢉⣛⣛⠫⢏⣈⣭⣥⣶⣶⣦⣭⣛⠄⠄⠄⠄⠄
⢀⣿⣿⣿⡿⠃⢀⣴⣿⣿⣿⣎⢩⠌⣡⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣆⠄⠄⠄
⢸⡿⢟⣽⠎⣰⣿⣿⣿⣿⣿⣿⢀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⠄⠄
⣰⠯⣾⢅⣼⣿⣿⣿⣿⣿⣿⡇⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡄⠄
⢰⣄⡉⣼⣿⣿⣿⣿⣿⣿⣿⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠄
⢯⣌⢹⣿⣿⣿⣿⣿⣿⣿⣿⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠄
⢸⣇⣽⣿⣿⣿⣿⣿⣿⣿⣿⠸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠄
⢸⣟⣧⡻⣿⣿⣿⣿⣿⣿⣿⣧⡻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠄
⠈⢹⡧⣿⣸⠿⢿⣿⣿⣿⣿⡿⠗⣈⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠄
⠄⠘⢷⡳⣾⣷⣶⣶⣶⣶⣶⣾⣿⣿⢀⣶⣶⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠇⠄
⠄⠄⠈⣵⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠄⠄
⠄⠄⠄⠸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠇⠄⠄
"""

import logging
import re
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from .. import loader, utils
from herokutl.types import Message

logger = logging.getLogger(__name__)

__version__ = (2, 0, 0)

@loader.tds
class SourceTriggerMod(loader.Module):
    """Отправляет медиа или текст из канала в ответ на текстовые триггеры."""

    strings = {
        "name": "SourceTriggerFork",
        "parsing_started": (
            "➡️ <b>Parsing started.</b> "
            "This will clear all old triggers and scan the channel from scratch. Please wait..."
        ),
        "parsing_progress": (
            "💬 <b>Parsing in progress...</b>\n"
            "Processed <b>{}</b> messages."
        ),
        "parsing_complete": (
            "✅ <b>Parsing complete!</b>\n"
            "Parsed trigger definitions:\n"
            "<b>{}</b> exact (<code>~</code>)\n"
            "<b>{}</b> contains (<code>~~</code>)\n"
            "<b>{}</b> exact+del (<code>~~~</code>)\n"
            "<b>{}</b> regex (<code>~|</code>)\n"
            "<b>{}</b> regex+del (<code>~~~|</code>)"
        ),
        "channel_error": (
            "❌ <b>Error accessing channel.</b> "
            "Make sure the ID is correct and you are a member of the channel."
            " Try forwarding any message from it to your Saved Messages."
        ),
        "add_trigger_error": (
            "❗️ <b>Failed to add trigger.</b>\n"
            "Make sure your userbot is a member of the source channel and has permission to post messages."
        ),
        "config_source_channel": "ID of the source channel with triggers and media/text.",
        "config_auto_parse_on_start": "Automatically run parsing when the module loads.",
        "trigger_added": "✅ <b>New response for trigger <code>{}</code> added.</b> <a href='{}'>Go to message</a>.",
        "must_be_reply": "➡️ <b>You must reply to a message.</b>",
        "no_trigger_specified": "📝 <b>You must specify a trigger.</b> Example: <code>.addtrigger ~hi</code>",
        "invalid_trigger_format": "❌ <b>Invalid trigger format.</b> Must start with <code>~</code>, <code>~~</code>, or <code>~~~</code>.",
        "trigger_format_examples": "📝 <b>Trigger format examples:</b>\n• <code>~text</code> - exact match\n• <code>~~text</code> - contains text\n• <code>~~~text</code> - exact match + delete\n• <code>~|pattern</code> - regex match\n• <code>~~~|pattern</code> - regex match + delete",
        "processing_add": "💬 <b>Processing...</b>",
        "help_title": "📚 <b>SourceTrigger Help</b>",
        "help_description": "Module for automatic responses to text triggers with media/text from channel.",
        "help_formats_title": "<b>🔤 Trigger Formats:</b>",
        "help_formats": "\n• <code>~text</code> - Exact match\n• <code>~~text</code> - Contains text\n• <code>~~~text</code> - Exact match + delete message\n• <code>~|pattern</code> - Regex match\n• <code>~~~|pattern</code> - Regex match + delete message",
        "help_commands_title": "<b>⚙️ Commands:</b>",
        "help_commands": "\n• <code>.trhelp</code> - Show this help\n• <code>.parsetriggers</code> - Update triggers from channel\n• <code>.addtrigger</code> [reply] [trigger] - Add new trigger\n• <code>.listtriggers</code> - Show triggers list\n• <code>.deltrigger</code> [number] - Delete trigger by number\n• <code>.sptr</code> - Manage triggers with inline menu",
        "help_scopes_title": "<b>🎯 Trigger Scopes:</b>",
        "help_scopes": "\n• <code>everyone</code> - Works in all chats\n• <code>here</code> - Only in current chat\n• <code>me</code> - Only on your messages",
        "help_examples_title": "<b>📝 Examples:</b>",
        "help_examples": "\n• Reply to media: <code>.addtrigger ~hello</code>\n• Channel setup: Send <code>~hi</code> as first line, media as reply\n• Scope setup: Choose scope when adding trigger",
        "triggers_list_title": "📋 <b>Triggers Management</b>",
        "triggers_list_empty": "❌ <b>No triggers found.</b>\nUse <code>.addtrigger</code> to add new triggers.",
        "triggers_selected": "<b>Selected for deletion: {}</b>",
        "triggers_delete_confirm": "⚠️ <b>Confirm deletion</b>\n\nSelected triggers will be permanently deleted.\n\n{}",
        "triggers_deleted": "✅ <b>Triggers deleted successfully!</b>\nDeleted: <b>{}</b> triggers.",
        "triggers_none_selected": "📝 <b>No triggers selected.</b>\nSelect triggers to delete them.",
        "_cls_doc": "Sends media/text based on triggers. Formats: ~exact, ~~contains, ~~~exact+del, ~|regex, ~~~|regex+del.",
        "_cmd_doc_trhelp": "Show help and usage instructions.",
        "_cmd_doc_parsetriggers": "Scan the source channel to update triggers.",
        "_cmd_doc_addtrigger": "<reply to message> [trigger] - Add a new trigger. Use ~trigger for exact match, ~~trigger for contains, ~~~trigger for exact+delete, ~|regex for regex match.",
        "_cmd_doc_trhelp_ru": "Показать справку и инструкции по использованию.",
        "_cmd_doc_parsetriggers_ru": "Сканировать исходный канал для обновления триггеров.",
        "_cmd_doc_addtrigger_ru": "<ответ на сообщение> [триггер] - Добавить новый триггер. Используйте ~триггер для точного совпадения, ~~триггер для содержания, ~~~триггер для точного+удаление, ~|regex для регулярного выражения.",
    }

    strings_ru = {
        "parsing_started": (
            "<emoji document_id=5204189706237004154>➡️</emoji> <b>Индексация начата.</b> "
            "Все старые триггеры будут удалены, канал будет просканирован заново. Пожалуйста, подождите..."
        ),
        "parsing_progress": (
            "<emoji document_id=5429411030960711866>💬</emoji> <b>Индексация в процессе...</b>\n"
            "Обработано <b>{}</b> сообщений."
        ),
        "parsing_complete": (
            "<emoji document_id=5260726538302660868>✅</emoji> <b>Индексация"
            " завершена!</b>\nОбработано определений триггеров:\n"
            "<b>{}</b> точных (<code>~</code>)\n"
            "<b>{}</b> по вхождению (<code>~~</code>)\n"
            "<b>{}</b> точных+удалить (<code>~~~</code>)\n"
            "<b>{}</b> regex (<code>~|</code>)\n"
            "<b>{}</b> regex+удалить (<code>~~~|</code>)"
        ),
        "channel_error": (
            "<emoji document_id=5260342697075416641>❌</emoji> <b>Ошибка доступа к"
            " каналу.</b> Убедитесь, что ID указан верно и вы состоите в канале."
            " Попробуйте переслать любое сообщение из него в 'Избранное'."
        ),
        "add_trigger_error": (
            "<emoji document_id=5258474669769497337>❗️</emoji> <b>Не удалось добавить триггер.</b>\n"
            "Убедитесь, что ваш юзербот является участником исходного канала и имеет права на отправку сообщений."
        ),
        "config_source_channel": "ID исходного канала с триггерами и медиа/текстом.",
        "config_auto_parse_on_start": "Автоматически запускать индексацию при загрузке модуля.",
        "config_allow_incoming": "Разрешить срабатывание триггеров на сообщения других пользователей",
        "trigger_added": "<emoji document_id=5260726538302660868>✅</emoji> <b>Новый ответ для триггера <code>{}</code> добавлен.</b> <a href='{}'>Перейти к сообщению</a>.",
        "must_be_reply": "<emoji document_id=5260450573768990626>➡️</emoji> <b>Нужно ответить на сообщение.</b>",
        "no_trigger_specified": "<emoji document_id=5257965174979042426>📝</emoji> <b>Нужно указать триггер.</b> Пример: <code>.addtrigger ~привет</code>",
        "invalid_trigger_format": "<emoji document_id=5260342697075416641>❌</emoji> <b>Неверный формат триггера.</b> Должен начинаться с <code>~</code>, <code>~~</code>, или <code>~~~</code>.",
        "trigger_format_examples": "<emoji document_id=5257965174979042426>📝</emoji> <b>Примеры форматов триггеров:</b>\n• <code>~текст</code> - точное совпадение\n• <code>~~текст</code> - содержит текст\n• <code>~~~текст</code> - точное + удалить\n• <code>~|шаблон</code> - regex\n• <code>~~~|шаблон</code> - regex + удалить",
        "processing_add": "<emoji document_id=5427181942934088912>💬</emoji> <b>Обработка...</b>",
        "help_title": "<emoji document_id=5875480137919940968>📚</emoji> <b>SourceTrigger Помощь</b>",
        "help_description": "Модуль для автоматических ответов на текстовые триггеры с медиа/текстом из канала.",
        "help_formats_title": "<b>🔤 Форматы триггеров:</b>",
        "help_formats": "\n• <code>~текст</code> - Точное совпадение\n• <code>~~текст</code> - Содержит текст\n• <code>~~~текст</code> - Точное совпадение + удалить сообщение\n• <code>~|шаблон</code> - Regex совпадение\n• <code>~~~|шаблон</code> - Regex совпадение + удалить сообщение",
        "help_commands_title": "<b>⚙️ Команды:</b>",
        "help_commands": "\n• <code>.trhelp</code> - Показать эту помощь\n• <code>.parsetriggers</code> - Обновить триггеры из канала\n• <code>.addtrigger</code> [ответ] [триггер] - Добавить новый триггер\n• <code>.listtriggers</code> - Показать список триггеров\n• <code>.deltrigger</code> [номер] - Удалить триггер по номеру\n• <code>.sptr</code> - Управление триггерами через инлайн-меню",
        "help_scopes_title": "<b>🎯 Области действия триггеров:</b>",
        "help_scopes": "\n• <code>everyone</code> - Работает во всех чатах\n• <code>here</code> - Только в текущем чате\n• <code>me</code> - Только на ваши сообщения",
        "help_examples_title": "<b>📝 Примеры:</b>",
        "help_examples": "\n• Ответить на медиа: <code>.addtrigger ~привет</code>\n• Настройка канала: Отправить <code>~привет</code> первой строкой, медиа в ответ\n• Настройка области: Выбрать область при добавлении триггера",
        "triggers_list_title": "<emoji document_id=5875480137919940968>📋</emoji> <b>Управление триггерами</b>",
        "triggers_list_empty": "<emoji document_id=5260342697075416641>❌</emoji> <b>Триггеры не найдены.</b>\nИспользуйте <code>.addtrigger</code> для добавления новых триггеров.",
        "triggers_selected": "<b>Выбрано для удаления: {}</b>",
        "triggers_delete_confirm": "<emoji document_id=5260342697075416641>⚠️</emoji> <b>Подтверждение удаления</b>\n\nВыбранные триггеры будут безвозвратно удалены.\n\n{}",
        "triggers_deleted": "<emoji document_id=5260726538302660868>✅</emoji> <b>Триггеры успешно удалены!</b>\nУдалено: <b>{}</b> триггеров.",
        "triggers_none_selected": "<emoji document_id=5257965174979042426>📝</emoji> <b>Не выбрано ни одного триггера.</b>\nВыберите триггеры для их удаления.",
        "trigger_limit_reached": "⚠️ <b>Достигнут лимит в 10 триггеров.</b>\nУдалите один или несколько триггеров, чтобы добавить новые.",
        "trigger_duplicate": "⚠️ <b>Дубликат триггера.</b>\nТриггер с такими параметрами уже существует.",
        "trigger_limit_reached_parsing": "\n\n⚠️ <b>Достигнут лимит в 10 триггеров.</b>",
        "_cls_doc": "Отправляет медиа/текст по триггерам. Форматы: ~точно, ~~содержит, ~~~точно+удал, ~|regex, ~~~|regex+удал.",
        "_cmd_doc_trhelp": "Показать помощь и инструкции по использованию.",
        "_cmd_doc_parsetriggers": "Сканировать исходный канал для обновления триггеров.",
        "_cmd_doc_addtrigger": "<ответ на сообщение> <триггер> - Добавить новый триггер.",
        "_cmd_doc_sptr": "Управление триггерами через инлайн-меню (выбор и удаление).",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "source_channel_id",
                None,
                lambda: self.strings("config_source_channel"),
                validator=loader.validators.Integer(),
            ),
            loader.ConfigValue(
                "auto_parse_on_start",
                True,
                lambda: self.strings("config_auto_parse_on_start"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "allow_incoming",
                False,
                lambda: self.strings("config_allow_incoming"),
                validator=loader.validators.Boolean(),
            ),
        )
        self.triggers = {}
        self.trigger_message_ids = {}
        self.BATCH_SIZE = 200
        self.client = None
        self.db = None

        self.trigger_creation_state = {}
        self._multi_select = {}

    async def _ui_edit_or_form(self, target, text, reply_markup):
        if isinstance(target, Message):
            await self.inline.form(text=text, message=target, reply_markup=reply_markup)
        else:
            await target.edit(text, reply_markup=reply_markup)

    def _normalize_trigger(self, ttype: str, trigger: str) -> str:
        if ttype in {"exact", "contains", "exact_delete"}:
            return (trigger or "").strip().lower()
        return (trigger or "").strip()

    async def _select_trigger_scope_inline_from_command(self, message):
        user_id = message.sender_id
        state = self.trigger_creation_state.get(user_id, {})

        format_names = {
            "exact": "Точное совпадение",
            "contains": "Содержит текст",
            "exact_delete": "Точное + удалить",
            "regex": "Regex",
            "regex_delete": "Regex + удалить"
        }

        trigger_display = state.get("original_trigger", state.get("trigger", "неизвестный"))
        format_display = format_names.get(state.get("format", "exact"), "неизвестный")

        text = (
            "👨‍💻<b> Создание триггера</b> | <b>Шаг 2/2: Выберите область действия</b>\n\n"
            f"<b>✅ Формат:</b> {format_display}\n"
            f"<b>✅ Триггер:</b> <code>{utils.escape_html(trigger_display)}</code>\n\n"
            "<b>🎯 Области действия:</b>\n"
            "<blockquote>• <code>Everyone</code> - работает во всех чатах\n"
            "• <code>Here</code> - только в этом чате\n"
            "• <code>Me</code> - только на ваши сообщения\n"
            "</blockquote><b>Выберите область:</b>"
        )

        await self.inline.form(
            text=text,
            message=message,
            reply_markup=[
                [{"text": "Everyone", "callback": lambda c: self._select_trigger_scope(c, "everyone", None, True)}],
                [{"text": "Here", "callback": lambda c: self._select_trigger_scope(c, "here", state.get("chat_id"), True)}],
                [{"text": "Me", "callback": lambda c: self._select_trigger_scope(c, "me", None, True)}],
                [{"text": "❌ Отмена", "callback": lambda c: self._cancel_trigger_creation(c, True)}],
            ]
        )

    async def _add_trigger_menu_inline(self, message):
        await self.inline.form(
            text=(
                "👨‍💻<b> Создание триггера</b> | <b>Шаг 1/2: Выберите формат триггера</b>\n\n"
                "<b>🎯 Форматы:</b>\n"
                "<blockquote>• <code>Точное совпадение</code> - срабатывает на точный текст\n"
                "• <code>Содержит текст</code> - срабатывает если содержит\n"
                "• <code>Точное + удалить</code> - точное совпадение с удалением\n"
                "• <code>Regex</code> - регулярное выражение\n"
                "• <code>Regex + удалить</code> - regex с удалением</blockquote>\n"
                "<b>Примеры:</b>\n"
                "<blockquote>• <code>привет</code> - точное совпадение\n"
                "• <code>привет</code>  , как дела?- содержит текст\n"
                "• <code>привет</code> - точное + удалить\n"
                "• <code>~|привет.*</code> - regex\n"
                "• <code>~~~|привет.*</code> - regex + удалить\n"
                "</blockquote><b>Выберите формат:</b>"
            ),
            message=message,
            reply_markup=self._get_format_buttons(True)
        )

    async def on_dlmod(self):
        stored_triggers = self.db.get("SourceTrigger", "triggers", {})
        stored_trigger_msg_ids = self.db.get("SourceTrigger", "trigger_message_ids", {})

        for key, value in stored_triggers.items():
            if isinstance(value, list):
                stored_triggers[key] = {
                    "msg_ids": value,
                    "scope": "everyone",
                    "chat_id": None
                }

        normalized_triggers: Dict[str, Dict[str, Any]] = {}
        normalized_trigger_msg_ids: Dict[str, int] = {}

        for key, trigger_data in stored_triggers.items():
            if not isinstance(key, str) or "::" not in key:
                continue
            ttype, pattern = key.split("::", 1)
            norm_pattern = self._normalize_trigger(ttype, pattern)
            norm_key = f"{ttype}::{norm_pattern}"

            if norm_key not in normalized_triggers:
                normalized_triggers[norm_key] = {
                    "msg_ids": list(trigger_data.get("msg_ids", [])),
                    "scope": trigger_data.get("scope", "everyone"),
                    "chat_id": trigger_data.get("chat_id"),
                }
            else:
                existing = normalized_triggers[norm_key]
                for mid in trigger_data.get("msg_ids", []):
                    if mid not in existing["msg_ids"]:
                        existing["msg_ids"].append(mid)

            if key in stored_trigger_msg_ids and norm_key not in normalized_trigger_msg_ids:
                normalized_trigger_msg_ids[norm_key] = stored_trigger_msg_ids[key]

        self.triggers = normalized_triggers
        self.trigger_message_ids = normalized_trigger_msg_ids

        self.db.set("SourceTrigger", "triggers", self.triggers)
        self.db.set("SourceTrigger", "trigger_message_ids", self.trigger_message_ids)

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        if self.config["auto_parse_on_start"]:
            await self._run_parser(message=None)

    def _get_source_channel(self):
        channel_id = self.config["source_channel_id"]
        return [channel_id] if channel_id else []

    async def _process_message_for_triggers(self, msg):
        """Processes a message to find a trigger definition and its target content."""
        if not msg:
            return None

        trigger_def_msg = msg
        content_msg = msg

        if msg.is_reply:
            replied = await msg.get_reply_message()
            if replied:
                content_msg = replied
            else:
                return None
        
        trigger_text = None
        if hasattr(trigger_def_msg, 'text') and trigger_def_msg.text:
            trigger_text = trigger_def_msg.text.strip()
        elif hasattr(trigger_def_msg, 'message') and trigger_def_msg.message:
            trigger_text = trigger_def_msg.message.strip()
        
        if not trigger_text:
            return None

        if "::" in trigger_text and "Область:" in trigger_text:
            lines = trigger_text.split('\n')
            first_line = lines[0].strip()
            
            if "::" in first_line:
                type_trigger_part = first_line.split("::", 1)
                if len(type_trigger_part) == 2:
                    ttype_part = type_trigger_part[0].strip()
                    trigger_part = type_trigger_part[1].strip()
                    
                    if ttype_part == "exact":
                        ttype, trigger = "exact", trigger_part.lower()
                    elif ttype_part == "exact_delete":
                        ttype, trigger = "exact_delete", trigger_part.lower()
                    elif ttype_part == "contains":
                        ttype, trigger = "contains", trigger_part.lower()
                    elif ttype_part == "regex":
                        try:
                            re.compile(trigger_part, re.IGNORECASE)
                            ttype, trigger = "regex", trigger_part
                        except re.error:
                            return None
                    elif ttype_part == "regex_delete":
                        try:
                            re.compile(trigger_part, re.IGNORECASE)
                            ttype, trigger = "regex_delete", trigger_part
                        except re.error:
                            return None
                    else:
                        return None
                    
                    if ttype and trigger:
                        return ttype, trigger, content_msg.id
        
        first_line = trigger_text.split('\n', 1)[0].strip()
        ttype, trigger = None, None
        
        if re.match(r"^~{1,3}", first_line):
            if first_line.startswith("~~~"):
                content_after = first_line[3:].lstrip()
                if content_after.startswith("|"):
                    pattern = content_after[1:].strip()
                    if pattern:
                        try:
                            re.compile(pattern, re.IGNORECASE)
                            ttype, trigger = "regex_delete", pattern
                        except re.error: pass
                else:
                    ttype, trigger = "exact_delete", content_after.strip().lower()
            elif first_line.startswith("~~"):
                ttype, trigger = "contains", first_line[2:].strip().lower()
            elif first_line.startswith("~"):
                content_after = first_line[1:].lstrip()
                if content_after.startswith("|"):
                    pattern = content_after[1:].strip()
                    if pattern:
                        try:
                            re.compile(pattern, re.IGNORECASE)
                            ttype, trigger = "regex", pattern
                        except re.error: pass
                else:
                    ttype, trigger = "exact", content_after.strip().lower()
        
        if ttype and trigger:
            return ttype, trigger, content_msg.id
        return None

    async def _process_batch(self, tasks: list, triggers_dict: dict, counts_dict: dict, status_msg, total_processed: int, added_count: int = 0):
        """Processes a batch of tasks and updates the data structures with ограничениями."""
        results = await asyncio.gather(*tasks)
        
        if added_count >= 10:
            return added_count, counts_dict
            
        for result in results:
            if not result:
                continue
            ttype, trigger, msg_id = result

            if added_count < 10:
                is_added, added_count = await self._add_trigger_safe(ttype, trigger, "everyone", [msg_id], None, added_count)
                if is_added:
                    counts_dict[ttype] += 1
            else:
                break
        
        if status_msg and total_processed % (self.BATCH_SIZE * 5) == 0:
            try:
                await utils.answer(status_msg, self.strings("parsing_progress").format(total_processed))
            except Exception:
                pass
                
        return added_count, counts_dict

    def _get_format_buttons(self, is_inline: bool = False):
        """Возвращает кнопки для выбора формата триггера."""
        base_buttons = [
            [{"text": "Точное совпадение", "callback": lambda c: self._select_trigger_format(c, "exact", is_inline)}],
            [{"text": "Содержит текст", "callback": lambda c: self._select_trigger_format(c, "contains", is_inline)}],
            [{"text": "Точное + удалить", "callback": lambda c: self._select_trigger_format(c, "exact_delete", is_inline)}],
            [{"text": "Regex", "callback": lambda c: self._select_trigger_format(c, "regex", is_inline)}],
            [{"text": "Regex + удалить", "callback": lambda c: self._select_trigger_format(c, "regex_delete", is_inline)}],
            [{"text": "❌ Отмена", "callback": lambda c: self._cancel_trigger_creation(c, is_inline)}],
        ]
        return base_buttons

    def _get_action_buttons(self, is_inline: bool = False):
        """Возвращает общие кнопки действий для меню управления триггерами."""
        if is_inline:
            return [
                [{"text": "🗑️ Удалить выбранные", "callback": self._confirm_delete_selected_inline}],
                [{"text": "🔄 Обновить", "callback": self._manage_triggers_menu_inline}],
            ]
        else:
            return [
                [{"text": "🗑️ Удалить выбранные", "callback": self._confirm_delete_selected}],
                [{"text": "🔄 Обновить", "callback": self._manage_triggers_menu}],
            ]

    def _get_confirm_buttons(self, is_inline: bool = False):
        """Возвращает кнопки подтверждения."""
        if is_inline:
            return [
                [{"text": "✅ Подтвердить", "callback": self._execute_delete_selected_inline}],
                [{"text": "❌ Отмена", "callback": self._manage_triggers_menu_inline}],
            ]
        else:
            return [
                [{"text": "✅ Подтвердить удаление", "callback": self._execute_delete_selected}],
                [{"text": "❌ Отмена", "callback": self._manage_triggers_menu}],
            ]

    def _get_navigation_buttons(self, is_inline: bool = False):
        """Возвращает навигационные кнопки."""
        if is_inline:
            return [
                [{"text": "📋 Управление триггерами", "callback": self._sptr_menu}],
            ]
        else:
            return [
                [{"text": "📋 Управление триггерами", "callback": self._manage_triggers_menu}],
            ]

    def _get_scope_buttons(self, state, is_inline: bool = False):
        """Возвращает кнопки для выбора области действия."""
        format_type = state.get("format", "exact")

        if is_inline:
            buttons = [
                [{"text": "Everyone 🌐", "callback": lambda c: self._select_trigger_scope(c, "everyone", None, True)}],
                [{"text": "Here 🏠", "callback": lambda c: self._select_trigger_scope(c, "here", getattr(c.message, 'chat_id', None), True)}],
                [{"text": "Me 👤", "callback": lambda c: self._select_trigger_scope(c, "me", None, True)}],
                [{"text": "⬅️ Назад", "callback": lambda c: self._add_trigger_menu(c, True)}],
                [{"text": "❌ Отмена", "callback": lambda c: self._cancel_trigger_creation(c, True)}],
            ]
        else:
            buttons = [
                [{"text": "Everyone 🌐", "callback": lambda c: self._select_trigger_scope(c, "everyone", None, False)}],
                [{"text": "Here 🏠", "callback": lambda c, chat_id=c.message.chat.id: self._select_trigger_scope(c, "here", chat_id, False)}],
                [{"text": "Me 👤", "callback": lambda c: self._select_trigger_scope(c, "me", None, False)}],
                [{"text": "⬅️ Назад", "callback": lambda c: self._select_trigger_format(c, format_type, False)}],
                [{"text": "❌ Отмена", "callback": lambda c: self._cancel_trigger_creation(c, False)}],
            ]
        return buttons

    async def _add_trigger_menu(self, call, is_inline: bool = False):
        """Унифицированное меню для добавления триггера - шаг 1: выбор формата"""
        user_id = call.from_user.id
        self.trigger_creation_state[user_id] = {"step": "format", "reply_msg": None}

        text = (
            "👨‍💻<b> Создание триггера</b> | <b>Шаг 1/2: Выберите формат триггера</b>\n\n"
            "<b>🎯 Форматы:</b>\n"
            "<blockquote>• <code>Точное совпадение</code> - срабатывает на точный текст\n"
            "• <code>Содержит текст</code> - срабатывает если содержит\n"
            "• <code>Точное + удалить</code> - точное совпадение с удалением\n"
            "• <code>Regex</code> - регулярное выражение\n"
            "• <code>Regex + удалить</code> - regex с удалением\n"
            "</blockquote><b>Выберите формат:</b>"
        )

        await call.edit(text, reply_markup=self._get_format_buttons(is_inline))

    async def _select_trigger_format(self, call, format_type, is_inline: bool = False):
        """Унифицированная обработка выбора формата триггера"""
        user_id = call.from_user.id
        if user_id not in self.trigger_creation_state:
            return

        state = self.trigger_creation_state[user_id]
        state["format"] = format_type
        state["step"] = "scope"

        format_names = {
            "exact": "Точное совпадение",
            "contains": "Содержит текст",
            "exact_delete": "Точное + удалить",
            "regex": "Regex",
            "regex_delete": "Regex + удалить"
        }

        text = (
            "<b>➕ Создание триггера</b>\n\n"
            f"<b>✅ Формат:</b> {format_names[format_type]}\n\n"
            "<b>Шаг 2/3: Выберите область действия</b>\n\n"
            "<b>🎯 Области:</b>\n"
            "• <code>Everyone</code> - работает во всех чатах\n"
            "• <code>Here</code> - только в этом чате\n"
            "• <code>Me</code> - только на ваши сообщения\n\n"
            "<b>Выберите область:</b>"
        )

        await call.edit(text, reply_markup=self._get_scope_buttons(state, is_inline))

    async def _select_trigger_scope(self, call, scope, chat_id=None, is_inline: bool = False):
        """Унифицированная обработка выбора области действия триггера"""
        user_id = call.from_user.id
        if user_id not in self.trigger_creation_state:
            return

        state = self.trigger_creation_state[user_id]
        state["scope"] = scope
        if chat_id:
            state["chat_id"] = chat_id

        if "trigger" in state and "format" in state:
            ttype = state["format"]
            trigger = state["trigger"]
            await self._create_trigger_from_state(call, ttype, trigger)
            return

        if "manual_input" in state and state["manual_input"] and "format" in state:
            ttype = state["format"]
            trigger = state["manual_input"].strip()
            if ttype in ["regex", "regex_delete"]:
                try:
                    re.compile(trigger, re.IGNORECASE)
                except re.error:
                    menu_callback = self._add_trigger_menu_inline if is_inline else self._add_trigger_menu
                    cancel_callback = lambda c: self._cancel_trigger_creation(c, is_inline)
                    await call.edit(
                        "<b>❌ Неверное регулярное выражение</b>\n\n"
                        f"<code>{utils.escape_html(trigger)}</code> не является допустимым регулярным выражением.\n\n"
                        "Примеры:\n"
                        "<blockquote><code>привет.*</code> - начинается с 'привет'\n"
                        "<code>.*привет.*</code> - содержит 'привет'\n"
                        "<code>^привет$</code> - точно 'привет'</blockquote>",
                        reply_markup=[
                            [{"text": "🔄 Попробовать снова", "callback": menu_callback}],
                            [{"text": "❌ Отмена", "callback": cancel_callback}],
                        ]
                    )
                    return

            await self._create_trigger_from_state(call, ttype, trigger)
            return

        state["step"] = "input_trigger"

        scope_names = {
            "everyone": "🌐 Everyone",
            "here": "🏠 Here",
            "me": "👤 Me"
        }

        format_names = {
            "exact": "🎯 Точное совпадение",
            "contains": "🔍 Содержит текст",
            "exact_delete": "🎯❌ Точное + удалить",
            "regex": "🔤 Regex",
            "regex_delete": "🔤❌ Regex + удалить"
        }

        text = (
            "<b>➕ Создание триггера</b>\n\n"
            f"<b>✅ Формат:</b> {format_names[state['format']]}\n"
            f"<b>✅ Область:</b> {scope_names[scope]}\n\n"
            "<b>Шаг 3/3: Введите триггер</b>\n\n"
            "Нажмите кнопку ниже, чтобы ввести текст триггера через инлайн-форму.\n\n"
            "<i>Примеры: ~привет, ~~привет, ~~~привет, ~|привет.*, ~~~|привет.*</i>"
        )

        if is_inline:
            reply_markup = [
                [{"text": "✏️ Ввести триггер", "callback": lambda c: self.inline.input(c, "Введите текст триггера", self._input_trigger_callback)}],
                [{"text": "⬅️ Назад", "callback": lambda c: self._select_trigger_format(c, state['format'], True)}],
                [{"text": "❌ Отмена", "callback": lambda c: self._cancel_trigger_creation_inline(c)}],
            ]
        else:
            reply_markup = [
                [{"text": "✏️ Ввести триггер", "input": "Введите текст триггера (например: ~привет)", "callback": self._input_trigger_callback}],
                [{"text": "⬅️ Назад", "callback": lambda c: self._select_trigger_format(c, state['format'], False)}],
                [{"text": "❌ Отмена", "callback": lambda c: self._cancel_trigger_creation(c, False)}],
            ]

        await call.edit(text, reply_markup=reply_markup)

    async def _cancel_trigger_creation(self, call, is_inline: bool = False):
        """Унифицированная отмена создания триггера"""
        user_id = call.from_user.id
        if user_id in self.trigger_creation_state:
            del self.trigger_creation_state[user_id]

        if is_inline:
            help_callback = lambda c: self._show_help_menu_inline(c)
        else:
            help_callback = self._show_help_menu

        await call.edit(
            "<b>❌ Создание триггера отменено</b>",
            reply_markup=[[{"text": "🔙 К помощи", "callback": help_callback}]]
        )




    async def _input_trigger_inline(self, call, trigger_text):
        """Обработка ввода триггера через inline"""
        user_id = call.from_user.id
        if user_id not in self.trigger_creation_state:
            return

        state = self.trigger_creation_state[user_id]
        
        if "manual_input" in state and state["manual_input"]:
            trigger_text = state["manual_input"]

        if not trigger_text or not trigger_text.strip():
            await call.edit(
                "<b>❌ Текст триггера не может быть пустым</b>\n\n"
                "Попробуйте снова ввести текст.",
                reply_markup=[[{"text": "🔄 Попробовать снова", "callback": lambda c: self.inline.input(c, "Введите текст триггера", self._input_trigger_callback)}]]
            )
            return

        if "format" in state:
            ttype = state["format"]
            trigger = trigger_text.strip()
            if ttype in ["regex", "regex_delete"]:
                try:
                    re.compile(trigger, re.IGNORECASE)
                except re.error:
                    await call.edit(
                        "<b>❌ Неверное регулярное выражение</b>\n\n"
                        f"<code>{utils.escape_html(trigger)}</code> не является допустимым регулярным выражением.\n\n"
                        "Примеры:\n"
                        "<blockquote><code>привет.*</code> - начинается с 'привет'\n"
                        "<code>.*привет.*</code> - содержит 'привет'\n"
                        "<code>^привет$</code> - точно 'привет'</blockquote>",
                        reply_markup=[
                            [{"text": "🔄 Попробовать снова", "input": "Введите текст триггера", "callback": self._input_trigger_inline}],
                            [{"text": "❌ Отмена", "callback": self._cancel_trigger_creation_inline}],
                        ]
                    )
                    return
        else:
            await call.edit(
                "<b>❌ Ошибка: формат не выбран</b>\n\n"
                "Пожалуйста, начните создание триггера заново.",
                reply_markup=[[{"text": "🔙 Назад", "callback": self._add_trigger_menu_inline}]]
            )
            return

        await self._create_trigger_from_state(call, ttype, trigger)

    async def _create_trigger_from_state(self, call, ttype, trigger):
        """Создание триггера из состояния с проверкой на дублирование и корректной обработкой всех типов медиафайлов"""
        user_id = call.from_user.id
        state = self.trigger_creation_state.get(user_id, {})

        trigger = self._normalize_trigger(ttype, trigger)

        reply_msg_id = state.get("reply_msg_id")
        source_chat_id = state.get("chat_id")

        try:
            reply = await self.client.get_messages(source_chat_id, ids=reply_msg_id)
            if not reply:
                await call.edit("<b>❌ Сообщение для ответа не найдено</b>")
                return
        except Exception:
            await call.edit("<b>❌ Ошибка получения сообщения</b>")
            return

        source_id = self.config["source_channel_id"]
        if not source_id:
            await call.edit("<b>❌ Канал не настроен</b>")
            return

        try:
            if len(self.triggers) >= 10:
                await call.edit(
                    "<b>❌ Достигнут лимит в 10 триггеров</b>\n\n"
                    "Удалите один или несколько триггеров, чтобы добавить новые.",
                    reply_markup=[[{"text": "📋 Управление триггерами", "callback": self._sptr_menu}]]
                )
                return

            scope = state.get('scope', 'everyone')
            chat_id = state.get('chat_id') if scope == 'here' else None
            
            if self._check_duplicate(ttype, trigger, scope, chat_id):
                await call.edit(
                    f"<b>❌ Дубликат триггера</b>\n\n"
                    f"Триггер <code>{utils.escape_html(trigger)}</code> с областью <code>{scope}</code> уже существует.",
                )
                return

            try:
                if reply.text and not reply.media:
                    content_msg = await self.client.send_message(source_id, reply.text, reply_to=reply.reply_to_msg_id)
                elif reply.media:
                    if reply.photo:
                        content_msg = await self.client.send_file(
                            source_id, 
                            reply.photo, 
                            caption=reply.text or "", 
                            reply_to=reply.reply_to_msg_id
                        )
                    elif reply.document:
                        content_msg = await self.client.send_file(
                            source_id, 
                            reply.document, 
                            caption=reply.text or "", 
                            reply_to=reply.reply_to_msg_id
                        )
                    elif reply.video:
                        content_msg = await self.client.send_file(
                            source_id, 
                            reply.video, 
                            caption=reply.text or "", 
                            reply_to=reply.reply_to_msg_id
                        )
                    elif reply.audio:
                        content_msg = await self.client.send_file(
                            source_id, 
                            reply.audio, 
                            caption=reply.text or "", 
                            reply_to=reply.reply_to_msg_id
                        )
                    elif reply.voice:
                        content_msg = await self.client.send_file(
                            source_id, 
                            reply.voice, 
                            caption=reply.text or "", 
                            reply_to=reply.reply_to_msg_id
                        )
                    elif reply.sticker:
                        content_msg = await self.client.send_file(
                            source_id, 
                            reply.sticker, 
                            reply_to=reply.reply_to_msg_id
                        )
                    elif reply.gif:
                        content_msg = await self.client.send_file(
                            source_id, 
                            reply.gif,
                            caption=reply.text or "",
                            reply_to=reply.reply_to_msg_id
                        )
                    else:
                        content_msg = await self.client.send_file(
                            source_id, 
                            reply.media, 
                            caption=reply.text or "", 
                            reply_to=reply.reply_to_msg_id
                        )
                else:
                    content_msg = await self.client.send_message(source_id, "[Пустое сообщение]", reply_to=reply.reply_to_msg_id)
                    
            except Exception as e:
                logger.error(f"Error sending media/content: {e}")
                try:
                    content_msg = await self.client.send_file(source_id, reply)
                except Exception as e2:
                    logger.error(f"Fallback send_file also failed: {e2}")
                    await call.edit(
                        "<b>❌ Ошибка отправки медиафайла</b>\n\n"
                        "Не удалось отправить медиафайл в исходный канал.",
                        reply_markup=[[{"text": "🔄 Попробовать снова", "callback": self._add_trigger_menu_inline}]]
                    )
                    return

            original_trigger = state.get("original_trigger", trigger)
            trigger_text = f"{ttype}::{trigger}"
            trigger_description = f"{trigger_text}\nОбласть: {state.get('scope', 'everyone')}"
            if state.get("scope") == "here" and state.get("chat_id"):
                trigger_description += f"\nЧат: {state.get('chat_id')}"

            trigger_msg = await self.client.send_message(source_id, trigger_description, reply_to=content_msg.id)

            trigger_key = f"{ttype}::{trigger}"
            self.trigger_message_ids[trigger_key] = trigger_msg.id

            is_added, _ = await self._add_trigger_safe(ttype, trigger, scope, [content_msg.id], chat_id, len(self.triggers))
            
            if not is_added:
                await call.edit(
                    f"<b>❌ Ошибка добавления триггера</b>\n\n"
                    f"Триггер уже существует или произошла ошибка.",
                    reply_markup=[[{"text": "🔄 Попробовать другой", "callback": self._add_trigger_menu_inline}]]
                )
                return

            channel_id_str = str(source_id).replace("-100", "")
            link = f"https://t.me/c/{channel_id_str}/{trigger_msg.id}"

            scope_names = {
                "everyone": "🌐 во всех чатах",
                "here": "🏠 в текущем чате",
                "me": "👤 только на ваши сообщения"
            }

            content_type = "Текст"
            if reply.photo:
                content_type = "📷 Фото"
            elif reply.video:
                content_type = "🎬 Видео"
            elif reply.audio:
                content_type = "🎵 Аудио"
            elif reply.voice:
                content_type = "🎤 Голосовое"
            elif reply.sticker:
                content_type = "😀 Стикер"
            elif reply.document:
                content_type = "📄 Документ"
            elif reply.gif:
                content_type = "🎞️ GIF"
            elif reply.media:
                content_type = "📎 Медиафайл"

            success_msg = (
                f"<b>✅ Триггер добавлен!</b>\n\n"
                f"<b>Триггер:</b> <code>{utils.escape_html(original_trigger)}</code>\n"
                f"<b>Область:</b> {scope_names.get(state.get('scope', 'everyone'), '🌐 во всех чатах')}\n"
                f"<b>Контент:</b> {content_type}\n\n"
                f"<a href='{link}'>Перейти к сообщению</a>\n\n"
                f"<i>Всего триггеров: {len(self.triggers)}/10</i>"
            )

            await call.edit(
                success_msg,
                reply_markup=[[{"text": "📋 Управление триггерами", "callback": self._sptr_menu}]],
            )

            if user_id in self.trigger_creation_state:
                del self.trigger_creation_state[user_id]

        except Exception as e:
            logger.exception("Failed to add trigger")
            await call.edit(
                "<b>❌ Ошибка добавления триггера</b>\n\n"
                f"<code>{utils.escape_html(str(e))}</code>",
                reply_markup=[[{"text": "❌ Отмена", "callback": self._cancel_trigger_creation_inline}]]
            )

    async def _cancel_trigger_creation_inline(self, call):
        """Отмена через inline"""
        user_id = call.from_user.id
        if user_id in self.trigger_creation_state:
            del self.trigger_creation_state[user_id]

        await call.edit(
            "<b>❌ Создание триггера отменено</b>",
            reply_markup=[[{"text": "🔙 К помощи", "callback": lambda c: self._show_help_menu_inline(c)}]]
        )

    async def _manage_triggers_menu_inline(self, call):
        """Меню управления через inline"""
        if not self.triggers:
            await call.edit(
                "<b>❌ Триггеры не найдены...</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "<b>Добавьте тригерры:</b>\n"
                "<blockquote>.addtrigger (ответом на сообщение)</blockquote>\n"
                "<b>Помощь:</b> .trhelp",
                reply_markup=[]
            )
            return

        triggers_text = f"{self.strings('triggers_list_title')}\n\n"

        buttons = []
        for i, (key, trigger_data) in enumerate(self.triggers.items()):
            scope = trigger_data.get("scope", "everyone")
            scope_emoji = {"everyone": "🌐", "here": "🏠", "me": "👤"}.get(scope, "❓")

            trigger_type, pattern = key.split("::", 1)
            type_emoji = {
                "exact": "🎯",
                "contains": "🔍",
                "exact_delete": "🎯❌",
                "regex": "🔤",
                "regex_delete": "🔤❌"
            }.get(trigger_type, "❓")

            triggers_text += f"{i+1}. {type_emoji} <code>{utils.escape_html(pattern)}</code> {scope_emoji}\n"

            buttons.append([{
                "text": f"☑️ {i+1}",
                "callback": lambda c, idx=i: self._toggle_trigger_selection_inline(c, idx)
            }])

        buttons.extend(self._get_action_buttons(True))

        await call.edit(triggers_text, reply_markup=buttons)

    async def _toggle_trigger_selection_inline(self, call, trigger_index):
        """Переключение выбора через inline"""
        user_id = call.from_user.id
        if user_id not in self.trigger_creation_state:
            self.trigger_creation_state[user_id] = {"selected_for_delete": set()}

        state = self.trigger_creation_state[user_id]
        if "selected_for_delete" not in state:
            state["selected_for_delete"] = set()

        if trigger_index in state["selected_for_delete"]:
            state["selected_for_delete"].remove(trigger_index)
        else:
            state["selected_for_delete"].add(trigger_index)

        await self._manage_triggers_menu_inline(call)

    async def _confirm_delete_selected_inline(self, call):
        """Подтверждение удаления через inline"""
        user_id = call.from_user.id
        if user_id not in self.trigger_creation_state:
            return

        state = self.trigger_creation_state[user_id]
        selected = state.get("selected_for_delete", set())

        if not selected:
            await call.answer("Выберите триггеры для удаления", show_alert=True)
            return

        selected_text = ""
        trigger_keys = list(self.triggers.keys())
        for idx in sorted(selected):
            if idx < len(trigger_keys):
                key = trigger_keys[idx]
                trigger_type, pattern = key.split("::", 1)
                selected_text += f"• <code>{utils.escape_html(pattern)}</code>\n"

        text = (
            "<b>⚠️ Подтверждение удаления</b>\n\n"
            "Выбранные триггеры будут удалены:\n\n"
            f"{selected_text}\n"
            f"<b>Количество: {len(selected)}</b>"
        )

        await call.edit(text, reply_markup=self._get_confirm_buttons(True))

    async def _execute_delete_selected_inline(self, call):
        """Выполнение удаления через inline"""
        user_id = call.from_user.id
        if user_id not in self.trigger_creation_state:
            return

        state = self.trigger_creation_state[user_id]
        selected = state.get("selected_for_delete", set())

        if not selected:
            return

        trigger_keys = list(self.triggers.keys())
        deleted_count = 0
        source_id = self.config["source_channel_id"]

        for idx in sorted(selected, reverse=True):
            if idx < len(trigger_keys):
                key = trigger_keys[idx]
                if source_id:
                    if key in self.trigger_message_ids:
                        try:
                            await self.client.delete_messages(source_id, self.trigger_message_ids[key])
                        except Exception:
                            pass
                        del self.trigger_message_ids[key]
                    
                    for msg_id in self.triggers[key]["msg_ids"]:
                        try:
                            await self.client.delete_messages(source_id, msg_id)
                        except Exception:
                            pass
                del self.triggers[key]
                deleted_count += 1

        self.db.set("SourceTrigger", "triggers", self.triggers)
        self.db.set("SourceTrigger", "trigger_message_ids", self.trigger_message_ids)
        del self.trigger_creation_state[user_id]

        await call.edit(
            f"<b>✅ Удалено {deleted_count} триггеров</b>",
            reply_markup=[[{"text": "🔙 К списку", "callback": self._manage_triggers_menu_inline}]]
        )

    async def _show_help_menu_inline(self, call):
        """Помощь через inline"""
        help_text = (
            "<b>📚 SourceTrigger Помощь</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "<b>Здесь показаны примеры</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔤 <b>Форматы триггеров:</b>\n"
            "• привет - Точное совпадение\n"
            "• привет , ка кдела? - Содержит текст\n"
            "• привет - Точное совпадение + удалить сообщение (после срабатывания тригера удалит само сообщение)\n"
            "• ~|шаблон - Regex совпадение\n"
            "• ~~~|шаблон - Regex совпадение + удалить сообщение (после срабатывания тригера удалит само сообщение)\n\n"
            "🎯 <b>Области действия триггеров:</b>\n"
            "• everyone - Работает во всех чатах (включая личные)\n"
            "• here - Только в текущем чате\n"
            "• me - Только на ваши сообщения\n\n"
            "📝 <b>Примеры использования:</b>\n"
            "• Ответ на медиа: .addtrigger\n"
            "• Ответ на медиа: .addtrigger привет\n"
            "• Ответ на медиа: .addtrigger ~привет"
        )

        await self._ui_edit_or_form(call, help_text, self._get_navigation_buttons(True))

    async def _manage_triggers_menu(self, call_or_message):
        """Меню управления триггерами - список с кнопками для удаления"""
        if not self.triggers:
            await self._ui_edit_or_form(
                call_or_message,
                "<b>❌ Триггеры не найдены...</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "<b>Добавьте тригерры:</b>\n"
                "<blockquote>.addtrigger (ответом на сообщение)</blockquote>\n"
                "<b>Помощь:</b> .trhelp",
                [],
            )
            return

        triggers_text = f"{self.strings('triggers_list_title')}\n\n"

        buttons = []
        for i, (key, trigger_data) in enumerate(self.triggers.items()):
            scope = trigger_data.get("scope", "everyone")
            scope_emoji = {"everyone": "🌐", "here": "🏠", "me": "👤"}.get(scope, "❓")

            trigger_type, pattern = key.split("::", 1)
            type_emoji = {
                "exact": "🎯",
                "contains": "🔍",
                "exact_delete": "🎯❌",
                "regex": "🔤",
                "regex_delete": "🔤❌"
            }.get(trigger_type, "❓")

            triggers_text += f"{i+1}. {type_emoji} <code>{utils.escape_html(pattern)}</code> {scope_emoji}\n"

            buttons.append([{
                "text": f"☑️ {i+1}",
                "callback": lambda c, idx=i: self._toggle_trigger_selection(c, idx)
            }])

        buttons.extend(self._get_action_buttons(False))

        await self._ui_edit_or_form(call_or_message, triggers_text, buttons)

    async def _toggle_trigger_selection(self, call, trigger_index):
        """Переключение выбора триггера для удаления"""
        user_id = call.from_user.id
        if user_id not in self.trigger_creation_state:
            self.trigger_creation_state[user_id] = {"selected_for_delete": set()}

        state = self.trigger_creation_state[user_id]
        if "selected_for_delete" not in state:
            state["selected_for_delete"] = set()

        if trigger_index in state["selected_for_delete"]:
            state["selected_for_delete"].remove(trigger_index)
        else:
            state["selected_for_delete"].add(trigger_index)

        await self._manage_triggers_menu(call)

    async def _confirm_delete_selected(self, call):
        """Подтверждение удаления выбранных триггеров"""
        user_id = call.from_user.id
        if user_id not in self.trigger_creation_state:
            return

        state = self.trigger_creation_state[user_id]
        selected = state.get("selected_for_delete", set())

        if not selected:
            await call.answer(self.strings("triggers_none_selected"), show_alert=True)
            return

        selected_text = ""
        trigger_keys = list(self.triggers.keys())
        for idx in sorted(selected):
            if idx < len(trigger_keys):
                key = trigger_keys[idx]
                trigger_type, pattern = key.split("::", 1)
                selected_text += f"• <code>{utils.escape_html(pattern)}</code>\n"

        text = (
            f"{self.strings('triggers_delete_confirm')}"
            f"{selected_text}\n"
            f"<b>Количество: {len(selected)}</b>"
        )

        await call.edit(text, reply_markup=self._get_confirm_buttons(False))

    async def _execute_delete_selected(self, call):
        """Выполнение удаления выбранных триггеров"""
        user_id = call.from_user.id
        if user_id not in self.trigger_creation_state:
            return

        state = self.trigger_creation_state[user_id]
        selected = state.get("selected_for_delete", set())

        if not selected:
            return

        trigger_keys = list(self.triggers.keys())
        deleted_count = 0
        source_id = self.config["source_channel_id"]

        for idx in sorted(selected, reverse=True):
            if idx < len(trigger_keys):
                key = trigger_keys[idx]
                if source_id:
                    if key in self.trigger_message_ids:
                        try:
                            await self.client.delete_messages(source_id, self.trigger_message_ids[key])
                        except Exception:
                            pass
                        del self.trigger_message_ids[key]
                    
                    for msg_id in self.triggers[key]["msg_ids"]:
                        try:
                            await self.client.delete_messages(source_id, msg_id)
                        except Exception:
                            pass

                del self.triggers[key]
                deleted_count += 1

        self.db.set("SourceTrigger", "triggers", self.triggers)
        self.db.set("SourceTrigger", "trigger_message_ids", self.trigger_message_ids)

        del self.trigger_creation_state[user_id]

        await call.edit(
            self.strings("triggers_deleted").format(deleted_count),
            reply_markup=[[{"text": "🔙 К списку", "callback": self._manage_triggers_menu}]]
        )

    async def _show_help_menu(self, call):
        """Показать меню помощи"""
        help_text = (
            f"{self.strings('help_title')}\n\n"
            f"{self.strings('help_description')}\n\n"
            f"{self.strings('help_formats_title')}"
            f"{self.strings('help_formats')}\n\n"
            f"{self.strings('help_commands_title')}"
            f"{self.strings('help_commands')}\n\n"
            f"{self.strings('help_scopes_title')}"
            f"{self.strings('help_scopes')}\n\n"
            f"{self.strings('help_examples_title')}"
            f"{self.strings('help_examples')}"
        )

        await self._ui_edit_or_form(call, help_text, self._get_navigation_buttons(False))

    async def _run_parser(self, message: Message = None):
        """Core logic for scanning the source channel and updating the trigger database.
        Runs silently if message is None."""
        
        if message:
            status_msg = await utils.answer(message, self.strings("parsing_started"))
        else:
            status_msg = None

        counts = {"exact": 0, "contains": 0, "exact_delete": 0, "regex": 0, "regex_delete": 0}
        source_id = self.config["source_channel_id"]
        if not source_id:
            if message:
                await utils.answer(status_msg, self.strings("channel_error") + "\n<code>Source channel ID not configured.</code>")
            return

        try:
            channel_entity = await self.client.get_entity(source_id)
            tasks = []
            processed_count = 0
            added_count = 0

            async for msg in self.client.iter_messages(channel_entity, limit=None):
                tasks.append(asyncio.create_task(self._process_message_for_triggers(msg)))
                processed_count += 1
                if len(tasks) >= self.BATCH_SIZE:
                    added_count, counts = await self._process_batch(tasks, self.triggers, counts, status_msg, processed_count, added_count)
                    tasks.clear()
                    
                if added_count >= 10:
                    break

            if tasks and added_count < 10:
                added_count, counts = await self._process_batch(tasks, self.triggers, counts, status_msg, processed_count, added_count)

            self.db.set("SourceTrigger", "triggers", self.triggers)
            self.db.set("SourceTrigger", "trigger_message_ids", self.trigger_message_ids)
            
            if status_msg:
                complete_msg = self.strings("parsing_complete").format(
                    counts["exact"], counts["contains"], counts["exact_delete"], counts["regex"], counts["regex_delete"]
                )
                
                if added_count >= 10:
                    complete_msg += "\n\n⚠️ <b>Достигнут лимит в 10 триггеров.</b>"
                    
                await utils.answer(status_msg, complete_msg)
            
        except Exception as e:
            logger.exception("Failed to parse triggers")
            if status_msg:
                await utils.answer(status_msg, self.strings("channel_error") + f"\n<code>{utils.escape_html(str(e))}</code>")


    @loader.command(ru_doc="Показать помощь и инструкции по использованию")
    async def trhelp(self, message: Message):
        """Show help and usage instructions."""
        await self._show_help_menu_inline(message)

    @loader.command(ru_doc="Обновить базу триггеров из канала")
    async def parsetriggers(self, message: Message):
        """Scans the source channel to update the trigger database."""
        await self._run_parser(message)

    @loader.command(ru_doc="Управление триггерами через инлайн-меню (выбор и удаление)")
    async def sptr(self, message: Message):
        """Manage triggers with inline menu (select and delete)."""
        await self._sptr_menu(message)

    def _parse_trigger_string(self, text: str, allow_plain_text: bool = True):
        """Parses a raw trigger string into ttype and trigger."""
        text = text.strip()
        ttype, trigger = None, None

        if allow_plain_text and not text.startswith("~"):
            ttype, trigger = "exact", text.lower()
            return ttype, trigger
        
        if text.startswith("~~~"):
            content_after = text[3:].lstrip()
            if content_after.startswith("|"):
                pattern = content_after[1:].strip()
                if pattern:
                    try:
                        re.compile(pattern, re.IGNORECASE)
                        ttype, trigger = "regex_delete", pattern
                    except re.error: return None, None
            else:
                ttype, trigger = "exact_delete", content_after.strip().lower()
        elif text.startswith("~~"):
            ttype, trigger = "contains", text[2:].strip().lower()
        elif text.startswith("~"):
            content_after = text[1:].lstrip()
            if content_after.startswith("|"):
                pattern = content_after[1:].strip()
                if pattern:
                    try:
                        re.compile(pattern, re.IGNORECASE)
                        ttype, trigger = "regex", pattern
                    except re.error: return None, None
            else:
                ttype, trigger = "exact", content_after.strip().lower()
        return ttype, trigger

    def _check_duplicate(self, ttype: str, trigger: str, scope: str, chat_id: Optional[int] = None) -> bool:
        """Проверяет, существует ли уже триггер с указанными параметрами."""
        trigger = self._normalize_trigger(ttype, trigger)
        key = f"{ttype}::{trigger}"
        if key in self.triggers:
            trigger_data = self.triggers[key]
            if trigger_data.get("scope") == scope:
                if scope == "here" and trigger_data.get("chat_id") == chat_id:
                    return True
                elif scope in ["everyone", "me"]:
                    return True
        return False

    async def _add_trigger_safe(self, ttype: str, trigger: str, scope: str, msg_ids: List[int], 
                                chat_id: Optional[int] = None, count: int = 0) -> Tuple[bool, int]:
        """
        Безопасно добавляет триггер с проверкой на дублирование и ограничениями.
        
        Returns:
            Tuple[bool, int]: (успех, количество добавленных триггеров)
        """
        if count >= 10:
            return False, count

        trigger = self._normalize_trigger(ttype, trigger)
        if self._check_duplicate(ttype, trigger, scope, chat_id):
            return False, count

        key = f"{ttype}::{trigger}"
        
        if key not in self.triggers:
            self.triggers[key] = {
                "msg_ids": [],
                "scope": scope,
                "chat_id": chat_id
            }

        added_count = 0
        for msg_id in msg_ids:
            if msg_id not in self.triggers[key]["msg_ids"]:
                self.triggers[key]["msg_ids"].append(msg_id)
                added_count += 1

        if added_count > 0:
            count += 1
            self.db.set("SourceTrigger", "triggers", self.triggers)
            self.db.set("SourceTrigger", "trigger_message_ids", self.trigger_message_ids)
            
        return added_count > 0, count

    def _initialize_trigger_state(self, user_id: int, reply: Message, message: Message, args: Optional[str] = None) -> Dict[str, Any]:
        """Инициализирует состояние создания триггера."""
        base_state = {
            "reply_msg_id": reply.id,
            "chat_id": message.chat_id
        }

        if not args:
            return {**base_state, "step": "format_selection"}

        if re.match(r"^~{1,3}", args):
            ttype, trigger = self._parse_trigger_string(args)
            if ttype and trigger:
                return {**base_state, "step": "scope_selection", "format": ttype, "trigger": trigger, "original_trigger": args}
            else:
                return {**base_state, "step": "format_selection", "manual_input": args}
        else:
            return {**base_state, "step": "format_selection", "manual_input": args}

    @loader.command(ru_doc="<ответ на сообщение> [триггер] - Добавить новый триггер")
    async def addtrigger(self, message: Message):
        """<reply to message> [trigger] - Add a new trigger"""
        reply = await message.get_reply_message()
        if not reply:
            await utils.answer(message, self.strings("must_be_reply"))
            return

        user_id = message.sender_id
        args = utils.get_args_raw(message)

        state = self._initialize_trigger_state(user_id, reply, message, args)
        self.trigger_creation_state[user_id] = state

        if state["step"] == "scope_selection":
            await self._select_trigger_scope_inline_from_command(message)
        else:
            await self._add_trigger_menu_inline(message)

    async def _sptr_menu(self, message):
        """Меню управления триггерами"""
        target = message

        if not self.triggers:
            await self._ui_edit_or_form(
                target,
                "<b>❌ Триггеры не найдены...</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "<b>Добавьте тригерры:</b>\n"
                "<blockquote>.addtrigger (ответом на сообщение)</blockquote>\n"
                "<b>Помощь:</b> .trhelp",
                [],
            )
            return

        text = "<b>📋 Управление триггерами</b>\n━━━━━━━━━━━━━━━━━━━━\n"

        for i, (key, trigger_data) in enumerate(self.triggers.items(), 1):
            scope = trigger_data.get("scope", "everyone")
            scope_emoji = {"everyone": "🌐", "here": "🏠", "me": "👤"}.get(scope, "❓")

            trigger_type, pattern = key.split("::", 1)
            type_emoji = {
                "exact": "🎯",
                "contains": "🔍",
                "exact_delete": "🎯❌",
                "regex": "🔤",
                "regex_delete": "🔤❌"
            }.get(trigger_type, "❓")

            text += f"{i}. <code>{utils.escape_html(pattern)}</code> ➜ {type_emoji} | {scope_emoji}\n"

        text += "━━━━━━━━━━━━━━━━━━━━\n<b>Выберите действие</b>"

        reply_markup = [
            [{"text": "🗑 Удалить триггер", "callback": self._delete_trigger_menu}],
            [{"text": "❌ Закрыть", "callback": self._close_sptr_menu}],
        ]

        await self._ui_edit_or_form(target, text, reply_markup)

    async def _delete_trigger_menu(self, call):
        """Меню выбора триггеров для удаления"""
        user_id = str(call.from_user.id)
        if user_id not in self._multi_select:
            self._multi_select[user_id] = set()

        selected = self._multi_select[user_id]
        text = "<b>🗑️ Удаление тригера</b>\n━━━━━━━━━━━━━━━━━━━━\n<blockquote>Когда вы выберите триггер он подсветится \"🟢\"\nпосле чего нажмите кнопку удалить , так же можно удалять несколько тригеров</blockquote>━━━━━━━━━━━━━━━━━━━━\n<b>Выберите тригер</b>\n\n"

        reply_markup = []
        for i, key in enumerate(self.triggers.keys(), 1):
            trigger_type, pattern = key.split("::", 1)
            type_emoji = {
                "exact": "🎯",
                "contains": "🔍",
                "exact_delete": "🎯❌",
                "regex": "🔤",
                "regex_delete": "🔤❌"
            }.get(trigger_type, "❓")
            
            prefix = "🟢 " if i in selected else ""
            text += f"{prefix}{i}. <code>{utils.escape_html(pattern)}</code> {type_emoji}\n"

            reply_markup.append([{
                "text": f"{prefix}{i}",
                "callback": self._toggle_trigger_deletion,
                "args": (i,),
            }])

        if selected:
            reply_markup.append([
                {"text": f"🗑️ Удалить ({len(selected)})", "callback": self._execute_delete_triggers},
            ])
        
        reply_markup.append([
            {"text": "⬅️ Назад", "callback": self._sptr_menu},
        ])

        await call.edit(text, reply_markup=reply_markup)

    async def _toggle_trigger_deletion(self, call, trigger_index):
        """Переключение выбора триггера для удаления"""
        user_id = str(call.from_user.id)
        selected = self._multi_select.get(user_id, set())
        if trigger_index in selected:
            selected.remove(trigger_index)
        else:
            selected.add(trigger_index)
        self._multi_select[user_id] = selected
        await self._delete_trigger_menu(call)

    async def _execute_delete_triggers(self, call):
        """Выполнение удаления выбранных триггеров"""
        user_id = str(call.from_user.id)
        selected = self._multi_select.get(user_id, set())
        if not selected:
            await call.answer("Выберите хотя бы один триггер!", show_alert=True)
            return

        trigger_keys = list(self.triggers.keys())
        
        deleted_count = 0
        source_id = self.config["source_channel_id"]
        
        for idx in sorted(selected, reverse=True):
            if idx - 1 < len(trigger_keys):
                key = trigger_keys[idx - 1]
                if source_id:
                    if key in self.trigger_message_ids:
                        try:
                            await self.client.delete_messages(source_id, self.trigger_message_ids[key])
                        except Exception:
                            pass
                        del self.trigger_message_ids[key]
                    
                    for msg_id in self.triggers[key]["msg_ids"]:
                        try:
                            await self.client.delete_messages(source_id, msg_id)
                        except Exception:
                            pass
                
                del self.triggers[key]
                deleted_count += 1
        
        self.db.set("SourceTrigger", "triggers", self.triggers)
        self.db.set("SourceTrigger", "trigger_message_ids", self.trigger_message_ids)
        
        if user_id in self._multi_select:
            del self._multi_select[user_id]

        if not self.triggers:
            await call.delete()
            return

        await call.edit(
            text=f"<b>✅ Удалено {deleted_count} триггеров</b>",
            reply_markup=[[{"text": "🔙 К списку триггеров", "callback": self._sptr_menu}]],
        )

    async def _close_sptr_menu(self, call):
        """Закрыть меню управления триггерами"""
        await call.delete()
        
        user_id = str(call.from_user.id)
        if user_id in self._multi_select:
            del self._multi_select[user_id]

    @loader.watcher(chats=_get_source_channel, only_messages=True)
    async def source_channel_watcher(self, message: Message):
        """Watches the source channel for new posts and updates triggers automatically."""
        result = await self._process_message_for_triggers(message)
        if not result: return

        if len(self.triggers) >= 10:
            return

        ttype, trigger, msg_id = result
        
        if self._check_duplicate(ttype, trigger, "everyone", None):
            return
            
        is_added, _ = await self._add_trigger_safe(ttype, trigger, "everyone", [msg_id], None, len(self.triggers))
        
        if not is_added:
            return

    async def _process_and_send(self, trigger_message: Message, msg_id: int):
        """Helper to fetch, prepare, and send a single response message."""
        source_id = self.config["source_channel_id"]

        try:
            source_msg = await self.client.get_messages(source_id, ids=msg_id)
            if not source_msg: return

            caption = source_msg.text or ""
            if caption:
                first_line = caption.split('\n', 1)[0].strip()
                if re.match(r"^~{1,3}", first_line):
                    lines = caption.split('\n')
                    caption = '\n'.join(lines[1:]).strip()

            reply_to_id = trigger_message.reply_to_msg_id if trigger_message.is_reply else None
            
            if source_msg.media:
                await self.client.send_file(
                    trigger_message.peer_id,
                    source_msg, 
                    caption=caption or None,
                    reply_to=reply_to_id
                )
            elif caption:
                await utils.answer(trigger_message, caption, reply_to=reply_to_id)
            
        except Exception as e:
            logger.error(f"Error sending trigger response for msg_id {msg_id}: {e}")
            pass

    @loader.watcher(no_commands=True)
    async def watcher(self, message: Message):
        """Watches for outgoing messages and responds with media if a trigger is found."""
        if not getattr(message, "text", None):
            return

        allow_incoming = bool(self.config.get("allow_incoming"))
        if not allow_incoming:
            if not getattr(message, "out", False):
                return

        text = message.raw_text
        low_text_stripped = text.strip().lower()
        
        matched_key = None
        
        for key in self.triggers:
            if key.startswith("regex_delete::"):
                pattern = key.split("::", 1)[1]
                try:
                    if re.fullmatch(pattern, text, re.IGNORECASE):
                        matched_key = key
                        break
                except re.error: continue
        
        if not matched_key:
            exact_delete_key = f"exact_delete::{low_text_stripped}"
            if exact_delete_key in self.triggers:
                matched_key = exact_delete_key

        if not matched_key:
            for key in self.triggers:
                if key.startswith("regex::"):
                    pattern = key.split("::", 1)[1]
                    try:
                        if re.fullmatch(pattern, text, re.IGNORECASE):
                            matched_key = key
                            break
                    except re.error: continue

        if not matched_key:
            exact_key = f"exact::{low_text_stripped}"
            if exact_key in self.triggers:
                matched_key = exact_key
        
        if not matched_key:
            for key in self.triggers:
                if key.startswith("contains::"):
                    trigger_text = key.split("::", 1)[1]
                    if trigger_text in text.lower():
                        matched_key = key
                        break
        
        if matched_key:
            trigger_data = self.triggers[matched_key]
            msg_ids = trigger_data["msg_ids"]
            scope = trigger_data["scope"]
            chat_id = trigger_data["chat_id"]

            if not msg_ids: return

            if scope == "here" and chat_id is not None and message.chat_id != chat_id:
                return
            elif scope == "me" and not message.out:
                return

            should_delete = "delete" in matched_key.split("::", 1)[0]

            tasks = [self._process_and_send(message, msg_id) for msg_id in msg_ids]
            await asyncio.gather(*tasks)

            if should_delete and message.out:
                await message.delete()

