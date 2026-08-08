# meta developer: @coddan
from .. import loader, utils


@loader.tds
class ScheduleMod(loader.Module):
    """
    Module for sending schedule and bells.
    Fully configurable via .config ScheduleMod
    """

    strings = {"name": "ScheduleMod"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "monday",
                "Расписание не настроено",
                "Расписание на понедельник",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "tuesday",
                "Расписание не настроено",
                "Расписание на вторник",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "wednesday",
                "Расписание не настроено",
                "Расписание на среду",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "thursday",
                "Расписание не настроено",
                "Расписание на четверг",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "friday",
                "Расписание не настроено",
                "Расписание на пятницу",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "saturday",
                "Расписание не настроено",
                "Расписание на субботу",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "sunday",
                "Выходной",
                "Расписание на воскресенье",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "bells",
                "Расписание звонков не настроено",
                "Расписание звонков",
                validator=loader.validators.String(),
            ),
        )

    @loader.command(ru_doc="Показать расписание на понедельник")
    async def понедельникcmd(self, message):
        """Show schedule for Monday"""
        text = f"<b>🗓 Понедельник:</b>\n\n{self.config['monday']}"
        await utils.answer(message, text)

    @loader.command(ru_doc="Показать расписание на вторник")
    async def вторникcmd(self, message):
        """Show schedule for Tuesday"""
        text = f"<b>🗓 Вторник:</b>\n\n{self.config['tuesday']}"
        await utils.answer(message, text)

    @loader.command(ru_doc="Показать расписание на среду")
    async def средаcmd(self, message):
        """Show schedule for Wednesday"""
        text = f"<b>🗓 Среда:</b>\n\n{self.config['wednesday']}"
        await utils.answer(message, text)

    @loader.command(ru_doc="Показать расписание на четверг")
    async def четвергcmd(self, message):
        """Show schedule for Thursday"""
        text = f"<b>🗓 Четверг:</b>\n\n{self.config['thursday']}"
        await utils.answer(message, text)

    @loader.command(ru_doc="Показать расписание на пятницу")
    async def пятницаcmd(self, message):
        """Show schedule for Friday"""
        text = f"<b>🗓 Пятница:</b>\n\n{self.config['friday']}"
        await utils.answer(message, text)

    @loader.command(ru_doc="Показать расписание на субботу")
    async def субботаcmd(self, message):
        """Show schedule for Saturday"""
        text = f"<b>🗓 Суббота:</b>\n\n{self.config['saturday']}"
        await utils.answer(message, text)

    @loader.command(ru_doc="Показать расписание на воскресенье")
    async def воскресеньеcmd(self, message):
        """Show schedule for Sunday"""
        text = f"<b>🗓 Воскресенье:</b>\n\n{self.config['sunday']}"
        await utils.answer(message, text)

    @loader.command(ru_doc="Показать расписание звонков")
    async def звонкиcmd(self, message):
        """Show bells schedule"""
        text = f"<b>🔔 Звонки:</b>\n\n{self.config['bells']}"
        await utils.answer(message, text)