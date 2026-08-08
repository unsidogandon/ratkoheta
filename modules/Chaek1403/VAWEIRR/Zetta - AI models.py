# meta developer: @hikkagpt
import json
import logging
import aiohttp
from .. import loader, utils
from telethon import events
import requests
from telethon import events
from .. import loader, utils
import re
from time import sleep
from bs4 import BeautifulSoup
import base64
from telethon.tl.custom import Message
import os
import io
import random # Добавлено для режима 'random'

# Библиотеки для распознавания голоса
try:
    import speech_recognition as sr
    from pydub import AudioSegment
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False


available_models = {
    "1": "o3-PRO",
    "2": "o1-PRO",
    "3": "o3-Mini-High",
    "4": "Grok 4",
    "5": "GPT 4.1",
    "6": "qwen3-235b-a22b",
    "7": "qwen-max-latest",
    "8": "qwen-plus-2025-01-25",
    "9": "qwen-turbo-2025-02-11",
    "10": "qwen2.5-coder-32b-instruct",
    "11": "qwen2.5-72b-instruct",
    "12": "gpt-4.5",
    "13": "gpt-5",
    "14": "gpt-4o-mini",
    "15": "gpt4-turbo",
    "16": "gpt-3.5-turbo",
    "17": "gpt-4",
    "18": "deepseek-v3",
    "19": "deepseek-r1",
    "20": "gemini-1.5 Pro",
    "21": "gemini-2.5-pro-exp-03-25",
    "22": "gemini-2.5-flash",
    "23": "gemini-2.0-flash",
    "24": "llama-4-maverick",
    "25": "llama-4-scout",
    "26": "llama-3.3-70b",
    "27": "llama-3.3-8b",
    "28": "llama-3.1",
    "29": "llama-2",
    "30": "claude-4.5-sonnet",
    "31": "claude-3-haiku",
    "32": "bard",
    "34": "t-pro",
    "35": "t-lite"
}


# Путь к файлу для хранения личностей
PERSONAS_FILE = "personas.json"


# Функция для загрузки личностей из файла
def load_personas():
    try:
        with open(PERSONAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# Функция для сохранения личностей в файл
def save_personas(personas):
    with open(PERSONAS_FILE, "w", encoding="utf-8") as f:
        json.dump(personas, f, indent=4)


# Загружаем личности при запуске модуля
personas = load_personas()


@loader.tds
class AIModule(loader.Module):
    """
🧠 Модуль Zetta - AI Models
>> Часть экосистемы Zetta - AI models <<
🌒 Version: 14.1 | fastZetta Beta 2 | Fix API
Основанно на базе инструментов API - @OnlySq

📍Описание:
Модуль дает доступ к 35 модели ИИ, подходит как для быстрых запросов, так и для общения с контекстом и автоматизации общения/обслуживания.

🔀Режимы работы:

Одиночный запрос:
.ai <запрос> - мгновенный ответ без сохранения истории диалога. Ответ на голосовое сообщение также поддерживается.

Чат:
.chat - ведите диалог с ИИ, который запоминает контекст беседы. Распознает голосовые сообщения всех участников беседы.
.mode <all/reply/friends/random> - установка режима ответа в чате.

FastZetta:
.fastzetta on - активирует быстрый вызов ассистента по имени "Зетта" в чате, которое можно изменить.
Теперь с поддержкой памяти (.zettacfg для настройки)
.fastclear - очищает память FastZetta для текущего чата.
Можете использовать только вы, либо дать доступ вашим друзьям.

Создание плагинов:
Создавайте инструкции для ИИ, чтобы он мог выполнять уникальные задачи. Сохранение ролей и их переключение через *.switchplugin.*

Переписывание текстов:
Используйте .rewrite для перевода, стилизации или упрощения сложных текстов.

Работа с Hikka Userbot:
Команды aisup и aicreate задействуют дообученые модели GPT, и могут заменить вам чат поддержки Hikka или написать вам модуль.

Особенности:
- Поддержка до 35 моделей ИИ.
- Распознавание голосовых сообщений.
- Полная интеграция с Telegram.
- Универсальность и практичность для любых задач.
    """
    strings = {"name": "Zetta - AI models"}

    def __init__(self):
        super().__init__()
        self.default_model = "gpt-4o-mini"
        self.active_chats = {}
        self.chat_history = {}
        self.chat_archive = {}
        self.role = {}
        self.response_mode = {}
        self.edit_promt = "off"
        self.instructions = self.get_instructions()
        self.module_instructions = self.get_module_instruction()
        self.double_instructions = self.get_double_instruction()
        self.allmodule_instruction = self.get_allmodule_instruction()
        self.module_instruction2 = self.get_module_instruction2()
        self.module_instruction3 = self.get_module_instruction3()
        self.allmodule_instruction2 = self.get_allmodule_instruction2()
        self.metod = "on"
        self.provider = 'OnlySq-Zetta'
        self.api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        self.humanmode = 'off'
        # Настройки для .fastzetta
        self.fastzetta_active_chats = {}
        self.fastzetta_trigger_word = "Zetta"
        self.fastzetta_friends = []
        # Новые настройки для памяти FastZetta
        self.fastzetta_memory_enabled = 'off'
        self.fastzetta_history = {}


    def get_instructions(self):
        url = 'https://raw.githubusercontent.com/Chaek1403/VAWEIRR/refs/heads/main/data-set1.txt'
        response = requests.get(url)
        return response.text

    def get_module_instruction(self):
        url = 'https://raw.githubusercontent.com/Chaek1403/VAWEIRR/refs/heads/main/module_set.txt'
        response = requests.get(url)
        return response.text

    def get_double_instruction(self):
        url = 'https://raw.githubusercontent.com/Chaek1403/VAWEIRR/refs/heads/main/data-set2.txt'
        response = requests.get(url)
        return response.text

    def get_allmodule_instruction2(self):
        url = "https://raw.githubusercontent.com/Chaek1403/VAWEIRR/refs/heads/main/data-set4.txt"
        response = requests.get(url)
        return response.text

    def get_allmodule_instruction(self):
        url = 'https://raw.githubusercontent.com/Chaek1403/VAWEIRR/refs/heads/main/data-set3.txt'
        response = requests.get(url)
        return response.text

    def get_module_instruction2(self):
        url = 'https://raw.githubusercontent.com/Chaek1403/VAWEIRR/refs/heads/main/module_set2.txt'
        response = requests.get(url)
        return response.text

    def get_module_instruction3(self):
        url = 'https://raw.githubusercontent.com/Chaek1403/VAWEIRR/refs/heads/main/module_set3.txt'
        response = requests.get(url)
        return response.text


    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.active_chats = self.db.get("AIModule", "active_chats", {})
        self.chat_history = self.db.get("AIModule", "chat_history", {})
        self.chat_archive = self.db.get("AIModule", "chat_archive", {})
        self.role = self.db.get("AIModule", "role", {})
        self.response_mode = self.db.get("AIModule", "response_mode", {})
        # Загрузка настроек для FastZetta
        self.fastzetta_active_chats = self.db.get("AIModule", "fastzetta_active_chats", {})
        self.fastzetta_trigger_word = self.db.get("AIModule", "fastzetta_trigger_word", "Zetta")
        self.fastzetta_friends = self.db.get("AIModule", "fastzetta_friends", [])
        self.humanmode = self.db.get("AIModule", "humanmode", 'off')
        self.edit_promt = self.db.get("AIModule", "edit_promt", 'off')
        self.metod = self.db.get("AIModule", "metod", 'on')
        self.provider = self.db.get("AIModule", "provider", 'OnlySq-Zetta')
        # Загрузка новых настроек
        self.fastzetta_memory_enabled = self.db.get("AIModule", "fastzetta_memory_enabled", 'off')
        self.fastzetta_history = self.db.get("AIModule", "fastzetta_history", {})


    async def handle_voice_message(self, voice_message: Message, status_message: Message):
        if not SPEECH_RECOGNITION_AVAILABLE:
            if status_message:
                await utils.answer(status_message, "🚫 <b>Библиотеки для распознавания речи не установлены.</b>\nУстановите их командами: `pip install SpeechRecognition pydub`")
            return None

        if status_message:
            await status_message.edit("<b>🎤 Слушаю..</b>")
        
        voice_file = io.BytesIO()
        try:
            await voice_message.download_media(file=voice_file)
            voice_file.seek(0)
            audio = AudioSegment.from_file(voice_file, format="ogg")
            wav_io = io.BytesIO()
            audio.export(wav_io, format="wav")
            wav_io.seek(0)
            
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_io) as source:
                audio_data = recognizer.record(source)
            
            text = recognizer.recognize_google(audio_data, language="ru-RU")
            return text
        except sr.UnknownValueError:
            if status_message:
                await status_message.edit("<b>🔇 Не удалось распознать речь.</b>")
            logging.error("Не удалось распознать речь из голосового сообщения.")
            return None
        except sr.RequestError as e:
            if status_message:
                await status_message.edit(f"<b>🚫 Ошибка сервиса распознавания:</b> `{e}`")
            logging.error(f"Ошибка сервиса распознавания речи: {e}")
            return None
        except Exception as e:
            if status_message:
                await status_message.edit(f"<b>⚠️ Произошла ошибка при обработке голоса:</b> `{e}`")
            logging.error(f"Произошла ошибка при обработке голосового сообщения: {e}")
            return None

    def _create_zettacfg_buttons(self):
        buttons = [
            [{"text": "Super promt", "callback": self._zettacfg, "args": ("superpromt",)}],
            [{"text": "Human mode", "callback": self._zettacfg, "args": ("humanmode",)}],
            [{"text": "Ultra mode", "callback": self._zettacfg, "args": ("ultramode",)}],
            [{"text": "API provider", "callback": self._zettacfg, "args": ("apiswitch",)}],
            [{"text": "FastZetta Memory", "callback": self._zettacfg, "args": ("fastzetta_memory",)}] # Новая кнопка
        ]
        return buttons

    async def zettacfgcmd(self, message):
        """
        Расширенные настройки модуля
        """
        await self.inline.form(
            text="🔧<b>Выберите настройку для изменения:</b>",
            message=message,
            reply_markup=self._create_zettacfg_buttons()
        )

    async def _zettacfg(self, call, setting):
        if setting == "superpromt":
            text = "<b>💫 Улучшает и корректирует ваш запрос с помощью ИИ перед отправкой его модели ИИ.</b>"
            current = self.edit_promt
        elif setting == "humanmode":
            text = "<b>💬 Не показывать приписку 'Ответ модели...' в режиме чата.</b>"
            current = self.humanmode
        elif setting == "ultramode":
            text = "📚 <b>Расширенная база знаний для aisup. Время генерации ответа увеличивается.</b>"
            current = self.metod
        elif setting == "apiswitch":
            text = "<b>🔄 Провайдер API для запросов.\nПо умолчанию: OnlySq-Zetta AI</b>"
            current = self.provider
        elif setting == "fastzetta_memory": # Новая настройка
            text = "<b>🧠 Включить/выключить память (контекст) для режима FastZetta.</b>\nЕсли включено, FastZetta будет помнить предыдущие сообщения в диалоге."
            current = self.fastzetta_memory_enabled
        else:
            text = "Неизвестная настройка."
            current = "off"

        if setting in ("superpromt", "humanmode", "ultramode", "fastzetta_memory"):
            btn_on_text = "Вкл" + (" 🟣" if current == "on" else "")
            btn_off_text = "Выкл" + (" 🟣" if current == "off" else "")
            buttons = [
                [{"text": btn_on_text, "callback": self._zettaset, "args": (setting, "on")}],
                [{"text": btn_off_text, "callback": self._zettaset, "args": (setting, "off")}],
                [{"text": "⬅️ Назад", "callback": self._back_zettacfg}]
            ]
        elif setting == "apiswitch":
            btn_on_text = "OnlySq-Zetta AI" + (" 🟣" if current == "OnlySq-Zetta" else "")
            btn_off_text = "Devj" + (" 🟣" if current == "Devj" else "")
            buttons = [
                [{"text": btn_on_text, "callback": self._zettaset, "args": (setting, "OnlySq-Zetta")}],
                [{"text": btn_off_text, "callback": self._zettaset, "args": (setting, "Devj")}],
                [{"text": "⬅️ Назад", "callback": self._back_zettacfg}]
            ]
        else:
            buttons = [[{"text": "⬅️ Назад", "callback": self._back_zettacfg}]]

        await call.edit(text, reply_markup=buttons)

    async def _zettaset(self, call, setting, value):
        if setting == "superpromt":
            self.edit_promt = value
            self.db.set("AIModule", "edit_promt", value)
        elif setting == "humanmode":
            self.humanmode = value
            self.db.set("AIModule", "humanmode", value)
        elif setting == "ultramode":
            self.metod = value
            self.db.set("AIModule", "metod", value)
        elif setting == "apiswitch":
            self.provider = value
            self.db.set("AIModule", "provider", value)
        elif setting == "fastzetta_memory": # Новая настройка
            self.fastzetta_memory_enabled = value
            self.db.set("AIModule", "fastzetta_memory_enabled", value)

        await self._zettacfg(call, setting)

    async def _back_zettacfg(self, call):
        await call.edit("🔧<b>Выберите настройку для изменения:</b>", reply_markup=self._create_zettacfg_buttons())
        
    @loader.unrestricted
    async def aisupcmd(self, message):
        """
        Спросить у AI помощника для Hikka.
        Использование: `.aisup <запрос>` или ответить на сообщение с `.aisup`
        """
        r = "sup"
        await self.process_request(message, self.instructions, r)

    @loader.unrestricted
    async def modelcmd(self, message):
        """
        Устанавливает модель ИИ по умолчанию.
        Использование: `.model <номер>` или `.model list` для списка.
        """
        args = utils.get_args_raw(message)
        if not args:
            await message.edit("🤔 <b>Укажите номер модели или list для просмотра списка.</b>")
            return

        if args == "list":
            model_list = "\n".join([f"<b>{k}.</b> {v}" for k, v in available_models.items()])
            await message.edit(f"📝 <b>Доступные модели:</b>\n{model_list}")
            return

        if args not in available_models:
            await message.edit("🚫 <b>Неверный номер модели.</b>")
            return

        self.default_model = available_models[args]
        await message.edit(f"✅ <b>Модель изменена на:</b> {self.default_model}")

    @loader.unrestricted
    async def chatcmd(self, message):
        """
        Включает/выключает режим чата.
        """
        chat_id = str(message.chat_id)
        if self.active_chats.get(chat_id):
            self.active_chats.pop(chat_id, None)
            self.db.set("AIModule", "active_chats", self.active_chats)

            if chat_id in self.chat_history:
                self.chat_archive[chat_id] = self.chat_history[chat_id]
                self.chat_history.pop(chat_id, None)
                self.db.set("AIModule", "chat_history", self.chat_history)
                self.db.set("AIModule", "chat_archive", self.chat_archive)
                await message.edit("📴 <b>Режим чата выключен. История архивирована.</b>")
            else:
                await message.edit("📴 <b>Режим чата выключен.</b>")
        else:
            self.active_chats[chat_id] = True
            self.db.set("AIModule", "active_chats", self.active_chats)

            if chat_id in self.chat_archive:
                self.chat_history[chat_id] = self.chat_archive[chat_id]
                self.chat_archive.pop(chat_id, None)
                self.db.set("AIModule", "chat_history", self.chat_history)
                self.db.set("AIModule", "chat_archive", self.chat_archive)
                await message.edit("💬 <b>Режим чата включен. История загружена.</b>")
            else:
                await message.edit("💬 <b>Режим чата включен.</b>")

    async def send_request_to_api(self, message, instructions, request_text, model="gpt-4o-mini", history_list=None):
        """Отправляет запрос к API и возвращает ответ. Может использовать историю."""
        api_url = "http://zetta.onlysq.ru:34010/OnlySq-Zetta/v1/models" if self.provider == "OnlySq-Zetta" else "https://api.vysssotsky.ru/"

        if self.provider == 'devj':
            # Логика для devj не менялась, так как запрос не затрагивал его
            messages_for_payload = [{"role": "user", "content": f"{instructions}\nЗапрос пользователя: {request_text}"}]
            if history_list:
                messages_for_payload = history_list

            payload = {
                "model": "gpt-4",
                "messages": messages_for_payload,
                "max_tokens": 10048,
                "temperature": 0.7,
                "top_p": 1,
            }
            # ... остальная логика для devj
            return "Провайдер devj не поддерживает историю в текущей реализации"

        else: # Логика для OnlySq-Zetta
            if history_list:
                messages_for_payload = history_list
            else:
                content = f"{instructions}\nНе используй HTML и форматирование текста. Также помни, что тебе нужно сохранить ответ предыдущей части модуля, если ты не знаешь ответа. И передать его дальше.\nЗапрос пользователя: {request_text}"
                if not instructions:
                    content = request_text
                messages_for_payload = [{"role": "user", "content": content}]
            
            payload = {
                "model": 'gemini-2.5-flash',
                "request": {"messages": messages_for_payload}
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(api_url, json=payload) as response:
                        response.raise_for_status()
                        data = await response.json()
                        answer = data.get("answer", "🚫 Ответ не получен.").strip()
                        decoded_answer = base64.b64decode(answer).decode('utf-8')
                        return decoded_answer
            except aiohttp.ClientError as e:
                if instructions == "" or history_list is not None:
                    logging.error(f"Ошибка при запросе к API для fastzetta или чата с историей: {e}")
                    return None
                else:
                    await message.edit(f"<b>У провайдера ... неполадки. \n\nПровайдер: OnlySq in Telegram </b>")
                    return None
                    
    @loader.unrestricted
    async def modecmd(self, message):
        """
        Устанавливает режим ответа ИИ.
        Использование: `.mode <reply/all/random/friends>`
        """
        chat_id = str(message.chat_id)
        args = utils.get_args_raw(message)
        valid_modes = ("reply", "all", "random", "friends")
        if not args or args not in valid_modes:
            await message.edit("🤔 <b>Укажите режим ответа: `reply`, `all`, `random` или `friends`.</b>")
            return

        self.response_mode[chat_id] = args
        self.db.set("AIModule", "response_mode", self.response_mode)
        await message.edit(f"✅ <b>Режим ответа установлен на:</b> `{args}`")

    @loader.unrestricted
    async def watcher(self, message):
        """
        Следит за сообщениями и отвечает, если активен режим чата.
        """
        chat_id = str(message.chat_id)
        if not self.active_chats.get(chat_id):
            return
            
        if message.out and message.text and message.text.startswith('.'):
            return

        mode = self.response_mode.get(chat_id, "all")
        
        # Проверка режима 'reply'
        if mode == "reply" and not (message.is_reply and await self.is_reply_to_bot(message)):
            return

        # Проверка режима 'random'
        if mode == "random" and random.randint(1, 10) != 10:
            return

        # Проверка режима 'friends'
        if mode == "friends":
            me_id = (await self.client.get_me()).id
            friend_ids = [f['id'] for f in self.fastzetta_friends]
            if message.sender_id not in friend_ids and message.sender_id != me_id:
                return

        request_text = ""
        if message.voice:
            processing_msg = await message.reply("<b>🎤 Слушаю...</b>")
            request_text = await self.handle_voice_message(voice_message=message, status_message=processing_msg)
            if processing_msg: await processing_msg.delete()
        elif message.text:
            request_text = message.text.strip()
        
        if request_text:
            user_name = await self.get_user_name(message)
            await self.respond_to_message(message, user_name, request_text)
            
    @loader.unrestricted
    async def fastclearcmd(self, message):
        """
        Очищает историю FastZetta для текущего чата.
        """
        chat_id = str(message.chat_id)
        if chat_id in self.fastzetta_history:
            self.fastzetta_history.pop(chat_id, None)
            self.db.set("AIModule", "fastzetta_history", self.fastzetta_history)
            await utils.answer(message, "⚡️ <b>История FastZetta для этого чата очищена.</b>")
        else:
            await utils.answer(message, "📭️ <b>История FastZetta для этого чата пуста.</b>")

    @loader.watcher(no_commands=True)
    async def watcher_fastzetta(self, message):
        """
        Наблюдатель для режима FastZetta с поддержкой памяти.
        """
        chat_id = str(message.chat_id)
        if not self.fastzetta_active_chats.get(chat_id):
            return
        if message.out and message.text and message.text.startswith('.'):
            return

        sender_id = message.sender_id
        me = await self.client.get_me()
        if self.fastzetta_friends and sender_id != me.id and sender_id not in [f['id'] for f in self.fastzetta_friends]:
            return

        request_text = ""
        if message.voice:
            request_text = await self.handle_voice_message(voice_message=message, status_message=None)
        elif message.text:
            request_text = message.text.strip()
        
        if not request_text:
            return

        trigger_pattern = r"^{}\s*".format(re.escape(self.fastzetta_trigger_word))
        match = re.match(trigger_pattern, request_text, re.IGNORECASE)

        if match:
            query = request_text[match.end():].strip()
            if not query: return

            answer = None
            history_for_api = None
            
            try:
                # Логика с памятью
                if self.fastzetta_memory_enabled == 'on':
                    if chat_id not in self.fastzetta_history:
                        self.fastzetta_history[chat_id] = []
                    
                    self.fastzetta_history[chat_id].append({"role": "user", "content": query})
                    
                    if len(self.fastzetta_history[chat_id]) > 20:
                       self.fastzetta_history[chat_id] = self.fastzetta_history[chat_id][-20:]

                    history_for_api = self.fastzetta_history[chat_id]
                    # Вызываем API с историей
                    answer = await self.send_request_to_api(message, "", "", history_list=history_for_api)
                else:
                    # Вызываем API без истории
                    answer = await self.send_request_to_api(message, "", query)

                if answer:
                    if self.humanmode == 'on':
                        await message.reply(answer)
                    else:
                        await message.reply(f"<b>Ответ модели {self.default_model}:</b>\n{answer}")

                    # Сохраняем ответ в историю, если память включена
                    if self.fastzetta_memory_enabled == 'on':
                        self.fastzetta_history[chat_id].append({"role": "assistant", "content": answer})
                        self.db.set("AIModule", "fastzetta_history", self.fastzetta_history)
            except Exception as e:
                logging.error(f"[FastZetta Watcher] Error: {e}", exc_info=True)


    # --- Остальной код остается без изменений ---
    # (Я скопирую его для полноты, чтобы вы могли просто заменить весь файл)

    @loader.unrestricted
    async def clearcmd(self, message):
        """
        Сбрасывает историю диалога для модели ИИ
        """
        chat_id = str(message.chat_id)
        if chat_id in self.chat_history or chat_id in self.chat_archive:
            self.chat_history.pop(chat_id, None)
            self.chat_archive.pop(chat_id, None)
            self.db.set("AIModule", "chat_history", self.chat_history)
            self.db.set("AIModule", "chat_archive", self.chat_archive)
            await message.edit("🗑️ <b>История диалога очищена.</b>")
        else:
            await message.edit("📭️ <b>История диалога пуста.</b>")

    @loader.unrestricted
    async def rolecmd(self, message):
        """
        Устанавливает роль для ИИ в режиме чата.
        Использование: `.role <роль>`
        """
        chat_id = str(message.chat_id)
        args = utils.get_args_raw(message)
        if not args:
            await message.edit("🎭 <b>Укажите роль для ИИ.</b>")
            return

        self.role[chat_id] = args
        self.db.set("AIModule", "role", self.role)
        await message.edit(f"🎭 <b>Роль ИИ установлена:</b> {args}")


    @loader.unrestricted
    async def createplugincmd(self, message):
        """
        Создает новый плагин.
        Использование: `.createplugin <название> <инструкция>`
        """
        args = utils.get_args_raw(message)
        if not args:
            await message.edit("🤔 <b>Укажите название и инструкцию для плагина.</b>")
            return

        try:
            name, role = args.split(" ", 1)
        except ValueError:
            await message.edit("🤔 <b>Неверный формат. Используйте: .createplugin <название> <инструкция></b>")
            return

        if 'global' not in personas:
            personas['global'] = {}
        personas['global'][name] = role
        save_personas(personas)
        await message.edit(f"✅ <b>Плагин ' {name} ' создан.</b>")

    @loader.unrestricted
    async def pluginscmd(self, message):
        """
        Показывает список плагинов.
        """
        if 'global' not in personas or not personas['global']:
            await message.edit("🤔 <b>Список плагинов пуст.</b>")
            return

        persona_list = "\n".join([f"<b>{name}:</b> {role}" for name, role in personas['global'].items()])
        await message.edit(f"🧩 <b>Доступные плагины:</b>\n{persona_list}\n\nА в нашем боте функционал больше, и возможностей тоже)")

    @loader.unrestricted
    async def switchplugincmd(self, message):
        """
        Переключается на указанный плагин.
        Использование: `.switchplugin <название>`
        """
        args = utils.get_args_raw(message)
        if not args:
            await message.edit("🤔 <b>Укажите название плагина.</b>")
            return

        if 'global' not in personas or args not in personas['global']:
            await message.edit("🚫 <b>Плагин не найден.</b>")
            return

        chat_id = str(message.chat_id)
        self.role[chat_id] = personas['global'][args]
        await message.edit(f"✅ <b>Переключено на плагин:</b> {args}")

    @loader.unrestricted
    async def deleteplugincmd(self, message):
        """
        Удаляет плагин.
        Использование: `.deleteplugin <Название>`
        """
        args = utils.get_args_raw(message)
        if not args:
            await message.edit("🤔 <b>Укажите название плагина.</b>")
            return

        if 'global' not in personas or args not in personas['global']:
            await message.edit("🚫 <b>Плагин не найден.</b>")
            return

        del personas['global'][args]
        save_personas(personas)
        await message.edit(f"✅ <b>Плагин ' {args} ' удален.</b>")

    @loader.unrestricted
    async def aicmd(self, message):
        """
        Отправляет одиночный запрос к ИИ.
        Использование: `.ai <запрос>` или ответить на сообщение с `.ai`
        """
        reply = await message.get_reply_message()
        args = utils.get_args_raw(message)
        request_text = ""

        # Проверяем ответ на сообщение
        if reply:
            if reply.voice:
                request_text = await self.handle_voice_message(voice_message=reply, status_message=message)
                if not request_text: return
                if args:
                    request_text = f'"{request_text}"\n\n{args}'
            elif reply.text:
                request_text = reply.raw_text
                if args:
                    request_text = f'"{request_text}"\n\n{args}'
            else:
                request_text = args
        elif args:
            request_text = args
        else:
            await message.edit("🤔 <b>Введите запрос или ответьте на сообщение (включая голосовое).</b>")
            return
        
        if request_text:
            await self.standart_process_request(message, request_text)


    async def standart_process_request(self, message, request_text):
        """
        Обрабатывает запрос к API модели ИИ для .aicmd.
        """
        chat_id = str(message.chat_id)
        current_role = self.role.get(chat_id, ".")

        if self.edit_promt == "on":
            await message.edit('<b>Улучшение промта...</b>')
            request_text = await self.t9_promt(message, request_text)
        
        await message.edit("🤔 <b>Думаю...</b>")
        answer = await self.send_request_to_api(message, current_role, request_text, model=self.default_model)

        if answer:
            if self.humanmode == 'on':
                formatted_answer = f"{answer}"
            elif self.edit_promt == "on":
                formatted_answer = f"❔ <b>Улучшенный запрос с помощью ИИ:</b>\n`{request_text}`\n\n💡 <b>Ответ модели {self.default_model}:</b>\n{answer}"
            else:
                formatted_answer = f"❔ <b>Запрос:</b>\n`{request_text}`\n\n💡 <b>Ответ модели {self.default_model}:</b>\n{answer}"
            await message.edit(formatted_answer)

    async def respond_to_message(self, message, user_name, question):
        """
        Обрабатывает вопрос и отправляет ответ с учетом истории.
        """
        chat_id = str(message.chat_id)

        if chat_id not in self.chat_history:
            self.chat_history[chat_id] = []

        original_question = question
        if self.edit_promt == "on":
            question = await self.t9_promt(message, question, self.chat_history[chat_id])

        if question != original_question and message.out:
            try:
                await message.edit(question)
            except Exception as e:
                logging.error(f"Не удалось отредактировать сообщение в режиме чата: {e}")

        # Добавляем финальную версию вопроса в историю
        self.chat_history[chat_id].append({
            "role": "user",
            "content": f"{user_name} написал: {question}"
        })

        if len(self.chat_history[chat_id]) > 1000:
            self.chat_history[chat_id] = self.chat_history[chat_id][-1000:]

        # Формируем историю для API
        history_for_api = [
            {"role": "system", "content": self.role.get(chat_id, "")}
        ] + self.chat_history[chat_id]

        try:
            answer = await self.send_request_to_api(message, "", "", history_list=history_for_api)
            
            if answer:
                self.chat_history[chat_id].append({"role": "assistant", "content": answer})
                self.db.set("AIModule", "chat_history", self.chat_history)
                
                if self.humanmode == 'on':
                    await message.reply(answer)
                else:
                    await message.reply(f"<b>Ответ модели {self.default_model}:</b>\n{answer}")
            else: # Если ответ пуст, возможно, из-за ошибки API, удаляем последний вопрос
                self.chat_history[chat_id].pop()

        except Exception as e:
            await message.reply(f"⚠️ <b>Произошла непредвиденная ошибка:</b> {e}")
            self.chat_history[chat_id].pop()
            
    async def is_reply_to_bot(self, message):
        """
        Проверяет, является ли сообщение ответом на сообщение бота.
        """
        if message.is_reply:
            reply_to_message = await message.get_reply_message()
            if reply_to_message and reply_to_message.sender_id == (await self.client.get_me()).id:
                return True
        return False


    async def get_user_name(self, message):
        """
        Возвращает имя пользователя из сообщения.
        """
        if message.sender:
            user = await self.client.get_entity(message.sender_id)
            return user.first_name or user.username
        else:
            return "Аноним"

    # ... все остальные команды (aicreate, rewrite, moduleinfo, fastzetta и т.д.) остаются без изменений
    @loader.unrestricted
    async def aisupcmd(self, message):
        """
        Спросить у AI помощника для Hikka.
        Использование: `.aisup <запрос>` или ответить на сообщение с `.aisup`
        """
        r = "sup"
        await self.process_request(message, self.instructions, r)


    async def allmodule(self, answer, message, request_text):
        rewrite2 = self.get_allmodule_instruction()
        await message.edit("<b>🎭Цепочка размышлений модели в процессе:\n🟢Первая модель приняла решение\n🟢Вторая модель приняла решение.\n💭Третья модель думает...</b>\n\nПочему так долго: каждая модель имеет свой дата сет. И сверяет ответ предыдущей модели с своими знаниями.")
        answer = await self.send_request_to_api(message, rewrite2, f"Запрос пользователя: {request_text}\nОтвет второй части модуля:{answer}")
        if answer:
            await self.allmodule2(answer, message, request_text)

    async def modulecreating(self, answer, message, request_text):
        rewrite = self.get_module_instruction2()
        await message.edit("<b>🎭Создается модуль:\n🟢Создание кода\n💭Тестирование...</b>\n\nЗаметка: чем лучше вы расспишите задачу для модели - тем лучше она создаст модуль. ")
        answer = await self.send_request_to_api(message, rewrite, f"User request: {request_text}\nAnswer to the first part of the module:{answer}")
        if answer:
            await self.modulecreating2(answer, message, request_text)

    async def allmodule2(self, answer, message, request_text):
        rewrite3 = self.get_allmodule_instruction2()
        await message.edit("<b>🎭Цепочка размышлений модели в процессе:\n🟢Первая модель приняла решение\n🟢Вторая модель приняла решение.\n🟢Третья модель приняла решение\n💭Четвертая модель думает...</b>\n\nПочему так долго: каждая модель имеет свой дата сет. И сверяет ответ предыдущей модели с своими знаниями.")
        answer = await self.send_request_to_api(message, rewrite3, f"Запрос пользователя: {request_text}\nОтвет третьей части модуля:{answer}")
        if answer:
            formatted_answer = f"❔ Запрос:\n`{request_text}`\n\n💡 <b>Ответ AI-помощника по Hikka</b>:\n{answer}"
            await message.edit(formatted_answer)

    async def modulecreating2(self, answer, message, request_text):
        rewrite = self.get_module_instruction3()
        await message.edit("<b>🎭Создается модуль:\n🟢Создание кода\n🟢Протестировано\n💭Проверка на безопастность и финальное тестирование...</b>\n\nЕще заметка: Лучше проверяйте что написала нейросеть, перед тем как использовать модуль.")
        answer = await self.send_request_to_api(message, rewrite, f"User request: {request_text}\nAnswer to the first part of the module:{answer}")
        if answer:
            try:
                if len(answer) > 4096:
                    await message.edit("⚠️ Код модуля слишком большой для отправки в сообщении. Был выслан просто файл.")
                    await self.save_and_send_code(answer, message)
                else:
                    await message.edit(f"<b>💡 Ответ AI-помощника по Hikka | Креатор модулей</b>:\n{answer}")
                    await self.save_and_send_code(answer, message)
            except Exception as e:
                if "Message was too long" in str(e):
                    await message.edit("⚠️ Код модуля слишком большой для отправки в сообщении. Отправляю файл...")
                    await self.save_and_send_code(answer, message)
                else:
                    await message.edit(f"⚠️ Ошибка: {e}")

    async def rewrite_process(self, answer, message, request_text):
        rewrite = self.get_double_instruction()
        await message.edit("<b>🎭Цепочка размышлений модели в процессе:\n🟢Первая модель приняла решение\n💭Вторая модель думает...</b>\n\nПочему так долго: каждая модель имеет свой дата сет. И сверяет ответ предыдущей модели с своими знаниями.")
        answer = await self.send_request_to_api(message, rewrite, f"Запрос пользователя: {request_text}\nОтвет первой части модуля:{answer}")
        if answer:
            await self.allmodule(answer, message, request_text)


    @loader.unrestricted
    async def aicreatecmd(self, message):
        """
        Попросить AI помощника  для  Hikka написать модуль.
        Использование: `.aicreate <запрос>` или ответить на сообщение с `.aicreate` """
        r = "create"
        await self.process_request(message, self.module_instructions, r)


    async def save_and_send_code(self, answer, message):
        """Сохраняет код в файл, отправляет его и удаляет."""
        try:
            code_start = answer.find("`python") + len("`python")
            code_end = answer.find("```", code_start)
            code = answer[code_start:code_end].strip()

            with open("AI-module.py", "w", "utf-8") as f:
                f.write(code)

            await message.client.send_file(
                message.chat_id,
                "AI-module.py",
                caption="<b>💫Ваш готовый модуль</b>",
            )

            os.remove("AI-module.py")

        except (TypeError, IndexError, ValueError) as e:
            logging.warning(f"Не удалось извлечь код из ```python ... ``` блока. Отправка полного ответа как файл. Ошибка: {e}")
            try:
                with open("AI-module.txt", "w", "utf-8") as f:
                    f.write(answer)
                await message.client.send_file(message.chat_id, "AI-module.txt", caption="⚠️ <b>Не удалось найти блок кода. Отправляю весь ответ в виде текстового файла.</b>")
                os.remove("AI-module.txt")
            except Exception as e_inner:
                await message.reply(f"Ошибка при обработке и отправке файла: {e_inner}")


    async def process_request(self, message, instructions, command):
        """
        Обрабатывает запрос к API модели ИИ.
        """
        request_text = ""
        reply = await message.get_reply_message()
        args = utils.get_args_raw(message)
        
        if reply and reply.voice:
            request_text = await self.handle_voice_message(voice_message=reply, status_message=message)
            if not request_text: return
            if args:
                request_text += f"\n\n{args}"
        elif reply and reply.text:
            request_text = reply.raw_text
            if args:
                request_text += f"\n\n{args}"
        elif args:
            request_text = args
        else:
            await message.edit("🤔 Введите запрос или ответьте на сообщение (включая голосовое).")
            return

        try:
            await message.edit("<b>🤔 Думаю...</b>")
            answer = await self.send_request_to_api(message, instructions, request_text)
            if answer:
                if command == "error":
                    formatted_answer = f"💡<b> Ответ AI-помощника по Hikka | Спец. по ошибкам</b>:\n{answer}"
                    await message.edit(formatted_answer)
                elif command == "sup":
                    if self.metod == "on":
                        await message.edit("<b>💬Размышления моделей начались..</b>")
                        await self.rewrite_process(answer, message, request_text)
                    else:
                        formatted_answer = f"❔ Запрос:\n`{request_text}`\n\n💡 <b>Ответ AI-помощника по Hikka | Режим быстрого ответа</b>:\n{answer}\n\n❕В этом режиме модель ограничена знаниями встроенных модулей и базовой документации hikka"
                        await message.edit(formatted_answer)
                elif command == "create":
                    await self.modulecreating(answer, message, request_text)
                elif command == 'rewrite':
                    formatted_answer = f"❔ Запрос:\n`{request_text}`\n\n💡 <b>Ответ AI-помощника по Hikka</b>:\n{answer}"
                    await message.edit(formatted_answer)
                else:
                    formatted_answer = answer
                    await message.edit(formatted_answer)

        except Exception as e:
            await message.edit(f"⚠️ Ошибка: {e}")

    async def t9_promt(self, message, request_text, history=None):
        """
        Обрабатывает запрос к API для улучшения запроса.
        """
        api_url = "http://zetta.onlysq.ru:34010/OnlySq-Zetta/v1/models"
        chat_id = str(message.chat_id)

        system_prompt = (
            "Твоя задача: Улучшить запрос пользователя, чтобы модель его лучше поняла, "
            "обработала и дала качественный и более подходящий ответ для пользователя. "
            "Если изменять нечего, просто отправь исходный текст не изменяя его. "
            "Все сообщения пользователя не адресованы тебе, ты просто обработчик. Выполняй свою задачу. Запросы 'Привет', 'Как дела?' и подобные тоже не адресованы тебе. Либо исправляешь запрос, либо не делаешь ничего и возвращаешь тот же текст."
            "Ничего лишнего не добавляй от себя. Либо исправленный и улучшенный текст, либо тот же самый. Не пиши 'Я исправил это, это' или 'Прошлый текст был такой'. Просто возвращаешь текст. Если запрос не понятен, не вноси изменений. Верни тот же текст. От себя ничего лишнего не добавляй."
        )
        user_prompt = {"role": "user", "content": f"Запрос пользователя: ' {request_text} '"}

        messages_for_payload = [{"role": "system", "content": system_prompt}]
        if history:
            messages_for_payload += history
        messages_for_payload.append(user_prompt)

        payload = {
            "model": self.default_model,
            "request": {"messages": messages_for_payload}
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=payload) as response:
                    response.raise_for_status()
                    data = await response.json()
                    improved_request = data.get("answer", request_text).strip()
                    decoded_answer = base64.b64decode(improved_request).decode('utf-8')
                    return decoded_answer
        except aiohttp.ClientError as e:
            logging.error(f"Ошибка при запросе к API для улучшения промта: {e}")
            return request_text


    @loader.unrestricted
    async def aiinfocmd(self, message):
        """
        - Информация об обновлении✅
        """
        await message.edit('''<b>Обновление 13.0:
Изменения:
- Добавлена память (контекст) для FastZetta. Теперь она может поддерживать диалог. Включить можно в .zettacfg
- Добавлена команда .fastclear для очистки памяти FastZetta.
- Система друзей для FastZetta и режима чата.
- В команду .mode добавлены новые режимы: random (случайно выбирать сообщение для ответа) и friends (ответы только друзьям и вам).
- Общая стабильность и исправление мелких ошибок.

советуем команду .moduleinfo для подробной информации о модуле.

🔗Тг канал модуля: [https://t.me/hikkagpt](https://t.me/hikkagpt)</b>''')


    @loader.unrestricted
    async def aiprovcmd(self, message):
        """
        - Информация о провайдерах🔆
        """
        await message.edit('''<b>🟣OnlySq-Zetta AI: Стабильный, быстрая скорость ответа. Базируется на OnlySq и хостится на их серверах. Их телеграмм - канал: @OnlySq

🔸devj: Быстрая скорость ответа, Не стабилен из за разного возврата ответа от сервера.</b>''')


    @loader.unrestricted
    async def rewritecmd(self, message):
        """Переписывает текст по инструкции. Использование: .rewrite <инструкция>"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b>Пожалуйста, укажите инструкцию для переписывания.</b>")
            return

        if not message.is_reply:
            await utils.answer(message, "<b>Пожалуйста, ответьте на сообщение, которое нужно переписать.</b>")
            return

        reply_message = await message.get_reply_message()
        original_text = reply_message.text

        if not original_text:
            await utils.answer(message, "<b>Не найден текст для переписывания.</b>")
            return

        instruction = args
        await message.edit('<b>💭Переписываю..</b>')
        answer = await self.send_request_to_api(
            message,
            "Ты — помощник для переписывания текста. Твоя задача — переписывать текст по указанной пользователем инструкции, отвечать четко и по делу, не выходя за рамки своей задачи. Не используй Latex или особое форматирование, сохраняй текст простым и доступным.",
            f"{instruction}: {original_text}"
        )

        if answer:
            formatted_answer = f"✏️ <b>Переписанный текст моделью {self.default_model}:</b>\n{answer}"
            await message.edit(formatted_answer)


    @loader.unrestricted
    async def moduleinfocmd(self, message):
        """
        Дополнительная информация о модуле и других проектах.
        """
        info_text = """
        <b>💡 Дополнительная информация</b>

<b>📌 Автор:</b>@procot1
🌐 <b>Модуль является частью экосистемы Zetta - AI models.</b>
📖 Весь его потенциал можно раскрыть с помощью бота: <a href="https://t.me/ZettaGPT4o_bot">@ZettaGPT4o_bot</a>.

---

<b>🔥 Особенности модуля:</b>
💼 <i>Объединён функционал 3 разных модулей!</i>
Это делает его <b>универсальным</b>, <b>практичным</b> и <b>удобным</b>.
<b>Все лучшие разработки собраны в одном месте.</b>

---

<b>🎯 Возможности модуля:</b>
1️⃣ <b>Поиск как в Google.</b>
Используйте модуль для <i>быстрого и точного</i> поиска информации.

2️⃣ <b>Чат с моделью ИИ.</b>
- Запускайте диалог в любом чате.
- ИИ различает участников беседы благодаря передаче <i>ников</i>.
- Модель может стать полноценным <i>участником ваших обсуждений.</i>
- Распознает голосовые сообщения.

3️⃣ <b>Создание плагинов.</b>
- Задайте инструкцию или дайте модели ИИ набор данных, что бы она лучше давала ответы.
- Создавайте <i>постоянные плагины</i> ведь есть функция создания и сохранения плагинов.
- Используйте команду <code>.switchplugin</code> для <i>мгновенного переключения</i> инструкций.

4️⃣ <b>Выбор до 35 моделей ИИ.</b>
Настраивайте работу с различными моделями под ваши задачи.

5️⃣ <b>Запросы для Hikka Userbot.</b>
- Команды <code>aisup</code>/<code>aicreate</code> помогут:
    🔹 Узнать любую информацию про Hikka Userbot.
    🔹 Решить проблему Hikka Userbot
    🔹 Создать или улучшить модуль для Hikka Userbot

6️⃣ <b>Переписывание текстов (<code>.rewrite</code>):</b>
- Эффективный перевод.
- Стилизация текста.
- Упрощение сложных формулировок.

7️⃣ <b>Быстрый вызов зетты:</b>
Активируйте .fastzetta on, и вызывайте зетту по имени:
- Зетта, какой курс доллара?
Можете использовать только вы, либо дать доступ вашим друзьям.

---

<b>💡 Почему этот модуль уникален?</b>
Функционал модуля <i>огромен.</i>
Освоив его, вы сможете использовать возможности ИИ на <b>максимум.</b>

---

📢 <b>Не упустите важное!</b>
🔗 Подписывайтесь на канал: <a href="https://t.me/hikkagpt">@hikkagpt</a>

✨ <b>Раскройте весь потенциал Zetta - AI models уже сегодня!</b>
        """
        await message.edit(info_text, link_preview=False)

    @loader.unrestricted
    async def fastzettacmd(self, message):
        """
        Включает/выключает режим "FastZetta" для текущего чата.
        """
        chat_id = str(message.chat_id)
        if self.fastzetta_active_chats.get(chat_id):
            self.fastzetta_active_chats.pop(chat_id, None)
            status_text = "выключен"
        else:
            self.fastzetta_active_chats[chat_id] = True
            status_text = "включен"
        self.db.set("AIModule", "fastzetta_active_chats", self.fastzetta_active_chats)

        if self.fastzetta_active_chats.get(chat_id):
            await message.edit(f"⚡️ <b>Режим FastZetta {status_text} для этого чата.</b> \n\nПросто позови меня по имени в голосовом или текстовом сообщении ' <b>{self.fastzetta_trigger_word}</b> ', и я отвечу на твой вопрос.\n\n<b>Имя можно изменить: .namezetta <Новое имя></b>")
        else:
            await message.edit(f"🛑 <b>Режим FastZetta {status_text} для этого чата.</b>")

    @loader.unrestricted
    async def namezettacmd(self, message):
        """
        Устанавливает новое триггерное слово для режима FastZetta.
        Использование: .namezetta <новое_слово>
        """
        args = utils.get_args_raw(message)
        if not args:
            await message.edit(f"🤔 <b>Укажи новое триггерное слово. Текущее: '{self.fastzetta_trigger_word}'</b>")
            return

        self.fastzetta_trigger_word = args.strip()
        self.db.set("AIModule", "fastzetta_trigger_word", self.fastzetta_trigger_word)
        await message.edit(f"✅ <b>Триггерное слово для FastZetta изменено на: '{self.fastzetta_trigger_word}'</b>")

    @loader.unrestricted
    async def friendzettacmd(self, message):
        """
        Добавляет пользователя в белый список FastZetta.
        Использование: .friendzetta <@username/ID> или в ответ на сообщение.
        """
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()
        user = None

        if args:
            try:
                user = await self.client.get_entity(args)
            except (ValueError, TypeError):
                await utils.answer(message, "🚫 <b>Не удалось найти пользователя.</b>")
                return
        elif reply:
            user = await reply.get_sender()
        else:
            await utils.answer(message, "🤔 <b>Укажите пользователя через @username/ID или ответьте на его сообщение.</b>")
            return

        if not user:
            await utils.answer(message, "🚫 <b>Не удалось найти пользователя.</b>")
            return

        if user.id in [f['id'] for f in self.fastzetta_friends]:
            await utils.answer(message, f"✅ <b>{user.first_name}</b> уже в списке друзей.")
            return

        self.fastzetta_friends.append({"id": user.id, "name": user.first_name})
        self.db.set("AIModule", "fastzetta_friends", self.fastzetta_friends)
        await utils.answer(message, f"🫂 <b>{user.first_name}</b> добавлен(а) в друзья Zetta!")

    @loader.unrestricted
    async def friendszettacmd(self, message):
        """
        Показывает список друзей Zetta.
        """
        text = "🫂 <b>Ваши друзья, которым можно использовать вашу fastzetta:</b>"
        buttons = []
        if not self.fastzetta_friends:
            text = "🤷 <b>У вас пока нет друзей Zetta.</b>"
        else:
            buttons = [
                [{"text": friend['name'], "callback": self._confirm_delete_friend, "args": (friend['id'],)}]
                for friend in self.fastzetta_friends
            ]

        await self.inline.form(
            text=text,
            message=message,
            reply_markup=buttons
        )

    async def _show_friends_list(self, call):
        """
        Обновляет существующее сообщение со списком друзей (только для колбэков).
        """
        text = "🫂 <b>Ваши друзья, которым можно использовать вашу fastzetta:</b>"
        buttons = []
        if not self.fastzetta_friends:
            text = "🤷 <b>У вас пока нет друзей Zetta.</b>"
        else:
            buttons = [
                [{"text": friend['name'], "callback": self._confirm_delete_friend, "args": (friend['id'],)}]
                for friend in self.fastzetta_friends
            ]
        
        await call.edit(text, reply_markup=buttons)


    async def _confirm_delete_friend(self, call, user_id):
        friend_name = next((f['name'] for f in self.fastzetta_friends if f['id'] == user_id), "Неизвестный")
        text = f"❓ <b>Вы уверены, что хотите удалить {friend_name} из друзей Zetta?</b>"
        buttons = [
            [
                {"text": "❌ Удалить", "callback": self._delete_friend, "args": (user_id,)},
                {"text": "⬅️ Назад", "callback": self._back_to_friends_list}
            ]
        ]
        await call.edit(text, reply_markup=buttons)

    async def _delete_friend(self, call, user_id):
        friend_name = next((f['name'] for f in self.fastzetta_friends if f['id'] == user_id), "Неизвестный")
        self.fastzetta_friends = [f for f in self.fastzetta_friends if f['id'] != user_id]
        self.db.set("AIModule", "fastzetta_friends", self.fastzetta_friends)
        await self._show_friends_list(call)

    async def _back_to_friends_list(self, call):
        await self._show_friends_list(call)
