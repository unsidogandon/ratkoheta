#                © Copyright 2025
#            ✈ https://t.me/json1c_modules
# 🆓 Released into the public domain under The Unlicense.
#
# This is free and unencumbered software released into the public domain.
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, for any purpose, commercial or non-commercial.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

# meta developer: @json1c_modules

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

from telethon.errors import (FloodWaitError, UsernameInvalidError,
                             UsernameNotOccupiedError)

from .. import loader, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


@loader.tds
class DevMontiroingMod(loader.Module):
    strings_ru = {
        "name": "DevMonitoring",
        "form_addmon": """<b>Мониторинг бота</b>

<b>🤖 Бот:</b> <code>{bot}</code>
<b>⏳ Интервал проверки:</b> <code>{interval} с.</code>
<b>⚙️ Команда:</b> <code>{command}</code>""",
        "form_bot_menu": """<b> Бот {bot}</b>

<b>⏳ Интервал:</b> <code>{interval} с.</code>
<b>⚙️ Команда:</b> <code>{command}</code>

<b>🕔 Последняя проверка:</b> <code>{last_check}</code>
<b>🔄 Статус:</b> <code>{status}</code>""",
        "status_bot_down": "Лежит",
        "status_bot_alive": "Живой",
        "status_not_checked": "Еще не проверялся",
        "action_started_monitoring": """<b>✅ Мониторинг бота запущен</b>

<b>🤖 Бот:</b> <code>{bot}</code>
<b>⏳ Интервал проверки:</b> <code>{interval} с.</code>
<b>⚙️ Команда:</b> <code>{command}</code>""",
        "action_bot_deleted": "<b>✅ Бот {bot} успешно снят с мониторинга</b>",
        "value_not_specified": "[укажите значение]",
        "enter_value": "✍️ Введите новое значение для этой опции",
        "msg_listmon": "Список ботов, подключенных к мониторингу",
        "msg_module_disabled": "<b>Модуль выключен.</b>",
        "msg_module_enabled": "<b>Модуль включен</b>",
        "btn_enter_bot": "🤖 Бот",
        "btn_enter_command": "⚙️ Команда",
        "btn_enter_interval": "⏳ Интервал",
        "btn_confirm": "✅ Запустить мониторинг",
        "btn_remove_bot": "🚫 Удалить бота с мониторинга",
        "err_empty": "🚫 Одно из значений пустое",
        "err_bot_exists": "<b>🚫 Бот {bot} уже находится на мониторинге</b>",
        "err_username_invalid": "<b>🚫 Юзернейма {username} не существует</b>",
        "err_resolving_username": "<b>🚫 Произошла ошибка при резолвинге юзернейма</b>\n\n{err}",
        "service_bot_deleted": "🚫 Бот {username} удален из мониторинга. Причина: бота с таким юзернеймом не существует",
        "service_bot_down": "🚫 Бот {username} лежит! (не ответил в течение {inverval} + 10 секунд)"
    }

    strings_en = {
        "name": "DevMonitoring",
        "form_addmon": """<b>Bot monitoring</b>

<b>🤖 Bot:</b> <code>{bot}</code>
<b>⏳ Interval:</b> <code>{interval} seconds</code>
<b>⚙️ Command:</b> <code>{command}</code>""",
        "form_bot_menu": """<b> Bot {bot}</b>

<b>⏳ Interval:</b> <code>{interval} seconds</code>
<b>⚙️ Command:</b> <code>{command}</code>

<b>🕔 Last check:</b> <code>{last_check}</code>
<b>🔄 Status:</b> <code>{status}</code>""",
        "action_started_monitoring": """<b>✅ Bot monitoring is started</b>

<b>🤖 Bot:</b> <code>{bot}</code>
<b>⏳ Interval:</b> <code>{interval} seconds</code>
<b>⚙️ Command:</b> <code>{command}</code>""",
        "status_bot_down": "Down",
        "status_bot_alive": "Alive",
        "status_not_checked": "Not checked",
        "action_bot_deleted": "<b>✅ Bot {bot} successfully deleted from monitoring list</b>",
        "value_not_specified": "[enter a value]",
        "enter_value": "✍️ Enter a new value for this option",
        "msg_listmon": "Bots in monitoring list",
        "msg_module_disabled": "<b>Module disabled.</b>",
        "msg_module_enabled": "<b>Module enabled</b>",
        "btn_enter_bot": "🤖 Bot",
        "btn_enter_command": "⚙️ Command",
        "btn_enter_interval": "⏳ Interval",
        "btn_confirm": "✅ Start monitoring",
        "btn_remove_bot": "🚫 Remove bot from monitoring",
        "err_empty": "🚫 One of the values is empty or invalid",
        "err_bot_exists": "<b>🚫 Bot {bot} already exists in monitoring list</b>",
        "err_username_invalid": "<b>🚫 Username {username} is invalid</b>",
        "err_resolving_username": "<b>🚫 An unknown error occurred while resolving username</b>\n\n{err}",
        "service_bot_deleted": "🚫 Bot {username} deleted from the monitoring list. Reason: invalid username",
        "service_bot_down": "🚫 Bot {username} is down! (the bot did not respond within {interval} + 10 seconds)"
    }

    async def client_ready(self):
        self.bots: list = self.pointer("bots", [])
        
        if self.get("enabled") is None:
            self.set("enabled", True)
    
    async def get_bot_entity(self, bot_username: str):
        bot_username = bot_username.replace("@", "").replace("https://t.me/", "").lower()
        
        try:
            entity = await self.client.get_entity(bot_username)
        except FloodWaitError:
            async for d in self.client.iter_dialogs():
                if getattr(d.entity, "username", None) is not None:
                    if d.entity.username.lower() == bot_username:
                        entity = d.entity
                        break
        
        return entity
    
    def update_bot(self, bot_username: str, key: str, value: Any):
        for bot_obj in self.bots:
            if bot_obj["bot"] == bot_username:
                bot_obj[key] = value
    
    async def remove_bot(self, call: InlineCall, bot_username: str):
        for bot_obj in self.bots:
            if bot_obj["bot"] == bot_username:
                self.bots.remove(bot_obj)
                break
        
        await call.edit(
            text=self.strings("action_bot_deleted").format(
                bot=bot_username
            )
        )

    async def confirm(self, call: InlineCall, args: dict):
        if None in args.values():
            return await call.answer(
                self.strings("err_empty"),
                show_alert=True
            )
        
        for bot_obj in self.bots:
            if bot_obj["bot"] == args["bot"]:
                return await call.edit(
                    text=self.strings("err_bot_exists").format(
                        bot=args["bot"]
                    )
                )

        await call.edit(
            text=self.strings("action_started_monitoring").format(
                bot=args.get("bot"),
                interval=args.get("interval"),
                command=args.get("command")
            ),
            reply_markup={
                "text": self.strings("btn_remove_bot"),
                "callback": self.remove_bot,
                "args": [args["bot"]]
            }
        )

        self.bots.append(args)

    async def update_value(self, call: InlineCall, option: str, param: str, args: dict):
        args[param] = option
        
        if param == "interval":
            if not option.isdigit():
                args[param] = 60
            else:
                args[param] = int(option)
        
        if param == "bot":
            try:
                entity = await self.get_bot_entity(option)
            except (UsernameInvalidError, UsernameNotOccupiedError):
                return await call.edit(
                    text=self.strings("err_username_invalid").format(
                        username=option
                    )
                )
            except Exception as error:
                return await call.edit(
                    text=self.strings("err_resolving_username").format(
                        err=error
                    )
                )
            else:
                option = "@" + entity.username
                args[param] = option

        await call.edit(
            text=self.strings("form_addmon").format(
                bot=args.get("bot") or self.strings("value_not_specified"),
                interval=args.get("interval") or self.strings("value_not_specified"),
                command=args.get("command") or self.strings("value_not_specified")
            ),
            disable_security=True,
            reply_markup=[
                [
                    {
                        "text": self.strings("btn_enter_bot"),
                        "input": self.strings("enter_value"),
                        "handler": self.update_value,
                        "kwargs": {"args": args, "param": "bot"}
                    }
                ],
                [
                    {
                        "text": self.strings("btn_enter_interval"),
                        "input": self.strings("enter_value"),
                        "handler": self.update_value,
                        "kwargs": {"args": args, "param": "interval"}
                    },
                    {
                        "text": self.strings("btn_enter_command"),
                        "input": self.strings("enter_value"),
                        "handler": self.update_value,
                        "kwargs": {"args": args, "param": "command"}
                    }
                ],
                [
                    {
                        "text": self.strings("btn_confirm"),
                        "callback": self.confirm,
                        "args": [args]
                    }
                ]
            ]
        )

    async def bot_menu(self, call: InlineCall, bot_obj: dict):
        statuses = {
            None: self.strings("status_bot_not_checked"),
            True: self.strings("status_bot_alive"),
            False: self.strings("status_bot_down")
        }
        
        status = statuses[bot_obj.get("alive")]
        last_check = "Not checked"
        
        if bot_obj.get("last_check") is not None:
            last_check = datetime.fromtimestamp(bot_obj["last_check"]).strftime("%d.%m %H:%M")
        
        await call.edit(
            text=self.strings("form_bot_menu").format(
                interval=bot_obj["interval"],
                command=bot_obj["command"],
                bot=bot_obj["bot"],
                last_check=last_check,
                status=status
            ),
            reply_markup={
                "text": self.strings("btn_remove_bot"),
                "callback": self.remove_bot,
                "args": [bot_obj["bot"]]
            }
        )

    @loader.command(
        ru_doc="Поставить бота на мониторинг",
        en_doc="Add bot to monitoring"
    )
    async def addmon(self, message):
        args = {
            "bot": None,
            "interval": 60,
            "command": "/start"
        }

        await self.inline.form(
            text=self.strings("form_addmon").format(
                bot=args.get("bot") or self.strings("value_not_specified"),
                interval=args.get("interval") or self.strings("value_not_specified"),
                command=args.get("command") or self.strings("value_not_specified")
            ),
            message=message,
            disable_security=True,
            reply_markup=[
                [
                    {
                        "text": self.strings("btn_enter_bot"),
                        "input": self.strings("enter_value"),
                        "handler": self.update_value,
                        "kwargs": {"args": args, "param": "bot"}
                    }
                ],
                [
                    {
                        "text": self.strings("btn_enter_interval"),
                        "input": self.strings("enter_value"),
                        "handler": self.update_value,
                        "kwargs": {"args": args, "param": "interval"}
                    },
                    {
                        "text": self.strings("btn_enter_command"),
                        "input": self.strings("enter_value"),
                        "handler": self.update_value,
                        "kwargs": {"args": args, "param": "command"}
                    }
                ],
                [
                    {
                        "text": self.strings("btn_confirm"),
                        "callback": self.confirm,
                        "args": [args]
                    }
                ]
            ]
        )

    @loader.command(
        ru_doc="Выключить/включить модуль",
        en_doc="Disable/enable module"
    )
    async def togglemon(self, message):
        enabled = self.get("enabled")
        enabled = not enabled
        self.set("enabled", enabled)
        
        if enabled:
            await utils.answer(
                message=message,
                response=self.strings("msg_module_enabled")
            )
        
        else:
            await utils.answer(
                message=message,
                response=self.strings("msg_module_disabled")
            )
    
    @loader.command(
        ru_doc="Управление ботами",
        en_doc="Manage bots"
    )
    async def listmon(self, message):
        reply_markup = []
        
        statuses = {
            None: "⚪️",
            True: "🟢",
            False: "🔴"
        }
        
        for bot_obj in self.bots:
            status = statuses[bot_obj.get("alive")]
            bot = bot_obj["bot"]
            last_check = ""
            
            if bot_obj.get("last_check") is not None:
                last_check = datetime.fromtimestamp(bot_obj["last_check"]).strftime("%d.%m %H:%M")
            
            reply_markup.append([
                {
                    "text": f"{status} {last_check} {bot}",
                    "args": [bot_obj],
                    "callback": self.bot_menu
                }
            ])
        
        await self.inline.form(
            text=self.strings("msg_listmon"),
            message=message,
            reply_markup=reply_markup
        )
    
    async def _check_bot_conv(self, bot_obj):        
        async with self.client.conversation(bot_obj["bot"]) as conv:
            message = await conv.send_message(bot_obj["command"])
            
            try:
                response = await conv.get_response(timeout=10)
            except asyncio.TimeoutError:
                await self.inline.bot.send_message(
                    self.tg_id,
                    self.strings("service_bot_down").format(
                        username=bot_obj["bot"],
                        interval=bot_obj["interval"]
                    )
                )
                
                self.update_bot(bot_obj["bot"], "alive", False)
            else:
                await conv.mark_read()
                await message.delete()
                await response.delete()
                
                self.update_bot(bot_obj["bot"], "alive", True)
            
            self.update_bot(bot_obj["bot"], "last_check", time.time())
    
    async def _check_interval(self, bot_obj):
        if not time.time() > bot_obj.get("last_check", 0) + bot_obj.get("interval"):
            return

        try:
            await self._check_bot_conv(bot_obj)
        except (UsernameInvalidError, UsernameNotOccupiedError):
            await self.inline.bot.send_message(
                self.tg_id,
                self.strings("service_bot_deleted").format(
                    username=bot_obj["bot"]
                )
            )

            self.bots.remove(bot_obj)

    @loader.loop(interval=1, autostart=True)
    async def check_bots(self):
        if not self.get("enabled"):
            return

        await asyncio.gather(*[
            self._check_interval(bot_obj)
            for bot_obj in self.bots
        ])