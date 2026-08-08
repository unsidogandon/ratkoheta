# meta developer: @kotcheat
# requires: SpeechRecognition pydub

from .. import loader, utils
import logging
import io
import os
import sys
import asyncio
import subprocess
import concurrent.futures

logger = logging.getLogger(__name__)

@loader.tds
class KOTvoicetotextMod(loader.Module):
    """Модуль преобразования голосовых и видео сообщений в текст (by @kotcheat)"""

    strings = {
        "name": "KOTvoicetotext",
        "processing": "<emoji document_id=5294339927318739359>🎙</emoji> <b>Обработка...</b>",
        "error_reply": "<emoji document_id=5436113877181941026>❓</emoji> Ответьте на голосовое/видео/аудио сообщение командой!",
        "error_media": "<emoji document_id=5436113877181941026>❓</emoji> Это сообщение не содержит аудио/видео!",
        "no_speech": "<emoji document_id=5253690110561494560>🔇</emoji> Речь не распознана или аудио не содержит речи.",
        "error_request": "<emoji document_id=6037255895275015803>⚠️</emoji>️ Ошибка сервиса распознавания: {}",
        "error_general": "<emoji document_id=5316999925664347033>❌</emoji> Ошибка обработки: {}",
        "result": "<emoji document_id=6001048779803856890>💬</emoji> <b>Вывод:</b> <code>{}</code>",
        "result_with_lang": "<emoji document_id=6001048779803856890>💬</emoji> <b>Вывод (язык: {}):</b>\n<i>{}</i>",
        "installing_deps": "<emoji document_id=5256094480498436162>📦</emoji> Установка системных зависимостей (ffmpeg, flac)...",
        "deps_installed": "<emoji document_id=6021838856762954501>✅</emoji> <b>Зависимости установлены успешно!</b>",
        "deps_failed": "<emoji document_id=6037255895275015803>⚠️</emoji>️ Не удалось установить зависимости автоматически. Установите вручную: {}",
        "cfg_engine": "Движок распознавания (google/sphinx/whisper)",
        "cfg_auto_detect_lang": "<emoji document_id=6037255895275015803>⚠️</emoji>️ Автоопределение языка (может работать некорректно, рекомендуется False)",
        "cfg_fallback_language": "Язык по умолчанию для распознавания",
        "cfg_auto_delete": "Автоудаление результата через N секунд (0 = отключено)",
        "cfg_show_language": "Показывать определенный язык в результате",
        "cfg_noise_reduction": "Уровень шумоподавления (0-1000, 0 = авто)",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "engine",
                "google",
                lambda: self.strings["cfg_engine"],
                validator=loader.validators.Choice(["google", "sphinx", "whisper"]),
            ),
            loader.ConfigValue(
                "auto_detect_lang",
                False,
                lambda: self.strings["cfg_auto_detect_lang"],
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "fallback_language",
                "ru-RU",
                lambda: self.strings["cfg_fallback_language"],
            ),
            loader.ConfigValue(
                "auto_delete",
                0,
                lambda: self.strings["cfg_auto_delete"],
                validator=loader.validators.Integer(minimum=0),
            ),
            loader.ConfigValue(
                "show_language",
                True,
                lambda: self.strings["cfg_show_language"],
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "noise_reduction",
                0,
                lambda: self.strings["cfg_noise_reduction"],
                validator=loader.validators.Integer(minimum=0, maximum=1000),
            ),
        )
        self._deps_checked = False

    async def client_ready(self, client, db):
        self.client = client
        self._db = db
        
        
        await self._check_and_install_deps()

    async def _check_and_install_deps(self):
        """Проверка и автоматическая установка системных зависимостей"""
        if self._deps_checked:
            return True
            
        try:
            
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            
            
            subprocess.run(
                ["flac", "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            
            self._deps_checked = True
            logger.info("System dependencies (ffmpeg, flac) are already installed")
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("Missing system dependencies, attempting to install...")
            
            try:
                
                install_cmd = None
                
                
                if os.path.exists("/data/data/com.termux"):
                    install_cmd = ["pkg", "install", "-y", "ffmpeg", "flac"]
                elif os.path.exists("/usr/bin/apt-get"):
                    install_cmd = ["apt-get", "install", "-y", "ffmpeg", "flac"]
                elif os.path.exists("/usr/bin/apt"):
                    install_cmd = ["apt", "install", "-y", "ffmpeg", "flac"]
                elif os.path.exists("/usr/bin/yum"):
                    install_cmd = ["yum", "install", "-y", "ffmpeg", "flac"]
                elif os.path.exists("/usr/bin/dnf"):
                    install_cmd = ["dnf", "install", "-y", "ffmpeg", "flac"]
                elif os.path.exists("/usr/bin/pacman"):
                    install_cmd = ["pacman", "-S", "--noconfirm", "ffmpeg", "flac"]
                
                if install_cmd:
                    result = subprocess.run(
                        install_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=300
                    )
                    
                    if result.returncode == 0:
                        self._deps_checked = True
                        logger.info("System dependencies installed successfully")
                        return True
                    else:
                        logger.error(f"Failed to install dependencies: {result.stderr.decode()}")
                        return False
                else:
                    logger.warning("Unknown package manager, cannot auto-install")
                    return False
                    
            except Exception as e:
                logger.error(f"Error installing dependencies: {e}")
                return False

    def _detect_language(self, audio_data, recognizer):
        """Автоопределение языка в аудио"""
        
        languages = ["ru-RU", "en-US", "de-DE", "fr-FR", "es-ES", "it-IT", "pl-PL"]
        
        best_result = None
        best_confidence = 0
        detected_lang = None
        
        for lang in languages:
            try:
                
                result = recognizer.recognize_google(
                    audio_data, 
                    language=lang,
                    show_all=True
                )
                
                if result and "alternative" in result:
                    alternatives = result["alternative"]
                    if alternatives and len(alternatives) > 0:
                        confidence = alternatives[0].get("confidence", 0)
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_result = alternatives[0].get("transcript", "")
                            detected_lang = lang
                            
            except Exception:
                continue
        
        return detected_lang, best_result

    def _process_audio(self, audio_file_path, engine, auto_detect, fallback_lang, noise_level):
        """Обработка аудио с выбранным движком и автоопределением языка"""
        try:
            import speech_recognition as sr
            from pydub import AudioSegment

            
            audio = AudioSegment.from_file(audio_file_path)
            
            
            audio = audio.normalize()
            
            wav_io = io.BytesIO()
            audio.export(wav_io, format="wav")
            wav_io.seek(0)

            
            if os.path.exists(audio_file_path):
                try:
                    os.remove(audio_file_path)
                except Exception:
                    pass

            recognizer = sr.Recognizer()
            
            
            if noise_level > 0:
                recognizer.energy_threshold = noise_level
                recognizer.dynamic_energy_threshold = False
            else:
                recognizer.dynamic_energy_threshold = True

            with sr.AudioFile(wav_io) as source:
                
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = recognizer.record(source)

            detected_language = None
            text = None
            
            
            if auto_detect and engine == "google":
                detected_language, text = self._detect_language(audio_data, recognizer)
                
                
                if not text:
                    detected_language = fallback_lang
                    text = recognizer.recognize_google(audio_data, language=fallback_lang)
            else:
                
                detected_language = fallback_lang
                
                if engine == "google":
                    text = recognizer.recognize_google(audio_data, language=fallback_lang)
                elif engine == "sphinx":
                    try:
                        lang_code = fallback_lang.split("-")[0]
                        text = recognizer.recognize_sphinx(audio_data, language=lang_code)
                    except Exception:
                        
                        text = recognizer.recognize_google(audio_data, language=fallback_lang)
                        engine = "google"
                elif engine == "whisper":
                    try:
                        lang_code = fallback_lang.split("-")[0]
                        text = recognizer.recognize_whisper(audio_data, language=lang_code)
                    except Exception:
                        
                        text = recognizer.recognize_google(audio_data, language=fallback_lang)
                        engine = "google"

            return {
                "success": True, 
                "text": text, 
                "language": detected_language,
                "engine": engine
            }

        except sr.UnknownValueError:
            return {"success": False, "error": "no_speech"}
        except sr.RequestError as e:
            return {"success": False, "error": f"request_error: {str(e)}"}
        except Exception as e:
            logger.exception("Audio processing error")
            return {"success": False, "error": f"general_error: {str(e)}"}

    async def _process_message(self, message, reply_message):
        """Обработка медиа сообщения"""
        
        if not self._deps_checked:
            deps_msg = await utils.answer(message, self.strings["installing_deps"])
            deps_ok = await self._check_and_install_deps()
            
            if not deps_ok:
                await utils.answer(
                    deps_msg,
                    self.strings["deps_failed"].format("apt-get install ffmpeg flac")
                )
                return
            else:
                await utils.answer(deps_msg, self.strings["deps_installed"])
                await asyncio.sleep(1)

        
        media_type = "голосового"
        if reply_message.video_note:
            media_type = "видео-кругляша"
        elif reply_message.video:
            media_type = "видео"
        elif reply_message.audio:
            media_type = "аудио"

        processing_msg = await utils.answer(
            message,
            self.strings["processing"].format(media_type)
        )

        try:
            
            media_file = await reply_message.download_media()

            
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor,
                    self._process_audio,
                    media_file,
                    self.config["engine"],
                    self.config["auto_detect_lang"],
                    self.config["fallback_language"],
                    self.config["noise_reduction"],
                )

            
            if result["success"]:
                if self.config["show_language"] and result.get("language"):
                    response_text = self.strings["result_with_lang"].format(
                        result["language"],
                        result["text"]
                    )
                else:
                    response_text = self.strings["result"].format(result["text"])
                
                await utils.answer(processing_msg, response_text)
                
                
                if self.config["auto_delete"] > 0:
                    await asyncio.sleep(self.config["auto_delete"])
                    try:
                        await processing_msg.delete()
                    except Exception:
                        pass
            else:
                error_type = result.get("error", "")
                if error_type == "no_speech":
                    await utils.answer(processing_msg, self.strings["no_speech"])
                elif error_type.startswith("request_error"):
                    await utils.answer(
                        processing_msg,
                        self.strings["error_request"].format(error_type.split(": ", 1)[1])
                    )
                else:
                    await utils.answer(
                        processing_msg,
                        self.strings["error_general"].format(error_type.split(": ", 1)[1])
                    )

        except Exception as e:
            logger.exception("Message processing error")
            await utils.answer(processing_msg, self.strings["error_general"].format(str(e)))

    @loader.command(ru_doc="[reply] - Преобразовать голосовое/видео/аудио сообщение в текст")
    async def vttcmd(self, message):
        """[reply] - Convert voice/video/audio message to text"""
        if not message.is_reply:
            await utils.answer(message, self.strings["error_reply"])
            return

        reply_message = await message.get_reply_message()

        
        if not reply_message or not (
            reply_message.voice
            or reply_message.video_note
            or reply_message.video
            or reply_message.audio
        ):
            await utils.answer(message, self.strings["error_media"])
            return

        await self._process_message(message, reply_message)
