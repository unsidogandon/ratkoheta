# meta developer: @CoderHoly
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
⠄⠘⢷⡳⣾⣷⣶⣶⣶⣶⣶⣾⣿⣿⢀⣶⣶⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⠇⠄
⠄⠄⠈⣵⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠄⠄
⠄⠄⠄⠸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠇⠄⠄
"""

import os
import json
import httpx
import re
import base64
import zlib
import logging
import hashlib
import tempfile
import asyncio
from .. import loader, utils
from telethon.tl.types import Message

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

__version__ = (2, 0, 0)


@loader.tds
class ReadFileMod(loader.Module):
    """Модуль для чтения и AI-анализа Python файлов"""

    strings = {
        "name": "ReadFileMod",
        "rf_doc": "Ответьте на Python файл для AI анализа",
        "spai_doc": "Посмотреть список доступных AI моделей",
        "cc_doc": "Очистить кеш и временные файлы",
        "updatef_doc": "Проверить и обновить версию модуля",
    }

    def __init__(self):
        self.analyzer = AnalyzerCore()
        self.ai_client = AiClient()
        self.cache_manager = CacheManager()
        self.ui_builder = UIBuilder()
        
        self._user_data = {}
        self._models_list = []
        
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "provider",
                "OnlySq",
                "Провайдер AI (OpenRouter или OnlySq)",
                validator=loader.validators.Choice(["OpenRouter", "OnlySq"]),
            ),
            loader.ConfigValue(
                "model",
                "llama-3.3-70b",
                "Модель ИИ для анализа кода",
            ),
            loader.ConfigValue(
                "api_key",
                "нема",
                "API ключ для OpenRouter. Получить: https://openrouter.ai/settings/keys",
                validator=loader.validators.Hidden(),
            ),
            loader.ConfigValue(
                "onlysq_api_key",
                "openai",
                "API ключ для OnlySq",
                validator=loader.validators.Hidden(),
            ),
        )

    def _get_user_data(self, user_id: int) -> dict:
        """Получить данные пользователя"""
        if user_id not in self._user_data:
            self._user_data[user_id] = {
                "chunks": [],
                "file_info": {},
                "file_content": "",
                "file_path": "",
                "analyzed_count": 0,
            }
        return self._user_data[user_id]

    def _clear_user_data(self, user_id: int):
        """Очистить данные пользователя"""
        if user_id in self._user_data:
            data = self._user_data[user_id]
            if data["file_path"] and os.path.exists(data["file_path"]):
                try:
                    os.remove(data["file_path"])
                except Exception:
                    pass
            del self._user_data[user_id]

    async def spaicmd(self, message: Message):
        """Показать список доступных AI моделей для анализа"""
        text = "Выберите провайдера для списка моделей:"

        buttons = [
            [
                {
                    "text": "OpenRouter",
                    "callback": self._select_provider_cb,
                    "args": ("OpenRouter",),
                }
            ],
            [
                {
                    "text": "OnlySq",
                    "callback": self._select_provider_cb,
                    "args": ("OnlySq",),
                }
            ],
        ]

        await self.inline.form(text=text, message=message, reply_markup=buttons)

    async def _select_provider_cb(self, call, provider):
        await call.edit("⏳ Загружаю список моделей...")

        try:
            self._models_list = await self.ai_client.get_models_list(
                provider, self.config
            )

            await self.ui_builder.show_models_page(
                self, call, self._models_list, 0, provider=provider
            )

        except Exception as e:
            await call.edit(f"❌ Ошибка API {provider}: {str(e)}")

    async def _show_models_page(self, call, page, provider):
        await self.ui_builder.show_models_page(
            self, call, self._models_list, page, provider=provider
        )

    async def _refresh_models_cb(self, call, provider):
        await call.edit("⏳ Обновляю список моделей...")

        try:
            self._models_list = await self.ai_client.get_models_list(
                provider, self.config
            )

            await self.ui_builder.show_models_page(
                self, call, self._models_list, 0, provider=provider
            )

        except Exception as e:
            await call.edit(f"❌ Ошибка API {provider}: {str(e)}")

    async def _info_cb(self, call, index):
        user_id = call.from_user.id
        user_data = self._get_user_data(user_id)

        if not user_data["file_content"]:
            await call.edit(
                "❌ Содержимое файла потеряно. Проанализируйте файл заново через .rf"
            )
            return

        h = self.cache_manager._content_hash(user_data["file_content"])
        data = self.cache_manager._load_ai_cache(h)

        if data is None:
            await call.edit("⏳ Анализирую модуль через AI...")

            try:
                data = await self.analyzer._generate_description(
                    user_data["file_content"], ai_client=self.ai_client, config=self.config
                )
                self.cache_manager._save_ai_cache(h, data)

            except Exception as e:
                await self.ui_builder.show_analysis_error(
                    self, call, str(e), user_data["file_info"]
                )
                return

        await self.ui_builder.show_analysis(self, call, data, user_data["file_info"])

    async def _ask_question_cb(self, call):
        await call.edit(
            "❓ <b>Задать вопрос о модуле</b>\n\n"
            "Напишите ваш вопрос в поле ввода ниже.\n"
            "Пример: 'Что делает эта функция?' или 'Объясни этот код'",
            reply_markup=[
                [
                    {
                        "text": "📝 Задать вопрос",
                        "input": "Введите ваш вопрос о модуле",
                        "handler": self._input_question_handler,
                    }
                ],
                [
                    {
                        "text": "⬅️ Назад к анализу",
                        "callback": self._info_cb,
                        "args": (0,),
                    }
                ],
            ],
        )

    async def _input_question_handler(self, call, question: str):
        max_length = self.config.get("max_question_length", 1000)
        
        if not question or not question.strip():
            await call.answer("Вопрос не может быть пустым", show_alert=True)
            return

        if max_length and len(question) > max_length:
            await call.answer(
                f"Вопрос слишком длинный! Максимум {max_length} символов.",
                show_alert=True
            )
            return

        user_id = call.from_user.id
        user_data = self._get_user_data(user_id)

        if not user_data["file_content"]:
            await call.edit(
                "❌ Содержимое файла потеряно. Проанализируйте файл заново через .rf"
            )
            return

        await call.edit(
            "⏳ <b>Обрабатываю вопрос...</b>\n\n"
            "Подождите немного, я анализирую код.",
            reply_markup=[],
        )

        provider = self.config["provider"]
        model = self.config["model"]

        system_prompt = (
            "Вы — опытный специалист по коду Python для ботов Telegram (Telethon/Hikka).\n"
            "Ваша задача — объяснить модуль обычному пользователю.\n\n"
            "--- ПРАВИЛА ---\n"
            "• Отвечайте на русском.\n"
            "• Сокращайте ответы и будьте ясными.\n"
            "• Объясняйте КОМАНДЫ (начинающиеся с точки, например, .rf) и как их использовать.\n"
            "• Давайте примеры использования.\n\n"
            "--- ФОРМАТИРОВАНИЕ (ОБЯЗАТЕЛЬНО) ---\n"
            "Используйте ТоЛишь Telegram HTML. Не используйте Markdown (*, **, #, и т.д.).\n"
            "Вы обязаны подчеркивать ключевую информацию с помощью этих тегов:\n"
            "• <b>Прописью</b> — для важных терминов, имён команд и эмоций.\n"
            "• <code>Моноширинный</code> — для фрагментов кода, примеров команд (например, <code>.rf</code>), и имён файлов.\n"
            "• <i>Курсивом</i> — для дополнительных заметок.\n"
            "• <blockquote>Цитата</blockquote> — для длинных объяснений или логических блоков.\n\n"
            "Пример хорошего ответа:\n"
            "Для работы с модулем используйте команду <code>.rf</code> (ответом на файл).\n"
            "<b>Важно:</b> файл должен иметь расширение <code>.py</code>.\n"
            "<blockquote>Это позволяет ИИ анализировать код и выдать вердикт.</blockquote>"
        )

        user_prompt = (
            f"Вопрос: {question.strip()}\n\n"
            f"Код модуля:\n{user_data['file_content'][:20000]}"
        )

        try:
            response = await asyncio.wait_for(
                self.ai_client.make_api_request(
                    provider, model, system_prompt, user_prompt, self.config
                ),
                timeout=60.0,
            )

        except asyncio.TimeoutError:
            await call.edit(
                "⏰ <b>Время ожидания истекло</b>\n\n"
                "Попробуйте задать вопрос еще раз или выберите более короткий вопрос.",
                reply_markup=[
                    [
                        {
                            "text": "📝 Задать другой вопрос",
                            "input": "Введите ваш вопрос",
                            "handler": self._input_question_handler,
                        }
                    ],
                    [
                        {
                            "text": "⬅️ Назад к анализу",
                            "callback": self._info_cb,
                            "args": (0,),
                        }
                    ],
                ],
            )
            return

        except Exception as e:
            await call.edit(
                f"❌ Ошибка: {utils.escape_html(str(e))}",
                reply_markup=[
                    [
                        {
                            "text": "⬅️ Назад к анализу",
                            "callback": self._info_cb,
                            "args": (0,),
                        }
                    ],
                ],
            )
            return

        clean_response = re.sub(r'[*_#]', '', str(response)).strip()

        await call.edit(
            f"🤖 <b>Ответ от модели:</b> <code>{utils.escape_html(model)}</code>\n\n"
            f"❓ <b>Вопрос:</b> <blockquote>{utils.escape_html(question)}</blockquote>\n\n"
            f"💡 <b>Ответ:</b> <blockquote>{clean_response}</blockquote>",
            reply_markup=[
                [
                    {
                        "text": "📝 Задать еще вопрос",
                        "input": "Введите ваш вопрос",
                        "handler": self._input_question_handler,
                    }
                ],
                [
                    {
                        "text": "⬅️ Назад к анализу",
                        "callback": self._info_cb,
                        "args": (0,),
                    }
                ],
            ],
        )

    async def rfcmd(self, message: Message):
        """<ответ на файл> - Проанализировать Python модуль через AI"""
        reply = await message.get_reply_message()

        if not reply or not reply.file:
            await message.edit("❌ Ответьте на файл.")
            return

        user_id = message.sender_id
        user_data = self._get_user_data(user_id)

        if user_data["file_path"] and os.path.exists(user_data["file_path"]):
            try:
                os.remove(user_data["file_path"])
            except Exception:
                pass

        await message.edit(f"⏳ Чтение файла: {reply.file.name}...")

        try:
            file_path = await reply.download_media()

            if os.path.getsize(file_path) > 10 * 1024 * 1024:
                os.remove(file_path)
                await message.edit("❌ Файл слишком большой (макс. 10 МБ).")
                return

            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()

        except Exception as e:
            await message.edit(f"❌ Ошибка чтения: {utils.escape_html(str(e))}")
            return

        user_data["file_path"] = file_path
        user_data["file_content"] = file_content
        user_data["chunks"] = self.ui_builder._split_text(file_content, 1500)

        filename = os.path.basename(file_path)
        display_name = filename

        strings_match = self.analyzer._strings_name_re.search(file_content)
        if strings_match:
            display_name = strings_match.group(1)
        else:
            class_match = self.analyzer._class_name_re.search(file_content)
            if class_match:
                class_name = class_match.group(1)
                if class_name.endswith("Module"):
                    display_name = class_name[:-6]
                elif class_name.endswith("Mod"):
                    display_name = class_name[:-3]
                else:
                    display_name = class_name
            elif filename.endswith(".py"):
                display_name = filename[:-3]

        user_data["file_info"] = {
            "Имя": display_name,
            "Размер": os.path.getsize(file_path),
            "Страниц": len(user_data["chunks"]),
            "Путь": file_path,
        }

        user_data["analyzed_count"] += 1

        await self.ui_builder.show_page(
            self, message, user_data["chunks"], user_data["file_info"], 0, user_id
        )

    async def _page_cb(self, call, index):
        user_id = call.from_user.id
        user_data = self._get_user_data(user_id)
        
        await self.ui_builder.show_page(
            self, call, user_data["chunks"], user_data["file_info"], index, user_id
        )

    async def cccmd(self, message: Message):
        """Показать статистику кеша и очистить временные файлы"""
        user_id = message.sender_id
        user_data = self._get_user_data(user_id)

        total_bytes, total_files = self.cache_manager._get_cache_stats(
            user_data["file_path"]
        )

        text, buttons = self.ui_builder.build_cache_stats_text(
            total_bytes, total_files, user_data["analyzed_count"]
        )

        buttons[0][0]["callback"] = self._clear_cache_cb

        await self.inline.form(text=text, message=message, reply_markup=buttons)

    async def _clear_cache_cb(self, call):
        user_id = call.from_user.id
        user_data = self._get_user_data(user_id)

        removed_files, removed_cache = self.cache_manager.clear_cache(
            user_data["file_path"]
        )

        self._clear_user_data(user_id)

        await call.edit(
            "🧹 <b>Кеш и временные файлы очищены!</b>\n"
            f"• Удалено временных файлов: {removed_files}\n"
            f"• Удалено файлов кеша: {removed_cache}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Можно продолжать анализ новых модулей 🙂"
        )

    async def updatefmcmd(self, message: Message):
        """Проверка и обновление версии модуля"""
        await utils.answer(message, "⏳ Проверка версии модуля...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://raw.githubusercontent.com/Holy16rus/Module-Holy/main/ReadFileMod.py"
                )
                response.raise_for_status()
                
                remote_content = response.text
                remote_version_match = re.search(
                    r"__version__\s*=\s*\((\d+),\s*(\d+),\s*(\d+)\)",
                    remote_content
                )
                
                if not remote_version_match:
                    await utils.answer(message, "❌ Не удалось определить версию в репозитории.")
                    return
                
                remote_version = tuple(map(int, remote_version_match.groups()))
                current_version = __version__
                
                if remote_version > current_version:
                    text = (
                        "<b>👻 Информация о Версии</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━\n"
                        f"<b>Версия:</b> {'.'.join(map(str, current_version))}\n"
                        f"<b>В репозитории:</b> {'.'.join(map(str, remote_version))}\n"
                        "━━━━━━━━━━━━━━━━━━━━\n"
                        "<b>Хотите обновить модуль?</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━"
                    )
                    
                    await self.inline.form(
                        text=text,
                        message=message,
                        reply_markup=[
                            [{"text": "Обновить", "callback": self._update_confirm_cb, "args": (remote_content,)}]
                        ]
                    )
                else:
                    text = (
                        "<b>👻 Информация о Версии</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━\n"
                        f"<b>Версия:</b> {'.'.join(map(str, current_version))}\n"
                        f"<b>В репозитории:</b> {'.'.join(map(str, remote_version))}\n"
                        "━━━━━━━━━━━━━━━━━━━━\n"
                        "<b>✅ У вас уже установлена актуальная версия!</b>\n"
                        "━━━━━━━━━━━━━━━━━━━━"
                    )
                    
                    await self.inline.form(
                        text=text,
                        message=message,
                        reply_markup=[]
                    )
        except Exception as e:
            await utils.answer(message, f"❌ Ошибка при проверке обновлений: {e}")

    async def _update_confirm_cb(self, call, remote_content: str):
        """Обработчик подтверждения обновления"""
        try:
            loader_module = self.lookup("loader")
            if not loader_module:
                await call.edit("❌ Ошибка: Не удалось найти модуль loader.")
                return
            
            remote_version_match = re.search(
                r"__version__\s*=\s*\((\d+),\s*(\d+),\s*(\d+)\)",
                remote_content
            )
            if remote_version_match:
                remote_version = tuple(map(int, remote_version_match.groups()))
            else:
                await call.edit("❌ Ошибка: Не удалось определить версию в обновлении.")
                return
            
            await call.edit("⏳ Обновление модуля...")
            
            for _ in range(5):
                await loader_module.download_and_install(
                    "https://raw.githubusercontent.com/Holy16rus/Module-Holy/main/ReadFileMod.py",
                    None
                )
                
                if getattr(loader_module, "fully_loaded", False):
                    loader_module.update_modules_in_db()
                
                is_loaded = any(
                    mod.__origin__ == "https://raw.githubusercontent.com/Holy16rus/Module-Holy/main/ReadFileMod.py"
                    for mod in self.allmodules.modules
                )
                
                if is_loaded:
                    await call.edit(
                        f"✅ Модуль успешно обновлён до версии {'.'.join(map(str, remote_version))}!"
                    )
                    break
            else:
                await call.edit("❌ Ошибка: Не удалось обновить модуль после нескольких попыток.")
        except Exception as e:
            await call.edit(f"❌ Ошибка при обновлении модуля: {e}")

    async def on_unload(self):
        """Очистка при выгрузке модуля"""
        await self.ai_client.close_http_client()
        
        for user_id in list(self._user_data.keys()):
            self._clear_user_data(user_id)


class AiClient:
    """Клиент для работы с AI API"""

    def __init__(self):
        self._http_client: httpx.AsyncClient | None = None

    async def _get_http_client(self, config):
        if self._http_client is None:
            proxy = config.get("proxy") or None
            client_args = {"timeout": 60}

            if proxy:
                client_args["proxies"] = proxy

            self._http_client = httpx.AsyncClient(**client_args)

        return self._http_client

    async def make_api_request(
        self, provider: str, model: str, system_prompt: str, user_content: str, config
    ) -> str:
        """Выполнить запрос к API"""
        if provider == "OnlySq":
            api_url = "https://api.onlysq.ru/ai/openai/chat/completions"
            api_key = config.get("onlysq_api_key", "")
            if not api_key:
                raise Exception("OnlySq API ключ не настроен. Используйте: .config ReadFileMod")
        else:  # OpenRouter
            api_url = "https://openrouter.ai/api/v1/chat/completions"
            api_key = config.get("api_key", "")
            if not api_key:
                raise Exception("OpenRouter API ключ не настроен. Получите на https://openrouter.ai/settings/keys")

        client = await self._get_http_client(config)
        headers, payload = self._build_request(provider, api_key, model, system_prompt, user_content)

        try:
            response = await client.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else None
            body = e.response.text if e.response is not None else ""
            hint = "Проверьте API ключ" if status == 401 else "Ошибка API"
            snippet = body.strip()
            if len(snippet) > 300:
                snippet = snippet[:300] + "..."
            msg = f"HTTP {status} ({provider}): {hint}"
            if snippet:
                msg = f"{msg}. Response: {snippet}"
            raise Exception(msg)
        except httpx.RequestError as e:
            raise Exception(f"Ошибка запроса ({provider}): {e}")

        try:
            data = response.json()
        except ValueError:
            text = response.text.strip()
            if len(text) > 300:
                text = text[:300] + "..."
            raise Exception(f"Некорректный ответ API ({provider}): {text}")

        try:
            raw_response = data["choices"][0]["message"]["content"]
        except Exception:
            raise Exception(f"Некорректный формат ответа API ({provider})")

        if raw_response is None:
            raise Exception(f"Пустой ответ API ({provider})")

        return str(raw_response).strip()

    def _build_request(self, provider, api_key, model, system_prompt, user_content):
        """Построить запрос к API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        }
        return headers, payload

    async def get_models_list(self, provider: str, config) -> list:
        """Получить список доступных моделей"""
        try:
            client = await self._get_http_client(config)

            if provider == "OnlySq":
                api_url = "https://api.onlysq.ru/ai/models"
            else:
                api_url = "https://openrouter.ai/api/v1/models"

            response = await client.get(api_url)
            response.raise_for_status()
            data = response.json()
            
            if provider == "OnlySq":
                all_models_dict = data.get("models", {})
                all_models = list(all_models_dict.values())
            else:
                all_models = data.get("data", [])

            free_models = []

            if provider == "OnlySq":
                all_models_dict = data.get("models", {})
                for model_id, m in all_models_dict.items():
                    limits = m.get("limits", {})
                    lvl0 = limits.get("lvl0", 0)
                    name = m.get("name", model_id)
                    
                    free_models.append(
                        {
                            "name": model_id,
                            "pretty_name": name,
                            "context": f"{lvl0}K" if lvl0 else "0K",
                            "description": m.get("description", "Нет описания")[:100] + "...",
                        }
                    )
            else:
                for m in all_models:
                    context_length = int(m.get("context_length", 0))
                    is_free = float(m.get("pricing", {}).get("prompt", 1)) == 0

                    if is_free and context_length >= 64000:
                        free_models.append(
                            {
                                "name": m.get("id"),
                                "pretty_name": m.get("name"),
                                "context": f"{context_length // 1024}K",
                                "description": m.get("description", "Нет описания")[:100] + "...",
                            }
                        )

            if provider == "OnlySq":
                free_models.sort(key=lambda x: x["pretty_name"])
            else:
                free_models.sort(
                    key=lambda x: int(x["context"].replace("K", "")), reverse=True
                )

            return free_models

        except Exception as e:
            raise Exception(f"❌ Ошибка API {provider}: {str(e)}")

    async def close_http_client(self):
        """Закрыть HTTP клиент"""
        if self._http_client:
            try:
                await self._http_client.aclose()
            except Exception:
                pass


class AnalyzerCore:
    """Ядро анализатора кода"""

    def __init__(self):
        raw_patterns = [
            (r"DeleteAccountRequest", "Попытка удаления аккаунта", "critical"),
            (r"ResetAuthorizationRequest", "Сброс всех сеансов авторизации", "critical"),
            (r"export_session_string", "Экспорт сессии (угон аккаунта)", "critical"),
            (r"edit_2fa|edit_cloud_password", "Смена пароля 2FA", "critical"),
            (r"terminate_all_sessions", "Завершение всех сеансов", "critical"),
            (r"\.session", "Работа с .session файлом", "critical"),
            (r"os\.environ", "Чтение переменных окружения", "warning"),
            (r"os\.system", "Выполнение системных команд", "critical"),
            (r"subprocess\.Popen|subprocess\.call", "Запуск внешних процессов", "critical"),
            (r"socket\.socket", "Создание сокетов", "critical"),
            (r"send_message.*loop|for.*send_message", "Массовая рассылка сообщений (спам)", "critical"),
        ]

        self._patterns = [
            (re.compile(p, re.IGNORECASE), msg, sev) for p, msg, sev in raw_patterns
        ]

        self._async_cmd_re = re.compile(r"async\s+def\s+(\w+cmd)\s*\(")
        self._sync_cmd_re = re.compile(r"def\s+(\w+cmd)\s*\(")
        self._class_name_re = re.compile(
            r"class\s+(\w+)\s*\(\s*(?:loader\.)?Module\s*\)", re.IGNORECASE
        )
        self._strings_name_re = re.compile(
            r'strings\s*=\s*\{.*?["\']name["\']\s*:\s*["\']([^"\']+)["\']',
            re.DOTALL | re.IGNORECASE,
        )
        self._b64_zlib_re = re.compile(r"b'([A-Za-z0-9+/=]+)'")

    def _decode_base64_zlib(self, encoded_string: str) -> str:
        """Декодировать base64 + zlib"""
        try:
            decoded_bytes = base64.b64decode(encoded_string)
            decompressed_bytes = zlib.decompress(decoded_bytes)
            return decompressed_bytes.decode("utf-8")
        except Exception as e:
            logger.debug(f"Ошибка при декодировании base64+zlib: {e}")
            raise ValueError("Incorrect padding")

    def _try_decode(self, code: str) -> tuple[str, bool]:
        """Попытка декодирования обфусцированного кода"""
        if "__import__('zlib')" in code and "__import__('base64')" in code:
            match = self._b64_zlib_re.search(code)
            if match:
                try:
                    encoded_string = match.group(1)
                    decoded_code = self._decode_base64_zlib(encoded_string)
                    logger.info("Код успешно декодирован.")
                    return decoded_code, True
                except Exception:
                    logger.debug("Не удалось декодировать код — пропускаем.")
                    return code, False
        return code, False

    def _recursive_decode(self, content: str, depth: int = 0) -> str:
        """Рекурсивное декодирование"""
        if depth > 5:
            return content

        try:
            m = self._b64_zlib_re.search(content)
            if m:
                encoded_string = m.group(1)
                try:
                    decoded_bytes = base64.b64decode(encoded_string)
                    try:
                        res = zlib.decompress(decoded_bytes).decode("utf-8")
                    except zlib.error:
                        res = decoded_bytes.decode("utf-8", errors="ignore")
                    return self._recursive_decode(res, depth + 1)
                except Exception:
                    return content

            if len(content) > 100 and " " not in content[:50]:
                try:
                    res = base64.b64decode(content).decode("utf-8")
                    return self._recursive_decode(res, depth + 1)
                except Exception:
                    pass
        except Exception:
            pass

        return content

    def _extract_json_text(self, text: str) -> str | None:
        """Извлечь JSON из текста"""
        if not text or not text.strip():
            return None

        s = text.strip()
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", s, re.DOTALL | re.IGNORECASE)

        if fence_match:
            return fence_match.group(1).strip()

        start = s.find("{")
        end = s.rfind("}")

        if start != -1 and end != -1 and end > start:
            return s[start : end + 1].strip()

        return None

    def _parse_json_response(self, raw_response: str) -> dict:
        """Парсинг JSON ответа от AI"""
        if not raw_response or not raw_response.strip():
            raise Exception("Пустой ответ модели")

        try:
            return json.loads(raw_response)
        except json.JSONDecodeError as e:
            extracted = self._extract_json_text(raw_response)
            if extracted:
                try:
                    return json.loads(extracted)
                except json.JSONDecodeError as e2:
                    snippet = raw_response.strip()
                    if len(snippet) > 300:
                        snippet = snippet[:300] + "..."
                    raise Exception(f"Ошибка парсинга JSON: {e2}. Ответ: {snippet}")

            snippet = raw_response.strip()
            if len(snippet) > 300:
                snippet = snippet[:300] + "..."
            raise Exception(f"JSON не найден в ответе. Ответ: {snippet}")

    async def _generate_description(self, content: str, ai_client, config) -> dict:
        """Сгенерировать описание модуля через AI"""
        provider = config["provider"]
        model = config["model"]

        system_prompt = (
            "You are a cybersecurity expert analyzing a module for Telegram bot developers (Hikka on Telethon).\n"
            "Your task is to conduct a detailed analysis and provide a verdict.\n\n"
            "REQUIRED: Respond only with valid JSON without markdown blocks and extra text.\n\n"
            "--- NORMAL API HIKKA ---\n"
            "This is NORMAL and SAFE:\n"
            "• loader.Module, @loader.tds, @loader.command — module basics\n"
            "• utils.answer, utils.escape_html, message.edit, message.respond — text output\n"
            "• self.config, self.set, self.get — settings handling\n"
            "• client.send_message, client.download_media, client.get_entity — standard Telethon functions\n"
            "• httpx.get/post for working with external APIs (GitHub, OpenRouter and etc.)\n"
            "• Reading/writing files to temporary directories (tempfile)\n"
            "• Using inline buttons for interface\n\n"
            "--- COMMAND DEFINITION ---\n"
            "IMPORTANT! Commands in Hikka are defined as functions with the following pattern:\n"
            "• async def {name}cmd(self, message) - called as .{name}\n"
            "• Example: timercmd → command .timer, notecmd → command .note\n"
            "• DON'T add 'cmd' suffix to the command name!\n"
            "• Find ALL functions with 'cmd' suffix and add them to the list\n"
            "• Read docstring of the command for description (text after def)\n\n"
            "--- ANALYSIS FEATURES ---\n"
            "Find ALL features of the module:\n"
            "• Background tasks (@loader.loop)\n"
            "• Event handlers (watcher)\n"
            "• Working with the configuration (self.set, self.get)\n"
            "• Working with APIs (httpx, requests)\n"
            "• Inline buttons and forms\n"
            "• Automatic actions\n"
            "• Data caching\n"
            "• Working with files\n\n"
            "--- RISK SCALE ---\n"
            "1. Dangerous module ⚠️ — intentional malware:\n"
            "   • Session string, API_HASH, tokens stealing\n"
            "   • eval()/exec() with user input\n"
            "   • Obfuscated code (base64+zlib without explanation)\n"
            "   • Account deletion, session reset\n"
            "   • Sending data to suspicious servers\n\n"
            "2. At your own risk 👨‍💻 — may result in a ban:\n"
            "   • Mass broadcasts without limits\n"
            "   • Spam/waves automation\n"
            "   • Aggressive chat member parsing\n"
            "   • Bypassing Telegram API limits\n\n"
            "3. Can be installed ✅ — safely:\n"
            "   • Useful utilities, tools\n"
            "   • Informational commands\n"
            "   • Working with legitimate APIs\n"
            "   • Message processing without malware\n\n"
            "--- FORMAT OF THE RESPONSE (strict JSON) ---\n"
            "{\n"
            '  "status": "one of: Can be installed ✅ | At your own risk 👨‍💻 | Dangerous module ⚠️",\n'
            '  "purpose": "Short module description (1-2 sentences, WITHOUT commands list)",\n'
            '  "items": [\n'
            '    {"type": "command", "name": "timer", "description": "Start a timer countdown"},\n'
            '    {"type": "command", "name": "stoptimer", "description": "Stop active timer"},\n'
            '    {"type": "capability", "description": "Live timer update in the message"},\n'
            '    {"type": "capability", "description": "Support for time formats: HH:MM:SS or seconds"}\n'
            "  ],\n"
            '  "dangerous_actions": false,\n'
            '  "hidden_threats": false\n'
            "}\n\n"
            "CRITICALLY IMPORTANT:\n"
            "• In 'name' field of commands, remove 'cmd' suffix (timercmd → timer)\n"
            "• Find ALL commands (all functions with 'cmd' suffix)\n"
            "• Enumerate ALL module capabilities (minimum 3-5 for a typical module)\n"
            "• In 'purpose', write ONLY the module's overall purpose\n"
            "• Commands specify in 'items' with 'command' type\n"
            "• Additional capabilities specify with 'capability' type\n"
            "• Do NOT add extra fields to the JSON\n"
            "• Do NOT use markdown blocks around JSON"
            "• The result of the analysis is speak Russian"
        )

        user_content = f"Код модуля для анализа:\n\n```python\n{content[:30000]}\n```"

        response = await ai_client.make_api_request(
            provider, model, system_prompt, user_content, config
        )

        data = self._parse_json_response(response)
        return data


class CacheManager:
    """Менеджер кеша"""

    def __init__(self):
        self._cache_dir = os.path.join(tempfile.gettempdir(), "readfilemod_cache")
        os.makedirs(self._cache_dir, exist_ok=True)
        self._desc_cache: dict[str, str] = {}

    def _content_hash(self, content: str) -> str:
        """Получить хэш контента"""
        h = hashlib.sha256()
        h.update(content.encode("utf-8"))
        return h.hexdigest()

    def _cache_path_for_hash(self, h: str) -> str:
        """Путь к файлу кеша по хэшу"""
        return os.path.join(self._cache_dir, f"{h}.json")

    def _load_ai_cache(self, h: str) -> dict | None:
        """Загрузить из кеша"""
        path = self._cache_path_for_hash(h)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("ai_json")
            except Exception:
                return None
        return None

    def _save_ai_cache(self, h: str, ai_json: dict):
        """Сохранить в кеш"""
        path = self._cache_path_for_hash(h)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"ai_json": ai_json}, f, ensure_ascii=False)
        except Exception as e:
            logger.debug(f"Не удалось сохранить кеш: {e}")

    def _get_cache_stats(self, file_path=None) -> tuple[int, int]:
        """Получить статистику кеша"""
        total_bytes = 0
        total_files = 0

        if os.path.isdir(self._cache_dir):
            for root, dirs, files in os.walk(self._cache_dir):
                for f in files:
                    path = os.path.join(root, f)
                    try:
                        total_bytes += os.path.getsize(path)
                        total_files += 1
                    except OSError:
                        pass

        if file_path and os.path.exists(file_path):
            try:
                total_bytes += os.path.getsize(file_path)
                total_files += 1
            except OSError:
                pass

        return total_bytes, total_files

    def clear_cache(self, file_path=None):
        """Очистить кеш"""
        removed_files = 0
        removed_cache = 0

        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                removed_files += 1
            except Exception:
                pass

        if os.path.isdir(self._cache_dir):
            for filename in os.listdir(self._cache_dir):
                path = os.path.join(self._cache_dir, filename)
                try:
                    os.remove(path)
                    removed_cache += 1
                except Exception:
                    pass

        self._desc_cache.clear()
        return removed_files, removed_cache


class UIBuilder:
    """Построитель интерфейса"""

    @staticmethod
    def _split_text(text, size):
        """Разбить текст на части"""
        return [text[i : i + size] for i in range(0, len(text), size)]

    @staticmethod
    def _format_size(size: int) -> str:
        """Форматировать размер файла"""
        if size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} мб"
        elif size >= 1024:
            return f"{int(size / 1024)} кб"
        else:
            return f"{size} байт"

    async def show_page(self, module, msg_or_call, chunks, file_info, index, user_id):
        """Показать страницу с кодом"""
        if not chunks:
            text = "❌ Файл пуст."
            buttons = [[{"text": "Закрыть", "action": "close"}]]

            if isinstance(msg_or_call, Message):
                await module.inline.form(
                    text=text, message=msg_or_call, reply_markup=buttons
                )
            elif hasattr(msg_or_call, "edit"):
                await msg_or_call.edit(text=text, reply_markup=buttons)
            return

        total = len(chunks)
        index = max(0, min(index, total - 1))

        text = (
            f"📒 Страница {index + 1}/{total}\n"
            f"<pre>{utils.escape_html(chunks[index])}</pre>"
        )

        buttons = [
            [
                {
                    "text": "⬅️",
                    "callback": module._page_cb,
                    "args": (index - 1,),
                },
                {
                    "text": "➡️",
                    "callback": module._page_cb,
                    "args": (index + 1,),
                },
            ],
            [{"text": "🔍 Анализ", "callback": module._info_cb, "args": (index,)}],
            [{"text": "❌ Закрыть", "action": "close"}],
        ]

        if isinstance(msg_or_call, Message):
            await module.inline.form(
                text=text, message=msg_or_call, reply_markup=buttons
            )
        elif hasattr(msg_or_call, "edit"):
            try:
                await msg_or_call.edit(text=text, reply_markup=buttons)
            except Exception:
                await msg_or_call.answer(text=text, reply_markup=buttons)

    async def show_models_page(
        self, module, msg_or_call, models, page: int, provider: str
    ):
        """Показать страницу со списком моделей"""
        items_per_page = 5
        total_pages = (len(models) + items_per_page - 1) // items_per_page
        page = max(0, min(page, total_pages - 1))

        start = page * items_per_page
        end = start + items_per_page
        current_page_models = models[start:end]

        text = (
            f"🤖 <b>Модели {provider}</b>\n"
            f"📊 Всего доступно: <b>{len(models)}</b>\n"
            f"📄 Страница: <b>{page + 1}/{total_pages}</b>\n\n"
            f"<b>Тыкайте пробуйте модельки всякие может сработает :)</b>\n\n"
        )

        for i, m in enumerate(current_page_models, start + 1):
            text += (
                f"<b>{i}. {m['pretty_name']}</b>\n"
                f"<blockquote>ID: <code>{m['name']}</code>\n"
                f"🧠 Контекст: <b>{m['context']}</b>\n"
                f"⚙️ Установить: <code>.fcfg ReadFileMod model {m['name']}</code></blockquote>\n\n"
            )

        buttons = []
        nav_row = []

        if page > 0:
            nav_row.append(
                {
                    "text": "⬅️ Назад",
                    "callback": module._show_models_page,
                    "args": (page - 1, provider),
                }
            )

        if page < total_pages - 1:
            nav_row.append(
                {
                    "text": "Вперед ➡️",
                    "callback": module._show_models_page,
                    "args": (page + 1, provider),
                }
            )

        if nav_row:
            buttons.append(nav_row)

        buttons.append(
            [
                {
                    "text": "🔄 Обновить список",
                    "callback": module._refresh_models_cb,
                    "args": (provider,),
                }
            ]
        )
        buttons.append([{"text": "❌ Закрыть", "action": "close"}])

        if hasattr(msg_or_call, "edit") and not isinstance(msg_or_call, Message):
            await msg_or_call.edit(text, reply_markup=buttons)
        else:
            await module.inline.form(
                text=text, message=msg_or_call, reply_markup=buttons
            )

    def build_cache_stats_text(self, total_bytes, total_files, analyzed_count):
        """Построить текст статистики кеша"""
        size_str = self._format_size(total_bytes)

        text = (
            "📊 <b>Статистика кеша ReadFileMod</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Занятое место:</b> {size_str}\n"
            f"<b>Файлов в кеше:</b> {total_files}\n"
            f"<b>Проанализировано модулей:</b> {analyzed_count}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Нажми кнопку ниже, чтобы очистить кеш и временные файлы."
        )

        buttons = [
            [{"text": "🗑 Очистить", "callback": lambda: None}]
        ]

        return text, buttons

    async def show_analysis(self, module, call, data, file_info):
        """Показать результаты анализа"""
        status = data.get("status", "Ошибка анализа")
        purpose = data.get("purpose", "Нет описания")
        items = data.get("items", [])

        model = utils.escape_html(str(module.config.get("model", "")))
        name = utils.escape_html(str(file_info.get("Имя", "")))
        size = self._format_size(int(file_info.get("Размер", 0)))
        pages = file_info.get("Страниц", 0)

        text = (
            f'📋 <b>Информация о модуле</b>\n'
            f"<blockquote><b>Имя:</b> {name}\n"
            f"<b>Размер:</b> {size}\n"
            f"<b>Страниц:</b> {pages}</blockquote>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f'🔍 <b>Анализ</b>\n'
            f"<blockquote><b>Статус:</b> {utils.escape_html(str(status))}\n"
            f"<b>Модель:</b> {model}</blockquote>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f'📖 <b>Назначение модуля:</b>\n'
            f"<blockquote>{utils.escape_html(str(purpose))}</blockquote>\n"
            f'⚙️ <b>Команды и возможности:</b>\n'
        )

        lines = []
        for item in items:
            if item.get("type") == "command":
                lines.append(
                    f"• Команда «{utils.escape_html(str(item.get('name', '')))}» — {utils.escape_html(str(item.get('description', '')))}"
                )
            elif item.get("type") == "capability":
                lines.append(f"⊱ {utils.escape_html(str(item.get('description', '')))}")

        if lines:
            joined_lines = '\n'.join(lines)
            text += f"<blockquote>{joined_lines}</blockquote>"
        else:
            text += "<blockquote>Нет команд</blockquote>"

        buttons = [
            [
                {"text": "❓ Задать вопрос", "callback": module._ask_question_cb},
            ],
            [
                {"text": "↩️ Назад к коду", "callback": module._page_cb, "args": (0,)},
            ],
            [{"text": "❌ Закрыть", "action": "close"}],
        ]

        await call.edit(text, reply_markup=buttons)

    async def show_analysis_error(self, module, call, error_text, file_info):
        """Показать ошибку анализа"""
        model = utils.escape_html(str(module.config.get("model", "")))
        name = utils.escape_html(str(file_info.get("Имя", "")))
        size = self._format_size(int(file_info.get("Размер", 0)))
        pages = file_info.get("Страниц", 0)
        err = utils.escape_html(str(error_text))

        text = (
            f'📋 <b>Информация о модуле</b>\n'
            f"<blockquote><b>Имя:</b> {name}\n"
            f"<b>Размер:</b> {size}\n"
            f"<b>Страниц:</b> {pages}</blockquote>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f'🔍 <b>Анализ</b>\n'
            f"<blockquote><b>Статус:</b> ❌ Ошибка\n"
            f"<b>Модель:</b> {model}</blockquote>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f'⚠️ <b>Детали ошибки</b>\n'
            f"<blockquote>{err}</blockquote>"
        )

        buttons = [
            [
                {"text": "❓ Задать вопрос", "callback": module._ask_question_cb},
            ],
            [
                {"text": "↩️ Назад к коду", "callback": module._page_cb, "args": (0,)},
            ],
            [{"text": "❌ Закрыть", "action": "close"}],
        ]

        await call.edit(text, reply_markup=buttons)
