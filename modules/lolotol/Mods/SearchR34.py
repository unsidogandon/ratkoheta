#██ ████ ██ ████ ████ ████ ██
#██ █   █ ██ █  █  ██  █   █ ██
#██ ████ ██ ████   ██  ████ ██

#   https://t.me/lolotol089
#   https://github.com/lolotol/Mods

# ---------------------------------------------------------------------------------
# Name: SearchR34
# Description: Поиск контента на Rule34.xxx с поддержкой видео и случайным режимом. Требует API ключ и user_id.
# meta developer: @lolotol89 x @dev_angel_7553
# ---------------------------------------------------------------------------------

import aiohttp
import asyncio
import random
import logging
import json
import os
from urllib.parse import urlencode
from typing import Dict, List, Optional
from telethon.types import Message

from .. import loader, utils

__version__ = (1, 3, 1)

logger = logging.getLogger(__name__)

@loader.tds
class Rule34(loader.Module):
    """Поиск контента на Rule34."""

    strings = {
        "name": "SearchR34",

        "searching": "<emoji document_id=5213311263290971174>🔍</emoji> <b>Ищу контент...</b>",
        "no_results": "<emoji document_id=5436062865855359364>☹️</emoji> <b>Ничего не найдено по запросу:</b> <code>{}</code>",
        "error": "<emoji document_id=5213335456841749820>❌</emoji> <b>Ошибка:</b> <code>{}</code>",
        "invalid_args": "<emoji document_id=5213335456841749820>❌</emoji> <b>Укажите теги для поиска или настрой default_tags!</b>\n<code>{}r34 теги</code>",
        "loading": "<emoji document_id=5877307202888273539>📥</emoji> <b>Загружаю медиа...</b>",
        "searching_random": "<emoji document_id=5960608239623082921>🎲</emoji> <b>Поиск случайного контента...</b>",
        "all_sources_failed": "<emoji document_id=5350629231829215420>💥</emoji> <b>Все источники недоступны</b>",
        "no_api_key": "<b><emoji document_id=5213335456841749820>❌</emoji> Настрой user_id и api_key в </b><code>{}cfg rule34</code>\n<b>Получи их на rule34.xxx в аккаунте (options).</b>",
        "download_error": "<b><emoji document_id=5213335456841749820>❌</emoji> Ошибка загрузки медиа</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "user_id",
                "",
                lambda: "Твой user_id на rule34.xxx (число, из account options)",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "api_key",
                "",
                lambda: "API ключ с rule34.xxx (из account options)",
                validator=loader.validators.Hidden(loader.validators.String())
            ),
            loader.ConfigValue(
                "default_tags",
                "",
                "Теги по умолчанию (через пробел)"
            ),
            loader.ConfigValue(
                "exclude_tags",
                "",
                "Исключающие теги по умолчанию"
            ),
            loader.ConfigValue(
                "antiai",
                True,
                "Фильтровать ИИ-контент",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "posts_limit",
                100,
                "Максимум постов для поиска (1-1000)",
                validator=loader.validators.Integer(minimum=1, maximum=1000)
            ),
            loader.ConfigValue(
                "separate_code_tags",
                False,
                "Отдельный <code> для каждого тега с запятыми между ними (если выкл — все теги через пробел в одном <code>)",
                validator=loader.validators.Boolean()
            ),
        )

        self._session = None

        self.api_sources = [
            {
                "name": "Rule34.xxx",
                "url": "https://api.rule34.xxx/index.php",
                "params": {"page": "dapi", "s": "post", "q": "index", "json": "1"},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        ]

    async def client_ready(self, client, db):
        self._client = client
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )

    async def on_unload(self):
        if self._session:
            await self._session.close()

    async def _make_request(self, source: Dict, tags: str, limit: int = 50) -> List[Dict]:
        try:
            params = source["params"].copy()
            params.update({"limit": min(limit, 1000)})
            if tags:
                params["tags"] = tags

            if not (self.config["user_id"] and self.config["api_key"]):
                return []

            params["user_id"] = self.config["user_id"]
            params["api_key"] = self.config["api_key"]

            url = f"{source['url']}?{urlencode(params)}"
            headers = {"User-Agent": source["user_agent"]}

            async with self._session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.warning(f"{source['name']}: HTTP {response.status}")
                    return []

                content_type = response.headers.get("content-type", "").lower()
                if "json" not in content_type and "text" not in content_type:
                    return []

                text = await response.text()
                if not text.strip():
                    return []

                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    return []

                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return data.get("post", []) or data.get("posts", [])
                else:
                    return []

        except Exception as e:
            logger.error(f"{source['name']}: Ошибка запроса: {e}")
            return []

    def _extract_info(self, post: Dict, source_name: str) -> Optional[Dict]:
        try:
            post_id = str(post.get("id", "unknown"))
            info = {
                "id": post_id,
                "file_url": post.get("file_url", "") or post.get("source", ""),
                "sample_url": post.get("sample_url", "") or post.get("file_url", ""),
                "preview_url": post.get("preview_url", "") or post.get("sample_url", ""),
                "tags": post.get("tags", "").split(),
                "score": int(post.get("score", 0)),
                "source": source_name,
                "post_url": f"https://rule34.xxx/index.php?page=post&s=view&id={post_id}"
            }

            urls = [info["file_url"], info["sample_url"], info["preview_url"]]
            valid_url = next((url for url in urls if url and url.startswith("http")), None)

            if not valid_url:
                return None

            info["media_url"] = valid_url
            info["type"] = "video" if valid_url.lower().endswith(('.mp4', '.webm', '.gif')) else "image"
            return info

        except Exception as e:
            logger.error(f"Ошибка извлечения данных: {e}")
            return None

    def _format_caption(self, info: Dict, search_query: str) -> str:
        tags_list = info.get("tags", [])[:500]
        base_prefix = (
            f"<emoji document_id=5210811489245482123>⭐️</emoji> <b>Score:</b> {info['score']}\n"
            f"<emoji document_id=5213204511878829395>🔎</emoji> <b>Запрос:</b> <code>{utils.escape_html(search_query)}</code>\n"
            f"<emoji document_id=5188324681161138411>🔗</emoji> <a href='{info['post_url']}'>Открыть оригинал на сайте</a>\n"
            f"<emoji document_id=5350305387000130384>📎</emoji> <b>Теги:</b> <blockquote expandable>"
        )
        suffix = "</blockquote>"

        max_len = 1024
        available_for_tags = max_len - len(base_prefix) - len(suffix) - 30

        current_tags_html = ""
        used_tags_count = 0

        if self.config["separate_code_tags"]:
            for i, tag in enumerate(tags_list):
                tag_html = f"<code>{utils.escape_html(tag)}</code>"
                separator = ', ' if current_tags_html else ''
                test_add = separator + tag_html
                if len(current_tags_html + test_add) > available_for_tags:
                    break
                current_tags_html += test_add
                used_tags_count = i + 1
        else:
            for i, tag in enumerate(tags_list):
                tag_html = utils.escape_html(tag)
                separator = ' ' if current_tags_html else ''
                test_add = separator + tag_html
                if len(current_tags_html + test_add) > available_for_tags:
                    break
                current_tags_html += test_add
                used_tags_count = i + 1
            if current_tags_html:
                current_tags_html = f"<code>{current_tags_html}</code>"

        if used_tags_count < len(tags_list):
            remaining = len(tags_list) - used_tags_count
            current_tags_html += f" <i>и ещё {remaining} тег{'ов' if remaining % 10 in (2,3,4) and remaining // 10 != 1 else 'а' if remaining % 10 == 1 and remaining // 10 != 1 else 'ов'}</i>"

        final_caption = base_prefix + (current_tags_html or "<i>Нет тегов</i>") + suffix
        return final_caption

    async def _fetch_results(self, tags: str) -> List[Dict]:
        all_results = []

        for source in self.api_sources:
            posts = await self._make_request(source, tags, self.config["posts_limit"])
            logger.info(f"{source['name']}: получено {len(posts)} постов")

            for post in posts:
                info = self._extract_info(post, source["name"])
                if info:
                    all_results.append(info)

        seen = set()
        unique = []
        for item in all_results:
            if item["id"] not in seen:
                seen.add(item["id"])
                unique.append(item)

        random.shuffle(unique)
        return unique

    async def _get_random_post(self, tags: str):
        results = await self._fetch_results(tags)
        if not results:
            return None
        return random.choice(results)

    async def _download_media(self, url: str) -> Optional[str]:
        try:
            ext = os.path.splitext(url.split("?")[0])[1].lower() or ".jpg"
            filename = f"r34_{random.randint(100000, 999999)}{ext}"
            path = os.path.join("downloads", filename)
            os.makedirs("downloads", exist_ok=True)

            async with self._session.get(url, timeout=30) as resp:
                if resp.status != 200:
                    return None
                with open(path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(8192):
                        f.write(chunk)
            return path
        except Exception as e:
            logger.error(f"Ошибка скачивания: {e}")
            return None

    def _build_tags_string(self, include: str) -> str:
        positive_tags = [t.strip() for t in include.split() if t.strip()]

        negative_tags = [t.strip() for t in self.config["exclude_tags"].split() if t.strip()]

        if self.config["antiai"]:
            ai_tags = ["ai_generated", "stable_diffusion", "midjourney", "novelai", "ai_art"]
            negative_tags.extend(ai_tags)

        full_tags = positive_tags + [f"-{t}" for t in negative_tags]
        return " ".join(full_tags)

    @loader.command()
    async def r34(self, message: Message):
        """ — поиск контента по тегам"""
        args = utils.get_args_raw(message)
        query = args.strip() or self.config["default_tags"]
        if not query.strip():
            await utils.answer(
                message,
                self.strings["invalid_args"].format(self.get_prefix())
            )
            return

        if not (self.config["user_id"] and self.config["api_key"]):
            await utils.answer(
                message,
                self.strings["no_api_key"].format(self.get_prefix())
            )
            return

        status_msg = await utils.answer(message, self.strings["searching"])

        try:
            tags_str = self._build_tags_string(query)

            result = await self._get_random_post(tags_str)

            if not result:
                await status_msg.edit(self.strings["no_results"].format(utils.escape_html(query)))
                return

            await status_msg.edit(self.strings["loading"])

            caption = self._format_caption(result, query)
            file_path = await self._download_media(result["media_url"])

            if not file_path:
                await status_msg.edit(f"{self.strings['download_error']}\n\n{caption}", parse_mode="html")
                return

            await status_msg.edit(caption, file=file_path, parse_mode="html")
            os.remove(file_path)

        except Exception as e:
            logger.error(f"Ошибка команды: {e}")
            await status_msg.edit(self.strings["error"].format(str(e)[:100]))

    @loader.command(alias="r34r")
    async def r34random(self, message: Message):
        """ — случайный контент"""
        if not (self.config["user_id"] and self.config["api_key"]):
            await utils.answer(
                message,
                self.strings["no_api_key"].format(self.get_prefix())
            )
            return

        status_msg = await utils.answer(message, self.strings["searching_random"])

        try:
            query = self.config["default_tags"]  # Для отображения в caption (может быть пустым)

            tags_str = self._build_tags_string(query)

            result = await self._get_random_post(tags_str)

            if not result:
                await status_msg.edit(self.strings["all_sources_failed"])
                return

            await status_msg.edit(self.strings["loading"])

            display_query = query.strip() or "случайный"
            caption = self._format_caption(result, display_query)

            file_path = await self._download_media(result["media_url"])

            if not file_path:
                await status_msg.edit(f"{self.strings['download_error']}\n\n{caption}", parse_mode="html")
                return

            await status_msg.edit(caption, file=file_path, parse_mode="html")
            os.remove(file_path)

        except Exception as e:
            logger.error(f"Ошибка случайной команды: {e}")
            await status_msg.edit(self.strings["error"].format(str(e)[:100]))
