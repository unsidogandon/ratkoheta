# meta developer: @coddan
import io
import re
import os
import asyncio
import aiohttp
from .. import loader, utils

@loader.tds
class TikTokAudioMod(loader.Module):
    """Модуль для скачивания звука из TikTok и извлечения аудио из видео сообщений"""
    
    strings = {
        "name": "TikTokAudio",
        "no_url": "<b>❌ Укажите ссылку на TikTok видео или ответьте на видео для извлечения звука.</b>",
        "downloading": "<b>⏳ Обрабатываю...</b>",
        "error": "<b>❌ Ошибка:</b> <code>{}</code>",
        "not_found": "<b>❌ Не удалось найти или скачать аудио.</b>"
    }

    @loader.command(ru_doc="<ссылка/ответ на видео> - Скачать/извлечь звук")
    async def ttaudiocmd(self, message):
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()
        
        text_to_search = args or ""
        if not text_to_search and reply and reply.raw_text:
            text_to_search = reply.raw_text

        url_match = re.search(r'(https?://(?:www\.|vm\.|vt\.)?tiktok\.com/[^\s]+)', text_to_search)
        
        if url_match:
            url = url_match.group(1)
            message = await utils.answer(message, self.strings("downloading"))
            try:
                async with aiohttp.ClientSession() as session:
                    api_url = "https://www.tikwm.com/api/"
                    async with session.post(api_url, data={"url": url}) as resp:
                        if resp.status != 200:
                            return await utils.answer(message, self.strings("error").format(f"HTTP {resp.status}"))
                        
                        data = await resp.json()
                        
                        if data.get("code") != 0 or "data" not in data or "music" not in data["data"]:
                            return await utils.answer(message, self.strings("not_found"))
                            
                        music_url = data["data"]["music"]
                        music_title = data["data"].get("music_info", {}).get("title", "tiktok_audio")
                        music_author = data["data"].get("music_info", {}).get("author", "Unknown")
                        
                        async with session.get(music_url) as music_resp:
                            if music_resp.status != 200:
                                return await utils.answer(message, self.strings("error").format(f"Audio HTTP {music_resp.status}"))
                                
                            music_bytes = await music_resp.read()
                            
                audio_file = io.BytesIO(music_bytes)
                audio_file.name = f"{music_author} - {music_title}.mp3"
                
                caption = f"<b>🎵 Звук из TikTok</b>\n👤 <b>Автор:</b> <code>{music_author}</code>\n📝 <b>Название:</b> <code>{music_title}</code>"
                await utils.answer_file(message, audio_file, caption=caption)
            except Exception as e:
                await utils.answer(message, self.strings("error").format(str(e)))
            return

        # Если нет ссылки, но есть ответ на видео
        if reply and (reply.video or (reply.document and reply.document.mime_type and reply.document.mime_type.startswith("video/"))):
            message = await utils.answer(message, self.strings("downloading"))
            try:
                video_path = await message.client.download_media(reply)
                if not video_path:
                    return await utils.answer(message, self.strings("error").format("Не удалось скачать видео"))
                
                audio_path = os.path.splitext(video_path)[0] + ".mp3"
                
                process = await asyncio.create_subprocess_exec(
                    "ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "libmp3lame", "-q:a", "2", audio_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                
                if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                    await message.client.send_file(
                        message.chat_id,
                        audio_path,
                        caption="<b>🎵 Извлечённый звук из видео</b>",
                        reply_to=reply.id
                    )
                    await message.delete()
                else:
                    await utils.answer(message, self.strings("error").format("Не удалось конвертировать видео (возможно, ffmpeg не установлен)"))
                
                for path in [video_path, audio_path]:
                    if os.path.exists(path):
                        os.remove(path)
            except Exception as e:
                await utils.answer(message, self.strings("error").format(str(e)))
            return

        # Если ни ссылки, ни видео в ответе нет
        await utils.answer(message, self.strings("no_url"))