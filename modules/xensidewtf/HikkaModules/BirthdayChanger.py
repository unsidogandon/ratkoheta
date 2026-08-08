import asyncio
from datetime import datetime, timedelta, timezone

from telethon.tl.functions.account import UpdateBirthdayRequest
from telethon.tl.types import Birthday

from .. import loader, utils

#░█░█░█▀▀░█▀█░█▀▀░▀█▀░█▀▄░█▀▀
#░▄▀▄░█▀▀░█░█░▀▀█░░█░░█░█░█▀▀
#░▀░▀░▀▀▀░▀░▀░▀▀▀░▀▀▀░▀▀░░▀▀▀

# 🔒 Licensed under All Rights Reserved.
# meta developer: @XenSideMOD

@loader.tds
class BirthdayChangerMod(loader.Module):
    """Автоматически меняет дату рождения, чтобы вам всегда был заданный возраст."""

    strings = {
        "name": "BirthdayChanger",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "enabled",
                False,
                "Включить/выключить автоматическое изменение возраста",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "age",
                69,
                "Возраст, который будет поддерживаться (от 1 до 146)",
                validator=loader.validators.Integer(minimum=1, maximum=146),
            ),
        )
        self.moscow_tz = timezone(timedelta(hours=3))
        self.task = None

    async def client_ready(self, client, db):
        self._client = client
        if self.config["enabled"]:
            self.task = asyncio.create_task(self._birthday_loop())

    async def _update_birthday(self, target_date=None):
        if target_date is None:
            target_date = datetime.now(self.moscow_tz).date()

        birth_year = target_date.year - self.config["age"]
        birthday = Birthday(day=target_date.day, month=target_date.month, year=birth_year)
        try:
            await self._client(UpdateBirthdayRequest(birthday=birthday))
        except Exception:
            pass
            
    def _get_next_midnight(self):
        now_msk = datetime.now(self.moscow_tz)
        tomorrow_msk = (now_msk + timedelta(days=1)).date()
        return datetime.combine(tomorrow_msk, datetime.min.time(), tzinfo=self.moscow_tz)

    async def _birthday_loop(self):
        await self._update_birthday()
        while True:
            now_msk = datetime.now(self.moscow_tz)
            next_midnight = self._get_next_midnight()
            
            update_time = next_midnight - timedelta(minutes=1)

            if update_time < now_msk:
               next_midnight += timedelta(days=1)
               update_time = next_midnight - timedelta(minutes=1)

            sleep_seconds = (update_time - now_msk).total_seconds()
            await asyncio.sleep(sleep_seconds)
            
            await self._update_birthday(target_date=next_midnight.date())
            
            await asyncio.sleep(61)

    def _get_remaining_time_str(self):
        now_msk = datetime.now(self.moscow_tz)
        next_midnight = self._get_next_midnight()
        update_time = next_midnight - timedelta(minutes=1)

        if update_time < now_msk:
            next_midnight += timedelta(days=1)
            update_time = next_midnight - timedelta(minutes=1)

        remaining = update_time - now_msk
        
        hours, remainder = divmod(remaining.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    async def bcstartcmd(self, message):
        """<возраст> - Включает/перезапускает цикл с указанным возрастом."""
        args = utils.get_args_raw(message)
        new_age_set = False
        
        if args:
            try:
                new_age = int(args)
                if not 0 < new_age < 147:
                    raise ValueError
                
                if new_age != self.config["age"]:
                    self.config["age"] = new_age
                    new_age_set = True
                
            except ValueError:
                await utils.answer(message, "<blockquote><emoji document_id=5278578973595427038>🚫</emoji> <b>Неверный возраст.</b> Укажите число от 1 до 146.</blockquote>")
                return

        is_running = self.task and not self.task.done()
        
        if is_running and not new_age_set:
            await utils.answer(message, self._status_message())
            return
            
        if is_running:
            self.task.cancel()
        
        await self._update_birthday()
        
        self.config["enabled"] = True
        self.task = asyncio.create_task(self._birthday_loop())
        
        await utils.answer(message, self._status_message(started=True))

    def _status_message(self, started=False):
        time_str = self._get_remaining_time_str()
        
        if started:
            header = "<emoji document_id=5278753302023004775>ℹ️</emoji> <b>Цикл запущен успешно.</b>"
            age_line = f"<emoji document_id=5206476089127372379>⭐️</emoji> <b>Установлен возраст:</b> <code>{self.config['age']}</code>"
        else:
            header = "<emoji document_id=5278753302023004775>ℹ️</emoji> <b>Цикл уже запущен.</b>"
            age_line = f"<emoji document_id=5206476089127372379>⭐️</emoji> <b>Текущий возраст:</b> <code>{self.config['age']}</code>"
            
        return (
            f"<blockquote>{header}\n"
            f"{age_line}\n"
            f"<emoji document_id=5276412364458059956>🕓</emoji> <b>До следующего изменения осталось:</b> <code>{time_str}</code></blockquote>"
        )

    async def bcstopcmd(self, message):
        """Останавливает цикл обновления дня рождения."""
        if not self.task or self.task.done():
            await utils.answer(message, "<blockquote><emoji document_id=5278753302023004775>ℹ️</emoji> <b>Цикл обновления и так не был запущен.</b></blockquote>")
            return

        self.config["enabled"] = False
        self.task.cancel()
        self.task = None
        await utils.answer(message, "<blockquote><emoji document_id=5278753302023004775>ℹ️</emoji> <b>Цикл обновления дня рождения остановлен.</b></blockquote>")
