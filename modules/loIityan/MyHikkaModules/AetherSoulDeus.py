#          _   _                   _                __  __           _       _
#         | | | | __ _ _ __ _   _ | |_ _   _  __ _ |  \/  | ___   __| |_   _| | ___  ___
#         | |_| |/ _` | '__| | | || __| | | |/ _` || |\/| |/ _ \ / _` | | | | |/ _ \/ __|
#         |  _  | (_| | |  | |_| || |_| |_| | (_| || |  | | (_) | (_| | |_| | |  __/\__ \
#         |_| |_|\__,_|_|   \__,_|\__|\__,  |\__,_||_|  |_|\___/ \__,_|\__,_|_|\___||___/
#                                       ___/
#
#                                     © Copyright 2025
#
#                                https://t.me/HarutyaModules
#
#   🔒 Code is licensed under GNU AGPLv3
#   🌐 https://www.gnu.org/licenses/agpl-3.0.html
#   ⛔️ You CANNOT edit this file without direct permission from the Great Alchemist.
#   ⛔️ You CANNOT distribute this file if you have modified it without my divine blessing.



# meta developer: @HarutyaModules
# scope: hikka_min 3.0.0
# meta banner: https://s5.iimage.su/s/24/gX2o3bWx7NGQmNbaYFCvPy7fmMs6poj28oXpNvWJ.jpg
# requires: aiohttp

__version__ = (3, 0, 0)

from .. import loader, utils
import logging
import json
import aiohttp
import asyncio
import io
import copy
import time

logger = logging.getLogger(__name__)

@loader.tds
class AetherSoulDeusMod(loader.Module):
    """
    Божественный конструкт для Ролевого Взаимодействия (RP) V3.
    Включает: Auto-Summary (Бесконечная память), Tavern Card Import, Lorebooks.
    Сложнейшая архитектура для искушенных.
    """

    strings = {
        "name": "AetherSoulDeus",
        "no_conf": "⚙️ <b>Душа мертва без настройки.</b>\n<code>.config AetherSoulDeus</code> -> API_KEY & BASE_URL.",
        "thinking": "💠 <b>{char} ({model}) вычисляет вероятности...</b>",
        "generated": "✨ <b>{char}:</b>\n{text}",
        "error": "⚡ <b>Разрыв Эфира:</b> {}",
        "summ_start": "📜 <b>История слишком длинная.</b> Сжимаю воспоминания...",
        "summ_done": "🧠 <b>Память оптимизирована.</b> Освобождено место для новых свершений.",
        "card_loaded": "🃏 <b>Карточка TavernAI принята.</b>\nИмя: {name}\nТокенов описания: {toks}",
        "lore_stats": "📖 <b>Активные знания:</b> {count} записей.",
        "export_caption": "🔮 Экспорт состояния AetherSoul (История + Персона + Лор)",
        "stats_header": "📊 <b>Deus Status Matrix</b>\n"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "API_KEY", "", "Ключ (sk-...) от OpenRouter, OpenAI или локального LLM",
            "BASE_URL", "https://openrouter.ai/api/v1", "Точка входа API",
            "MODEL", "sao10k/l3-euryale-70b", "Основная модель для RP",
            "SUMMARY_MODEL", "meta-llama/llama-3-8b-instruct", "Модель для суммаризации (подешевле)",
            "CONTEXT_LIMIT", 15, "Сколько *пар* сообщений держать до сжатия (summary)",
            "MY_NAME", "User", "Твое имя для подстановки {{user}}",
            "TEMPERATURE", 0.85, "Хаотичность (Temperature)",
            "AUTO_SUMMARIZE", True, "Включить авто-сжатие истории?"
        )
        # Основные структуры данных
        self.history = {}       # {chat_id: [{"role":..., "content":...}]}
        self.active_state = {}  # {chat_id: {"char_name": "", "persona": "", "summary": ""}}
        self.lorebooks = {}     # {chat_id: {keyword: content}}
        self.temp_params = {}   # Временные параметры генерации

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        # Восстанавливаем данные из базы данных
        self.active_state = self.db.get(self.strings["name"], "state", {})
        self.lorebooks = self.db.get(self.strings["name"], "lore", {})
        self.history = self.db.get(self.strings["name"], "history", {})

    def _save_all(self):
        """Ритуал сохранения состояния в БД"""
        self.db.set(self.strings["name"], "state", self.active_state)
        self.db.set(self.strings["name"], "lore", self.lorebooks)
        self.db.set(self.strings["name"], "history", self.history)

    def _get_char_name(self, chat_id):
        chat_str = str(chat_id)
        if chat_str in self.active_state:
            return self.active_state[chat_str].get("char_name", "AI")
        return "AI"

    def _process_placeholders(self, text, chat_id):
        """Замена макросов {{user}} и {{char}}"""
        user_name = self.config["MY_NAME"]
        char_name = self._get_char_name(chat_id)
        text = text.replace("{{user}}", user_name).replace("{{User}}", user_name)
        text = text.replace("{{char}}", char_name).replace("{{Char}}", char_name)
        return text

    def _inject_lore(self, chat_id, text_input):
        """Поиск знаний в Лорбуке"""
        chat_str = str(chat_id)
        if chat_str not in self.lorebooks:
            return []
        
        injections = []
        for key, content in self.lorebooks[chat_str].items():
            # Поиск целого слова (границы слова \b) для точности
            if key.lower() in text_input.lower():
                processed_content = self._process_placeholders(content, chat_id)
                injections.append(processed_content)
        return injections

    async def _make_api_call(self, messages, model, max_tokens=1000):
        """Низкоуровневый вызов API через aiohttp"""
        base = self.config["BASE_URL"].rstrip("/")
        if "/chat/completions" not in base and "ollama" not in base:
            base += "/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.config['API_KEY']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Hikka-Userbot",
            "X-Title": "AetherSoul Deus"
        }

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": self.config["TEMPERATURE"],
            "stream": False
        }

        # Anti-censorship magic for OpenRouter
        if "openrouter" in base:
            payload["provider"] = {"allow_fallbacks": False}

        try:
            timeout = aiohttp.ClientTimeout(total=240)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(base, json=payload, headers=headers) as resp:
                    if resp.status != 200:
                        err = await resp.text()
                        raise ValueError(f"API {resp.status}: {err}")
                    return await resp.json()
        except Exception as e:
            logger.error(f"API Fail: {e}")
            raise e

    async def _summarize_history(self, chat_id, message_obj=None):
        """Сжатие истории (Summarization Logic)"""
        chat_str = str(chat_id)
        if chat_str not in self.history or len(self.history[chat_str]) < 4:
            return

        # Берем старую половину истории для сжатия
        full_hist = self.history[chat_str]
        # Оставляем последние 4 сообщения нетронутыми
        to_summarize = full_hist[:-4]
        to_keep = full_hist[-4:]

        text_block = "\n".join([f"{m['role']}: {m['content']}" for m in to_summarize])
        
        summ_prompt = (
            "Summarize the following roleplay conversation concisely in 3-5 sentences. "
            "Keep important facts, names, and current events. Write in 3rd person."
        )

        sys_msg = [{"role": "system", "content": summ_prompt}, {"role": "user", "content": text_block}]
        
        if message_obj:
            await utils.answer(message_obj, self.strings("summ_start"))

        try:
            # Используем (обычно) более дешевую/быструю модель для саммари
            data = await self._make_api_call(sys_msg, self.config["SUMMARY_MODEL"], max_tokens=300)
            summary_text = data["choices"][0]["message"]["content"]
            
            # Сохраняем саммари
            prev_sum = self.active_state[chat_str].get("summary", "")
            if prev_sum:
                self.active_state[chat_str]["summary"] = f"{prev_sum}\nPrevious events: {summary_text}"
            else:
                self.active_state[chat_str]["summary"] = f"Previous events: {summary_text}"

            # Обрезаем историю
            self.history[chat_str] = to_keep
            self._save_all()

            if message_obj:
                 await utils.answer(message_obj, self.strings("summ_done"))

        except Exception as e:
            if message_obj:
                await utils.answer(message_obj, f"Summary failed: {e}")

    @loader.command()
    async def aschat(self, message):
        """<текст> — Основной вход в мир Aether."""
        args = utils.get_args_raw(message)
        chat_id = message.chat_id
        chat_str = str(chat_id)

        # 1. Обработка реплая (контекст)
        reply = await message.get_reply_message()
        if reply:
            s_name = getattr(reply.sender, 'first_name', 'Unknown')
            t_content = reply.text or "[Image/Media]"
            args = f"(Replying to {s_name}: {t_content})\n{args}"

        if not args.strip():
            await utils.answer(message, "☁️")
            return

        # 2. Подготовка состояния
        if chat_str not in self.active_state:
            self.active_state[chat_str] = {"char_name": "Assistant", "persona": "You are a helpful AI.", "summary": ""}
        if chat_str not in self.history:
            self.history[chat_str] = []

        # 3. Авто-саммаризация
        if self.config["AUTO_SUMMARIZE"]:
            if len(self.history[chat_str]) > self.config["CONTEXT_LIMIT"] * 2:
                # Отправляем сообщение о начале процесса пользователю, чтобы он не ждал в тишине
                wait_msg = await utils.answer(message, self.strings("summ_start"))
                await self._summarize_history(chat_id, wait_msg) 
                # wait_msg может измениться в функции, но логика понятна
        
        # 4. Формирование Промпта
        state = self.active_state[chat_str]
        char_name = state.get("char_name", "AI")
        
        # Системный промпт = Персона + (Саммари) + (Лорбук)
        full_system = self._process_placeholders(state["persona"], chat_id)
        
        # Добавляем Summary (Память)
        if state.get("summary"):
            full_system += f"\n\n[System Note: Summary of past events:\n{state['summary']}]"
        
        # Сканируем Lorebook (по последним сообщениям + текущему)
        recent_text = args
        for m in self.history[chat_str][-3:]:
            recent_text += " " + m["content"]
            
        lore_injects = self._inject_lore(chat_id, recent_text)
        if lore_injects:
            full_system += "\n\n[World/Character Knowledge:\n" + "\n".join(lore_injects) + "]"

        # Собираем финальный массив сообщений
        messages = [{"role": "system", "content": full_system}]
        messages.extend(self.history[chat_str])
        messages.append({"role": "user", "content": args})

        # 5. Визуализация и Запрос
        ui_msg = await utils.answer(message, self.strings("thinking").format(char=char_name, model=self.config["MODEL"]))
        
        try:
            resp = await self._make_api_call(messages, self.config["MODEL"])
            
            try:
                ai_content = resp["choices"][0]["message"]["content"]
            except:
                ai_content = str(resp)

            # Сохраняем в историю
            self.history[chat_str].append({"role": "user", "content": args})
            self.history[chat_str].append({"role": "assistant", "content": ai_content})
            self._save_all()

            await utils.answer(ui_msg, ai_content)

        except Exception as e:
            logger.error(f"Fatal Deus Error: {e}")
            await utils.answer(ui_msg, self.strings("error").format(e))

    @loader.command()
    async def asimport(self, message):
        """<reply file.json> — Импорт персонажа (TavernAI/SillyTavern Spec)."""
        reply = await message.get_reply_message()
        if not reply or not reply.media:
            return await utils.answer(message, "❌ Ответь на .json файл карточки.")

        file_data = await self.client.download_file(reply.media, bytes)
        try:
            card = json.loads(file_data)
        except json.JSONDecodeError:
            return await utils.answer(message, "❌ Невалидный JSON.")

        # Парсинг формата TavernAI V2
        # (Спецификация Tavern сложная, это базовая адаптация)
        char_name = "Unknown"
        description = ""
        first_mes = ""
        scenario = ""
        
        # Попытка найти поля (структура может отличаться в V1 и V2)
        if "data" in card: # V2 structure inside PNG chunks often looks like this, or refined json
            if "name" in card["data"]:
                char_name = card["data"].get("name", "Unknown")
                description = card["data"].get("description", "")
                personality = card["data"].get("personality", "")
                scenario = card["data"].get("scenario", "")
                first_mes = card["data"].get("first_mes", "")
        elif "char_name" in card: # V1 pure JSON
            char_name = card.get("char_name", "Unknown")
            description = card.get("description", "")
            personality = card.get("personality", "")
            scenario = card.get("world_scenario", "")
            first_mes = card.get("first_mes", "")
        elif "name" in card: # Basic TextGenWebUI yaml-like json
             char_name = card.get("name", "Unknown")
             description = card.get("description", "")
             first_mes = card.get("first_mes", "")

        # Собираем богатый System Prompt
        system_prompt = (
            f"You are playing the role of {char_name}.\n"
            f"Description: {description}\n"
            f"Personality: {personality if 'personality' in locals() else ''}\n"
            f"Scenario: {scenario}\n"
            f"Write extensive, creative responses."
        )

        chat_str = str(message.chat_id)
        self.active_state[chat_str] = {
            "char_name": char_name,
            "persona": system_prompt,
            "summary": ""
        }
        
        # Устанавливаем первое сообщение
        self.history[chat_str] = []
        if first_mes:
            self.history[chat_str].append({"role": "assistant", "content": self._process_placeholders(first_mes, message.chat_id)})
            await utils.answer(message, self.strings("card_loaded").format(name=char_name, toks=len(description)) + f"\n\n💬: {first_mes}")
        else:
            await utils.answer(message, self.strings("card_loaded").format(name=char_name, toks=len(description)))
        
        self._save_all()

    @loader.command()
    async def asexport(self, message):
        """— Скачать JSON дамп текущего чата (Бэкап)."""
        chat_str = str(message.chat_id)
        dump = {
            "state": self.active_state.get(chat_str, {}),
            "history": self.history.get(chat_str, []),
            "lore": self.lorebooks.get(chat_str, {})
        }
        
        f = io.BytesIO(json.dumps(dump, indent=2, ensure_ascii=False).encode('utf-8'))
        f.name = f"AetherDeus_{chat_str}.json"
        
        await utils.answer(message, self.strings("export_caption"))
        await self.client.send_file(message.chat_id, f)

    @loader.command()
    async def asreset(self, message):
        """— Сброс саммари и истории (Оставить персону)."""
        c_id = str(message.chat_id)
        if c_id in self.history: self.history[c_id] = []
        if c_id in self.active_state: self.active_state[c_id]["summary"] = ""
        self._save_all()
        await utils.answer(message, "🧨 <b>Амнезия вызвана успешно.</b>")

    @loader.command()
    async def asstatus(self, message):
        """— Техническая информация о сессии."""
        c = str(message.chat_id)
        state = self.active_state.get(c, {})
        hist_len = len(self.history.get(c, []))
        lore_len = len(self.lorebooks.get(c, {}))
        
        summ = state.get("summary", "")
        summ_preview = (summ[:50] + "...") if summ else "Нет"
        
        info = (
            f"{self.strings('stats_header')}"
            f"👤 <b>Персона:</b> {state.get('char_name', 'None')}\n"
            f"📜 <b>История:</b> {hist_len} сообщ.\n"
            f"🧠 <b>Саммари:</b> {summ_preview}\n"
            f"📚 <b>Лорбук:</b> {lore_len} ключей\n"
            f"🤖 <b>Модель:</b> {self.config['MODEL']}\n"
            f"🧬 <b>Auto-Summ:</b> {'ON' if self.config['AUTO_SUMMARIZE'] else 'OFF'}"
        )
        await utils.answer(message, info)

    @loader.command()
    async def aslore(self, message):
        """<add/del/list> <key> [content] — Ручное управление лором."""
        args = utils.get_args_raw(message).split(maxsplit=2)
        c = str(message.chat_id)
        if c not in self.lorebooks: self.lorebooks[c] = {}
        
        if not args:
            return await utils.answer(message, "Command: .aslore list / add key text / del key")
            
        cmd = args[0].lower()
        if cmd == "list":
            res = "<b>Lorebook Keys:</b>\n" + ", ".join(self.lorebooks[c].keys())
            await utils.answer(message, res)
            
        elif cmd == "add":
            if len(args) < 3: return
            key, content = args[1], args[2]
            self.lorebooks[c][key] = content
            self._save_all()
            await utils.answer(message, f"➕ Добавлено знание о: <b>{key}</b>")
            
        elif cmd == "del":
            if len(args) < 2: return
            key = args[1]
            if key in self.lorebooks[c]:
                del self.lorebooks[c][key]
                self._save_all()
                await utils.answer(message, f"➖ Удалено: {key}")

    @loader.command()
    async def assum(self, message):
        """— Принудительно сжать историю (вызвать summary)."""

        await self._summarize_history(message.chat_id, message)




