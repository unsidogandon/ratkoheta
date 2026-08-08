__version__ = (2, 1, 5)

# meta developer: @karps_lol
# meta pic: https://raw.githubusercontent.com/unsidogandon/ratkoheta/main/assets/banner.jpg
# meta banner: https://raw.githubusercontent.com/unsidogandon/ratkoheta/main/assets/banner.jpg

import asyncio
import aiohttp
import re
import uuid
import inspect
import logging
import time
from typing import Optional, Dict, List, Union, Any
from urllib.parse import unquote

import telethon
from .. import loader, utils


class RepoIndex:
    MAX_AGE = 300

    def __init__(self) -> None:
        self.items: List[Dict[str, Any]] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.repo: str = ""
        self.loaded_at: float = 0.0

    @property
    def base(self) -> str:
        return f"https://raw.githubusercontent.com/{self.repo}/main"

    async def connect(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def fetch_index(self) -> bool:
        session = await self.connect()
        try:
            async with session.get(
                f"{self.base}/index.json",
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status != 200:
                    return False
                data = await response.json(content_type=None)
            if not isinstance(data, list):
                return False
            for item in data:
                item["install"] = f"{self.base}/{item['path']}"
            self.items = data
            self.loaded_at = time.time()
            return True
        except Exception:
            return False

    async def ensure_fresh(self) -> bool:
        if self.items and time.time() - self.loaded_at < self.MAX_AGE:
            return True
        return await self.fetch_index() or bool(self.items)

    def search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        query = query.lower().strip()
        if not query:
            return []
        scored = []
        for item in self.items:
            score = 0
            name = (item.get("name") or "").lower()
            author = (item.get("author") or "").lower()
            if query in name:
                score += 100 + (50 if name.startswith(query) else 0)
            if query in author:
                score += 60
            for cmd in item.get("commands", []):
                if query in (cmd.get("name") or "").lower():
                    score += 30
                    break
            for ph in item.get("placeholders", []):
                if query in (ph.get("name") or "").lower():
                    score += 25
                    break
            if not score:
                desc = item.get("description") or {}
                texts = list(desc.values()) if isinstance(desc, dict) else [str(desc)]
                texts += [(c.get("doc") or "") for c in item.get("commands", [])]
                texts += [(p.get("doc") or "") for p in item.get("placeholders", [])]
                if any(query in str(t).lower() for t in texts):
                    score += 10
            if score:
                scored.append((score, item))
        scored.sort(key=lambda x: (-x[0], (x[1].get("name") or "").lower()))
        return [item for _, item in scored[:limit]]


class RhetaUI:
    def __init__(self, main: 'Rheta') -> None:
        self.main = main

    def emoji(self, key: str) -> str:
        return self.main.THEMES[self.main.config["theme"]][key]

    def format(self, data: Dict[str, Any], query: str = "", index: int = 1, total: int = 1, inline: bool = False) -> str:
        version = data.get("version", "?.?.?")
        limit = 3700
        name = utils.escape_html(data.get("name", ""))
        author = utils.escape_html(data.get("author", "") or "???")

        text = f"{self.emoji('module')} <code>{name}</code> <b>{self.main.strings['author']}</b> <code>{author}</code>"
        if version != "?.?.?":
            text += f" (<code>v{version}</code>)"

        description = data.get("description")
        if description:
            if isinstance(description, dict):
                string = description.get(self.main.strings["lang"]) or description.get("doc") or next(iter(description.values()), "")
            else:
                string = description
            text += f"\n\n{self.emoji('description')} <b>{self.main.strings['description']}:</b>\n<blockquote expandable>{utils.escape_html(str(string))}</blockquote>"

        text += self.render(data.get("commands", []), "cmd", limit - len(re.sub(r'<[^>]+>', '', text)))
        text += self.render(data.get("placeholders", []), "ph", limit - len(re.sub(r'<[^>]+>', '', text)))

        return text

    def render(self, items: List[Dict[str, Any]], kind: str, limit: int) -> str:
        if not items:
            return ""

        lines = []
        language = self.main.strings["lang"]

        title = "commands" if kind == "cmd" else "placeholders"
        more = "morecommands" if kind == "cmd" else "moreplaceholders"

        for index, item in enumerate(items):
            description = item.get("description", {})
            if isinstance(description, dict):
                description = description.get(language) or description.get("doc") or item.get("doc", "")
            elif item.get("doc") and not description:
                description = item["doc"]

            description = utils.escape_html(str(description)).split('\n')[0] if description else ""
            name = utils.escape_html(item.get("name", ""))

            if item.get('inline'):
                character = '@' + self.main.inline.bot_username + ' '
                display_name = name
            elif kind == "ph":
                character = ""
                display_name = f"{{{name}}}"
            else:
                character = self.main.get_prefix()
                display_name = name

            row = f"<code>{character}{display_name}</code> {description}".strip()

            extra = f"<i>{self.main.strings[more].format(remaining=len(items) - index)}</i>"
            test = "\n".join(lines + [row, extra])

            if len(re.sub(r'<[^>]+>', '', test)) > limit and index > 0:
                lines.append(extra)
                break

            lines.append(row)

        return f"\n\n{self.emoji('command' if kind == 'cmd' else 'placeholder')} <b>{self.main.strings[title]}:</b>\n<blockquote expandable>{chr(10).join(lines)}</blockquote>"

    def buttons(self, link: str, stats: Dict[str, Any], index: int, modules: Optional[List[Dict[str, Any]]] = None, query: str = "") -> List[List[Dict[str, Any]]]:
        buttons = []

        row = [
            {"text": self.main.strings["install"], "callback": self.main.install, "args": (link, index, modules, query)},
            {"text": self.main.strings["code"], "url": link},
        ]
        if query:
            row.insert(0, {"text": self.main.strings["query"], "copy": query})
        buttons.append(row)

        if modules and len(modules) > 1:
            count = {"text": self.main.strings["counter"].format(idx=index + 1, total=len(modules)), "callback": self.main.show, "args": (index, modules, query)}
            buttons[-1].append(count)

            navigation = []
            if index > 0:
                navigation.append({"text": "←", "callback": self.main.navigate, "args": (index - 1, modules, query)})
            if index < len(modules) - 1:
                navigation.append({"text": "→", "callback": self.main.navigate, "args": (index + 1, modules, query)})

            if navigation:
                buttons.append(navigation)

        return buttons

    def pagination(self, modules: List[Dict[str, Any]], query: str, page: int = 0, current: int = 0) -> List[List[Dict[str, Any]]]:
        buttons = []
        start = page * 8
        end = min(start + 8, len(modules))

        for index in range(start, end):
            name = modules[index].get('name', 'Unknown')
            author = modules[index].get('author', '') or '???'
            buttons.append([
                {"text": f"{index + 1}. {name} {self.main.strings['author']} {author}", "callback": self.main.navigate, "args": (index, modules, query)}
            ])

        navigation = []
        if page > 0:
            navigation.append({"text": "←", "callback": self.main.page, "args": (page - 1, modules, query, current)})
        if page < (len(modules) + 7) // 8 - 1:
            navigation.append({"text": "→", "callback": self.main.page, "args": (page + 1, modules, query, current)})

        if navigation:
            buttons.append(navigation)

        buttons.append([{"text": "✘", "callback": self.main.navigate, "args": (current, modules, query)}])
        return buttons


@loader.tds
class Rheta(loader.Module):
    '''ratkoheta this is a fork of the fheta but it doesn't crash every 3 seconds.'''

    strings = {
        "name": "ratkoheta",
        "lang": "en",
        "author": "by",
        "description": "Description",
        "commands": "Commands",
        "placeholders": "Placeholders",
        "morecommands": "...and {remaining} more commands.",
        "moreplaceholders": "...and {remaining} more placeholders.",
        "list": "All found modules:",
        "search": "Searching for {query}...",
        "noquery": "You didn't enter a search query, example: {prefix}rheta your query",
        "notfound": "Nothing found for query {query}.",
        "toolong": "Your query is too big, please try reducing it to 168 characters.",
        "prompt": "Enter a query to search.",
        "hint": "Name, command, description, author.",
        "retry": "Try another query.",
        "query": "Query",
        "install": "Install",
        "counter": "{idx}/{total}",
        "code": "Code",
        "success": "✔ Module successfully installed!",
        "error": "✘ Error, perhaps the module is broken!",
        "overwrite": "✘ Error, module tried to overwrite built-in module!",
        "dependency": "✘ Dependencies installation error!",
        "docrepo": "GitHub repo with modules, format: user/repo",
        "doctheme": "Theme for emojis.",
        "install_via_repo": "Enable Install via repo links?",
        "index_fail": "✘ Failed to load index. Check the repo config.",
        "updating": "Updating module...",
        "uptodate": "Already up to date (v{version}).",
        "updated": "✔ Module updated to v{version}!",
    }

    strings_ru = {
        "_cls_doc": "ратко хета это форк фхеты только не падает от любого чиха",
        "lang": "ru",
        "author": "от",
        "description": "Описание",
        "commands": "Команды",
        "placeholders": "Плейсхолдеры",
        "morecommands": "...и еще {remaining} команд.",
        "moreplaceholders": "...и еще {remaining} плейсхолдеров.",
        "list": "Все найденные модули:",
        "search": "Поиск по запросу {query}...",
        "noquery": "Вы не ввели запрос для поиска, пример: {prefix}rheta ваш запрос",
        "notfound": "Ничего не найдено по запросу {query}.",
        "toolong": "Ваш запрос слишком большой, пожалуйста, сократите его до 168 символов.",
        "prompt": "Введите запрос для поиска.",
        "hint": "Название, команда, описание, автор.",
        "retry": "Попробуйте другой запрос.",
        "query": "Запрос",
        "install": "Установить",
        "counter": "{idx}/{total}",
        "code": "Код",
        "success": "✔ Модуль успешно установлен!",
        "error": "✘ Ошибка, возможно, модуль сломан!",
        "overwrite": "✘ Ошибка, модуль пытался перезаписать встроенный модуль!",
        "dependency": "✘ Ошибка установки зависимостей!",
        "docrepo": "GitHub-репо с модулями в формате user/repo",
        "doctheme": "Тема для эмодзи.",
        "install_via_repo": "Включить установку по ссылкам на репо?",
        "index_fail": "✘ Не удалось загрузить индекс. Проверь конфиг репо.",
        "updating": "Обновляю модуль...",
        "uptodate": "Уже стоит последняя версия (v{version}).",
        "updated": "✔ Модуль обновлён до v{version}!",
    }

    THEMES = {
        "default": {
            "search": '<tg-emoji emoji-id="5188217332748527444">🔍</tg-emoji>',
            "error": '<tg-emoji emoji-id="5465665476971471368">❌</tg-emoji>',
            "warn": '<tg-emoji emoji-id="5447644880824181073">⚠️</tg-emoji>',
            "description": '<tg-emoji emoji-id="5334882760735598374">📝</tg-emoji>',
            "command": '<tg-emoji emoji-id="5341715473882955310">⚙️</tg-emoji>',
            "placeholder": '<tg-emoji emoji-id="5359785904535774578">🗒️</tg-emoji>',
            "module": '<tg-emoji emoji-id="5454112830989025752">📦</tg-emoji>',
            "modules_list": '<tg-emoji emoji-id="5197269100878907942">📋</tg-emoji>'
        },
        "winter": {
            "search": '<tg-emoji emoji-id="5431895003821513760">❄️</tg-emoji>',
            "error": '<tg-emoji emoji-id="5404728536810398694">🧊</tg-emoji>',
            "warn": '<tg-emoji emoji-id="5447644880824181073">🌨️</tg-emoji>',
            "description": '<tg-emoji emoji-id="5255850496291259327">📜</tg-emoji>',
            "command": '<tg-emoji emoji-id="5199503707938505333">🎅</tg-emoji>',
            "placeholder": '<tg-emoji emoji-id="5204046675236109418">🗒️</tg-emoji>',
            "module": '<tg-emoji emoji-id="5197708768091061888">🎁</tg-emoji>',
            "modules_list": '<tg-emoji emoji-id="5345935030143196497">🎄</tg-emoji>'
        },
        "summer": {
            "search": '<tg-emoji emoji-id="5188217332748527444">🔍</tg-emoji>',
            "error": '<tg-emoji emoji-id="5470049770997292425">🌡️</tg-emoji>',
            "warn": '<tg-emoji emoji-id="5447644880824181073">⚠️</tg-emoji>',
            "description": '<tg-emoji emoji-id="5361684086807076580">🍹</tg-emoji>',
            "command": '<tg-emoji emoji-id="5442644589703866634">🏄</tg-emoji>',
            "placeholder": '<tg-emoji emoji-id="5434121252874756456">🗒️</tg-emoji>',
            "module": '<tg-emoji emoji-id="5433645645376264953">🏖️</tg-emoji>',
            "modules_list": '<tg-emoji emoji-id="5472178859300363509">🏖️</tg-emoji>'
        },
        "spring": {
            "search": '<tg-emoji emoji-id="5449885771420934013">🌱</tg-emoji>',
            "error": '<tg-emoji emoji-id="5208923808169222461">🥀</tg-emoji>',
            "warn": '<tg-emoji emoji-id="5447644880824181073">⚠️</tg-emoji>',
            "description": '<tg-emoji emoji-id="5251524493561569780">🍃</tg-emoji>',
            "command": '<tg-emoji emoji-id="5449850741667668411">🦋</tg-emoji>',
            "placeholder": '<tg-emoji emoji-id="5434121252874756456">🗒️</tg-emoji>',
            "module": '<tg-emoji emoji-id="5440911110838425969">🌿</tg-emoji>',
            "modules_list": '<tg-emoji emoji-id="5440748683765227563">🌺</tg-emoji>'
        },
        "autumn": {
            "search": '<tg-emoji emoji-id="5253944419870062295">🍂</tg-emoji>',
            "error": '<tg-emoji emoji-id="5281026503658728615">🍁</tg-emoji>',
            "warn": '<tg-emoji emoji-id="5447644880824181073">⚠️</tg-emoji>',
            "description": '<tg-emoji emoji-id="5406631276042002796">📜</tg-emoji>',
            "command": '<tg-emoji emoji-id="5212963577098417551">🍂</tg-emoji>',
            "placeholder": '<tg-emoji emoji-id="5363965354391388799">🗒️</tg-emoji>',
            "module": '<tg-emoji emoji-id="5249157915041855558">🍄</tg-emoji>',
            "modules_list": '<tg-emoji emoji-id="5305495722618010655">🍂</tg-emoji>'
        }
    }

    def __init__(self) -> None:
        self.rheta_cache: Dict[str, Dict[str, Any]] = {}
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "repo",
                "unsidogandon/ratkoheta",
                lambda: self.strings["docrepo"],
                validator=loader.validators.RegExp(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
            ),
            loader.ConfigValue(
                "install_via_repo",
                True,
                lambda: self.strings["install_via_repo"],
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "theme",
                "default",
                lambda: self.strings["doctheme"],
                validator=loader.validators.Choice(["default", "winter", "summer", "spring", "autumn"])
            )
        )

    async def on_unload(self) -> None:
        if hasattr(self, "idx") and self.idx.session and not self.idx.session.closed:
            await self.idx.session.close()
        if hasattr(self, "inline") and hasattr(self.inline, "unregister_bot_update_handler"):
            self.inline.unregister_bot_update_handler("rheta_chosen")

    async def client_ready(self, client: 'telethon.TelegramClient', database: 'loader.Database') -> None:
        self.idx = RepoIndex()
        self.idx.repo = self.config["repo"]
        self.ui = RhetaUI(self)

        await self.idx.fetch_index()

        self.rheta_cache: Dict[str, Dict[str, Any]] = {}

        if hasattr(self.inline, "register_bot_update_handler"):
            async def rheta_chosen(event: Any) -> None:
                if isinstance(event, telethon.tl.types.UpdateBotInlineSend) and getattr(event, "id", "").startswith("rh_"):
                    await self.chosen(event)
            self.inline.register_bot_update_handler("rheta_chosen", "chosen_inline_result", rheta_chosen)

    @loader.loop(interval=1800, autostart=True)
    async def refresh(self):
        self.idx.repo = self.config["repo"]
        await self.idx.fetch_index()

    async def answer(self, callback: Any, text: Optional[str] = None, alert: bool = False) -> None:
        if not hasattr(callback, "answer"):
            return
        await callback.answer(text=text or "", show_alert=alert)

    async def edit(self, target: Any, text: str, buttons: List[List[Dict[str, Any]]], banner: Optional[str] = None) -> None:
        markup = self.inline.generate_markup(buttons)

        if banner and banner not in text:
            text = f'<a href="{banner}">&#8204;</a>' + text

        inline_msg_id = target.inline_message_id if hasattr(target, "inline_message_id") else None

        await self.inline.bot.edit_message(
            inline_msg_id or target.chat_id,
            None if inline_msg_id else target.message_id,
            text,
            parse_mode="HTML",
            buttons=markup,
            link_preview=banner is not None,
            invert_media=banner is not None
        )

    async def chosen(self, event: Any) -> None:
        parts = getattr(event, "id", "").split("_")
        if len(parts) != 3:
            return
        queryid, index = parts[1], int(parts[2])
        saved = self.rheta_cache.get(queryid)
        if not saved:
            return
        query = saved.get("query", "")
        modules = saved.get("mods", [])
        if not modules or index >= len(modules):
            return
        data = modules[index]
        text = self.ui.format(data, query, 1, 1, True)
        buttons = self.ui.buttons(data.get("install", ""), data, 0, [data], query)
        banner = data.get("banner")
        if banner and banner not in text:
            text = f'<a href="{banner}">&#8204;</a>' + text
        await self.inline.bot.edit_message(
            event.msg_id,
            None,
            text,
            parse_mode="HTML",
            buttons=self.inline.generate_markup(buttons),
            link_preview=banner is not None,
            invert_media=banner is not None
        )

    async def show(self, callback: Any, index: int, modules: List[Dict[str, Any]], query: str) -> None:
        await self.answer(callback)
        text = f"{self.ui.emoji('modules_list')} <b>{self.strings['list']}</b>"
        await self.edit(callback, text, self.ui.pagination(modules, query, 0, index))

    async def page(self, callback: Any, current: int, modules: List[Dict[str, Any]], query: str, index: int) -> None:
        await self.answer(callback)
        text = f"{self.ui.emoji('modules_list')} <b>{self.strings['list']}</b>"
        await self.edit(callback, text, self.ui.pagination(modules, query, current, index))

    async def navigate(self, callback: Any, index: int, modules: List[Dict[str, Any]], query: str = "") -> None:
        await self.answer(callback)
        if 0 <= index < len(modules):
            data = modules[index]
            text = self.ui.format(data, query, index + 1, len(modules))
            buttons = self.ui.buttons(data.get('install', ''), data, index, modules, query)
            await self.edit(callback, text, buttons, data.get("banner"))

    def get_logs(self) -> str:
        return "\n".join(
            [
                "\n".join(
                    handler.dumps(0, client_id=getattr(self, "client", self._client).tg_id)
                    if "client_id" in inspect.signature(handler.dumps).parameters
                    else handler.dumps(0)
                )
                for handler in logging.getLogger().handlers
                if hasattr(handler, "dumps")
            ]
        )

    @staticmethod
    def parse_deps(logs: str) -> str:
        found = []
        for pattern in (
            r"could not find a version that satisfies the requirement ([^\s,]+)",
            r"no matching distribution found for ([^\s,]+)",
        ):
            found += re.findall(pattern, logs)
        if not found:
            m = re.search(
                r"--no-warn-script-location\s+(.+?)\) with exit code",
                logs,
                re.S,
            )
            if m:
                found = m.group(1).split()
        return ", ".join(dict.fromkeys(found))

    async def install(self, callback: Any, link: str, index: int, modules: Optional[List[Dict[str, Any]]], query: str = "") -> None:
        ologs = self.get_logs()

        res = await self.lookup("loader").download_and_install(link)

        if res == 1:
            await self.answer(callback, self.strings["success"], True)
            return

        alogs = self.get_logs()
        nlogs = alogs[len(ologs):].lower()

        if "overwrite" in nlogs:
            await self.answer(callback, self.strings["overwrite"], True)
        elif any(x in nlogs for x in ("requir", "depend", "package")):
            deps = self.parse_deps(nlogs)
            text = self.strings["dependency"] + (f" ({deps})" if deps else "")
            await self.answer(callback, text, True)
        else:
            await self.answer(callback, self.strings["error"], True)

    @loader.inline_handler(
        ru_doc="(запрос) - поиск модулей в твоём репо.",
    )
    async def rheta(self, event: 'loader.InlineCall') -> Union[Dict[str, str], None]:
        '''(query) - search modules in your GitHub repo.'''
        query = event.args

        if not query:
            return {
                "title": self.strings["prompt"],
                "description": self.strings["hint"],
                "message": f"{self.ui.emoji('error')} <b>{self.strings['noquery'].format(prefix=f'<code>@{self.inline.bot_username} ')}</code></b>",
                "thumb": "https://raw.githubusercontent.com/unsidogandon/ratkoheta/main/assets/magnifying_glass.png"
            }

        if len(query) > 168:
            return {
                "title": self.strings["toolong"],
                "description": self.strings["retry"],
                "message": f"{self.ui.emoji('warn')} <b>{self.strings['toolong']}</b>",
                "thumb": "https://raw.githubusercontent.com/unsidogandon/ratkoheta/main/assets/try_other_query.png"
            }

        await self.idx.ensure_fresh()

        modules = self.idx.search(query, limit=50)

        if not modules:
            return {
                "title": self.strings["retry"],
                "description": self.strings["hint"],
                "message": f"{self.ui.emoji('error')} <b>{self.strings['notfound'].format(query=f'<code>{utils.escape_html(query)}</code>')}</b>",
                "thumb": "https://raw.githubusercontent.com/unsidogandon/ratkoheta/main/assets/try_other_query.png"
            }

        queryid = str(uuid.uuid4())[:8]
        self.rheta_cache[queryid] = {"query": query, "mods": modules[:50]}
        results = []

        for index, data in enumerate(modules[:50]):
            description = data.get("description", "")
            if isinstance(description, dict):
                description = description.get(self.strings["lang"]) or description.get("doc") or next(iter(description.values()), "")

            markup = self.inline.generate_markup(self.ui.buttons(data.get("install", ""), data, index, modules, query))

            thumb_url = data.get("pic") or "https://raw.githubusercontent.com/unsidogandon/ratkoheta/main/assets/empty_pic.png"
            thumb = self.inline._web_document(thumb_url)

            results.append(
                await event.builder.article(
                    id=f"rh_{queryid}_{index}",
                    title=utils.escape_html(data.get("name", "")),
                    description=utils.escape_html(str(description)[:250] + ("..." if len(str(description)) > 250 else "")),
                    thumb=thumb,
                    text="🪐",
                    parse_mode="HTML",
                    buttons=markup
                )
            )

        await event.answer(results, cache_time=0)

    @loader.command(
        ru_doc="(запрос) - поиск модулей в твоём репо.",
    )
    async def rhetacmd(self, message: 'telethon.types.Message') -> Any:
        '''(query) - search modules in your GitHub repo.'''
        query = utils.get_args_raw(message)

        if not query:
            return await utils.answer(message, f"{self.ui.emoji('error')} <b>{self.strings['noquery'].format(prefix=f'<code>{self.get_prefix()}')}</code></b>")

        if len(query) > 168:
            return await utils.answer(message, f"{self.ui.emoji('warn')} <b>{self.strings['toolong']}</b>")

        message = await utils.answer(message, f"{self.ui.emoji('search')} <b>{self.strings['search'].format(query=f'<code>{utils.escape_html(query)}</code>')}</b>")

        if not await self.idx.ensure_fresh() and not self.idx.items:
            return await utils.answer(message, f"{self.ui.emoji('error')} <b>{self.strings['index_fail']}</b>")

        modules = self.idx.search(query, limit=50)

        if not modules:
            return await utils.answer(message, f"{self.ui.emoji('error')} <b>{self.strings['notfound'].format(query=f'<code>{utils.escape_html(query)}</code>')}</b>")

        data = modules[0]
        buttons = self.ui.buttons(data.get("install", ""), data, 0, modules, query)
        text = self.ui.format(data, query, 1, len(modules))
        banner = data.get("banner")

        if banner and banner not in text:
            text = f'<a href="{banner}">&#8204;</a>' + text

        msg = await self.inline.form(
            text,
            message,
            reply_markup=buttons,
            silent=True
        )

        if banner and msg:
            await asyncio.sleep(0.4)
            await self.edit(msg, text, buttons, banner)

    @loader.command(ru_doc="- обновить модуль до последней версии из репо.")
    async def rupdatecmd(self, message: 'telethon.types.Message') -> Any:
        '''- update this module to the latest version from the repo.'''
        url = f"{self.idx.base}/Rheta.py"
        message = await utils.answer(message, f"{self.ui.emoji('search')} <b>{self.strings['updating']}</b>")

        session = await self.idx.connect()
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status != 200:
                    return await utils.answer(message, f"{self.ui.emoji('error')} <b>{self.strings['index_fail']}</b>")
                code = await resp.text()
        except Exception:
            return await utils.answer(message, f"{self.ui.emoji('error')} <b>{self.strings['index_fail']}</b>")

        m = re.search(r"__version__\s*=\s*\((\d+),\s*(\d+),\s*(\d+)\)", code)
        remote_version = tuple(int(x) for x in m.groups()) if m else None

        if remote_version and remote_version <= __version__:
            return await utils.answer(
                message,
                f"{self.ui.emoji('module')} <b>{self.strings['uptodate'].format(version='.'.join(map(str, __version__)))}</b>"
            )

        try:
            await self.lookup("loader").download_and_install(url)
        except Exception:
            return await utils.answer(message, f"{self.ui.emoji('error')} <b>{self.strings['error']}</b>")

        try:
            await utils.answer(
                message,
                f"{self.ui.emoji('module')} <b>{self.strings['updated'].format(version='.'.join(map(str, remote_version)))}</b>"
            )
        except Exception:
            pass

    @loader.watcher()
    async def watcher(self, message: 'telethon.types.Message') -> None:
        if not self.config["install_via_repo"]:
            return

        url = message.raw_text.strip()

        if not url.startswith(f"https://raw.githubusercontent.com/{self.config['repo']}/main/modules/"):
            return

        ologs = self.get_logs()

        res = await self.lookup("loader").download_and_install(url)

        if res == 1:
            reply = await message.respond("✅")
        else:
            alogs = self.get_logs()
            nlogs = alogs[len(ologs):].lower()

            if "overwrite" in nlogs:
                reply = await message.respond("😨")
            elif any(x in nlogs for x in ("requir", "depend", "package")):
                deps = self.parse_deps(nlogs)
                reply = await message.respond(f"📋{','.join(deps.split(', ')[:5])}" if deps else "📋")
            else:
                reply = await message.respond("❌")

        await asyncio.sleep(1)
        await reply.delete()
        await message.delete()
