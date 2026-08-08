# meta developer: @coddan
from .. import loader, utils

@loader.tds
class MySocialsMod(loader.Module):
    """Module for quickly sharing your social networks and managing them"""
    
    strings = {
        "name": "MySocials",
        "no_socials": "<b>❌ You haven't added any social networks yet.</b>\n<i>Use </i><code>.addsoc &lt;name&gt; | &lt;link&gt;</code><i> to add one.</i>",
        "added": "<b>✅ Social network </b><code>{}</code><b> successfully added!</b>",
        "removed": "<b>✅ Social network </b><code>{}</code><b> successfully removed!</b>",
        "not_found": "<b>❌ Social network </b><code>{}</code><b> not found.</b>",
        "invalid_format": "<b>❌ Invalid format. Use:</b> <code>.addsoc &lt;name&gt; | &lt;link&gt;</code>",
        "socials_en": "🌐 <b>My Social Networks:</b>",
        "socials_ru": "🌐 <b>Мои социальные сети:</b>"
    }

    strings_ru = {
        "no_socials": "<b>❌ Вы еще не добавили ни одной соцсети.</b>\n<i>Используйте </i><code>.addsoc &lt;название&gt; | &lt;ссылка&gt;</code><i> для добавления.</i>",
        "added": "<b>✅ Соцсеть </b><code>{}</code><b> успешно добавлена!</b>",
        "removed": "<b>✅ Соцсеть </b><code>{}</code><b> успешно удалена!</b>",
        "not_found": "<b>❌ Соцсеть </b><code>{}</code><b> не найдена.</b>",
        "invalid_format": "<b>❌ Неверный формат. Используйте:</b> <code>.addsoc &lt;название&gt; | &lt;ссылка&gt;</code>"
    }

    async def client_ready(self, client, db):
        self.db = db

    def _get_socials(self):
        return self.db.get(self.strings("name"), "socials", {})

    def _set_socials(self, socials):
        self.db.set(self.strings("name"), "socials", socials)

    @loader.command(ru_doc="<название> | <ссылка> - Добавить соцсеть")
    async def addsoc(self, message):
        """<name> | <link> - Add a social network"""
        args = utils.get_args_raw(message)
        if "|" not in args:
            await utils.answer(message, self.strings("invalid_format"))
            return
        
        name, link = [x.strip() for x in args.split("|", 1)]
        if not name or not link:
            await utils.answer(message, self.strings("invalid_format"))
            return
            
        if not link.startswith(("http://", "https://", "tg://", "mailto:")):
            link = "https://" + link
            
        socials = self._get_socials()
        socials[name] = link
        self._set_socials(socials)
        
        await utils.answer(message, self.strings("added").format(name))

    @loader.command(ru_doc="<название> - Удалить соцсеть")
    async def remsoc(self, message):
        """<name> - Remove a social network"""
        name = utils.get_args_raw(message).strip()
        if not name:
            await utils.answer(message, self.strings("not_found").format("None"))
            return
            
        socials = self._get_socials()
        if name not in socials:
            await utils.answer(message, self.strings("not_found").format(name))
            return
            
        del socials[name]
        self._set_socials(socials)
        
        await utils.answer(message, self.strings("removed").format(name))

    @loader.command(
        alias="socials",
        ru_doc="Показать список моих соцсетей"
    )
    async def soccmd(self, message):
        """Show your social networks"""
        socials = self._get_socials()
        
        if not socials:
            await utils.answer(message, self.strings("no_socials"))
            return
            
        # Default language based on userbot translation settings
        default_lang = "ru" if self.strings("socials_en") != self.strings("socials_ru") and "Мои" in self.strings("socials_ru") else "en"
        await self._send_socials(message, default_lang)

    async def _send_socials(self, message, lang="en", call=None):
        socials = self._get_socials()
        
        text = self.strings("socials_en") if lang == "en" else self.strings("socials_ru")
        
        buttons = []
        row = []
        for name, link in socials.items():
            row.append({"text": name, "url": link})
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
            
        switch_lang = "ru" if lang == "en" else "en"
        btn_text = "🇷🇺 RU" if lang == "en" else "🇬🇧 EN"
        
        buttons.append([{"text": btn_text, "callback": self._switch_lang, "args": (switch_lang,)}])
        
        if call:
            await call.edit(text, reply_markup=buttons)
        else:
            await self.inline.form(
                text=text,
                message=message,
                reply_markup=buttons
            )

    async def _switch_lang(self, call, switch_lang):
        await self._send_socials(None, lang=switch_lang, call=call)
