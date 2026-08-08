# ====================================================================================================================
#   ██████╗  ██████╗ ██╗   ██╗███╗   ███╗ ██████╗ ██████╗ ██╗   ██╗██╗     ███████╗███████╗
#  ██╔════╝ ██╔═══██╗╚██╗ ██╔╝████╗ ████║██╔═══██╗██╔══██╗██║   ██║██║     ██╔════╝██╔════╝
#  ██║  ███╗██║   ██║ ╚████╔╝ ██╔████╔██║██║   ██║██║  ██║██║   ██║██║     █████╗  ███████╗
#  ██║   ██║██║   ██║  ╚██╔╝  ██║╚██╔╝██║██║   ██║██║  ██║██║   ██║██║     ██╔══╝  ╚════██║
#  ╚██████╔╝╚██████╔╝   ██║   ██║ ╚═╝ ██║╚██████╔╝██████╔╝╚██████╔╝███████╗███████╗███████║
#   ╚═════╝  ╚═════╝    ╚═╝   ╚═╝     ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚══════╝
#
#   OFFICIAL USERNAMES: @goymodules | @samsepi0l_ovf
#   MODULE: omni
#
#   THIS MODULE IS LICENSED UNDER GNU AGPLv3, PROTECTED AGAINST UNAUTHORIZED COPYING/RESALE,
#   AND ITS ORIGINAL AUTHORSHIP BELONGS TO @samsepi0l_ovf.
#   ALL OFFICIAL UPDATES, RELEASE NOTES, AND PATCHES ARE PUBLISHED IN THE TELEGRAM CHANNEL @goymodules.
# ====================================================================================================================

# requires: yt-dlp imageio-ffmpeg
# meta developer: @goymodules
# meta tags: media-downloader, video, audio, instagram, youtube, tiktok, heroku, загрузчик-медиа, видео, аудио, инстаграм, ютуб, тикток, хероку
# authors: @goymodules
# Description: Universal media downloader — async chunked upload, instant.
# meta banner: https://raw.githubusercontent.com/sepiol026-wq/goypulse/main/assets/omniload.png

__version__ = (1, 7, 2)
import asyncio
import contextlib
import json
import logging
import os
import shutil
import tempfile
import sys
import time
import uuid
from telethon.tl.types import Message, DocumentAttributeAudio, DocumentAttributeVideo
import imageio_ffmpeg
from .. import loader, utils
from ..inline.types import InlineCall, InlineQuery

logger = logging.getLogger(__name__)

@loader.tds
class OmniLoad(loader.Module):
    """Универсальный загрузчик медиа."""

    strings = {
        "name": "OmniLoad",
        "no_args": "<tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> <b>No URL provided.</b> Please specify a link.",
        "fetching": "<tg-emoji emoji-id=5255971360965930740>🕔</tg-emoji> <b>Parsing target...</b>",
        "menu": "<tg-emoji emoji-id=5253877736207821121>🔥</tg-emoji> <b>Target:</b> <i>{title}</i>\nChoose format & quality:",
        "downloading": "<tg-emoji emoji-id=5253877736207821121>🔥</tg-emoji> <b>Downloading & rendering...</b>",
        "uploading": "<tg-emoji emoji-id=5255971360965930740>🕔</tg-emoji> <b>Uploading to Telegram...</b>",
        "error": "<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>Error:</b> <code>{error}</code>",
        "expired": "<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>Cache expired.</b> Please search again.",
        "caption": "<tg-emoji emoji-id=5253651477330667400>🎞</tg-emoji> <b>{title}</b>\n<tg-emoji emoji-id=5255835635704408236>👤</tg-emoji> {author}\n<tg-emoji emoji-id=5253490441826870592>🔗</tg-emoji> <a href='{url}'>Source</a>"
    }

    strings_ru = {
        "no_args": "<tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> <b>Аргументы где?</b> Укажи ссылку.",
        "fetching": "<tg-emoji emoji-id=5255971360965930740>🕔</tg-emoji> <b>Паршу таргет...</b>",
        "menu": "<tg-emoji emoji-id=5253877736207821121>🔥</tg-emoji> <b>Таргет:</b> <i>{title}</i>\nВыбирай качество:",
        "downloading": "<tg-emoji emoji-id=5253877736207821121>🔥</tg-emoji> <b>Дамплю сурс & рендерю...</b>",
        "uploading": "<tg-emoji emoji-id=5255971360965930740>🕔</tg-emoji> <b>Аплоад в Telegram...</b>",
        "error": "<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>Ошибка:</b> <code>{error}</code>",
        "expired": "<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>Кэш устарел.</b> Сделай запрос заново.",
        "caption": "<tg-emoji emoji-id=5253651477330667400>🎞</tg-emoji> <b>{title}</b>\n<tg-emoji emoji-id=5255835635704408236>👤</tg-emoji> {author}\n<tg-emoji emoji-id=5253490441826870592>🔗</tg-emoji> <a href='{url}'>Сурс</a>"
    }

    strings_de = {
        "no_args": "<tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> <b>Kein URL angegeben.</b>",
        "fetching": "<tg-emoji emoji-id=5255971360965930740>🕔</tg-emoji> <b>Ziel wird analysiert...</b>",
        "menu": "<tg-emoji emoji-id=5253877736207821121>🔥</tg-emoji> <b>Ziel:</b> <i>{title}</i>\nWählen Sie die Qualität:",
        "downloading": "<tg-emoji emoji-id=5253877736207821121>🔥</tg-emoji> <b>Herunterladen & Verarbeiten...</b>",
        "uploading": "<tg-emoji emoji-id=5255971360965930740>🕔</tg-emoji> <b>Hochladen zu Telegram...</b>",
        "error": "<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>Fehler:</b> <code>{error}</code>",
        "expired": "<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>Cache abgelaufen.</b> Bitte erneut versuchen.",
        "caption": "<tg-emoji emoji-id=5253651477330667400>🎞</tg-emoji> <b>{title}</b>\n<tg-emoji emoji-id=5255835635704408236>👤</tg-emoji> {author}\n<tg-emoji emoji-id=5253490441826870592>🔗</tg-emoji> <a href='{url}'>Quelle</a>"
    }

    strings_jp = {
        "no_args": "<tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> <b>URLが提供されていません。</b>",
        "fetching": "<tg-emoji emoji-id=5255971360965930740>🕔</tg-emoji> <b>ターゲットを解析中...</b>",
        "menu": "<tg-emoji emoji-id=5253877736207821121>🔥</tg-emoji> <b>ターゲット:</b> <i>{title}</i>\n品質を選択してください:",
        "downloading": "<tg-emoji emoji-id=5253877736207821121>🔥</tg-emoji> <b>ダウンロードとレンダリング中...</b>",
        "uploading": "<tg-emoji emoji-id=5255971360965930740>🕔</tg-emoji> <b>Telegramにアップロード中...</b>",
        "error": "<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>エラー:</b> <code>{error}</code>",
        "expired": "<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>キャッシュの期限切れ。</b> 再試行してください。",
        "caption": "<tg-emoji emoji-id=5253651477330667400>🎞</tg-emoji> <b>{title}</b>\n<tg-emoji emoji-id=5255835635704408236>👤</tg-emoji> {author}\n<tg-emoji emoji-id=5253490441826870592>🔗</tg-emoji> <a href='{url}'>ソース</a>"
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
            loader.ConfigValue("ytdl_timeout", 300, "Timeout for downloading", validator=loader.validators.Integer(minimum=30)),
            loader.ConfigValue("upload_timeout", 600, "Timeout for Telegram upload", validator=loader.validators.Integer(minimum=60)),
            loader.ConfigValue("inline_timeout", 15, "Timeout for inline metadata fetch", validator=loader.validators.Integer(minimum=5))
        )
        self._cache = {}
        self._inline_cache = {}
        self.storage_dir = os.path.join(os.getcwd(), "omniload_storage")
        os.makedirs(self.storage_dir, exist_ok=True)

    async def _run_proc(self, cmd: list, timeout: int = 60):
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return proc.returncode, stdout, stderr
        except asyncio.TimeoutError:
            with contextlib.suppress(ProcessLookupError):
                proc.kill()
            return -1, b"", b"TimeoutError"

    async def _fast_upload(self, call, file_path, target_chat_id, reply_id, caption, attrs=None, file_size=None):
        """Turbo async chunked upload — force_document for speed, 1s progress with MB/s."""
        if file_size is None:
            try:
                file_size = os.path.getsize(file_path)
            except OSError:
                file_size = 0

        # force_document for files > 50MB — skips Telegram server-side processing
        force_doc = file_size > 50 * 1024 * 1024
        last_update = [0.0]
        start_time = time.time()

        async def progress_cb(current, total):
            now = time.time()
            if now - last_update[0] < 0.8:
                return
            last_update[0] = now
            pct = round((current / total) * 100, 1) if total else 0
            elapsed = now - start_time
            speed = (current / elapsed / 1024 / 1024) if elapsed > 0 else 0
            eta = ((total - current) / (speed * 1024 * 1024)) if speed > 0 else 0
            text = (
                f"<tg-emoji emoji-id=5255971360965930740>🕔</tg-emoji> <b>Apload</b> {pct}% "
                f"<code>{speed:.1f} MB/s</code>"
            )
            if eta > 1:
                text += f" • ~{int(eta)}с"
            with contextlib.suppress(Exception):
                await call.edit(text)

        with contextlib.suppress(Exception):
            await call.edit(
                f"<tg-emoji emoji-id=5255971360965930740>🕔</tg-emoji> <b>Apload</b> 0%"
            )

        kwargs = {
            "entity": target_chat_id,
            "file": file_path,
            "caption": caption,
            "reply_to": reply_id,
            "part_size_kb": 512,
            "progress_callback": progress_cb,
            "force_document": force_doc,
        }
        if attrs:
            kwargs["attributes"] = attrs

        try:
            await self._client.send_file(**kwargs)
        except Exception as e:
            if "reply" in str(e).lower():
                kwargs.pop("reply_to", None)
                await self._client.send_file(**kwargs)
            else:
                raise e

    @loader.inline_handler(
        ru_doc="<ссылка> — быстрое скачивание через inline",
        en_doc="<url> — quick inline media download",
        uk_doc="<посилання> — швидке завантаження через inline",
        de_doc="<url> — schneller Inline-Mediendownload",
        jp_doc="<url> — インラインでメディアをダウンロード",
    )
    async def omni_inline(self, event: InlineQuery):
        """<url> — inline media downloader"""
        url = event.args

        if not url:
            return {
                "title": "OmniLoad",
                "description": self.strings("no_args"),
                "message": "🔥 <b>OmniLoad:</b> отправь ссылку на видео/аудио для быстрого скачивания.",
                "thumb": "https://raw.githubusercontent.com/sepiol026-wq/goypulse/main/assets/omniload.png"
            }

        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [
            sys.executable, "-m", "yt_dlp", "--no-warnings", "--dump-json",
            "--extractor-args", "youtube:player_client=android",
            "--ffmpeg-location", ffmpeg_path, url
        ]

        ret, stdout, stderr = await self._run_proc(cmd, timeout=self.config["inline_timeout"])

        if ret != 0 or not stdout:
            await event.e404()
            return

        try:
            info = json.loads(stdout.decode('utf-8').split('\n')[0])
        except json.JSONDecodeError:
            await event.e500()
            return

        formats = info.get("formats", [])
        heights = {}
        for f in formats:
            vcodec = f.get("vcodec", "none")
            h = f.get("height")
            if vcodec and vcodec != "none" and h and h > 0:
                if h not in heights or (
                    f.get("filesize") or 0
                ) > (heights[h].get("filesize") or 0):
                    heights[h] = f

        sorted_heights = sorted(heights.keys(), reverse=True)
        label_map = []
        seen_labels = set()
        for h in sorted_heights:
            if h >= 4320:
                lbl = "8K"
            elif h >= 2160:
                lbl = "4K"
            elif h >= 1440:
                lbl = "2K"
            elif h >= 1080:
                lbl = "1080p"
            elif h >= 720:
                lbl = "720p"
            elif h >= 480:
                lbl = "480p"
            elif h >= 360:
                lbl = "360p"
            else:
                lbl = f"{h}p"
            if lbl not in seen_labels:
                seen_labels.add(lbl)
                label_map.append((lbl, h))

        cache_id = str(uuid.uuid4())[:8]
        if len(self._inline_cache) >= 50:
            self._inline_cache.pop(next(iter(self._inline_cache)))
        self._inline_cache[cache_id] = {"info": info, "url": url}

        title = info.get("title", "Unknown")[:40]
        author = info.get("uploader", info.get("channel", "Unknown User"))

        results = []

        markup = self.inline.generate_markup([[
            {
                "text": "⚡ Instant",
                "callback": self._inline_dl_callback,
                "args": (cache_id, "bestvideo+bestaudio[ext=m4a]/best[ext=mp4]/best", "video"),
            }
        ]])

        results.append(await event.builder.article(
            id=f"om_{cache_id}_instant",
            title=f"⚡ Instant — {utils.escape_html(title)}",
            description=author,
            text=f"🎬 <b>{utils.escape_html(title)}</b>\n👤 {utils.escape_html(author)}\n\n⚡ Instant download",
            parse_mode="HTML",
            buttons=markup,
            link_preview=False
        ))

        for lbl, h in label_map[:5]:
            fmt = heights[h]
            fid = fmt["format_id"]
            spec = f"{fid}+bestaudio[ext=m4a]/best[ext=mp4]/best"

            markup = self.inline.generate_markup([[
                {
                    "text": f"⬇ {lbl}",
                    "callback": self._inline_dl_callback,
                    "args": (cache_id, spec, "video"),
                }
            ]])

            results.append(await event.builder.article(
                id=f"om_{cache_id}_{lbl}",
                title=f"🎬 {lbl} — {utils.escape_html(title)}",
                description=author,
                text=f"🎬 <b>{utils.escape_html(title)}</b> — {lbl}\n👤 {utils.escape_html(author)}",
                parse_mode="HTML",
                buttons=markup,
                link_preview=False
            ))

        markup = self.inline.generate_markup([[
            {
                "text": "🎵 Audio",
                "callback": self._inline_dl_callback,
                "args": (cache_id, "bestaudio[ext=m4a]/best", "audio"),
            }
        ]])

        results.append(await event.builder.article(
            id=f"om_{cache_id}_audio",
            title=f"🎵 Audio — {utils.escape_html(title)}",
            description=author,
            text=f"🎵 <b>{utils.escape_html(title)}</b>\n👤 {utils.escape_html(author)}",
            parse_mode="HTML",
            buttons=markup,
            link_preview=False
        ))

        await event.answer(results, cache_time=0)

    async def _inline_dl_callback(
        self,
        call: InlineCall,
        cache_id: str,
        format_spec: str,
        media_type: str,
    ):
        await call.answer("⬇ Starting download...")

        data = self._inline_cache.pop(cache_id, None)
        if not data:
            await call.answer("❌ Cache expired. Try again.", show_alert=True)
            return

        info = data["info"]
        url = data["url"]
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        user_id = call.from_user.id

        with contextlib.suppress(Exception):
            await call.edit(
                text=f"<b>⬇ Downloading...</b>\n🎬 {utils.escape_html(info.get('title', 'Unknown')[:40])}",
                parse_mode="HTML",
            )

        dl_dir = tempfile.mkdtemp(prefix="omniload_")

        try:
            cmd = [
                sys.executable,
                "-m",
                "yt_dlp",
                "--format",
                format_spec,
                "--extractor-args",
                "youtube:player_client=android",
                "--ffmpeg-location",
                ffmpeg_path,
                "-o",
                os.path.join(dl_dir, "%(id)s.%(ext)s"),
                "--no-playlist",
                "--concurrent-fragments", "16",
                "--buffer-size", "16K",
                "--no-check-certificates",
            ]

            if media_type in ("audio", "flac"):
                ext = "flac" if media_type == "flac" else "mp3"
                cmd.extend(["-x", "--audio-format", ext])

            ret, stdout, stderr = await self._run_proc(
                cmd, timeout=self.config["ytdl_timeout"]
            )

            if ret != 0:
                err_text = (
                    stderr.decode("utf-8", errors="ignore")[-150:]
                    if stderr
                    else "Unknown error"
                )
                with contextlib.suppress(Exception):
                    await call.edit(
                        text=f"<b>❌ Download failed:</b>\n<code>{utils.escape_html(err_text)}</code>",
                        parse_mode="HTML",
                    )
                return

            files = [
                f
                for f in os.listdir(dl_dir)
                if os.path.isfile(os.path.join(dl_dir, f))
                and not f.endswith(".part")
                and not f.endswith(".ytdl")
            ]

            if not files:
                with contextlib.suppress(Exception):
                    await call.edit(
                        text="<b>❌ No output file</b>", parse_mode="HTML"
                    )
                return

            final_path = os.path.join(dl_dir, files[0])

            title = info.get("title", "Unknown")
            author = info.get("uploader", info.get("channel", "Unknown User"))
            duration = int(info.get("duration") or 0)

            caption = self.strings("caption").format(
                title=utils.escape_html(title),
                author=utils.escape_html(author),
                url=url,
            )

            attrs = None
            if media_type == "video":
                w = int(info.get("width") or 0)
                h = int(info.get("height") or 0)
                if w > 0 and h > 0:
                    attrs = [
                        DocumentAttributeVideo(
                            duration=duration, w=w, h=h, supports_streaming=True
                        )
                    ]
            else:
                attrs = [
                    DocumentAttributeAudio(
                        duration=duration, title=title, performer=author
                    )
                ]

            await self._fast_upload(
                call, final_path, user_id, None, caption, attrs
            )

            with contextlib.suppress(Exception):
                await call.edit(
                    text=f"✅ <b>Sent to PM!</b>\n🎬 {utils.escape_html(title[:40])}",
                    parse_mode="HTML",
                )

        except Exception as e:
            with contextlib.suppress(Exception):
                await call.edit(
                    text=f"<b>❌ Error:</b>\n<code>{utils.escape_html(str(e)[:100])}</code>",
                    parse_mode="HTML",
                )
        finally:
            shutil.rmtree(dl_dir, ignore_errors=True)

    @loader.command(
        ru_doc="<ссылка> - Скачать медиа (Видео/Аудио) из любого сервиса",
        en_doc="<url> - Download media (Video/Audio) from any service",
        de_doc="<url> - Medien (Video/Audio) herunterladen",
        jp_doc="<url> - メディア（ビデオ/オーディオ）をダウンロード"
    )
    async def dlcmd(self, message: Message):
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, self.strings("no_args"))

        force = False
        if args.endswith(" --force"):
            args = args[:-len(" --force")].strip()
            force = True
        elif args.endswith(" -f"):
            args = args[:-len(" -f")].strip()
            force = True

        msg = await utils.answer(message, self.strings("fetching"))
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

        cmd = [
            sys.executable, "-m", "yt_dlp", "--no-warnings", "--dump-json",
            "--extractor-args", "youtube:player_client=android",
            "--ffmpeg-location", ffmpeg_path, args
        ]

        ret, stdout, stderr = await self._run_proc(cmd, timeout=45)

        if ret != 0 or not stdout:
            err_text = stderr.decode('utf-8', errors='ignore')[-100:]
            return await utils.answer(msg, self.strings("error").format(error=err_text or "Extraction failed"))

        try:
            info = json.loads(stdout.decode('utf-8').split('\n')[0])
        except json.JSONDecodeError:
            return await utils.answer(msg, self.strings("error").format(error="JSON Parse failed"))

        call_id = str(message.id)
        target_chat_id = utils.get_chat_id(message)
        reply_id = message.id

        if force:
            formats = info.get("formats", [])
            is_video = any(
                (f.get("vcodec") and f.get("vcodec") != "none" and (f.get("height") or 0) > 0)
                for f in formats
            ) if formats else False
            format_spec = "bestvideo+bestaudio[ext=m4a]/best[ext=mp4]/best" if is_video else "bestaudio[ext=m4a]/best"
            media_type = "video" if is_video else "audio"
            self._cache[call_id] = {"info": info, "url": args}
            await self._do_download(msg, call_id, format_spec, media_type, target_chat_id, reply_id, info, args, ffmpeg_path, force=True)
            return

        self._cache[call_id] = {"info": info, "url": args}
        title = info.get("title", "Unknown")[:40]

        keyboard = self._build_formats(info, call_id, target_chat_id, reply_id)

        await self.inline.form(
            self.strings("menu").format(title=utils.escape_html(title)),
            message=msg,
            reply_markup=keyboard
        )

    def _build_formats(self, info: dict, call_id: str, target_chat_id: int, reply_id: int) -> list:
        formats = info.get("formats", [])
        heights = {}
        for f in formats:
            vcodec = f.get("vcodec", "none")
            h = f.get("height")
            if vcodec and vcodec != "none" and h and h > 0:
                if h not in heights or (f.get("filesize") or 0) > (heights[h].get("filesize") or 0):
                    heights[h] = f

        sorted_heights = sorted(heights.keys(), reverse=True)
        label_map = []
        seen_labels = set()
        for h in sorted_heights:
            if h >= 4320:
                lbl = "8K"
            elif h >= 2160:
                lbl = "4K"
            elif h >= 1440:
                lbl = "2K"
            elif h >= 1080:
                lbl = "1080p"
            elif h >= 720:
                lbl = "720p"
            elif h >= 480:
                lbl = "480p"
            elif h >= 360:
                lbl = "360p"
            else:
                lbl = f"{h}p"
            if lbl not in seen_labels:
                seen_labels.add(lbl)
                label_map.append((lbl, h))

        keyboard = []
        row = []
        for lbl, h in label_map[:6]:
            fmt = heights[h]
            fid = fmt["format_id"]
            spec = f"{fid}+bestaudio[ext=m4a]/best[ext=mp4]/best"
            row.append({"text": f"🎬 {lbl}", "callback": self._dl_callback, "args": (call_id, spec, "video", target_chat_id, reply_id)})
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        keyboard.append([
            {"text": "🎧 MP3", "callback": self._dl_callback, "args": (call_id, "bestaudio/best", "audio", target_chat_id, reply_id)},
            {"text": "🎧 FLAC", "callback": self._dl_callback, "args": (call_id, "bestaudio/best", "flac", target_chat_id, reply_id)}
        ])
        keyboard.append([{"text": "❌ Cancel", "callback": self._cancel_callback, "args": (call_id,)}])
        return keyboard

    async def _do_download(self, call, call_id: str, format_spec: str, media_type: str, target_chat_id: int, reply_id: int, info: dict, url: str, ffmpeg_path: str, force: bool = False):
        dl_dir = tempfile.mkdtemp(prefix="omniload_")

        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--format", format_spec,
            "--extractor-args", "youtube:player_client=android",
            "--ffmpeg-location", ffmpeg_path,
            "-o", os.path.join(dl_dir, "%(id)s.%(ext)s"),
            "--no-playlist",
            "--concurrent-fragments", "16",
            "--buffer-size", "16K",
            "--no-check-certificates",
        ]

        if not force:
            cmd.append("--embed-metadata")

        if media_type == "video":
            cmd.extend(["--merge-output-format", "mp4"])
        elif media_type in ("audio", "flac"):
            ext = "flac" if media_type == "flac" else "mp3"
            cmd.extend(["-x", "--audio-format", ext])

        cmd.append(url)

        ret, _, stderr = await self._run_proc(cmd, timeout=self.config["ytdl_timeout"])

        try:
            out_files = [f for f in os.listdir(dl_dir) if os.path.isfile(os.path.join(dl_dir, f))]
            target_file = out_files[0] if out_files else None

            if ret != 0 or not target_file:
                err_text = stderr.decode('utf-8', errors='ignore')[-100:]
                with contextlib.suppress(Exception):
                    await call.edit(self.strings("error").format(error=err_text or "Download failed"))
                return

            final_path = os.path.join(dl_dir, target_file)

            title = info.get("title", "Unknown")
            author = info.get("uploader", info.get("channel", "Unknown User"))
            duration = int(info.get("duration") or 0)

            caption = self.strings("caption").format(
                title=utils.escape_html(title),
                author=utils.escape_html(author),
                url=url
            )

            if info.get("tags"):
                tags_str = " ".join([f"#{t.replace(' ', '_')}" for t in info["tags"][:5]])
                caption += f"\n\n{tags_str}"

            attrs = None
            if media_type == "video":
                w = int(info.get("width") or 0)
                h = int(info.get("height") or 0)
                if w > 0 and h > 0:
                    attrs = [DocumentAttributeVideo(
                        duration=duration,
                        w=w,
                        h=h,
                        supports_streaming=True
                    )]
            else:
                attrs = [DocumentAttributeAudio(
                    duration=duration,
                    title=title,
                    performer=author
                )]

            await self._fast_upload(
                call, final_path, target_chat_id, reply_id, caption, attrs
            )

            with contextlib.suppress(Exception):
                await call.delete()

        except Exception as upload_err:
            err_msg = self.strings("error").format(error=f"Send Error: {upload_err}")
            try:
                await call.edit(err_msg)
            except Exception:
                await self._client.send_message(target_chat_id, err_msg)

        finally:
            shutil.rmtree(dl_dir, ignore_errors=True)

    async def _dl_callback(self, call, call_id: str, format_spec: str, media_type: str, target_chat_id: int, reply_id: int):
        with contextlib.suppress(Exception):
            await call.answer("<tg-emoji emoji-id=5253613479754999811>➡️</tg-emoji> Processing...")

        if call_id not in self._cache:
            with contextlib.suppress(Exception):
                await call.edit(self.strings("expired"), reply_markup=None)
            return

        with contextlib.suppress(Exception):
            await call.edit(self.strings("downloading"), reply_markup=None)

        data = self._cache.pop(call_id)
        info = data["info"]
        url = data["url"]
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

        await self._do_download(call, call_id, format_spec, media_type, target_chat_id, reply_id, info, url, ffmpeg_path)

    async def _cancel_callback(self, call, call_id: str):
        self._cache.pop(call_id, None)
        with contextlib.suppress(Exception):
            await call.answer("Canceled")
        with contextlib.suppress(Exception):
            await call.delete()
