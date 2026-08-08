# -*- coding: utf-8 -*-

__version__ = (1, 2, 1) # Версия изменена из-за фикса бага
# meta developer: @Harutyamodules
# name: ChannelDlArchiver

from herokutl.types import Message
from .. import loader, utils
import logging
import os
from pathlib import Path
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import asyncio
import zipfile 
from typing import Optional, List

logger = logging.getLogger(__name__)

@loader.tds
class ChannelDlArchiver(loader.Module):
    """
    Модуль для скачивания всех фото и видео из Telegram-канала и
    последующей отправки их в ZIP-архиве.
    Теперь с возможностью указать количество скачиваемых медиа.
    """

    strings = {
        "name": "ChannelDlArchiver",
        "dl_channel_doc": "<channel_id_or_link> [path] [limit] - Download photos and videos from specified channel. Path and limit are optional.",
        "send_dl_doc": "[channel_id_or_link] - Archive and send downloaded media from channel. If no args, tries to archive last downloaded.",
        "download_started": "✨ Запускаю скачивание медиа из <b>{}</b>...\n\nПуть сохранения: <code>{}</code>\nЛимит медиа: <b>{}</b>",
        "channel_not_found": "🚫 Канал <b>{}</b> не найден или недоступен.",
        "no_media_found": "😕 В канале <b>{}</b> не найдено фото или видео.",
        "download_progress": "🔄 Скачано: <b>{} / {}</b> медиа из <b>{}</b>...",
        "download_finished": "✅ Скачивание из <b>{}</b> завершено!\n\nВсего скачано: <b>{}</b> медиа.\nСохранено в: <code>{}</code>",
        "download_error": "❌ Ошибка при скачивании из <b>{}</b>. Подробности в логах.",
        "media_dl_error": "⚠️ Ошибка при скачивании медиа (ID {}): {}",
        "path_created": "📁 Создана папка: <code>{}</code>",
        "archive_creating": "🗜️ Создаю архив из папки <code>{}</code>...",
        "archive_sending": "📤 Отправляю архив <b>{}</b>...",
        "archive_sent_cleaned": "✅ Архив <b>{}</b> отправлен и временные файлы удалены.",
        "archive_send_error": "❌ Ошибка при создании/отправке архива: {}.\nВременные файлы могут остаться, проверьте.",
        "archive_not_found_or_empty": "Папка <code>{}</code> не найдена или пуста для архивирования.",
        "too_many_files_for_zip": "⚠️ Слишком много файлов для одного архива или превышен лимит Telegram (2GB). Файлы остались в папке <code>{}</code>.",
        "invalid_limit": "⚠️ Неверное значение лимита: <b>{}</b>. Лимит должен быть положительным числом.",
    }

    strings_ru = {
        "dl_channel_doc": "<ID_или_ссылка_на_канал> [путь] [лимит] - Скачать фото и видео из указанного канала. Путь и лимит необязательны.",
        "send_dl_doc": "[ID_или_ссылка_на_канал] - Архивировать и отправить скачанные медиа из канала. Если без аргументов, попытается архивировать последние загруженные.",
        "download_started": "✨ Запускаю скачивание медиа из <b>{}</b>...\n\nПуть сохранения: <code>{}</code>\nЛимит медиа: <b>{}</b>",
        "channel_not_found": "🚫 Канал <b>{}</b> не найден или недоступен.",
        "no_media_found": "😕 В канале <b>{}</b> не найдено фото или видео.",
        "download_progress": "🔄 Скачано: <b>{} / {}</b> медиа из <b>{}</b>...",
        "download_finished": "✅ Скачивание из <b>{}</b> завершено!\n\nВсего скачано: <b>{}</b> медиа.\nСохранено в: <code>{}</code>",
        "download_error": "❌ Ошибка при скачивании из <b>{}</b>. Подробности в логах.",
        "media_dl_error": "⚠️ Ошибка при скачивании медиа (ID {}): {}",
        "path_created": "📁 Создана папка: <code>{}</code>",
        "archive_creating": "🗜️ Создаю архив из папки <code>{}</code>...",
        "archive_sending": "📤 Отправляю архив <b>{}</b>...",
        "archive_sent_cleaned": "✅ Архив <b>{}</b> отправлен и временные файлы удалены.",
        "archive_send_error": "❌ Ошибка при создании/отправке архива: {}.\nВременные файлы могут остаться, проверьте.",
        "archive_not_found_or_empty": "Папка <code>{}</code> не найдена или пуста для архивирования.",
        "too_many_files_for_zip": "⚠️ Слишком много файлов для одного архива или превышен лимит Telegram (2GB). Файлы остались в папке <code>{}</code>.",
        "invalid_limit": "⚠️ Неверное значение лимита: <b>{}</b>. Лимит должен быть положительным числом.",
        "_cls_doc": "Модуль для скачивания медиа из канала и их архивирования.",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "download_base_path",
                "downloads",
                lambda: "Базовый путь для сохранения скачанных медиа.",
            ),
            loader.ConfigValue(
                "progress_update_interval",
                50,
                lambda: "Обновлять сообщение о прогрессе каждые N скачанных медиа.",
            ),
            loader.ConfigValue(
                "max_zip_size_mb",
                1900,
                lambda: "Максимальный размер ZIP-архива в МБ перед отправкой (лимит Telegram ~2ГБ).",
            ),
        )
        self._last_downloaded_channel_path: Optional[Path] = None

    async def client_ready(self, client, db):
        self.client = client
    
    def _sanitize_title_for_path(self, title: str) -> str:
        """Санитизирует название для использования в имени папки."""
        sanitized = "".join(
            c for c in title if c.isalnum() or c in (" ", ".", "_", "-")
        ).strip()
        return sanitized.replace(" ", "_")

    def _get_channel_download_path(self, channel_identifier: str) -> Path:
        """
        Формирует полный путь для сохранения медиа, включая название канала.
        channel_identifier может быть username или ID.
        """
        sanitized_identifier = self._sanitize_title_for_path(channel_identifier)
        base_path = Path(self.config["download_base_path"])
        full_path = base_path / sanitized_identifier
        return full_path

    async def dlchannelcmd(self, message: Message):
        """Скачать все фото и видео из указанного канала."""
        raw_args = utils.get_args_raw(message).split()
        if not raw_args:
            await utils.answer(message, self.strings("dl_channel_doc"))
            return

        channel_id_or_link = raw_args[0]
        custom_path_str = None
        media_limit: Optional[int] = None

        # Разбираем аргументы: канал [путь] [лимит]
        # Проверяем, является ли последний аргумент числом (лимитом)
        if len(raw_args) > 1:
            try:
                parsed_limit = int(raw_args[-1]) 
                if parsed_limit > 0:
                    media_limit = parsed_limit
                    # Если лимит - последний аргумент, то путь может быть предпоследним
                    if len(raw_args) > 2: # Если аргументов больше двух, то средние - это путь
                        custom_path_str = " ".join(raw_args[1:-1])
                else:
                    await utils.answer(message, self.strings("invalid_limit").format(raw_args[-1]))
                    return
            except ValueError:
                # Если последний аргумент не число, то это весь остаток строки как путь
                custom_path_str = " ".join(raw_args[1:])
        
        # Если после разбора все еще есть только один дополнительный аргумент (и он не был лимитом), 
        # то это путь
        if len(raw_args) == 2 and media_limit is None:
             custom_path_str = raw_args[1]


        status_msg = None
        try:
            entity = await self.client.get_entity(channel_id_or_link)
            
            if custom_path_str:
                download_path = Path(custom_path_str)
            else:
                download_path = self._get_channel_download_path(entity.title or channel_id_or_link)

            if not download_path.exists():
                download_path.mkdir(parents=True, exist_ok=True)
                status_msg = await utils.answer(message, self.strings("path_created").format(download_path))
                await asyncio.sleep(1) 
            
            limit_display = str(media_limit) if media_limit is not None else "без ограничения"
            status_msg = await utils.answer(
                message,
                self.strings("download_started").format(entity.title, download_path, limit_display)
            )

            total_media_found = 0
            downloaded_count = 0
            
            logger.info(f"Начинаю скачивание медиа из канала {entity.title} (лимит: {limit_display})...")
            
            # Итерируем по сообщениям канала с учетом лимита
            # Telethon.iter_messages сам принимает аргумент limit
            async for msg in self.client.iter_messages(entity, reverse=True, limit=media_limit): 
                if msg.photo or (msg.document and msg.document.mime_type and msg.document.mime_type.startswith(("video/", "image/"))):
                    total_media_found += 1 

                    file_name = None
                    if msg.photo:
                        file_name = f"photo_{msg.id}.jpg"
                    elif msg.document and msg.document.mime_type.startswith("video/"):
                        file_name = getattr(msg.document, "file_name", f"video_{msg.id}.mp4")
                    elif msg.document and msg.document.mime_type.startswith("image/"):
                        file_name = getattr(msg.document, "file_name", f"image_{msg.id}.gif")
                        
                    if not file_name: 
                        file_name = f"media_{msg.id}"
                        
                    full_file_path = download_path / file_name

                    try:
                        await self.client.download_media(msg, file=full_file_path)
                        downloaded_count += 1
                        
                        if downloaded_count % self.config["progress_update_interval"] == 0:
                            # ИСПРАВЛЕНИЕ: Используем status_msg.edit вместо utils.edit_message
                            await status_msg.edit(
                                self.strings("download_progress").format(
                                    downloaded_count, total_media_found, entity.title
                                )
                            )
                            await asyncio.sleep(0.5) 
                    except Exception as e:
                        logger.error(self.strings("media_dl_error").format(msg.id, e))

            if downloaded_count == 0 and total_media_found == 0:
                # ИСПРАВЛЕНИЕ: Используем status_msg.edit
                await status_msg.edit(self.strings("no_media_found").format(entity.title))
            else:
                # ИСПРАВЛЕНИЕ: Используем status_msg.edit
                await status_msg.edit(
                    self.strings("download_finished").format(entity.title, downloaded_count, download_path)
                )
            
            self._last_downloaded_channel_path = download_path 

        except Exception as e:
            logger.error(f"Error in dlchannelcmd: {e}")
            if status_msg:
                # ИСПРАВЛЕНИЕ: Используем status_msg.edit в блоке обработки ошибок
                await status_msg.edit(self.strings("download_error").format(channel_id_or_link))
            else:
                await utils.answer(message, self.strings("channel_not_found").format(channel_id_or_link))

    async def senddlcmd(self, message: Message):
        """Архивирует и отправляет скачанные медиа в ZIP-файле."""
        args = utils.get_args_raw(message).split(maxsplit=1)
        
        target_path: Optional[Path] = None
        if args:
            channel_identifier = args[0]
            if Path(channel_identifier).is_dir():
                target_path = Path(channel_identifier)
            else:
                target_path = self._get_channel_download_path(channel_identifier)
        else:
            target_path = self._last_downloaded_channel_path

        if not target_path or not target_path.exists() or not any(target_path.iterdir()):
            await utils.answer(message, self.strings("archive_not_found_or_empty").format(target_path or "неизвестная папка"))
            return

        zip_filename = f"{self._sanitize_title_for_path(target_path.name)}_media.zip"
        zip_filepath = Path(zip_filename) 

        status_msg = await utils.answer(message, self.strings("archive_creating").format(target_path))

        try:
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
                for file_in_dir in target_path.iterdir():
                    if file_in_dir.is_file():
                        zipf.write(file_in_dir, arcname=file_in_dir.name) 

            if zip_filepath.stat().st_size > self.config["max_zip_size_mb"] * 1024 * 1024:
                # ИСПРАВЛЕНИЕ: Используем status_msg.edit
                await status_msg.edit(
                    self.strings("too_many_files_for_zip").format(target_path)
                )
                zip_filepath.unlink(missing_ok=True) 
                return

            # ИСПРАВЛЕНИЕ: Используем status_msg.edit
            await status_msg.edit(self.strings("archive_sending").format(zip_filename))
            
            await self.client.send_file(
                message.peer_id, 
                file=str(zip_filepath),
                caption=f"✅ Архив медиа из {target_path.name}"
            )
            
            # ИСПРАВЛЕНИЕ: Используем status_msg.edit
            await status_msg.edit(self.strings("archive_sent_cleaned").format(zip_filename))

        except Exception as e:
            logger.error(f"Error creating/sending archive: {e}")
            # ИСПРАВЛЕНИЕ: Используем status_msg.edit в блоке обработки ошибок
            await status_msg.edit(self.strings("archive_send_error").format(e))
        finally:
            zip_filepath.unlink(missing_ok=True)
            if target_path.exists():
                 for file_in_dir in target_path.iterdir():
                    if file_in_dir.is_file():
                        file_in_dir.unlink(missing_ok=True)
                 try:
                     target_path.rmdir() 
                 except OSError:
                     logger.warning(f"Could not remove directory {target_path}, it might not be empty.")