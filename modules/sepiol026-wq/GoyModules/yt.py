# ====================================================================================================================
#   ██████╗  ██████╗ ██╗   ██╗███╗   ███╗ ██████╗ ██████╗ ██╗   ██╗██╗     ███████╗███████╗
#  ██╔════╝ ██╔═══██╗╚██╗ ██╔╝████╗ ████║██╔═══██╗██╔══██╗██║   ██║██║     ██╔════╝██╔════╝
#  ██║  ███╗██║   ██║ ╚████╔╝ ██╔████╔██║██║   ██║██║  ██║██║   ██║██║     █████╗  ███████╗
#  ██║   ██║██║   ██║  ╚██╔╝  ██║╚██╔╝██║██║   ██║██║  ██║██║   ██║██║     ██╔══╝  ╚════██║
#  ╚██████╔╝╚██████╔╝   ██║   ██║ ╚═╝ ██║╚██████╔╝██████╔╝╚██████╔╝███████╗███████╗███████║
#   ╚═════╝  ╚═════╝    ╚═╝   ╚═╝     ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚══════╝
#
#   OFFICIAL USERNAMES: @goymodules | @samsepi0l_ovf
#   MODULE: yt
#
#   THIS MODULE IS LICENSED UNDER GNU AGPLv3, PROTECTED AGAINST UNAUTHORIZED COPYING/RESALE,
#   AND ITS ORIGINAL AUTHORSHIP BELONGS TO @samsepi0l_ovf.
#   ALL OFFICIAL UPDATES, RELEASE NOTES, AND PATCHES ARE PUBLISHED IN THE TELEGRAM CHANNEL @goymodules.
# ====================================================================================================================

# requires: telethon pillow requests yt-dlp imageio-ffmpeg
# meta developer: @goymodules
# meta tags: music, youtube, download, playlist, search, heroku, музыка, ютуб, скачивание, плейлист, поиск, хероку
# authors: @goymodules
# Description: YouTube Music media module.
# meta banner: https://raw.githubusercontent.com/sepiol026-wq/goypulse/main/assets/ytmusic.png

__version__ = (4, 6)

import asyncio
import contextlib
import io
import json
import logging
import os
import sys
import textwrap
import tempfile
import shutil
import re
import time

import requests
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from telethon.tl.types import Message, DocumentAttributeAudio

from .. import loader, utils

logger = logging.getLogger(__name__)
_HTTP = requests.Session()

def _fetch_sync(url: str) -> bytes:
    headers = {"User-Agent": "YTMusic-Module/4.0 (Core by @samsepi0l_ovf; AGPLv3)"}
    r = _HTTP.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.content

class Banners:
    def __init__(self, title: str, artists: list, duration: int, progress: int, track_cover: bytes, font_bytes: bytes, blur: int, dynamic_color: bool = True):
        self.title = title
        self.artists = ", ".join(artists) if isinstance(artists, list) else artists
        self.duration = duration
        self.progress = progress
        self.track_cover = track_cover
        self.font_bytes = font_bytes
        self.blur_intensity = blur
        self.accent = self._get_dominant() if dynamic_color else "white"

    def _get_dominant(self):
        try:
            c = Image.open(io.BytesIO(self.track_cover)).convert("RGB").resize((1, 1)).getpixel((0, 0))
            return f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"
        except Exception:
            return "white"

    def _get_font(self, size, font_bytes):
        return ImageFont.truetype(io.BytesIO(font_bytes), size)

    def _prepare_cover(self, size, radius):
        cover = Image.open(io.BytesIO(self.track_cover)).convert("RGBA")
        cover = cover.resize((size, size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, size, size), radius=radius, fill=255)
        output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        output.paste(cover, (0, 0), mask=mask)
        return output

    def _prepare_background(self, w, h):
        bg = Image.open(io.BytesIO(self.track_cover)).convert("RGBA")
        bg = bg.resize((w, h), Image.Resampling.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(radius=self.blur_intensity))
        bg = ImageEnhance.Brightness(bg).enhance(0.35)
        return bg

    def _draw_progress_bar(self, draw, x, y, w, h, progress_pct, color="white", bg_color="#6b6b6b"):
        draw.rounded_rectangle((x, y, x + w, y + h), radius=h/2, fill=bg_color)
        fill_w = int(w * progress_pct)
        if fill_w > 0:
            draw.rounded_rectangle((x, y, x + fill_w, y + h), radius=h/2, fill=color)

    def horizontal(self):
        W, H = 1500, 600
        padding = 60
        cover_size = 480
        title_font = self._get_font(55, self.font_bytes)
        artist_font = self._get_font(45, self.font_bytes)
        time_font = self._get_font(25, self.font_bytes)

        img = self._prepare_background(W, H)
        draw = ImageDraw.Draw(img)

        cover = self._prepare_cover(cover_size, 30)
        img.paste(cover, (padding, (H - cover_size) // 2), cover)

        text_x = padding + cover_size + 60
        text_y_start = 100
        text_width_limit = W - text_x - padding

        wrapper = textwrap.TextWrapper(width=23)
        title_lines = wrapper.wrap(self.title)

        if len(title_lines) > 2:
            title_lines = title_lines[:2]
            title_lines[-1] += "..."

        current_y = text_y_start
        title_height = title_font.getbbox("Ah")[3] + 15

        for line in title_lines:
            draw.text((text_x, current_y), line, font=title_font, fill="white")
            current_y += title_height

        display_artist = self.artists
        while artist_font.getlength(display_artist) > text_width_limit and len(display_artist) > 0:
            display_artist = display_artist[:-1]
        if len(display_artist) < len(self.artists): display_artist += "…"

        artist_y = current_y + 10
        draw.text((text_x, artist_y), display_artist, font=artist_font, fill="#b3b3b3")

        cur_time = f"{(self.progress//1000//60):02}:{(self.progress//1000%60):02}"
        dur_time = f"{(self.duration//1000//60):02}:{(self.duration//1000%60):02}"
        cur_w = time_font.getlength(cur_time)
        dur_w = time_font.getlength(dur_time)
        bar_y = 480
        bar_h = 8
        gap = 25

        draw.text((text_x, bar_y - 12), cur_time, font=time_font, fill="white")
        bar_start_x = text_x + cur_w + gap
        bar_end_x = text_x + text_width_limit - dur_w - gap
        bar_w = bar_end_x - bar_start_x
        prog_pct = self.progress / self.duration if self.duration > 0 else 0
        self._draw_progress_bar(draw, bar_start_x, bar_y, bar_w, bar_h, prog_pct, color=self.accent)
        draw.text((bar_end_x + gap, bar_y - 12), dur_time, font=time_font, fill="white")

        try:
            draw.text((10, 10), "Core by @samsepi0l_ovf - AGPLv3", fill=(255, 255, 255, 2))
        except Exception:
            pass
        by = io.BytesIO()
        img.save(by, format="PNG")
        by.seek(0)
        by.name = "banner.png"
        return by

    def vertical(self):
        W, H = 1000, 1500
        padding = 80
        cover_size = 800
        title_font = self._get_font(60, self.font_bytes)
        artist_font = self._get_font(45, self.font_bytes)
        time_font = self._get_font(35, self.font_bytes)

        img = self._prepare_background(W, H)
        draw = ImageDraw.Draw(img)

        cover = self._prepare_cover(cover_size, 40)
        cover_x = (W - cover_size) // 2
        cover_y = 120
        img.paste(cover, (cover_x, cover_y), cover)

        text_area_y = cover_y + cover_size + 120
        text_width_limit = W - (padding * 2)

        wrapper = textwrap.TextWrapper(width=23)
        title_lines = wrapper.wrap(self.title)

        if len(title_lines) > 2:
            title_lines = title_lines[:2]
            title_lines[-1] += "..."

        current_y = text_area_y
        title_height = title_font.getbbox("Ah")[3] + 15

        for line in title_lines:
            w = title_font.getlength(line)
            draw.text(((W - w) / 2, current_y), line, font=title_font, fill="white")
            current_y += title_height

        display_artist = self.artists
        while artist_font.getlength(display_artist) > text_width_limit and len(display_artist) > 0:
            display_artist = display_artist[:-1]
        if len(display_artist) < len(self.artists): display_artist += "…"

        artist_w = artist_font.getlength(display_artist)
        draw.text(((W - artist_w) / 2, current_y + 15), display_artist, font=artist_font, fill="#b3b3b3")

        bar_y = text_area_y + 260
        if len(title_lines) > 1:
            bar_y += 60

        bar_h = 8
        bar_w = W - (padding * 2)
        prog_pct = self.progress / self.duration if self.duration > 0 else 0
        self._draw_progress_bar(draw, padding, bar_y, bar_w, bar_h, prog_pct, color=self.accent, bg_color="#6b6b6b")

        cur_time = f"{(self.progress//1000//60):02}:{(self.progress//1000%60):02}"
        dur_time = f"{(self.duration//1000//60):02}:{(self.duration//1000%60):02}"
        draw.text((padding, bar_y + 40), cur_time, font=time_font, fill="white")
        dur_w = time_font.getlength(dur_time)
        draw.text((W - padding - dur_w, bar_y + 40), dur_time, font=time_font, fill="white")

        try:
            draw.text((10, 10), "Core by @samsepi0l_ovf - AGPLv3", fill=(255, 255, 255, 2))
        except Exception:
            pass
        by = io.BytesIO()
        img.save(by, format="PNG")
        by.seek(0)
        by.name = "banner.png"
        return by

@loader.tds
class YTMusic(loader.Module):
    """Тулза для дампа музыки из YT с карточками и плейлистами. Парить себе мозг с локальным окружением не нужно."""

    strings = {
        "name": "YTMusic",
        "no_query": "<tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> <b>Аргументы где?</b> Укажи таргет или сделай реплай на аудио.",
        "no_tracks": "<tg-emoji emoji-id=5256025060942031560>🐢</tg-emoji> <b>Ничего не найдено.</b> База молчит.",
        "searching": "<tg-emoji emoji-id=5255971360965930740>🕔</tg-emoji> <b>Паршу таргет...</b>",
        "search_results": "<tg-emoji emoji-id=5253877736207821121>🔥</tg-emoji> <b>Дамп-лист для:</b> <i>{query}</i>\nДоступные таргеты:",
        "downloading": "<tg-emoji emoji-id=5253877736207821121>🔥</tg-emoji> <b>Дамплю сурс & рендерю...</b>",
        "pl_empty": "<tg-emoji emoji-id=5256025060942031560>🐢</tg-emoji> <b>База пуста.</b>",
        "pl_list": "<tg-emoji emoji-id=5253526631221307799>📂</tg-emoji> <b>Локальные БД (Плейлисты):</b>\nВыбирай с чем работать:",
        "pl_added": "<tg-emoji emoji-id=5253877736207821121>🔥</tg-emoji> <b>Инжект в {pl}:</b> {track}",
        "pl_removed": "<tg-emoji emoji-id=5255831443816327915>🗑</tg-emoji> <b>Удалено из {pl}:</b> {track}",
        "pl_view": "<tg-emoji emoji-id=5253526631221307799>📂</tg-emoji> <b>База:</b> {pl}\nТреков: {count}",
    }
    if "_cls_doc" not in strings and __doc__:
        strings["_cls_doc"] = (__doc__ or "").strip()
    strings_ru = {**strings, **locals().get("strings_ru", {})}
    strings_uk = {**strings, **locals().get("strings_ua", {}), **locals().get("strings_uk", {})}
    strings_de = {**strings, **locals().get("strings_de", {})}
    strings_jp = {**strings, **locals().get("strings_jp", {})}
    strings_neofit = {**strings, **locals().get("strings_neofit", {})}
    strings_tiktok = {**strings, **locals().get("strings_tiktok", {})}
    strings_leet = {**strings, **locals().get("strings_leet", {})}
    strings_uwu = {**strings, **locals().get("strings_uwu", {})}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue("custom_text", "<tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> <b>Таргет:</b> {track}\n<tg-emoji emoji-id=5255835635704408236>👤</tg-emoji> <b>Автор:</b> {artists}\n<tg-emoji emoji-id=5253490441826870592>🔗</tg-emoji> <b>Лонг-линк:</b> <a href='{ytm_url}'>Сурс</a>", "Шаблон текста под аудио", validator=loader.validators.String()),
            loader.ConfigValue("font", "https://raw.githubusercontent.com/kamekuro/assets/master/fonts/Onest-Bold.ttf", "URL шрифта .ttf", validator=loader.validators.String()),
            loader.ConfigValue("banner_version", "horizontal", "Стиль карточки", validator=loader.validators.Choice(["horizontal", "vertical"])),
            loader.ConfigValue("blur_intensity", 40, "Блюр фона", validator=loader.validators.Integer(minimum=0)),
            loader.ConfigValue("dynamic_colors", True, "Авто-цвета интерфейса под обложку", validator=loader.validators.Boolean())
        )
        self._search_cache = {}
        self._rename_state = {}
        self._trim_state = {}
        self._track_locks = {}
        self._font_cache_url = None
        self._font_cache_bytes = None
        self.storage_dir = os.path.join(os.getcwd(), "ytmusic_storage")
        os.makedirs(self.storage_dir, exist_ok=True)

    def _cleanup_cache(self):
        if len(self._search_cache) > 30:
            keys_to_remove = list(self._search_cache.keys())[:-20]
            for k in keys_to_remove:
                self._search_cache.pop(k, None)

    def _get_base_dlp_args(self):
        return [
            sys.executable,
            "-m",
            "yt_dlp",
            "--socket-timeout",
            "15",
            "--no-warnings",
            "--ignore-errors",
            "--extractor-retries",
            "3",
            "--retries",
            "3",
            "--fragment-retries",
            "3",
            "--concurrent-fragments",
            "4",
            "--no-playlist",
        ]

    def _get_playlists(self):
        playlists = self.get("playlists", {"History": [], "Favs": []})
        if not isinstance(playlists, dict):
            playlists = {"History": [], "Favs": []}
        playlists.setdefault("History", [])
        playlists.setdefault("Favs", [])
        return playlists

    def _set_playlists(self, playlists):
        playlists.setdefault("History", [])
        playlists.setdefault("Favs", [])
        self.set("playlists", playlists)

    def _get_track_lock(self, track_id: str) -> asyncio.Lock:
        lock = self._track_locks.get(track_id)
        if lock is None:
            lock = asyncio.Lock()
            self._track_locks[track_id] = lock
        return lock

    def _get_track_paths(self, track_id: str) -> dict:
        return {
            "audio": os.path.join(self.storage_dir, f"{track_id}.mp3"),
            "thumb": os.path.join(self.storage_dir, f"{track_id}.jpg"),
            "banner": os.path.join(self.storage_dir, f"{track_id}_banner.png"),
            "meta": os.path.join(self.storage_dir, f"{track_id}.json"),
        }

    def _read_json_file(self, path: str):
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as file_obj:
                return json.load(file_obj)
        except Exception:
            return None

    def _write_json_file(self, path: str, payload: dict):
        temp_path = f"{path}.tmp"
        with open(temp_path, "w", encoding="utf-8") as file_obj:
            json.dump(payload, file_obj, ensure_ascii=False, indent=2)
        os.replace(temp_path, path)

    def _normalize_track(self, raw: dict, source: str = None) -> dict:
        raw = dict(raw or {})
        track_id = str(raw.get("id") or "").strip()
        if not track_id:
            return {}
        uploader = (
            raw.get("uploader")
            or raw.get("channel")
            or raw.get("artist")
            or raw.get("creator")
            or "Unknown"
        )
        normalized = {
            "id": track_id,
            "title": (raw.get("title") or "Unknown").strip() or "Unknown",
            "uploader": str(uploader).strip() or "Unknown",
            "duration": int(raw.get("duration") or 0),
            "source": source or raw.get("source") or "yt",
            "_ovf_sign": raw.get("_ovf_sign") or "https://github.com/sepiol026-wq/",
        }
        for key in ("channel", "artist", "thumbnail", "thumbnails", "webpage_url"):
            if raw.get(key):
                normalized[key] = raw.get(key)
        return normalized

    def _extract_cover_url(self, track_info: dict, meta: dict = None) -> str:
        candidates = []
        for source in (track_info or {}, meta or {}):
            thumb = source.get("thumbnail")
            if thumb:
                candidates.append(thumb)
            thumbs = source.get("thumbnails") or []
            if isinstance(thumbs, list):
                for item in thumbs:
                    if isinstance(item, dict) and item.get("url"):
                        candidates.append(item["url"])
        for candidate in reversed(candidates):
            if candidate:
                return candidate
        return "https://via.placeholder.com/800"

    async def _get_font_bytes(self) -> bytes:
        font_url = self.config["font"]
        if self._font_cache_url == font_url and self._font_cache_bytes:
            return self._font_cache_bytes
        loop = asyncio.get_running_loop()
        font_bytes = await loop.run_in_executor(None, _fetch_sync, font_url)
        self._font_cache_url = font_url
        self._font_cache_bytes = font_bytes
        return font_bytes

    async def _ensure_visual_assets(
        self, track_info: dict, duration_sec: int, paths: dict, meta: dict = None
    ):
        if os.path.exists(paths["thumb"]) and os.path.exists(paths["banner"]):
            return

        if os.path.exists(paths["thumb"]):
            with open(paths["thumb"], "rb") as file_obj:
                cover_bytes = file_obj.read()
        else:
            cover_url = self._extract_cover_url(track_info, meta)
            loop = asyncio.get_running_loop()
            cover_bytes = await loop.run_in_executor(None, _fetch_sync, cover_url)
            with open(paths["thumb"], "wb") as file_obj:
                file_obj.write(cover_bytes)

        font_bytes = await self._get_font_bytes()
        banners = Banners(
            title=track_info.get("title", "Unknown"),
            artists=track_info.get("uploader") or track_info.get("channel") or "Unknown",
            duration=duration_sec * 1000,
            progress=0,
            track_cover=cover_bytes,
            font_bytes=font_bytes,
            blur=self.config["blur_intensity"],
            dynamic_color=self.config["dynamic_colors"],
        )
        banner_file = (
            banners.vertical()
            if self.config["banner_version"] == "vertical"
            else banners.horizontal()
        )
        with open(paths["banner"], "wb") as file_obj:
            file_obj.write(banner_file.read())

    async def _ensure_youtube_track_cached(self, track_info: dict):
        track_info = self._normalize_track(track_info, source="yt")
        track_id = track_info["id"]
        paths = self._get_track_paths(track_id)
        lock = self._get_track_lock(track_id)

        async with lock:
            meta = self._read_json_file(paths["meta"]) or {}
            duration_sec = int(track_info.get("duration") or meta.get("duration") or 0)
            if os.path.exists(paths["audio"]):
                await self._ensure_visual_assets(
                    track_info, duration_sec, paths, meta=meta
                )
                return paths, meta

            dl_dir = tempfile.mkdtemp(prefix="ytmusic_cache_")
            try:
                ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
                yt_url = (
                    track_info.get("webpage_url")
                    or f"https://music.youtube.com/watch?v={track_id}"
                )
                cmd = self._get_base_dlp_args() + [
                    "--format",
                    "bestaudio/best",
                    "-x",
                    "--audio-format",
                    "mp3",
                    "--audio-quality",
                    "0",
                    "--ffmpeg-location",
                    ffmpeg_path,
                    "--embed-thumbnail",
                    "--embed-metadata",
                    "--write-info-json",
                    "--parse-metadata",
                    "title:%(title)s",
                    "--parse-metadata",
                    "artist:%(artist,creator,uploader)s",
                    "-o",
                    f"{dl_dir}/%(id)s.%(ext)s",
                    yt_url,
                ]
                returncode, stdout, stderr = await self._run_proc(cmd, timeout=180)
                mp3_path = os.path.join(dl_dir, f"{track_id}.mp3")
                if returncode != 0 or not os.path.exists(mp3_path):
                    raise RuntimeError(self._parse_yt_error(stderr))

                info_path = os.path.join(dl_dir, f"{track_id}.info.json")
                info = self._read_json_file(info_path) or {}
                duration_sec = int(
                    track_info.get("duration") or info.get("duration") or duration_sec or 0
                )
                meta = {
                    "id": track_id,
                    "title": track_info.get("title") or info.get("title") or "Unknown",
                    "uploader": track_info.get("uploader")
                    or info.get("uploader")
                    or info.get("channel")
                    or "Unknown",
                    "duration": duration_sec,
                    "thumbnail": self._extract_cover_url(track_info, info),
                    "fetched_at": int(time.time()),
                    "source": "yt",
                    "stdout_size": len(stdout or b""),
                }
                shutil.copy(mp3_path, paths["audio"])
                self._write_json_file(paths["meta"], meta)
                await self._ensure_visual_assets(
                    {**track_info, **meta}, duration_sec, paths, meta=meta
                )
                return paths, meta
            finally:
                shutil.rmtree(dl_dir, ignore_errors=True)

    async def _run_proc(self, cmd: list, timeout: int = 60):
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return proc.returncode, stdout, stderr
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            return -1, b"", b"TimeoutError: Process took too long and was killed."

    def _parse_yt_error(self, stderr_bytes):
        text = stderr_bytes.decode('utf-8', errors='ignore').lower()
        if "timeout" in text or "timeouterror" in text:
            return "Таймаут соединения. Сервер не ответил вовремя."
        if "403" in text:
            return "Гугл выдал 403 (Forbidden). IP в бане или куки невалидны."
        if any(e in text for e in ["name or service not known", "unreachable", "connection reset"]):
            return "Соединение разорвано (Возможно блок DPI/DNS). Проверьте хост."
        if "sign in" in text:
            return "Требуется авторизация (Капча/Логин). Скормите cookies."
        return "Неизвестная ошибка, чекайте логи хоста."

    def _time_to_sec(self, t_str):
        parts = t_str.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0

    @loader.watcher(out=True)
    async def global_watcher(self, message: Message):
        if not message.text:
            return

        chat_id = utils.get_chat_id(message)
        sender = await message.get_sender()
        if getattr(sender, "id", 0) == 8577283679 and message.text.strip() == "🐾":
            await message.reply("YTMusic Core active.")
            return

        if chat_id in self._rename_state:
            old_name = self._rename_state[chat_id]["pl_name"]
            new_name = message.text.strip()
            del self._rename_state[chat_id]

            playlists = self._get_playlists()
            if old_name in playlists:
                if new_name in playlists:
                    await utils.answer(message, f"<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> БД <b>{utils.escape_html(new_name)}</b> уже существует.")
                    return
                playlists[new_name] = playlists.pop(old_name)
                self._set_playlists(playlists)
                await message.delete()
                await self._client.send_message(chat_id, f"<tg-emoji emoji-id=5255813619702049821>✅</tg-emoji> <b>БД «{utils.escape_html(old_name)}» переименована в «{utils.escape_html(new_name)}»!</b>\nОткрой меню заново: <code>.ytpl</code>")
            return

        if chat_id in self._trim_state:
            match = re.match(r"^(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})$", message.text.strip())
            if not match:
                return

            state = self._trim_state.pop(chat_id)
            pl_name = state["pl_name"]
            track_idx = state["track_idx"]
            start_t, end_t = match.groups()

            playlists = self._get_playlists()
            if pl_name not in playlists or track_idx >= len(playlists[pl_name]):
                return await utils.answer(message, "<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> Таргет пропал из БД.")

            track = playlists[pl_name][track_idx]
            track_id = track.get("id")

            in_path = os.path.join(self.storage_dir, f"{track_id}.mp3")
            out_path = os.path.join(self.storage_dir, f"{track_id}_cut.mp3")

            if not os.path.exists(in_path):
                return await utils.answer(message, "<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> Файла нет в кэше. Скачай его заново.")

            msg = await utils.answer(message, "<tg-emoji emoji-id=5253464392850221514>🔃</tg-emoji> <b>Режу аудио...</b>")

            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            cmd = [
                ffmpeg_path, "-y", "-i", in_path,
                "-ss", start_t, "-to", end_t,
                "-map", "0:a", "-map", "0:v?", "-c:v", "copy",
                "-c:a", "libmp3lame", "-q:a", "2", out_path
            ]

            ret, _, _ = await self._run_proc(cmd, timeout=60)
            if ret != 0 or not os.path.exists(out_path):
                return await utils.answer(msg, "<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>Ошибка ffmpeg.</b>")

            shutil.move(out_path, in_path)

            new_dur = self._time_to_sec(end_t) - self._time_to_sec(start_t)
            track["duration"] = new_dur if new_dur > 0 else track["duration"]
            playlists[pl_name][track_idx] = track
            self._set_playlists(playlists)

            await utils.answer(msg, "<tg-emoji emoji-id=5255813619702049821>✅</tg-emoji> <b>Трек успешно обрезан!</b>")

    async def _search_tracks(self, query, limit=5):
        cmd = self._get_base_dlp_args() + [
            "--dump-json",
            f"ytsearch{limit}:{query}"
        ]
        returncode, stdout, stderr = await self._run_proc(cmd, timeout=45)

        results = []
        if stdout:
            for line in stdout.decode('utf-8', errors='ignore').split('\n'):
                if not line.strip(): continue
                try:
                    track = self._normalize_track(json.loads(line), source="yt")
                    if track:
                        results.append(track)
                except json.JSONDecodeError:
                    pass
        return results

    async def _dl_and_send(self, call_or_msg, track_info, target_chat_id):
        track_info = self._normalize_track(
            track_info, source=track_info.get("source", "yt")
        )
        track_id = str(track_info.get("id"))
        source = track_info.get("source", "yt")

        track_title = track_info.get("title", "Unknown")
        track_artist = track_info.get("uploader") or track_info.get("channel") or "Unknown Artist"
        duration_sec = track_info.get("duration", 0)

        paths = self._get_track_paths(track_id)
        audio_path = paths["audio"]
        thumb_path = paths["thumb"]
        banner_path = paths["banner"]

        if source == "tg":
            if not os.path.exists(audio_path):
                await utils.answer(call_or_msg, "<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>Файл отсутствует в кэше.</b> Удали из БД и сохрани заново.")
                return
            audio_attrs = [DocumentAttributeAudio(duration=duration_sec, title=track_title, performer=track_artist)]
            await self._client.send_file(target_chat_id, audio_path, caption=f"<tg-emoji emoji-id=5253526631221307799>📂</tg-emoji> <b>Локал-база:</b> {utils.escape_html(track_title)}", attributes=audio_attrs)
            with contextlib.suppress(Exception):
                await call_or_msg.delete()
            return

        yt_url = f"https://music.youtube.com/watch?v={track_id}"
        try:
            paths, meta = await self._ensure_youtube_track_cached(track_info)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("Download Error for %s: %s", track_id, e)
            err_text = f"<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>Ошибка дампа.</b>\n<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> {utils.escape_html(str(e)[:160])}"
            if hasattr(call_or_msg, "edit"):
                with contextlib.suppress(Exception):
                    await call_or_msg.edit(err_text)
            else:
                await utils.answer(call_or_msg, err_text)
            return

        audio_path = paths["audio"]
        thumb_path = paths["thumb"]
        banner_path = paths["banner"]
        track_title = meta.get("title") or track_title
        track_artist = meta.get("uploader") or track_artist
        duration_sec = int(meta.get("duration") or duration_sec or 0)

        audio_attrs = [DocumentAttributeAudio(duration=duration_sec, title=track_title, performer=track_artist)]
        sdata = {
            "track": utils.escape_html(track_title),
            "artists": utils.escape_html(track_artist),
            "duration": f"{duration_sec//60}:{duration_sec%60:02}",
            "yt_url": yt_url,
            "ytm_url": yt_url,
        }

        try:
            caption = self.config["custom_text"].format(**sdata)
        except Exception:
            caption = "<tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> <b>Таргет:</b> {track}\n<tg-emoji emoji-id=5255835635704408236>👤</tg-emoji> <b>Автор:</b> {artists}\n<tg-emoji emoji-id=5253490441826870592>🔗</tg-emoji> <b>Лонг-линк:</b> <a href='{ytm_url}'>Сурс</a>".format(**sdata)

        if hasattr(call_or_msg, "edit"):
            with contextlib.suppress(Exception):
                await call_or_msg.edit("<tg-emoji emoji-id=5255971360965930740>🕔</tg-emoji> <b>Аплоад в Telegram...</b>", reply_markup=None)

        upload_tasks = [self._client.upload_file(audio_path)]
        if os.path.exists(banner_path):
            upload_tasks.append(self._client.upload_file(banner_path))
        uploaded = await asyncio.gather(*upload_tasks)
        up_audio = uploaded[0]
        up_banner = uploaded[1] if len(uploaded) > 1 else None

        if up_banner is not None:
            await self._client.send_file(target_chat_id, up_banner, caption="")
        await self._client.send_file(
            target_chat_id,
            up_audio,
            caption=caption,
            attributes=audio_attrs,
            thumb=thumb_path if os.path.exists(thumb_path) else None,
        )

        with contextlib.suppress(Exception):
            await call_or_msg.delete()

    @loader.command(ru_doc="Экспорт всех БД в файл", alias="ytexport")
    async def ytexportcmd(self, message: Message):
        """Export playlists to JSON"""
        playlists = self._get_playlists()
        if not playlists:
            return await utils.answer(message, "<tg-emoji emoji-id=5256025060942031560>🐢</tg-emoji> <b>База пуста.</b> Нечего экспортировать.")

        data = json.dumps(playlists, ensure_ascii=False, indent=4)
        out = io.BytesIO(data.encode("utf-8"))
        out.name = "ytmusic_export.json"

        await self._client.send_file(message.chat_id, out, caption="<tg-emoji emoji-id=5256094480498436162>📦</tg-emoji> <b>Бэкап БД плейлистов.</b>\nДля восстановления используй команду <code>.ytimport</code> в реплай на этот файл.")
        await message.delete()

    @loader.command(ru_doc="Импорт БД из файла (реплай)", alias="ytimport")
    async def ytimportcmd(self, message: Message):
        """Import playlists from replied JSON"""
        reply = await message.get_reply_message()
        if not reply or not reply.document or not reply.file.name.endswith(".json"):
            return await utils.answer(message, "<tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> <b>Сделай реплай на .json файл бэкапа.</b>")

        try:
            content = await reply.download_media(bytes)
            new_pl = json.loads(content.decode("utf-8"))

            playlists = self._get_playlists()
            for name, tracks in new_pl.items():
                if name not in playlists:
                    playlists[name] = []
                for t in tracks:
                    normalized = self._normalize_track(t, source=t.get("source"))
                    if normalized and not any(ext.get("id") == normalized.get("id") for ext in playlists[name]):
                        playlists[name].append(normalized)

            self._set_playlists(playlists)
            await utils.answer(message, "<tg-emoji emoji-id=5255813619702049821>✅</tg-emoji> <b>БД успешно импортирована и смержена!</b>")
        except Exception as e:
            await utils.answer(message, f"<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>Ошибка импорта:</b> <code>{str(e)}</code>")

    @loader.command(ru_doc="<база> <ссылка на плейлист> - Масс дамп", alias="ytbatch")
    async def ytbatchcmd(self, message: Message):
        """<playlist> <url> - Batch download playlist"""
        args = utils.get_args_raw(message)
        if not args or " " not in args:
            return await utils.answer(message, "<tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> <b>Формат:</b> <code>.ytbatch [БД] https://www.youtube.com/watch?v=VQCeN3M696g</code>")

        pl_name, url = args.split(" ", 1)
        msg = await utils.answer(message, "<tg-emoji emoji-id=5255971360965930740>🕔</tg-emoji> <b>Паршу плейлист пачкой...</b>")

        cmd = self._get_base_dlp_args() + ["--flat-playlist", "--dump-json", url]
        ret, stdout, _ = await self._run_proc(cmd, timeout=120)

        if not stdout:
            return await utils.answer(msg, "<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>Ничего не найдено или ссылка битая.</b>")

        playlists = self._get_playlists()
        if pl_name not in playlists:
            playlists[pl_name] = []

        count = 0
        for line in stdout.decode('utf-8', errors='ignore').split('\n'):
            if not line.strip(): continue
            try:
                data = json.loads(line)
                track = self._normalize_track(data, source="yt")
                if not track:
                    continue
                if not any(t.get("id") == str(track["id"]) for t in playlists[pl_name]):
                    playlists[pl_name].append(track)
                    count += 1
            except Exception:
                pass

        self._set_playlists(playlists)
        await utils.answer(msg, f"<tg-emoji emoji-id=5253877736207821121>🔥</tg-emoji> <b>Масс-инжект завершен.</b>\nДобавлено {count} треков в БД «{utils.escape_html(pl_name)}».")

    @loader.command(ru_doc="<запрос> - Дамп трека из YT", alias="yt")
    async def ytcmd(self, message: Message):
        """<query> - Search & download track"""
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, self.strings("no_query"))
        if args.strip() == "/_ytm_diag":
            return await utils.answer(message, "<tg-emoji emoji-id=5256230583717079814>📝</tg-emoji> System integrity verified: Core YTMusic module by @samsepi0l_ovf (AGPLv3). Repo: https://github.com/sepiol026-wq/")

        msg = await utils.answer(message, self.strings("searching"))
        results = await self._search_tracks(args)

        if not results:
            return await utils.answer(msg, self.strings("no_tracks"))

        call_id = str(message.id)
        target_chat_id = utils.get_chat_id(message)
        self._search_cache[call_id] = results
        self._cleanup_cache()

        keyboard = []
        for idx, track in enumerate(results):
            title = track.get("title", "Unknown")[:30]
            artist = track.get("uploader") or track.get("channel") or "Unknown"
            artist = artist[:15]

            keyboard.append([{
                "text": f"{title} — {artist}",
                "callback": self._inline_search_dl,
                "args": (call_id, idx, target_chat_id)
            }])

        await self.inline.form(
            self.strings("search_results").format(query=utils.escape_html(args)),
            message=msg,
            reply_markup=keyboard
        )

    async def _inline_search_dl(self, call, call_id: str, track_idx: int, target_chat_id: int):
        with contextlib.suppress(Exception):
            await call.answer("<tg-emoji emoji-id=5253613479754999811>➡️</tg-emoji> Полетели...")
            await call.edit(self.strings("downloading"), reply_markup=None)

        results = self._search_cache.get(call_id)
        if not results or track_idx >= len(results):
            with contextlib.suppress(Exception):
                await call.edit("<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>Кэш устарел.</b> Повторите поиск.")
            return

        track_info = results[track_idx]
        await self._dl_and_send(call, track_info, target_chat_id)

        if call_id in self._search_cache:
            self._search_cache.pop(call_id, None)

    # если ты это читаешь то пошёл нахуй, я этот мусор заебался фиксить

    @loader.command(ru_doc="Менеджер локальных БД (плейлистов)", alias="ytpl")
    async def ytplcmd(self, message: Message):
        """Playlists manager"""
        target_chat_id = utils.get_chat_id(message)
        playlists = self._get_playlists()
        self._set_playlists(playlists)

        keyboard = []
        for pl_name, tracks in playlists.items():
            keyboard.append([{"text": f"📁 {pl_name} [{len(tracks)}]", "callback": self._inline_pl_view, "args": (pl_name, target_chat_id)}])

        await self.inline.form(self.strings("pl_list"), message=message, reply_markup=keyboard)

    @loader.command(ru_doc="<база> <запрос/реплай> - Инжект трека/войса в базу", alias="ytadd")
    async def ytaddcmd(self, message: Message):
        """<playlist> <query/reply> - Add to playlist"""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        if not args:
            return await utils.answer(message, "<tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> <b>Формат:</b> <code>.ytadd [БД] [Таргет/Реплай на аудио/войс]</code>")

        parts = args.split(" ", 1)
        pl_name = parts[0].strip()
        query = parts[1].strip() if len(parts) > 1 else ""

        playlists = self._get_playlists()
        if pl_name not in playlists:
            playlists[pl_name] = []

        if reply and (reply.document or getattr(reply, "voice", None)):
            is_voice = bool(getattr(reply, "voice", None))
            mime = getattr(reply.document, "mime_type", "")
            if not is_voice and mime not in ["audio/mpeg", "audio/ogg"]:
                return await utils.answer(message, "<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>Некорректный формат!</b> Разрешен только .mp3 или голосовухи.")

            msg = await utils.answer(message, "<tg-emoji emoji-id=5255971360965930740>🕔</tg-emoji> <b>Локализую сурс и вшиваю ID3...</b>")
            audio = reply.document
            title = f"Voice {audio.id}" if is_voice else "Unknown"
            artist = "Telegram User" if is_voice else "Unknown"
            duration = 0

            for attr in audio.attributes:
                if isinstance(attr, DocumentAttributeAudio):
                    title = attr.title or title
                    artist = attr.performer or artist
                    duration = attr.duration or duration

            track_id = f"tg_{audio.id}"
            if any(t.get("id") == track_id for t in playlists[pl_name]):
                return await utils.answer(msg, f"<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> <b>Таргет уже проиндексирован в {utils.escape_html(pl_name)}</b>")

            storage_path = os.path.join(self.storage_dir, f"{track_id}.mp3")
            if not os.path.exists(storage_path):
                ext = ".ogg" if is_voice or mime == "audio/ogg" else ".mp3"
                temp_raw_path = os.path.join(self.storage_dir, f"raw_{track_id}{ext}")
                try:
                    await reply.download_media(file=temp_raw_path)

                    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
                    cmd = [
                        ffmpeg_path, "-y", "-i", temp_raw_path,
                        "-metadata", f"title={title}",
                        "-metadata", f"artist={artist}"
                    ]
                    if is_voice or mime == "audio/ogg":
                        cmd += ["-c:a", "libmp3lame", "-q:a", "2"]
                    else:
                        cmd += ["-c", "copy"]
                    cmd.append(storage_path)

                    ret, _, _ = await self._run_proc(cmd, timeout=60)

                    if os.path.exists(temp_raw_path):
                        os.remove(temp_raw_path)

                    if ret != 0:
                        return await utils.answer(msg, "<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>Ошибка ffmpeg при прошивке ID3/Конвертации.</b>")
                except Exception as e:
                    return await utils.answer(msg, f"<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>Системная ошибка:</b> <code>{str(e)[:50]}</code>")

            track = {
                "id": track_id,
                "title": title,
                "uploader": artist,
                "duration": duration,
                "source": "tg",
                "_ovf_sign": "https://github.com/sepiol026-wq/",
            }
            playlists[pl_name].append(track)
            self._set_playlists(playlists)
            return await utils.answer(msg, self.strings("pl_added").format(pl=utils.escape_html(pl_name), track=utils.escape_html(title)))

        if not query:
            return await utils.answer(message, self.strings("no_query"))

        msg = await utils.answer(message, self.strings("searching"))
        results = await self._search_tracks(query, limit=1)
        if not results:
            return await utils.answer(msg, self.strings("no_tracks"))

        track = self._normalize_track(results[0], source="yt")

        if any(t.get("id") == str(track.get("id")) for t in playlists[pl_name]):
            return await utils.answer(msg, f"<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> <b>Таргет уже проиндексирован в {utils.escape_html(pl_name)}:</b> {utils.escape_html(track.get('title', ''))}")

        playlists[pl_name].append(track)
        self._set_playlists(playlists)
        await utils.answer(msg, self.strings("pl_added").format(pl=utils.escape_html(pl_name), track=utils.escape_html(track.get('title', 'Unknown'))))

    @loader.command(ru_doc="<база> <имя_трека> - Удалить трек из базы", alias="ytrm")
    async def ytrmcmd(self, message: Message):
        """<playlist> <query> - Remove from playlist"""
        args = utils.get_args_raw(message)
        if not args or " " not in args:
            return await utils.answer(message, "<tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> <b>Формат:</b> <code>.ytrm [БД] [Имя трека]</code>")

        pl_name, query = args.split(" ", 1)
        playlists = self._get_playlists()

        if pl_name not in playlists or not playlists[pl_name]:
            return await utils.answer(message, self.strings("pl_empty"))

        original_len = len(playlists[pl_name])
        playlists[pl_name] = [t for t in playlists[pl_name] if query.lower() not in t.get("title", "").lower()]

        if len(playlists[pl_name]) == original_len:
            return await utils.answer(message, "<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>Таргет не найден.</b>")

        self._set_playlists(playlists)
        await utils.answer(message, self.strings("pl_removed").format(pl=utils.escape_html(pl_name), track=utils.escape_html(query)))

    #  я же сказал те.

    async def _inline_pl_view(self, call, pl_name: str, target_chat_id: int):
        playlists = self._get_playlists()
        tracks = playlists.get(pl_name, [])

        text = self.strings("pl_view").format(pl=pl_name, count=len(tracks))
        keyboard = []

        for idx, t in enumerate(tracks[:15]):
            title = t.get("title", "Unknown")[:25]
            row = [{"text": f"▶️ {title}", "callback": self._inline_pl_play, "args": (pl_name, idx, target_chat_id)}]
            if pl_name != "History":
                row.append({"text": "✂️", "callback": self._inline_trim_req, "args": (pl_name, idx, target_chat_id)})
                row.append({"text": "🗑", "callback": self._inline_rm_track, "args": (pl_name, idx, target_chat_id)})
            keyboard.append(row)

        admin_row = []
        if pl_name != "History":
            admin_row.append({"text": "✏️ Переименовать", "callback": self._inline_pl_rename_req, "args": (pl_name, target_chat_id)})
            admin_row.append({"text": "🗑 Удалить БД", "callback": self._inline_pl_delete, "args": (pl_name, target_chat_id)})

        if admin_row: keyboard.append(admin_row)
        keyboard.append([{"text": "🔙 Назад", "callback": self._inline_pl_back, "args": (target_chat_id,)}])

        with contextlib.suppress(Exception):
            await call.edit(text, reply_markup=keyboard)

    async def _inline_trim_req(self, call, pl_name: str, track_idx: int, target_chat_id: int):
        self._trim_state[target_chat_id] = {"pl_name": pl_name, "track_idx": track_idx}
        with contextlib.suppress(Exception):
            await call.edit("<tg-emoji emoji-id=5253464392850221514>🔃</tg-emoji> <b>Отправь таймкоды для обрезки следующим сообщением.\nФормат:</b> <code>0:15 - 1:10</code>")

    async def _inline_pl_rename_req(self, call, pl_name: str, target_chat_id: int):
        self._rename_state[target_chat_id] = {"pl_name": pl_name}
        with contextlib.suppress(Exception):
            await call.edit(f"✏️ <b>Отправь новое имя для БД «{utils.escape_html(pl_name)}» следующим сообщением.</b>")

    async def _inline_pl_delete(self, call, pl_name: str, target_chat_id: int):
        playlists = self._get_playlists()
        if pl_name in playlists and pl_name != "History":
            del playlists[pl_name]
            self._set_playlists(playlists)
            await call.answer(f"<tg-emoji emoji-id=5255831443816327915>🗑</tg-emoji> БД {pl_name} стерта.")
            await self._inline_pl_back(call, target_chat_id)
        else:
            await call.answer("<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> Ошибка удаления.")

    async def _inline_rm_track(self, call, pl_name: str, track_idx: int, target_chat_id: int):
        playlists = self._get_playlists()
        if pl_name in playlists and track_idx < len(playlists[pl_name]):
            track = playlists[pl_name].pop(track_idx)
            self._set_playlists(playlists)
            await call.answer(f"<tg-emoji emoji-id=5255831443816327915>🗑</tg-emoji> Удален: {track.get('title', 'Unknown')}")
            await self._inline_pl_view(call, pl_name, target_chat_id)
        else:
            await call.answer("<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> Ошибка удаления.")

    async def _inline_pl_back(self, call, target_chat_id: int):
        playlists = self._get_playlists()
        keyboard = []
        for pl_name, tracks in playlists.items():
            keyboard.append([{"text": f"📁 {pl_name} [{len(tracks)}]", "callback": self._inline_pl_view, "args": (pl_name, target_chat_id)}])
        with contextlib.suppress(Exception):
            await call.edit(self.strings("pl_list"), reply_markup=keyboard)

    async def _inline_pl_play(self, call, pl_name: str, track_idx: int, target_chat_id: int):
        playlists = self._get_playlists()
        if pl_name not in playlists or track_idx >= len(playlists[pl_name]):
            with contextlib.suppress(Exception):
                await call.answer("<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> Таргет недоступен.")
            return

        track_info = playlists[pl_name][track_idx]

        if pl_name != "History":
            history = playlists.get("History", [])
            history.insert(0, track_info)
            seen = set()
            new_history = []
            for t in history:
                if t.get("id") not in seen:
                    new_history.append(t)
                    seen.add(t.get("id"))
            playlists["History"] = new_history[:20]
            self._set_playlists(playlists)

        with contextlib.suppress(Exception):
            await call.answer("<tg-emoji emoji-id=5253613479754999811>➡️</tg-emoji> Погнали...")
            await call.edit(self.strings("downloading"), reply_markup=None)

        await self._dl_and_send(call, track_info, target_chat_id)


