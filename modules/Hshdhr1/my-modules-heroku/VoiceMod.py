# meta developer: @space_modules, Gemini 3.8 Flash
# Name: VoiceMod
# meta link: https://raw.githubusercontent.com/Hshdhr1/my-modules-heroku/main/VoiceMod.py
# meta banner: https://raw.githubusercontent.com/Hshdhr1/my-modules-heroku/main/banner_voicemod.jpg
# meta pic: https://raw.githubusercontent.com/Hshdhr1/my-modules-heroku/main/banner_voicemod.jpg
# meta fhsdesc: voicemod, voice, music, audio, video, player, radio, stream, стрим, музыка, видео, голосовой чат, войс, плейлист
# meta tags: voice, music, audio, video, player, стрим, музыка
# meta license: AGPL-3.0
# scope: heroku
# packages: ffmpeg
# requires: yt-dlp py-tgcalls
#
# ©️ Ne_Xomyahok (@space_modules), 2026
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html
#
# При любом распространении или модификации весь код обязан оставаться открытым
# под лицензией GNU AGPLv3 с обязательным сохранением авторства (@space_modules).
# Запрещается закрывать исходный код или использовать его в проприетарных форках.

__version__ = (2, 6, 0)

import asyncio
import atexit
import builtins
import contextlib
import importlib
import importlib.machinery
import importlib.util
import inspect
import logging
import os
import platform
import re
import shutil
import site
import sys
import tarfile
import tempfile
import time
import traceback
import urllib.request
import uuid
import zipfile
from typing import Any, Dict, List, Optional, Tuple

from telethon.tl import functions, types
from telethon.tl.types import Message

from .. import loader, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)

def _ensure_site_packages():
    home = os.path.expanduser("~")
    py_ver = f"python{sys.version_info.major}.{sys.version_info.minor}"
    candidates = [
        f"/root/.local/lib/{py_ver}/site-packages",
        f"/root/.local/lib/python3/site-packages",
        os.path.join(home, ".local", "lib", py_ver, "site-packages"),
        os.path.join(home, ".local", "lib", "python3", "site-packages"),
        f"/usr/local/lib/{py_ver}/site-packages",
        f"/usr/local/lib/{py_ver}/dist-packages",
        f"/usr/lib/{py_ver}/site-packages",
        f"/usr/lib/{py_ver}/dist-packages",
    ]

    try:
        user_site = site.getusersitepackages()
        if user_site and user_site not in candidates:
            candidates.insert(0, user_site)
    except Exception:
        pass

    for base in (home, "/root", "/var/root"):
        local_lib = os.path.join(base, ".local", "lib")
        if os.path.isdir(local_lib):
            try:
                for entry in os.scandir(local_lib):
                    if entry.is_dir() and entry.name.startswith("python"):
                        sp = os.path.join(entry.path, "site-packages")
                        if os.path.isdir(sp) and sp not in candidates:
                            candidates.insert(0, sp)
            except Exception:
                pass

    for p in candidates:
        if os.path.isdir(p):
            with contextlib.suppress(Exception):
                site.addsitedir(p)
            if p not in sys.path:
                sys.path.insert(0, p)

_ensure_site_packages()

HAS_PYTGCALLS = False
HAS_GROUP_CALL_FACTORY = False
PyTgCallsClass = None
GroupCallFactoryClass = None
MediaStreamClass = None
AudioPipedClass = None
AudioVideoPipedClass = None
RecordStreamClass = None
HighQualityAudioClass = None
HighQualityVideoClass = None
AudioQualityClass = None
VideoQualityClass = None
StreamTypeClass = None
PYTGCALLS_VERSION = "unknown"
PYTGCALLS_IMPORT_ERROR: Optional[str] = None


def _fix_heroku_import_hook():
    orig_import = builtins.__import__
    if getattr(orig_import, "_voicemod_fixed", False):
        return

    loader_mod = sys.modules.get("heroku.loader") or sys.modules.get("loader")
    native_import = getattr(loader_mod, "native_import", None) or importlib.__import__

    def _fixed_import(name, *args, **kwargs):
        level = kwargs.get("level", args[3] if len(args) >= 4 else 0)
        if (level > 0 and name.startswith("telethon")) or (
            name.startswith("telethon") and name != "telethon" and not name.startswith("telethon.")
        ):
            return native_import(name, *args, **kwargs)
        return orig_import(name, *args, **kwargs)

    _fixed_import._voicemod_fixed = True
    builtins.__import__ = _fixed_import

    if loader_mod and hasattr(loader_mod, "patched_import"):
        with contextlib.suppress(Exception):
            loader_mod_orig_native = getattr(loader_mod, "native_import", importlib.__import__)
            orig_patched = loader_mod.patched_import
            if not getattr(orig_patched, "_voicemod_fixed", False):
                def _loader_fixed_import(name, *args, **kwargs):
                    level = kwargs.get("level", args[3] if len(args) >= 4 else 0)
                    if (level > 0 and name.startswith("telethon")) or (
                        name.startswith("telethon") and name != "telethon" and not name.startswith("telethon.")
                    ):
                        return loader_mod_orig_native(name, *args, **kwargs)
                    return orig_patched(name, *args, **kwargs)

                _loader_fixed_import._voicemod_fixed = True
                loader_mod.patched_import = _loader_fixed_import


def _alias_pytgcalls_telethon_client():
    _fix_heroku_import_hook()
    try:
        import pytgcalls.mtproto.telethon_client as tc_mod
        sys.modules["pytgcalls.mtproto.herokutl_client"] = tc_mod
        mt_mod = sys.modules.get("pytgcalls.mtproto")
        if mt_mod:
            setattr(mt_mod, "herokutl_client", tc_mod)
    except Exception:
        pass


_fix_heroku_import_hook()


def _setup_telethon_alias():
    _fix_heroku_import_hook()
    _alias_pytgcalls_telethon_client()
    try:
        class _TelethonAliasLoader:
            def __init__(self, mod):
                self._mod = mod

            def create_module(self, spec):
                return self._mod

            def exec_module(self, module):
                pass

        class _TelethonAliasFinder:
            @classmethod
            def find_spec(cls, fullname: str, path=None, target=None):
                if fullname == "telethon" or fullname.startswith("telethon."):
                    alt_name = "herokutl" + fullname[8:]
                    try:
                        alt_mod = importlib.import_module(alt_name)
                        is_pkg = hasattr(alt_mod, "__path__")
                        loader = _TelethonAliasLoader(alt_mod)
                        spec = importlib.machinery.ModuleSpec(fullname, loader, is_package=is_pkg)
                        if is_pkg:
                            spec.submodule_search_locations = list(alt_mod.__path__)
                        return spec
                    except Exception:
                        pass
                return None

        if not any(getattr(f, "__name__", "") == "_TelethonAliasFinder" for f in sys.meta_path):
            sys.meta_path.insert(0, _TelethonAliasFinder)

        target_base = None
        for b in ("herokutl", "telethon"):
            if b in sys.modules:
                target_base = sys.modules[b]
                break
        if not target_base:
            with contextlib.suppress(Exception):
                target_base = importlib.import_module("herokutl")
        if target_base:
            base_name = getattr(target_base, "__name__", "herokutl")
            sys.modules.setdefault("telethon", target_base)
            for m_name, mod in list(sys.modules.items()):
                if m_name.startswith(f"{base_name}."):
                    alias = "telethon" + m_name[len(base_name):]
                    sys.modules.setdefault(alias, mod)
    except Exception as e:
        logger.debug(f"[VoiceMod] telethon alias error: {e}")


def _patch_bridged_client():
    patched = False

    bc_mod = sys.modules.get("pytgcalls.mtproto.bridged_client")
    if bc_mod and hasattr(bc_mod, "BridgedClient"):
        bc_mod.BridgedClient.package_name = staticmethod(lambda obj: "telethon")
        patched = True
        logger.debug("[VoiceMod] BridgedClient patched via sys.modules")

    mc_mod = sys.modules.get("pytgcalls.mtproto.mtproto_client")
    if mc_mod and hasattr(mc_mod, "BridgedClient"):
        mc_mod.BridgedClient.package_name = staticmethod(lambda obj: "telethon")
        patched = True
        logger.debug("[VoiceMod] BridgedClient patched via mtproto_client module")

    if not patched:
        try:
            from pytgcalls.mtproto.bridged_client import BridgedClient
            BridgedClient.package_name = staticmethod(lambda obj: "telethon")
            patched = True
            logger.debug("[VoiceMod] BridgedClient patched via direct import")
        except Exception as e:
            logger.warning(f"[VoiceMod] BridgedClient patch FAILED: {e}")

    try:
        env_mod = sys.modules.get("pytgcalls.environment")
        if env_mod and hasattr(env_mod, "Environment"):
            env_mod.Environment.check_environment = lambda self: None
        else:
            from pytgcalls.environment import Environment
            Environment.check_environment = lambda self: None
    except Exception as e:
        logger.debug(f"[VoiceMod] Environment patch error: {e}")

    _alias_pytgcalls_telethon_client()
    return patched


def _patch_telethon_client():
    try:
        tc_mod = sys.modules.get("pytgcalls.mtproto.telethon_client")
        if not tc_mod or not hasattr(tc_mod, "TelethonClient"):
            logger.debug("[VoiceMod] TelethonClient not in sys.modules, skipping patch")
            return
        TelethonClientCls = tc_mod.TelethonClient

        async def _patched_start(self):
            pass
        TelethonClientCls.start = _patched_start
        logger.debug("[VoiceMod] TelethonClient.start patched (no-op)")

        async def _patched_resolve_peer(self, user_id):
            try:
                return await self._app.get_input_entity(user_id)
            except Exception:
                with contextlib.suppress(Exception):
                    me = await self._app.get_me()
                    me_id = getattr(me, "id", None)
                    if me_id and (user_id == me_id or user_id in ("me", "self")):
                        from telethon.tl.types import InputPeerSelf
                        return InputPeerSelf()
                raise
        TelethonClientCls.resolve_peer = _patched_resolve_peer
        logger.debug("[VoiceMod] TelethonClient.resolve_peer patched")
    except Exception as e:
        logger.debug(f"[VoiceMod] TelethonClient patch error: {e}")


def _try_import_pytgcalls() -> Tuple[bool, Optional[str]]:
    global HAS_PYTGCALLS, PyTgCallsClass, PYTGCALLS_VERSION, PYTGCALLS_IMPORT_ERROR
    global GroupCallFactoryClass, HAS_GROUP_CALL_FACTORY
    global MediaStreamClass, AudioPipedClass, AudioVideoPipedClass, RecordStreamClass
    global HighQualityAudioClass, HighQualityVideoClass, AudioQualityClass, VideoQualityClass, StreamTypeClass

    _ensure_site_packages()
    _setup_telethon_alias()
    importlib.invalidate_caches()

    try:
        import pytgcalls
        HAS_PYTGCALLS = True
        PYTGCALLS_VERSION = getattr(pytgcalls, "__version__", "unknown")
    except Exception as e:
        HAS_PYTGCALLS = False
        PyTgCallsClass = None
        tb = traceback.format_exc()
        PYTGCALLS_IMPORT_ERROR = f"{e.__class__.__name__}: {e}\n{tb[-300:]}".strip()
        return False, PYTGCALLS_IMPORT_ERROR

    _patch_bridged_client()
    _alias_pytgcalls_telethon_client()

    try:
        from pytgcalls import PyTgCalls
        PyTgCallsClass = PyTgCalls
    except Exception as e:
        HAS_PYTGCALLS = False
        PyTgCallsClass = None
        tb = traceback.format_exc()
        PYTGCALLS_IMPORT_ERROR = f"PyTgCalls import: {e}\n{tb[-300:]}".strip()
        return False, PYTGCALLS_IMPORT_ERROR

    for mod_name in (
        "pytgcalls.types",
        "pytgcalls.types.stream",
        "pytgcalls.types.input_stream",
        "pytgcalls",
    ):
        try:
            m = importlib.import_module(mod_name)
            if hasattr(m, "MediaStream") and MediaStreamClass is None:
                MediaStreamClass = getattr(m, "MediaStream")
            if hasattr(m, "RecordStream") and RecordStreamClass is None:
                RecordStreamClass = getattr(m, "RecordStream")
            if hasattr(m, "AudioPiped") and AudioPipedClass is None:
                AudioPipedClass = getattr(m, "AudioPiped")
            if hasattr(m, "AudioVideoPiped") and AudioVideoPipedClass is None:
                AudioVideoPipedClass = getattr(m, "AudioVideoPiped")
            if hasattr(m, "AudioQuality") and AudioQualityClass is None:
                AudioQualityClass = getattr(m, "AudioQuality")
            if hasattr(m, "VideoQuality") and VideoQualityClass is None:
                VideoQualityClass = getattr(m, "VideoQuality")
            if hasattr(m, "StreamType") and StreamTypeClass is None:
                StreamTypeClass = getattr(m, "StreamType")
        except Exception:
            pass

    if AudioPipedClass is None and MediaStreamClass is not None:
        AudioPipedClass = MediaStreamClass

    for mod_name in (
        "pytgcalls.types.input_stream.quality",
        "pytgcalls.types.stream.quality",
        "pytgcalls.types.quality",
        "pytgcalls.types",
    ):
        try:
            m = importlib.import_module(mod_name)
            if hasattr(m, "HighQualityAudio") and HighQualityAudioClass is None:
                HighQualityAudioClass = getattr(m, "HighQualityAudio")
            if hasattr(m, "HighQualityVideo") and HighQualityVideoClass is None:
                HighQualityVideoClass = getattr(m, "HighQualityVideo")
        except Exception:
            pass

    try:
        from pytgcalls import GroupCallFactory
        GroupCallFactoryClass = GroupCallFactory
        HAS_GROUP_CALL_FACTORY = True
    except Exception:
        pass

    PYTGCALLS_IMPORT_ERROR = None
    return True, None


_try_import_pytgcalls()


@loader.tds
class VoiceMod(loader.Module):
    """Модуль для воспроизведения музыки, аудио и видео в голосовых чатах Telegram."""

    strings = {
        "name": "VoiceMod",
        "no_args": "<b>[VoiceMod]</b> ❌ Provide a link, search query, or reply to audio/video!",
        "searching": "<b>[VoiceMod]</b> 🔍 Searching and processing track...",
        "downloading": "<b>[VoiceMod]</b> 📥 Downloading audio...",
        "converting": "<b>[VoiceMod]</b> ⚙️ Converting...",
        "playing": (
            "<b>[VoiceMod] 🎧 Now Playing:</b>\n"
            "🎵 <b>Track:</b> <code>{title}</code>\n"
            "⏱ <b>Duration:</b> <code>{duration}</code>\n"
            "👤 <b>Requested by:</b> {requester}\n"
            "📊 <b>Queue:</b> <code>{queue_len}</code>"
        ),
        "playing_video": (
            "<b>[VoiceMod] 🎬 Now Streaming Video:</b>\n"
            "📹 <b>Video:</b> <code>{title}</code>\n"
            "⏱ <b>Duration:</b> <code>{duration}</code>\n"
            "👤 <b>Requested by:</b> {requester}\n"
            "📊 <b>Queue:</b> <code>{queue_len}</code>"
        ),
        "queued": (
            "<b>[VoiceMod] 📥 Added to queue (#{pos}):</b>\n"
            "{icon} <code>{title}</code> (⏱ {duration})"
        ),
        "paused": "<b>[VoiceMod]</b> ⏸ Playback paused.",
        "resumed": "<b>[VoiceMod]</b> ▶️ Playback resumed.",
        "muted": "<b>[VoiceMod]</b> 🔇 Microphone muted.",
        "unmuted": "<b>[VoiceMod]</b> 🔈 Microphone unmuted.",
        "skipped": "<b>[VoiceMod]</b> ⏭ Track skipped.",
        "stopped": "<b>[VoiceMod]</b> ⏹ Playback stopped, queue cleared.",
        "joined": "<b>[VoiceMod]</b> 🎙 Joined voice chat.",
        "left": "<b>[VoiceMod]</b> 🚪 Left voice chat.",
        "not_joined": "<b>[VoiceMod]</b> ❌ Not in a voice chat (use {p}vplay or {p}vjoin).",
        "empty_queue": "<b>[VoiceMod]</b> 📭 Queue is empty.",
        "queue_title": "<b>[VoiceMod] 📋 Track Queue ({count}):</b>\n\n{items}",
        "btn_pause": "⏸ Pause",
        "btn_resume": "▶️ Resume",
        "btn_mute": "🔇 Mute",
        "btn_unmute": "🔈 Unmute",
        "btn_skip": "⏭ Skip",
        "btn_stop": "⏹ Stop",
        "btn_queue": "📋 Queue",
        "btn_repeat_on": "🔂 Repeat: ON",
        "btn_repeat_off": "🔁 Repeat: OFF",
        "repeat_on": "<b>[VoiceMod]</b> 🔂 Loop track enabled.",
        "repeat_off": "<b>[VoiceMod]</b> 🔁 Loop track disabled.",
        "btn_close": "❌ Close",
        "error": "<b>[VoiceMod] ⚠️ Error:</b> <code>{err}</code>",
        "no_pytgcalls": (
            "<b>[VoiceMod] ❌ py-tgcalls library is not installed or failed to start!</b>\n"
            "⚠️ <b>Error:</b> <code>{err}</code>\n\n"
            "Install and verify it directly: <code>{p}vinstall</code>\n"
            "<i>(or via terminal: <code>{p}terminal pip install py-tgcalls yt-dlp</code>)</i>\n"
            "After install, restart userbot: <code>{p}restart</code>"
        ),
        "no_active_vc": (
            "<b>[VoiceMod] ❌ No active voice chat in this chat!</b>\n"
            "Please start a voice chat in the group first."
        ),
        "ffmpeg_missing": (
            "<b>[VoiceMod] ❌ FFmpeg is not found in your system!</b>\n\n"
            "FFmpeg is required to stream audio in voice chats.\n"
            "Install it automatically using: <code>{p}vinstallffmpeg</code>"
        ),
        "ffmpeg_installed": (
            "<b>[VoiceMod] ✅ FFmpeg successfully installed and ready!</b>\n\n"
            "📍 <b>Path:</b> <code>{path}</code>\n"
            "ℹ️ <b>Version:</b> <code>{version}</code>"
        ),
        "ffmpeg_already": (
            "<b>[VoiceMod] ℹ️ FFmpeg is already installed!</b>\n\n"
            "📍 <b>Path:</b> <code>{path}</code>\n"
            "ℹ️ <b>Version:</b> <code>{version}</code>\n\n"
            "<i>To force reinstallation:</i> <code>{p}vinstallffmpeg -f</code>"
        ),
        "ffmpeg_installing": (
            "<b>[VoiceMod]</b> ⏳ <b>Installing FFmpeg...</b>\n"
            "<i>{status}</i>"
        ),
        "ffmpeg_error": (
            "<b>[VoiceMod] ⚠️ FFmpeg installation failed:</b>\n"
            "<code>{err}</code>\n\n"
            "<i>Try installing it manually via your system's package manager.</i>"
        ),
    }

    strings_ru = {
        "name": "VoiceMod",
        "no_args": "<b>[VoiceMod]</b> ❌ Укажите ссылку, поисковый запрос или ответьте на аудио/видео!",
        "searching": "<b>[VoiceMod]</b> 🔍 Поиск и обработка трека...",
        "downloading": "<b>[VoiceMod]</b> 📥 Загрузка аудио...",
        "converting": "<b>[VoiceMod]</b> ⚙️ Конвертация...",
        "playing": (
            "<b>[VoiceMod] 🎧 Сейчас играет:</b>\n"
            "🎵 <b>Трек:</b> <code>{title}</code>\n"
            "⏱ <b>Длительность:</b> <code>{duration}</code>\n"
            "👤 <b>Запросил:</b> {requester}\n"
            "📊 <b>В очереди:</b> <code>{queue_len}</code>"
        ),
        "playing_video": (
            "<b>[VoiceMod] 🎬 Сейчас транслируется видео:</b>\n"
            "📹 <b>Видео:</b> <code>{title}</code>\n"
            "⏱ <b>Длительность:</b> <code>{duration}</code>\n"
            "👤 <b>Запросил:</b> {requester}\n"
            "📊 <b>В очереди:</b> <code>{queue_len}</code>"
        ),
        "queued": (
            "<b>[VoiceMod] 📥 Добавлено в очередь (#{pos}):</b>\n"
            "🎵 <code>{title}</code> (⏱ {duration})"
        ),
        "paused": "<b>[VoiceMod]</b> ⏸ Воспроизведение приостановлено.",
        "resumed": "<b>[VoiceMod]</b> ▶️ Воспроизведение возобновлено.",
        "muted": "<b>[VoiceMod]</b> 🔇 Микрофон заглушен.",
        "unmuted": "<b>[VoiceMod]</b> 🔈 Микрофон включен.",
        "skipped": "<b>[VoiceMod]</b> ⏭ Трек пропущен.",
        "stopped": "<b>[VoiceMod]</b> ⏹ Воспроизведение остановлено, очередь очищена.",
        "joined": "<b>[VoiceMod]</b> 🎙 Подключился к голосовому чату.",
        "left": "<b>[VoiceMod]</b> 🚪 Покинул голосовой чат.",
        "not_joined": "<b>[VoiceMod]</b> ❌ Бот не находится в голосовом чате (используйте {p}vplay или {p}vjoin).",
        "empty_queue": "<b>[VoiceMod]</b> 📭 Очередь пуста.",
        "queue_title": "<b>[VoiceMod] 📋 Очередь воспроизведения ({count}):</b>\n\n{items}",
        "btn_pause": "⏸ Пауза",
        "btn_resume": "▶️ Играть",
        "btn_mute": "🔇 Заглушить",
        "btn_unmute": "🔈 Включить",
        "btn_skip": "⏭ След.",
        "btn_stop": "⏹ Стоп",
        "btn_queue": "📋 Очередь",
        "btn_repeat_on": "🔂 Повтор: ВКЛ",
        "btn_repeat_off": "🔁 Повтор: ВЫКЛ",
        "repeat_on": "<b>[VoiceMod]</b> 🔂 Повтор трека включён.",
        "repeat_off": "<b>[VoiceMod]</b> 🔁 Повтор трека выключен.",
        "btn_close": "❌ Закрыть",
        "error": "<b>[VoiceMod] ⚠️ Ошибка:</b> <code>{err}</code>",
        "no_pytgcalls": (
            "<b>[VoiceMod] ❌ Библиотека py-tgcalls не установлена или не может запуститься!</b>\n"
            "⚠️ <b>Ошибка:</b> <code>{err}</code>\n\n"
            "Установите и проверьте её командой: <code>{p}vinstall</code>\n"
            "<i>(или через терминал: <code>{p}terminal pip install py-tgcalls yt-dlp</code>)</i>\n"
            "После установки перезапустите юзербота: <code>{p}restart</code>"
        ),
        "no_active_vc": (
            "<b>[VoiceMod] ❌ В этом чате нет активного голосового чата!</b>\n"
            "Сначала включите голосовой чат в группе перед подключением."
        ),
        "ffmpeg_missing": (
            "<b>[VoiceMod] ❌ FFmpeg не найден в системе!</b>\n\n"
            "FFmpeg необходим для трансляции звука и конвертации медиа.\n"
            "Установите его автоматически командой: <code>{p}vinstallffmpeg</code>"
        ),
        "ffmpeg_installed": (
            "<b>[VoiceMod] ✅ FFmpeg успешно установлен и готов к работе!</b>\n\n"
            "📍 <b>Путь:</b> <code>{path}</code>\n"
            "ℹ️ <b>Версия:</b> <code>{version}</code>"
        ),
        "ffmpeg_already": (
            "<b>[VoiceMod] ℹ️ FFmpeg уже установлен в системе!</b>\n\n"
            "📍 <b>Путь:</b> <code>{path}</code>\n"
            "ℹ️ <b>Версия:</b> <code>{version}</code>\n\n"
            "<i>Для принудительной переустановки используйте:</i> <code>{p}vinstallffmpeg -f</code>"
        ),
        "ffmpeg_installing": (
            "<b>[VoiceMod]</b> ⏳ <b>Установка FFmpeg...</b>\n"
            "<i>{status}</i>"
        ),
        "ffmpeg_error": (
            "<b>[VoiceMod] ⚠️ Ошибка установки FFmpeg:</b>\n"
            "<code>{err}</code>\n\n"
            "<i>Попробуйте установить вручную через терминал или пакетный менеджер системы.</i>"
        ),
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "auto_leave",
                True,
                lambda: "Автоматически выходить из голосового чата, когда очередь закончится",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "quality",
                "high",
                lambda: "Качество аудио (high / medium / low)",
                validator=loader.validators.Choice(["high", "medium", "low"]),
            ),
            loader.ConfigValue(
                "video_quality",
                "720p",
                lambda: "Качество видео стрима (360p / 480p / 720p / 1080p)",
                validator=loader.validators.Choice(["360p", "480p", "720p", "1080p"]),
            ),
            loader.ConfigValue(
                "auto_reconnect",
                True,
                lambda: "Автоматически переподключаться при неожиданном обрыве стрима",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "max_cache_mb",
                500,
                lambda: "Максимальный размер кеша временных файлов в МБ",
                validator=loader.validators.Integer(minimum=50, maximum=5000),
            ),
        )
        self._temp_dir: Optional[str] = None
        self._queue: Dict[int, List[Dict[str, Any]]] = {}
        self._current: Dict[int, Dict[str, Any]] = {}
        self._calls: Dict[int, Any] = {}
        self._muted: Dict[int, bool] = {}
        self._paused: Dict[int, bool] = {}
        self._repeat: Dict[int, bool] = {}
        self._last_prefix: Optional[str] = None
        self._is_pytgcalls_client: bool = False
        self._tgcalls: Any = None
        self._active_tasks: List[asyncio.Task] = []
        self._recordings: Dict[int, Dict[str, Any]] = {}
        self._expected_leave: set = set()
        self._reconnect_attempts: Dict[int, int] = {}
        self._track_start_time: Dict[int, float] = {}
        self._diag: Dict[str, Any] = {
            "init_error": None,
            "backend": "None",
        }

    async def client_ready(self, client=None, db=None):
        self._client = client or getattr(self, "_client", None) or getattr(self, "client", None)
        self._db = db or getattr(self, "_db", None) or getattr(self, "db", None)
        self._temp_dir = tempfile.mkdtemp(prefix="heroku_voicemod_")
        self._ensure_local_ffmpeg_path()
        self._last_prefix = self._prefix()

        _ensure_site_packages()
        _setup_telethon_alias()
        if self._client and hasattr(self._client, "_no_updates") is False:
            with contextlib.suppress(Exception):
                self._client._no_updates = False

        if self._client:
            success, err = _try_import_pytgcalls()
            if success and PyTgCallsClass is not None:
                try:
                    _patch_bridged_client()
                    _alias_pytgcalls_telethon_client()
                    self._tgcalls = PyTgCallsClass(self._client)
                    _patch_telethon_client()
                    try:
                        self._tgcalls.loop = asyncio.get_running_loop()
                    except Exception:
                        pass
                    start_res = self._tgcalls.start()
                    if inspect.isawaitable(start_res):
                        await start_res
                    self._is_pytgcalls_client = True
                    self._diag["backend"] = f"PyTgCalls (v{PYTGCALLS_VERSION})"
                    self._diag["init_error"] = None

                    if hasattr(self._tgcalls, "on_stream_end"):
                        try:
                            @self._tgcalls.on_stream_end()
                            async def _on_stream_end(app, update):
                                chat_id = getattr(update, "chat_id", None) or getattr(update, "id", None)
                                if chat_id:
                                    task = asyncio.create_task(self._handle_track_end(chat_id))
                                    self._active_tasks.append(task)
                        except Exception as e_stream_end:
                            logger.debug(f"[VoiceMod] on_stream_end handler hook: {e_stream_end}")
                except Exception as e1:
                    logger.warning(f"[VoiceMod] Ошибка запуска PyTgCalls: {e1}")
                    tb1 = traceback.format_exc()
                    self._diag["init_error"] = f"PyTgCalls start error: {e1}\n{tb1[-300:]}".strip()
                    self._is_pytgcalls_client = False
            else:
                self._diag["init_error"] = err or "Библиотека py-tgcalls не установлена"

        if not self._is_pytgcalls_client and HAS_GROUP_CALL_FACTORY:
            self._diag["backend"] = "GroupCallFactory"

    async def _ensure_backend_ready(self) -> bool:
        if self._is_pytgcalls_client and self._tgcalls:
            return True

        client = getattr(self, "_client", None) or getattr(self, "client", None)
        if not client:
            self._diag["init_error"] = "Telegram клиент не готов (client_ready ещё не выполнен)"
            return False
        self._client = client

        success, err = _try_import_pytgcalls()
        if not success or PyTgCallsClass is None:
            self._diag["init_error"] = err or "Библиотека py-tgcalls не установлена"
            return False

        if hasattr(self._client, "_no_updates") is False:
            with contextlib.suppress(Exception):
                self._client._no_updates = False

        try:
            _patch_bridged_client()
            _alias_pytgcalls_telethon_client()
            self._tgcalls = PyTgCallsClass(self._client)
            _patch_telethon_client()
            try:
                self._tgcalls.loop = asyncio.get_running_loop()
            except Exception:
                pass
            start_res = self._tgcalls.start()
            if inspect.isawaitable(start_res):
                await start_res
            self._is_pytgcalls_client = True
            self._diag["backend"] = f"PyTgCalls (v{PYTGCALLS_VERSION})"
            self._diag["init_error"] = None

            if hasattr(self._tgcalls, "on_stream_end"):
                with contextlib.suppress(Exception):
                    @self._tgcalls.on_stream_end()
                    async def _dyn_on_stream_end(app, update):
                        chat_id = getattr(update, "chat_id", None) or getattr(update, "id", None)
                        if chat_id:
                            task = asyncio.create_task(self._handle_track_end(chat_id))
                            self._active_tasks.append(task)
            return True
        except Exception as e:
            logger.warning(f"[VoiceMod] _ensure_backend_ready error: {e}")
            tb2 = traceback.format_exc()
            self._diag["init_error"] = f"PyTgCalls start error: {e}\n{tb2[-300:]}".strip()
            return False



    async def on_unload(self):
        for task in self._active_tasks:
            if not task.done():
                task.cancel()

        for chat_id, rec in list(self._recordings.items()):
            if self._is_pytgcalls_client and self._tgcalls and hasattr(self._tgcalls, "record"):
                with contextlib.suppress(Exception):
                    res = self._tgcalls.record(chat_id, stream=None)
                    if inspect.isawaitable(res):
                        await res

        for chat_id in list(self._calls.keys()):
            with contextlib.suppress(Exception):
                await self._leave_call(chat_id)

        if self._tgcalls and self._is_pytgcalls_client:
            with contextlib.suppress(Exception):
                if hasattr(self._tgcalls, "stop"):
                    res = self._tgcalls.stop()
                    if inspect.isawaitable(res):
                        await res

        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir, ignore_errors=True)

    def _format_duration(self, seconds: Optional[int]) -> str:
        if not seconds or seconds <= 0:
            return "Стрим / Live"
        mins, secs = divmod(int(seconds), 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    def _get_marked_chat_id(self, obj: Any) -> int:
        if obj is None:
            return 0
        try:
            import telethon.utils as tl_utils
            if hasattr(obj, "peer_id") and obj.peer_id is not None:
                return tl_utils.get_peer_id(obj.peer_id)
            if hasattr(obj, "id") and not isinstance(obj, int):
                return tl_utils.get_peer_id(obj)
            if hasattr(obj, "chat_id") and obj.chat_id is not None:
                return obj.chat_id
        except Exception:
            pass

        if isinstance(obj, int):
            if obj < 0:
                return obj
            if obj > 1000000000:
                return -1000000000000 - obj
            return -obj

        raw_id = utils.get_chat_id(obj)
        if raw_id > 0:
            if raw_id > 1000000000:
                return -1000000000000 - raw_id
            return -raw_id
        return raw_id

    async def _ensure_marked_chat_id(self, chat_id: int) -> int:
        if chat_id < 0:
            return chat_id
        try:
            entity = await self._client.get_entity(chat_id)
            import telethon.utils as tl_utils
            marked = tl_utils.get_peer_id(entity)
            if marked < 0:
                return marked
        except Exception:
            pass
        if chat_id > 1000000000:
            return -1000000000000 - chat_id
        return -chat_id

    async def _resolve_target(self, message: Message) -> Tuple[int, Any]:
        args = utils.get_args_raw(message)
        if args:
            parts = args.split(maxsplit=1)
            target = parts[0]
            if target.startswith("-100") or target.startswith("-") or target.isdigit() or target.startswith("@"):
                try:
                    target_val = int(target) if target.lstrip("-").isdigit() else target
                    entity = await self._client.get_entity(target_val)
                    chat_id = self._get_marked_chat_id(entity)
                    return chat_id, entity
                except Exception:
                    pass
        chat = await message.get_chat()
        chat_id = getattr(message, "chat_id", None)
        if chat_id is None and chat:
            chat_id = self._get_marked_chat_id(chat)
        if chat_id is None:
            chat_id = self._get_marked_chat_id(message)
        return chat_id, chat

    async def _get_active_call(self, chat_id: int) -> Optional[types.InputGroupCall]:
        chat_id = await self._ensure_marked_chat_id(chat_id)
        try:
            peer = await self._client.get_input_entity(chat_id)
            if isinstance(peer, types.InputPeerChannel):
                full = await self._client(functions.channels.GetFullChannelRequest(peer))
                return getattr(full.full_chat, "call", None)
            elif isinstance(peer, types.InputPeerChat):
                full = await self._client(functions.messages.GetFullChatRequest(peer.chat_id))
                return getattr(full.full_chat, "call", None)
        except Exception as e:
            logger.debug(f"[VoiceMod] Ошибка проверки group call: {e}")
        return None

    def _ensure_local_ffmpeg_path(self) -> None:
        candidate_dirs = [
            os.path.abspath("ffmpeg_bin"),
            os.path.expanduser("~/.local/bin"),
            os.path.join(tempfile.gettempdir(), "ffmpeg_bin"),
        ]
        path_env = os.environ.get("PATH", "")
        paths = path_env.split(os.pathsep)
        for c_dir in candidate_dirs:
            if os.path.isdir(c_dir):
                has_bin = any(
                    os.path.isfile(os.path.join(c_dir, name))
                    for name in ("ffmpeg", "ffmpeg.exe")
                )
                if has_bin and c_dir not in paths:
                    os.environ["PATH"] = c_dir + os.pathsep + os.environ.get("PATH", "")
                    paths.insert(0, c_dir)

    def _prefix(self, message_or_id: Optional[Any] = None) -> str:
        if message_or_id is not None:
            raw_text = (
                getattr(message_or_id, "raw_text", None)
                or getattr(message_or_id, "message", None)
                or getattr(message_or_id, "text", None)
            )
            if isinstance(raw_text, str) and raw_text:
                stripped = raw_text.strip()
                cmd_names = (
                    "vplay", "vvideo", "vdebug", "vjoin", "vleave", "vstop", "vpause",
                    "vresume", "vmute", "vunmute", "vskip", "vqueue", "vnow",
                    "vquality", "vrecord", "vcache",
                    "vffmpeg", "vinstallffmpeg", "vinstall", "restart", "reload"
                )
                pattern = r"^(.*?)(" + "|".join(cmd_names) + r")(?:\s|$)"
                m = re.match(pattern, stripped, flags=re.IGNORECASE)
                if m:
                    extracted = m.group(1).strip()
                    if extracted:
                        self._last_prefix = extracted
                        return extracted

                m2 = re.match(r"^(\S+?)[a-zA-Zа-яА-Я]", stripped)
                if m2:
                    extracted = m2.group(1).strip()
                    if extracted and len(extracted) <= 5:
                        self._last_prefix = extracted
                        return extracted

        ent_id = None
        if isinstance(message_or_id, int):
            ent_id = message_or_id
        elif message_or_id is not None:
            ent_id = getattr(message_or_id, "sender_id", None) or getattr(message_or_id, "from_id", None)

        if not ent_id:
            ent_id = getattr(self, "tg_id", None) or getattr(getattr(self, "_client", None), "tg_id", None)

        for fn in (
            getattr(self, "get_prefix", None),
            getattr(getattr(self, "allmodules", None), "get_prefix", None),
        ):
            if callable(fn):
                with contextlib.suppress(Exception):
                    if ent_id:
                        p = fn(ent_id)
                        if p and p != ".":
                            self._last_prefix = str(p)
                            return str(p)
                    p = fn()
                    if p and p != ".":
                        self._last_prefix = str(p)
                        return str(p)

        db = getattr(self, "_db", None) or getattr(self, "db", None)
        if db:
            for namespace in ("heroku.main", "__main__", "main"):
                with contextlib.suppress(Exception):
                    prefixes = db.get(namespace, "command_prefixes", {})
                    if prefixes and isinstance(prefixes, dict):
                        if ent_id and str(ent_id) in prefixes:
                            p = str(prefixes[str(ent_id)])
                            if p:
                                self._last_prefix = p
                                return p
                        for val in prefixes.values():
                            if val and val != ".":
                                self._last_prefix = str(val)
                                return str(val)

                    p = db.get(namespace, "command_prefix", None)
                    if p and p != ".":
                        self._last_prefix = str(p)
                        return str(p)

        for fn in (
            getattr(self, "get_prefixes", None),
            getattr(getattr(self, "allmodules", None), "get_prefixes", None),
        ):
            if callable(fn):
                with contextlib.suppress(Exception):
                    all_p = fn()
                    if all_p and isinstance(all_p, (set, list, tuple)):
                        for p in all_p:
                            if p and p != ".":
                                self._last_prefix = str(p)
                                return str(p)

        client_pref = getattr(getattr(self, "_client", None), "command_prefix", None)
        if client_pref and client_pref != ".":
            self._last_prefix = str(client_pref)
            return str(client_pref)

        if hasattr(self, "_last_prefix") and self._last_prefix:
            return self._last_prefix

        if db:
            with contextlib.suppress(Exception):
                p = db.get("heroku.main", "command_prefix", ".")
                if p:
                    return str(p)

        return "."

    def _str_no_pytgcalls(self, p: Optional[str] = None, err: Optional[str] = None) -> str:
        actual_p = p or self._prefix()
        actual_err = err or self._diag.get("init_error") or PYTGCALLS_IMPORT_ERROR or "Библиотека py-tgcalls не установлена"
        try:
            return self.strings("no_pytgcalls").format(p=actual_p, err=actual_err)
        except Exception:
            return (
                f"<b>[VoiceMod] ❌ Библиотека py-tgcalls не установлена или не работает!</b>\n"
                f"⚠️ <b>Ошибка:</b> <code>{actual_err}</code>\n\n"
                f"Установите её командой: <code>{actual_p}vinstall</code>\n"
                f"После установки: <code>{actual_p}restart</code>"
            )

    def _is_ffmpeg_installed(self) -> Tuple[bool, Optional[str]]:
        self._ensure_local_ffmpeg_path()
        bin_path = shutil.which("ffmpeg")
        return (bool(bin_path), bin_path)

    async def _get_ffmpeg_version(self) -> str:
        has_ff, bin_path = self._is_ffmpeg_installed()
        if not has_ff:
            return "Не установлен"
        try:
            proc = await asyncio.create_subprocess_exec(
                bin_path,
                "-version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
            if stdout:
                lines = stdout.decode("utf-8", errors="ignore").splitlines()
                if lines:
                    return lines[0].strip()
        except Exception as e:
            logger.debug(f"[VoiceMod] Ошибка проверки версии ffmpeg: {e}")
        return "Установлен (версия неизвестна)"

    def _download_and_extract_static(self, url: str, is_zip: bool, dest_dir: str):
        os.makedirs(dest_dir, exist_ok=True)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        req = urllib.request.Request(url, headers=headers)
        tmp_archive = os.path.join(tempfile.gettempdir(), f"ffmpeg_dl_{uuid.uuid4().hex[:8]}")

        try:
            with urllib.request.urlopen(req, timeout=180) as resp, open(tmp_archive, "wb") as f_out:
                shutil.copyfileobj(resp, f_out)

            if is_zip:
                with zipfile.ZipFile(tmp_archive, "r") as z:
                    for member in z.namelist():
                        base = os.path.basename(member).lower()
                        if base in ("ffmpeg.exe", "ffprobe.exe", "ffmpeg", "ffprobe"):
                            target_file = os.path.join(dest_dir, os.path.basename(member))
                            with z.open(member) as src, open(target_file, "wb") as dst:
                                shutil.copyfileobj(src, dst)
                            with contextlib.suppress(Exception):
                                os.chmod(target_file, 0o755)
            else:
                with tarfile.open(tmp_archive, "r:*") as tar:
                    for member in tar.getmembers():
                        base = os.path.basename(member.name).lower()
                        if base in ("ffmpeg", "ffprobe", "ffmpeg.exe", "ffprobe.exe"):
                            target_file = os.path.join(dest_dir, os.path.basename(member.name))
                            extracted_f = tar.extractfile(member)
                            if extracted_f:
                                with open(target_file, "wb") as dst:
                                    shutil.copyfileobj(extracted_f, dst)
                                with contextlib.suppress(Exception):
                                    os.chmod(target_file, 0o755)
        finally:
            if os.path.exists(tmp_archive):
                with contextlib.suppress(Exception):
                    os.remove(tmp_archive)

    async def _install_ffmpeg_routine(self, status_callback=None) -> Tuple[bool, str]:
        is_win = sys.platform.startswith("win")
        is_linux = sys.platform.startswith("linux")
        is_darwin = sys.platform.startswith("darwin")
        is_root = False
        if hasattr(os, "geteuid"):
            with contextlib.suppress(Exception):
                is_root = (os.geteuid() == 0)

        cmd = None
        if is_linux:
            if shutil.which("apt-get") or shutil.which("apt"):
                pm = shutil.which("apt-get") or shutil.which("apt")
                cmd = [pm, "install", "-y", "ffmpeg"]
            elif shutil.which("apk"):
                cmd = ["apk", "add", "--no-cache", "ffmpeg"]
            elif shutil.which("pacman"):
                cmd = ["pacman", "-Sy", "--noconfirm", "ffmpeg"]
            elif shutil.which("dnf"):
                cmd = ["dnf", "install", "-y", "ffmpeg"]
            elif shutil.which("pkg"):
                cmd = ["pkg", "install", "-y", "ffmpeg"]
            if cmd and not is_root and shutil.which("sudo"):
                cmd = ["sudo", *cmd]
        elif is_darwin:
            if shutil.which("brew"):
                cmd = ["brew", "install", "ffmpeg"]
        elif is_win:
            if shutil.which("winget"):
                cmd = ["winget", "install", "Gyan.FFmpeg", "--accept-package-agreements", "--accept-source-agreements"]
            elif shutil.which("choco"):
                cmd = ["choco", "install", "ffmpeg", "-y"]

        if cmd:
            if status_callback:
                await status_callback(f"Попытка установки через пакетный менеджер ({cmd[0]})...")
            try:
                utils.ensure_child_watcher()
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.wait_for(proc.communicate(), timeout=300)
                if proc.returncode == 0:
                    self._ensure_local_ffmpeg_path()
                    has_ff, path = self._is_ffmpeg_installed()
                    if has_ff:
                        ver = await self._get_ffmpeg_version()
                        return True, f"Установлен через {cmd[0]}: {ver} ({path})"
            except Exception as e:
                logger.warning(f"[VoiceMod] Системный установщик не сработал: {e}")

        if status_callback:
            await status_callback("Скачивание портативного статического FFmpeg бинарника (~60-90 МБ)...")

        machine = platform.machine().lower()
        url = None
        is_zip = False

        if is_win:
            url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
            is_zip = True
        elif is_darwin:
            url = "https://evermeet.cx/ffmpeg/getrelease/zip"
            is_zip = True
        elif is_linux:
            if "arm" in machine or "aarch64" in machine:
                url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz"
            else:
                url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
            is_zip = False

        if not url:
            return False, f"Не поддерживаемая ОС/архитектура для прямой загрузки: {sys.platform} ({machine})"

        dest_dir = os.path.abspath("ffmpeg_bin")
        try:
            os.makedirs(dest_dir, exist_ok=True)
            test_file = os.path.join(dest_dir, ".test_write")
            with open(test_file, "w") as f:
                f.write("1")
            os.remove(test_file)
        except Exception:
            dest_dir = os.path.join(tempfile.gettempdir(), "ffmpeg_bin")
            os.makedirs(dest_dir, exist_ok=True)

        try:
            await asyncio.to_thread(self._download_and_extract_static, url, is_zip, dest_dir)
        except Exception as dl_err:
            logger.error(f"[VoiceMod] Ошибка загрузки FFmpeg: {dl_err}", exc_info=True)
            return False, f"Ошибка загрузки бинарника: {dl_err}"

        self._ensure_local_ffmpeg_path()
        has_ff, path = self._is_ffmpeg_installed()
        if not has_ff:
            return False, f"Бинарник распакован в {dest_dir}, но не найден в PATH"

        ver = await self._get_ffmpeg_version()
        return True, f"{ver} ({path})"

    def _get_silence_file(self) -> str:
        silence_path = os.path.join(self._temp_dir, "silence.wav")
        if not os.path.exists(silence_path):
            try:
                import wave
                with wave.open(silence_path, "wb") as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(48000)
                    w.writeframes(b"\x00\x00" * 48000)
            except Exception:
                with open(silence_path, "wb") as f:
                    f.write(b"\x00" * 192000)
        return silence_path

    def _get_video_quality_params(self) -> Tuple[Any, int]:
        val = str(self.config.get("video_quality", "720p")).lower()
        mapping = {
            "360p": ("SD_360p", 360),
            "480p": ("SD_480p", 480),
            "720p": ("HD_720p", 720),
            "1080p": ("FHD_1080p", 1080),
        }
        attr, height = mapping.get(val, ("HD_720p", 720))
        param = getattr(VideoQualityClass, attr, None) if VideoQualityClass is not None else None
        return param, height

    def _get_cache_size(self) -> Tuple[int, int]:
        if not self._temp_dir or not os.path.exists(self._temp_dir):
            return 0, 0
        total_size = 0
        file_count = 0
        for entry in os.scandir(self._temp_dir):
            if entry.is_file():
                try:
                    total_size += entry.stat().st_size
                    file_count += 1
                except Exception:
                    pass
        return total_size, file_count

    def _enforce_cache_limit(self):
        if not self._temp_dir or not os.path.exists(self._temp_dir):
            return

        max_mb = self.config.get("max_cache_mb", 500)
        max_bytes = max_mb * 1024 * 1024

        total_size, _ = self._get_cache_size()
        if total_size <= max_bytes:
            return

        active_files = set()
        silence_file = os.path.join(self._temp_dir, "silence.raw")
        active_files.add(os.path.abspath(silence_file))

        for track in self._current.values():
            for k in ("file_path", "raw_path"):
                p = track.get(k)
                if p:
                    active_files.add(os.path.abspath(p))

        for q in self._queue.values():
            for track in q:
                for k in ("file_path", "raw_path"):
                    p = track.get(k)
                    if p:
                        active_files.add(os.path.abspath(p))

        for rec in self._recordings.values():
            p = rec.get("path")
            if p:
                active_files.add(os.path.abspath(p))

        candidates = []
        for entry in os.scandir(self._temp_dir):
            if entry.is_file():
                abs_p = os.path.abspath(entry.path)
                if abs_p not in active_files:
                    try:
                        st = entry.stat()
                        candidates.append((st.st_mtime, st.st_size, entry.path))
                    except Exception:
                        pass

        candidates.sort(key=lambda x: x[0])
        target_size = int(max_bytes * 0.75)

        for _, size, path in candidates:
            if total_size <= target_size:
                break
            with contextlib.suppress(Exception):
                os.remove(path)
                total_size -= size

    async def _extract_track_info(self, query: str, is_video: bool = False) -> Dict[str, Any]:
        loop = asyncio.get_running_loop()
        _, max_height = self._get_video_quality_params()

        def _yt_extract():
            import yt_dlp
            fmt = f"best[height<={max_height}]/bestvideo[height<={max_height}]+bestaudio/best" if is_video else "bestaudio/best"
            ydl_opts = {
                "format": fmt,
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "default_search": "ytsearch",
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                target = query if re.match(r"^https?://", query) else f"ytsearch1:{query}"
                info = ydl.extract_info(target, download=False)
                if "entries" in info and info["entries"]:
                    info = info["entries"][0]

                video_url = info.get("url")
                audio_url = None
                req_formats = info.get("requested_formats")
                if req_formats and len(req_formats) >= 2:
                    video_url = req_formats[0].get("url")
                    audio_url = req_formats[1].get("url")

                return {
                    "title": info.get("title", "Неизвестный трек"),
                    "duration": info.get("duration", 0),
                    "url": video_url,
                    "audio_url": audio_url,
                    "webpage_url": info.get("webpage_url", query),
                    "is_live": info.get("is_live", False),
                    "is_video": is_video,
                }

        return await loop.run_in_executor(None, _yt_extract)

    async def _convert_to_raw(self, source_path_or_url: str, output_path: str) -> bool:
        self._ensure_local_ffmpeg_path()
        ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
        cmd = [
            ffmpeg_bin, "-y",
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "5",
            "-i", source_path_or_url,
            "-f", "s16le",
            "-acodec", "pcm_s16le",
            "-ac", "2",
            "-ar", "48000",
            output_path,
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.communicate()
            return proc.returncode == 0 and os.path.exists(output_path)
        except FileNotFoundError:
            logger.error("[VoiceMod] FFmpeg не найден в системе!")
            return False
        except Exception as e:
            logger.error(f"[VoiceMod] Ошибка конвертации FFmpeg: {e}")
            return False

    async def _play_stream(self, chat_id: int, track: Dict[str, Any]):
        chat_id = await self._ensure_marked_chat_id(chat_id)
        self._current[chat_id] = track
        self._paused[chat_id] = False
        self._muted[chat_id] = False

        is_video = bool(track.get("is_video", False))

        if self._is_pytgcalls_client and self._tgcalls:
            stream_source = track.get("url") or track.get("file_path")
            audio_source = track.get("audio_url")
            stream = stream_source

            if is_video:
                video_param, _ = self._get_video_quality_params()
                if MediaStreamClass is not None:
                    try:
                        ms_kwargs = {}
                        if video_param is not None:
                            ms_kwargs["video_parameters"] = video_param
                        elif VideoQualityClass is not None and hasattr(VideoQualityClass, "HD_720p"):
                            ms_kwargs["video_parameters"] = getattr(VideoQualityClass, "HD_720p")
                        if AudioQualityClass is not None and hasattr(AudioQualityClass, "HIGH"):
                            ms_kwargs["audio_parameters"] = getattr(AudioQualityClass, "HIGH")
                        if audio_source:
                            ms_kwargs["audio_path"] = audio_source
                        stream = MediaStreamClass(stream_source, **ms_kwargs)
                    except Exception as e_ms:
                        logger.debug(f"[VoiceMod] MediaStream video wrap failed: {e_ms}")
                        stream = stream_source
                elif AudioVideoPipedClass is not None:
                    try:
                        piped_args = []
                        if HighQualityAudioClass is not None:
                            piped_args.append(HighQualityAudioClass())
                        if HighQualityVideoClass is not None:
                            piped_args.append(HighQualityVideoClass())
                        stream = AudioVideoPipedClass(stream_source, *piped_args)
                    except Exception as e_av:
                        logger.debug(f"[VoiceMod] AudioVideoPiped wrap failed: {e_av}")
                        stream = stream_source
                elif AudioPipedClass is not None:
                    stream = AudioPipedClass(stream_source)
            else:
                if MediaStreamClass is not None:
                    try:
                        ms_kwargs = {}
                        flags = getattr(MediaStreamClass, "Flags", None)
                        ignore_flag = getattr(flags, "IGNORE", None) if flags else None
                        if ignore_flag is not None:
                            ms_kwargs["video_flags"] = ignore_flag
                        if AudioQualityClass is not None and hasattr(AudioQualityClass, "HIGH"):
                            ms_kwargs["audio_parameters"] = getattr(AudioQualityClass, "HIGH")
                        stream = MediaStreamClass(stream_source, **ms_kwargs)
                    except Exception as e_ms:
                        logger.debug(f"[VoiceMod] MediaStream audio wrap failed: {e_ms}")
                        stream = stream_source
                elif AudioPipedClass is not None:
                    try:
                        if HighQualityAudioClass is not None:
                            stream = AudioPipedClass(stream_source, HighQualityAudioClass())
                        else:
                            stream = AudioPipedClass(stream_source)
                    except Exception as e_pipe:
                        logger.debug(f"[VoiceMod] AudioPiped wrap failed: {e_pipe}")
                        stream = stream_source

            if hasattr(self._tgcalls, "play"):
                try:
                    res = self._tgcalls.play(chat_id, stream)
                    if inspect.isawaitable(res):
                        await res
                    self._track_start_time[chat_id] = time.time()
                    self._expected_leave.discard(chat_id)
                    return
                except Exception as e_play:
                    logger.warning(f"[VoiceMod] self._tgcalls.play failed ({e_play})")
                    if not hasattr(self._tgcalls, "join_group_call"):
                        raise RuntimeError(f"PyTgCalls: {e_play}")

            if hasattr(self._tgcalls, "join_group_call"):
                try:
                    kwargs = {}
                    if StreamTypeClass is not None:
                        with contextlib.suppress(Exception):
                            kwargs["stream_type"] = StreamTypeClass().pulse_stream
                    res = self._tgcalls.join_group_call(chat_id, stream, **kwargs)
                    if inspect.isawaitable(res):
                        await res
                    self._track_start_time[chat_id] = time.time()
                    self._expected_leave.discard(chat_id)
                    return
                except Exception as e1:
                    if hasattr(self._tgcalls, "change_stream"):
                        try:
                            res = self._tgcalls.change_stream(chat_id, stream)
                            if inspect.isawaitable(res):
                                await res
                            self._track_start_time[chat_id] = time.time()
                            self._expected_leave.discard(chat_id)
                            return
                        except Exception as e2:
                            logger.error(f"[VoiceMod] Ошибка PyTgCalls join/change: {e1} | {e2}")
                            raise RuntimeError(f"PyTgCalls: {e1}")
                    raise RuntimeError(f"PyTgCalls: {e1}")

        if HAS_GROUP_CALL_FACTORY:
            raw_path = os.path.join(self._temp_dir, f"vc_{abs(chat_id)}_{uuid.uuid4().hex[:6]}.raw")
            source = track.get("url") or track.get("file_path")
            success = await self._convert_to_raw(source, raw_path)
            if not success:
                raise RuntimeError("Ошибка конвертации FFmpeg (проверьте наличие ffmpeg в системе)")

            track["raw_path"] = raw_path

            if chat_id not in self._calls:
                factory = GroupCallFactoryClass(
                    self._client,
                    GroupCallFactoryClass.MTPROTO_CLIENT_TYPE.TELETHON,
                )
                call = factory.get_file_group_call(raw_path)
                self._calls[chat_id] = call

                try:
                    await call.start(chat_id)
                except Exception:
                    entity = await self._client.get_entity(chat_id)
                    await call.start(getattr(entity, "id", chat_id))
            else:
                call = self._calls[chat_id]
                old_raw = track.get("raw_path")
                if old_raw and old_raw != raw_path and os.path.exists(old_raw):
                    with contextlib.suppress(Exception):
                        os.remove(old_raw)
                call.input_filename = raw_path
            self._track_start_time[chat_id] = time.time()
            self._expected_leave.discard(chat_id)
            return

        raise RuntimeError(self._str_no_pytgcalls(self._prefix()))

    async def _pytgcalls_call(self, method_names: List[str], chat_id: int) -> bool:
        if not self._tgcalls:
            return False
        chat_id = await self._ensure_marked_chat_id(chat_id)
        for name in method_names:
            if hasattr(self._tgcalls, name):
                try:
                    func = getattr(self._tgcalls, name)
                    res = func(chat_id)
                    if inspect.isawaitable(res):
                        await res
                    return True
                except Exception as e:
                    logger.debug(f"[VoiceMod] Call {name} failed: {e}")
        return False

    async def _handle_track_end(self, chat_id: int, force_skip: bool = False):
        if chat_id in self._expected_leave:
            return

        current = self._current.get(chat_id)
        if current and self.config["auto_reconnect"] and not force_skip:
            start_t = self._track_start_time.get(chat_id, 0)
            elapsed = time.time() - start_t
            duration = current.get("duration", 0)
            is_live = current.get("is_live", False)
            premature = is_live or (duration > 0 and elapsed < (duration - 8))
            if premature:
                attempts = self._reconnect_attempts.get(chat_id, 0)
                if attempts < 3:
                    vc_call = await self._get_active_call(chat_id)
                    if vc_call:
                        self._reconnect_attempts[chat_id] = attempts + 1
                        logger.info(f"[VoiceMod] Premature stream end in {chat_id} (elapsed {elapsed:.1f}s / {duration}s). Reconnecting ({attempts + 1}/3)...")
                        await asyncio.sleep(2)
                        try:
                            await self._play_stream(chat_id, current)
                            return
                        except Exception as e_rec:
                            logger.warning(f"[VoiceMod] Reconnect attempt {attempts + 1} failed: {e_rec}")

        self._reconnect_attempts.pop(chat_id, None)
        self._track_start_time.pop(chat_id, None)

        if not force_skip and self._repeat.get(chat_id, False) and current:
            logger.info(f"[VoiceMod] Replaying track in {chat_id}: {current.get('title')}")
            try:
                await self._play_stream(chat_id, current)
                return
            except Exception as e_repeat:
                logger.warning(f"[VoiceMod] Repeat play_stream failed: {e_repeat}")
                webpage = current.get("webpage_url")
                if webpage:
                    try:
                        info = await self._extract_track_info(webpage, is_video=current.get("is_video", False))
                        current["url"] = info["url"]
                        current["audio_url"] = info.get("audio_url")
                        await self._play_stream(chat_id, current)
                        return
                    except Exception as e_reex:
                        logger.error(f"[VoiceMod] Repeat re-extract failed: {e_reex}")

        current = self._current.pop(chat_id, None)
        if current:
            for key in ("file_path", "raw_path"):
                path = current.get(key)
                if path and os.path.exists(path):
                    with contextlib.suppress(Exception):
                        os.remove(path)

        queue = self._queue.get(chat_id, [])
        if queue:
            next_track = queue.pop(0)
            await self._play_stream(chat_id, next_track)
        else:
            if self.config["auto_leave"]:
                await self._leave_call(chat_id)

        self._enforce_cache_limit()

    async def _leave_call(self, chat_id: int):
        chat_id = await self._ensure_marked_chat_id(chat_id)
        self._expected_leave.add(chat_id)
        self._reconnect_attempts.pop(chat_id, None)
        self._track_start_time.pop(chat_id, None)

        if self._is_pytgcalls_client and self._tgcalls:
            with contextlib.suppress(Exception):
                await self._pytgcalls_call(["leave_group_call", "leave_call", "leave"], chat_id)

        if chat_id in self._calls:
            with contextlib.suppress(Exception):
                await self._calls[chat_id].stop()
            del self._calls[chat_id]

        queue = self._queue.pop(chat_id, [])
        for item in queue:
            for key in ("file_path", "raw_path"):
                path = item.get(key)
                if path and os.path.exists(path):
                    with contextlib.suppress(Exception):
                        os.remove(path)

        current = self._current.pop(chat_id, None)
        if current:
            for key in ("file_path", "raw_path"):
                path = current.get(key)
                if path and os.path.exists(path):
                    with contextlib.suppress(Exception):
                        os.remove(path)

        self._muted.pop(chat_id, None)
        self._paused.pop(chat_id, None)
        self._repeat.pop(chat_id, None)

    def _get_player_buttons(self, chat_id: int) -> List[List[Dict[str, Any]]]:
        is_paused = self._paused.get(chat_id, False)
        is_muted = self._muted.get(chat_id, False)
        is_repeat = self._repeat.get(chat_id, False)

        btn_pp = {
            "text": self.strings("btn_resume") if is_paused else self.strings("btn_pause"),
            "callback": self._cb_toggle_play,
            "args": (chat_id,),
        }
        btn_mm = {
            "text": self.strings("btn_unmute") if is_muted else self.strings("btn_mute"),
            "callback": self._cb_toggle_mute,
            "args": (chat_id,),
        }
        btn_skip = {
            "text": self.strings("btn_skip"),
            "callback": self._cb_skip,
            "args": (chat_id,),
        }
        btn_stop = {
            "text": self.strings("btn_stop"),
            "callback": self._cb_stop,
            "args": (chat_id,),
        }
        btn_queue = {
            "text": self.strings("btn_queue"),
            "callback": self._cb_show_queue,
            "args": (chat_id,),
        }
        btn_repeat = {
            "text": self.strings("btn_repeat_on") if is_repeat else self.strings("btn_repeat_off"),
            "callback": self._cb_toggle_repeat,
            "args": (chat_id,),
        }

        return [
            [btn_pp, btn_mm],
            [btn_skip, btn_stop],
            [btn_queue, btn_repeat],
        ]

    async def _cb_toggle_play(self, call: InlineCall, chat_id: int):
        is_paused = self._paused.get(chat_id, False)
        try:
            if self._is_pytgcalls_client and self._tgcalls:
                methods = ["resume", "resume_stream"] if is_paused else ["pause", "pause_stream"]
                await self._pytgcalls_call(methods, chat_id)
            elif chat_id in self._calls:
                if is_paused:
                    self._calls[chat_id].resume_playout()
                else:
                    self._calls[chat_id].pause_playout()

            self._paused[chat_id] = not is_paused
            await call.edit(
                self._format_now_playing(chat_id),
                reply_markup=self._get_player_buttons(chat_id),
            )
            await call.answer(self.strings("resumed") if is_paused else self.strings("paused"))
        except Exception as e:
            await call.answer(f"Ошибка: {e}", show_alert=True)

    async def _cb_toggle_mute(self, call: InlineCall, chat_id: int):
        is_muted = self._muted.get(chat_id, False)
        try:
            if self._is_pytgcalls_client and self._tgcalls:
                methods = ["unmute", "unmute_stream"] if is_muted else ["mute", "mute_stream"]
                await self._pytgcalls_call(methods, chat_id)
            elif chat_id in self._calls:
                self._calls[chat_id].set_is_mute(not is_muted)

            self._muted[chat_id] = not is_muted
            await call.edit(
                self._format_now_playing(chat_id),
                reply_markup=self._get_player_buttons(chat_id),
            )
            await call.answer(self.strings("unmuted") if is_muted else self.strings("muted"))
        except Exception as e:
            await call.answer(f"Ошибка: {e}", show_alert=True)

    async def _cb_skip(self, call: InlineCall, chat_id: int):
        queue = self._queue.get(chat_id, [])
        if not queue and chat_id not in self._current:
            await call.answer("Очередь пуста!", show_alert=True)
            return

        await call.answer("⏭ Пропускаем трек...")
        self._track_start_time.pop(chat_id, None)
        await self._handle_track_end(chat_id, force_skip=True)
        if chat_id in self._current:
            await call.edit(
                self._format_now_playing(chat_id),
                reply_markup=self._get_player_buttons(chat_id),
            )
        else:
            await call.edit(self.strings("stopped"))

    async def _cb_toggle_repeat(self, call: InlineCall, chat_id: int):
        is_repeat = self._repeat.get(chat_id, False)
        self._repeat[chat_id] = not is_repeat
        await call.edit(
            self._format_now_playing(chat_id),
            reply_markup=self._get_player_buttons(chat_id),
        )
        msg_text = "🔂 Повтор песни включён" if not is_repeat else "🔁 Повтор песни выключен"
        await call.answer(msg_text)

    async def _cb_stop(self, call: InlineCall, chat_id: int):
        await self._leave_call(chat_id)
        await call.answer(self.strings("stopped"))
        await call.edit(self.strings("stopped"))

    async def _cb_show_queue(self, call: InlineCall, chat_id: int):
        queue = self._queue.get(chat_id, [])
        if not queue:
            await call.answer("Очередь пуста!", show_alert=True)
            return

        lines = []
        for i, item in enumerate(queue[:10], start=1):
            dur = self._format_duration(item.get("duration"))
            lines.append(f"<b>{i}.</b> <code>{item['title']}</code> (⏱ {dur})")

        text = self.strings("queue_title").format(
            count=len(queue),
            items="\n".join(lines),
        )
        markup = [
            [
                {
                    "text": "◀️ Назад к плееру",
                    "callback": self._cb_back_to_player,
                    "args": (chat_id,),
                }
            ]
        ]
        await call.edit(text, reply_markup=markup)

    async def _cb_back_to_player(self, call: InlineCall, chat_id: int):
        if chat_id not in self._current:
            await call.edit(self.strings("stopped"))
            return
        await call.edit(
            self._format_now_playing(chat_id),
            reply_markup=self._get_player_buttons(chat_id),
        )

    def _format_now_playing(self, chat_id: int) -> str:
        current = self._current.get(chat_id)
        if not current:
            return self.strings("empty_queue")

        queue_len = len(self._queue.get(chat_id, []))
        is_video = current.get("is_video", False)
        template_key = "playing_video" if is_video else "playing"
        queue_text = f"{queue_len} трек(ов)"
        if self._repeat.get(chat_id, False):
            queue_text += " | 🔂 Повтор: ВКЛ"

        return self.strings(template_key).format(
            title=current["title"],
            duration=self._format_duration(current.get("duration")),
            requester=current.get("requester", "Аноним"),
            queue_len=queue_text,
        )

    @loader.command(
        ru_doc="[чат] - Диагностика работы PyTgCalls, FFmpeg и активного голосового чата",
    )
    async def vdebug(self, message: Message):
        """[chat] - Diagnostic info about voice chat backend and MTProto connection"""
        p = self._prefix(message)
        await self._ensure_backend_ready()
        chat_id, entity = await self._resolve_target(message)
        active_call = await self._get_active_call(chat_id)

        call_status = "❌ Не активен"
        if active_call:
            call_status = f"✅ Активен (id={active_call.id})"

        backend = self._diag.get("backend", "None")
        init_err = self._diag.get("init_error") or "None"

        has_ffmpeg, ff_path = self._is_ffmpeg_installed()
        ff_info = f"✅ Installed ({ff_path})" if has_ffmpeg else f"❌ Not found (use {p}vinstallffmpeg)"

        pytgcalls_status = (
            f"✅ Installed (v{PYTGCALLS_VERSION})"
            if HAS_PYTGCALLS
            else f"❌ Not installed ({PYTGCALLS_IMPORT_ERROR or 'No module named pytgcalls'})"
        )
        hint = f"\n💡 <b>Решение:</b> отправьте <code>{p}vinstall</code> для установки py-tgcalls\n" if not HAS_PYTGCALLS else ""

        cache_size, file_count = self._get_cache_size()
        cache_mb = cache_size / (1024 * 1024)
        max_cache = self.config.get("max_cache_mb", 500)
        is_rec = "✅ Recording" if chat_id in self._recordings else "❌ Inactive"

        res = (
            "<b>[VoiceMod Debug Info]</b>\n\n"
            f"🔤 <b>Command Prefix:</b> <code>{p}</code>\n"
            f"📦 <b>pytgcalls installed:</b> <code>{pytgcalls_status}</code>\n"
            f"🎬 <b>System FFmpeg:</b> <code>{ff_info}</code>\n"
            f"⚙️ <b>Backend:</b> <code>{backend}</code>\n"
            f"🤖 <b>PyTgCalls Client Active:</b> <code>{self._is_pytgcalls_client}</code>\n"
            f"🏭 <b>GroupCallFactory Available:</b> <code>{HAS_GROUP_CALL_FACTORY}</code>\n"
            f"📹 <b>Video Quality:</b> <code>{self.config.get('video_quality', '720p')}</code>\n"
            f"🔄 <b>Auto-Reconnect:</b> <code>{self.config.get('auto_reconnect', True)}</code>\n"
            f"🔴 <b>Voice Chat Recorder:</b> <code>{is_rec}</code>\n"
            f"💾 <b>Cache Usage:</b> <code>{cache_mb:.2f} / {max_cache} MB</code> ({file_count} files)\n"
            f"👤 <b>Client class:</b> <code>{self._client.__class__.__name__}</code>\n"
            f"📍 <b>Current Chat ID:</b> <code>{chat_id}</code>\n"
            f"🏷 <b>Chat Title:</b> <code>{getattr(entity, 'title', getattr(entity, 'first_name', 'Unknown'))}</code>\n"
            f"🎙 <b>Telegram Voice Chat:</b> {call_status}\n"
            f"⚠️ <b>Init Error:</b> <code>{init_err}</code>\n"
            f"{hint}"
        )
        await utils.answer(message, res)

    async def _play_common(self, message: Message, is_video: bool = False):
        p = self._prefix(message)
        ready = await self._ensure_backend_ready()
        if not ready and not HAS_GROUP_CALL_FACTORY:
            return await utils.answer(
                message,
                self._str_no_pytgcalls(p),
            )

        has_ffmpeg, _ = self._is_ffmpeg_installed()
        if not has_ffmpeg:
            return await utils.answer(message, self.strings("ffmpeg_missing").format(p=p))

        chat_id, _ = await self._resolve_target(message)
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        query = args.strip() if args else ""
        if query and (query.split()[0].startswith("-100") or query.split()[0].startswith("@")):
            parts = query.split(maxsplit=1)
            query = parts[1] if len(parts) > 1 else ""

        if not query and not (reply and reply.media):
            return await utils.answer(message, self.strings("no_args"))

        active_call = await self._get_active_call(chat_id)
        if not active_call:
            return await utils.answer(message, self.strings("no_active_vc"))

        msg = await utils.answer(message, self.strings("searching"))

        sender = await message.get_sender()
        requester = f"@{sender.username}" if sender and getattr(sender, "username", None) else (
            sender.first_name if sender else "Пользователь"
        )

        track: Optional[Dict[str, Any]] = None

        if reply and reply.media:
            msg = await utils.answer(msg, self.strings("downloading"))
            is_media_video = bool(getattr(reply, "video", False) or getattr(reply, "video_note", False))
            ext = ".mp4" if is_media_video else (".ogg" if getattr(reply, "voice", False) else ".mp3")

            temp_file = os.path.join(self._temp_dir, f"dl_{uuid.uuid4().hex[:8]}{ext}")
            await reply.download_media(file=temp_file)
            self._enforce_cache_limit()

            title = "Медиафайл"
            if reply.file and reply.file.name:
                title = reply.file.name
            elif getattr(reply, "voice", False):
                title = "Голосовое сообщение"
            elif getattr(reply, "video_note", False):
                title = "Видеосообщение"
            elif is_media_video:
                title = "Видео"
            elif getattr(reply, "audio", False):
                title = "Аудиозапись"

            duration = 0
            if reply.file and hasattr(reply.file, "duration"):
                duration = reply.file.duration or 0

            track = {
                "title": title,
                "duration": duration,
                "file_path": temp_file,
                "requester": requester,
                "is_video": is_video or is_media_video,
            }

        elif query:
            try:
                info = await self._extract_track_info(query, is_video=is_video)
                track = {
                    "title": info["title"],
                    "duration": info["duration"],
                    "url": info["url"],
                    "audio_url": info.get("audio_url"),
                    "webpage_url": info["webpage_url"],
                    "requester": requester,
                    "is_video": is_video,
                }
            except Exception as e:
                return await utils.answer(msg, self.strings("error").format(err=f"yt-dlp: {e}"))

        if not track:
            return await utils.answer(msg, self.strings("error").format(err="Не удалось извлечь медиа"))

        if chat_id in self._current:
            self._queue.setdefault(chat_id, []).append(track)
            pos = len(self._queue[chat_id])
            dur = self._format_duration(track.get("duration"))
            media_icon = "🎬" if track.get("is_video") else "🎵"
            return await utils.answer(
                msg,
                self.strings("queued").format(pos=pos, icon=media_icon, title=track["title"], duration=dur),
            )

        try:
            await self._play_stream(chat_id, track)
            text = self._format_now_playing(chat_id)
            buttons = self._get_player_buttons(chat_id)
            await self.inline.form(
                message=msg,
                text=text,
                reply_markup=buttons,
            )
        except Exception as e:
            logger.error(f"[VoiceMod] Ошибка запуска стрима: {e}", exc_info=True)
            await utils.answer(msg, self.strings("error").format(err=str(e)))

    @loader.command(
        ru_doc="[чат] <ссылка/поиск/реплай> - Включить или добавить трек в очередь голосового чата",
        de_doc="[Chat] <Link/Suche/Reply> - Musik in den Sprachchat abspielen oder zur Warteschlange hinzufügen",
    )
    async def vplay(self, message: Message):
        """[chat] <link/search/reply> - Play or add track to voice chat queue"""
        await self._play_common(message, is_video=False)

    @loader.command(
        ru_doc="[чат] <ссылка/поиск/реплай> - Воспроизвести видео со звуком в голосовом чате",
        de_doc="[Chat] <Link/Suche/Reply> - Video mit Audio im Sprachchat abspielen",
    )
    async def vvideo(self, message: Message):
        """[chat] <link/search/reply> - Play video with audio in voice chat"""
        await self._play_common(message, is_video=True)

    @loader.command(
        ru_doc="[чат] - Показать текущий трек и инлайн-пульт управления",
        de_doc="[Chat] - Zeigt den aktuellen Track und die Inline-Steuerung an",
    )
    async def vnow(self, message: Message):
        """[chat] - Show currently playing track and controls"""
        self._prefix(message)
        chat_id, _ = await self._resolve_target(message)
        if chat_id not in self._current:
            return await utils.answer(message, self.strings("empty_queue"))

        text = self._format_now_playing(chat_id)
        buttons = self._get_player_buttons(chat_id)
        await self.inline.form(
            message=message,
            text=text,
            reply_markup=buttons,
        )

    @loader.command(
        ru_doc="[чат] - Показать очередь воспроизведения",
        de_doc="[Chat] - Wiedergabeliste anzeigen",
    )
    async def vqueue(self, message: Message):
        """[chat] - Show current track queue"""
        self._prefix(message)
        chat_id, _ = await self._resolve_target(message)
        queue = self._queue.get(chat_id, [])
        if not queue and chat_id not in self._current:
            return await utils.answer(message, self.strings("empty_queue"))

        lines = []
        if chat_id in self._current:
            curr = self._current[chat_id]
            lines.append(f"▶️ <b>Сейчас:</b> <code>{curr['title']}</code> (⏱ {self._format_duration(curr.get('duration'))})")

        for i, item in enumerate(queue, start=1):
            dur = self._format_duration(item.get("duration"))
            lines.append(f"<b>{i}.</b> <code>{item['title']}</code> (⏱ {dur})")

        await utils.answer(
            message,
            self.strings("queue_title").format(
                count=len(queue) + (1 if chat_id in self._current else 0),
                items="\n".join(lines),
            ),
        )

    @loader.command(
        ru_doc="[чат] - Пропустить текущий трек",
        de_doc="[Chat] - Aktuellen Track überspringen",
    )
    async def vskip(self, message: Message):
        """[chat] - Skip current track"""
        self._prefix(message)
        chat_id, _ = await self._resolve_target(message)
        if chat_id not in self._current:
            return await utils.answer(message, self.strings("empty_queue"))

        await utils.answer(message, self.strings("skipped"))
        self._track_start_time.pop(chat_id, None)
        await self._handle_track_end(chat_id, force_skip=True)

    @loader.command(
        ru_doc="[чат] - Включить или выключить повтор текущей песни (зацикливание)",
        de_doc="[Chat] - Wiederholung des aktuellen Tracks ein- oder ausschalten",
    )
    async def vloop(self, message: Message):
        """[chat] - Toggle loop/repeat mode for the current track"""
        self._prefix(message)
        chat_id, _ = await self._resolve_target(message)
        is_repeat = self._repeat.get(chat_id, False)
        self._repeat[chat_id] = not is_repeat
        if self._repeat[chat_id]:
            await utils.answer(message, self.strings("repeat_on"))
        else:
            await utils.answer(message, self.strings("repeat_off"))

    @loader.command(
        ru_doc="[чат] - Алиас для команды .vloop (повтор текущей песни)",
    )
    async def vrepeat(self, message: Message):
        """[chat] - Alias for .vloop"""
        await self.vloop(message)

    @loader.command(
        ru_doc="[чат] - Приостановить воспроизведение",
        de_doc="[Chat] - Wiedergabe pausieren",
    )
    async def vpause(self, message: Message):
        """[chat] - Pause playback"""
        chat_id, _ = await self._resolve_target(message)
        p = self._prefix(message)
        if chat_id not in self._current and chat_id not in self._calls:
            return await utils.answer(message, self.strings("not_joined").format(p=p))

        if self._is_pytgcalls_client and self._tgcalls:
            await self._pytgcalls_call(["pause", "pause_stream"], chat_id)
        elif chat_id in self._calls:
            self._calls[chat_id].pause_playout()

        self._paused[chat_id] = True
        await utils.answer(message, self.strings("paused"))

    @loader.command(
        ru_doc="[чат] - Возобновить воспроизведение",
        de_doc="[Chat] - Wiedergabe fortsetzen",
    )
    async def vresume(self, message: Message):
        """[chat] - Resume playback"""
        p = self._prefix(message)
        chat_id, _ = await self._resolve_target(message)
        if chat_id not in self._current and chat_id not in self._calls:
            return await utils.answer(message, self.strings("not_joined").format(p=p))

        if self._is_pytgcalls_client and self._tgcalls:
            await self._pytgcalls_call(["resume", "resume_stream"], chat_id)
        elif chat_id in self._calls:
            self._calls[chat_id].resume_playout()

        self._paused[chat_id] = False
        await utils.answer(message, self.strings("resumed"))

    @loader.command(
        ru_doc="[чат] - Заглушить бота в голосовом чате",
        de_doc="[Chat] - Bot im Sprachchat stummschalten",
    )
    async def vmute(self, message: Message):
        """[chat] - Mute player in voice chat"""
        p = self._prefix(message)
        chat_id, _ = await self._resolve_target(message)
        if chat_id not in self._current and chat_id not in self._calls:
            return await utils.answer(message, self.strings("not_joined").format(p=p))

        if self._is_pytgcalls_client and self._tgcalls:
            await self._pytgcalls_call(["mute", "mute_stream"], chat_id)
        elif chat_id in self._calls:
            self._calls[chat_id].set_is_mute(True)

        self._muted[chat_id] = True
        await utils.answer(message, self.strings("muted"))

    @loader.command(
        ru_doc="[чат] - Включить микрофон бота в голосовом чате",
        de_doc="[Chat] - Mikrofon des Bots im Sprachchat einschalten",
    )
    async def vunmute(self, message: Message):
        """[chat] - Unmute player in voice chat"""
        p = self._prefix(message)
        chat_id, _ = await self._resolve_target(message)
        if chat_id not in self._current and chat_id not in self._calls:
            return await utils.answer(message, self.strings("not_joined").format(p=p))

        if self._is_pytgcalls_client and self._tgcalls:
            await self._pytgcalls_call(["unmute", "unmute_stream"], chat_id)
        elif chat_id in self._calls:
            self._calls[chat_id].set_is_mute(False)

        self._muted[chat_id] = False
        await utils.answer(message, self.strings("unmuted"))

    @loader.command(
        ru_doc="[чат] - Остановить воспроизведение и очистить очередь",
        de_doc="[Chat] - Wiedergabe stoppen und Warteschlange leeren",
    )
    async def vstop(self, message: Message):
        """[chat] - Stop playback and clear queue"""
        self._prefix(message)
        chat_id, _ = await self._resolve_target(message)
        await self._leave_call(chat_id)
        await utils.answer(message, self.strings("stopped"))

    @loader.command(
        ru_doc="[чат] - Подключиться к голосовому чату без воспроизведения",
        de_doc="[Chat] - Sprachchat beitreten",
    )
    async def vjoin(self, message: Message):
        """[chat] - Join voice chat"""
        p = self._prefix(message)
        ready = await self._ensure_backend_ready()
        if not ready and not HAS_GROUP_CALL_FACTORY:
            return await utils.answer(message, self._str_no_pytgcalls(p))

        chat_id, _ = await self._resolve_target(message)
        chat_id = await self._ensure_marked_chat_id(chat_id)

        active_call = await self._get_active_call(chat_id)
        if not active_call:
            return await utils.answer(message, self.strings("no_active_vc"))

        msg = await utils.answer(message, "<b>[VoiceMod]</b> ⏳ Подключение...")

        if self._is_pytgcalls_client and self._tgcalls:
            silence_file = self._get_silence_file()
            stream = silence_file
            if MediaStreamClass is not None:
                try:
                    stream = MediaStreamClass(silence_file)
                except Exception:
                    stream = silence_file
            elif AudioPipedClass is not None:
                try:
                    if HighQualityAudioClass is not None:
                        stream = AudioPipedClass(silence_file, HighQualityAudioClass())
                    else:
                        stream = AudioPipedClass(silence_file)
                except Exception:
                    stream = silence_file

            if hasattr(self._tgcalls, "play"):
                try:
                    res = self._tgcalls.play(chat_id, stream)
                    if inspect.isawaitable(res):
                        await res
                    return await utils.answer(msg, self.strings("joined"))
                except Exception as e:
                    logger.warning(f"[VoiceMod] vjoin play failed: {e}")
                    if not hasattr(self._tgcalls, "join_group_call"):
                        return await utils.answer(msg, self.strings("error").format(err=f"PyTgCalls: {e}"))

            if hasattr(self._tgcalls, "join_group_call"):
                try:
                    kwargs = {}
                    if StreamTypeClass is not None:
                        with contextlib.suppress(Exception):
                            kwargs["stream_type"] = StreamTypeClass().pulse_stream
                    res = self._tgcalls.join_group_call(chat_id, stream, **kwargs)
                    if inspect.isawaitable(res):
                        await res
                    return await utils.answer(msg, self.strings("joined"))
                except Exception as e:
                    logger.error(f"[VoiceMod] Ошибка vjoin PyTgCalls: {e}")
                    return await utils.answer(msg, self.strings("error").format(err=f"PyTgCalls: {e}"))

        if HAS_GROUP_CALL_FACTORY:
            try:
                if chat_id not in self._calls:
                    silence_file = self._get_silence_file()
                    factory = GroupCallFactoryClass(
                        self._client,
                        GroupCallFactoryClass.MTPROTO_CLIENT_TYPE.TELETHON,
                    )
                    self._calls[chat_id] = factory.get_file_group_call(silence_file)
                    try:
                        await self._calls[chat_id].start(chat_id)
                    except Exception:
                        entity = await self._client.get_entity(chat_id)
                        await self._calls[chat_id].start(getattr(entity, "id", chat_id))

                return await utils.answer(msg, self.strings("joined"))
            except Exception as e:
                logger.error(f"[VoiceMod] Ошибка vjoin GroupCallFactory: {e}")
                return await utils.answer(msg, self.strings("error").format(err=f"GroupCall: {e}"))

        await utils.answer(msg, self._str_no_pytgcalls(p))

    @loader.command(
        ru_doc="[чат] - Покинуть голосовой чат",
        de_doc="[Chat] - Sprachchat verlassen",
    )
    async def vleave(self, message: Message):
        """[chat] - Leave voice chat"""
        self._prefix(message)
        chat_id, _ = await self._resolve_target(message)
        await self._leave_call(chat_id)
        await utils.answer(message, self.strings("left"))

    @loader.command(
        ru_doc="[-f/--force] - Автоматически установить или скачать бинарник FFmpeg",
        de_doc="[-f/--force] - FFmpeg-Binärdatei automatisch installieren oder herunterladen",
    )
    async def vinstallffmpeg(self, message: Message):
        """[-f/--force] - Automatically install or download FFmpeg binary"""
        args = (utils.get_args_raw(message) or "").lower()
        force = "-f" in args or "--force" in args

        p = self._prefix(message)
        has_ff, bin_path = self._is_ffmpeg_installed()
        if has_ff and not force:
            ver = await self._get_ffmpeg_version()
            return await utils.answer(
                message,
                self.strings("ffmpeg_already").format(path=bin_path, version=ver, p=p),
            )

        msg = await utils.answer(
            message,
            self.strings("ffmpeg_installing").format(status="Определение ОС и запуск установщика..."),
        )

        async def _update_status(status_text: str):
            with contextlib.suppress(Exception):
                await utils.answer(
                    msg,
                    self.strings("ffmpeg_installing").format(status=status_text),
                )

        ok, result = await self._install_ffmpeg_routine(status_callback=_update_status)
        if ok:
            _, bin_path = self._is_ffmpeg_installed()
            await utils.answer(
                msg,
                self.strings("ffmpeg_installed").format(
                    path=bin_path or "ffmpeg_bin/",
                    version=result,
                ),
            )
        else:
            await utils.answer(
                msg,
                self.strings("ffmpeg_error").format(err=result),
            )

    @loader.command(
        ru_doc="[install/check/path] - Проверить или установить утилиту FFmpeg",
        de_doc="[install/check/path] - FFmpeg-Status überprüfen oder installieren",
    )
    async def vffmpeg(self, message: Message):
        """[install/check/path] - Check or install FFmpeg tool"""
        p = self._prefix(message)
        args = (utils.get_args_raw(message) or "").strip().lower()
        if args.startswith("install") or "--force" in args or "-f" in args:
            return await self.vinstallffmpeg(message)

        has_ff, bin_path = self._is_ffmpeg_installed()
        if has_ff:
            ver = await self._get_ffmpeg_version()
            await utils.answer(
                message,
                self.strings("ffmpeg_already").format(path=bin_path, version=ver, p=p),
            )
        else:
            await utils.answer(message, self.strings("ffmpeg_missing").format(p=p))

    @loader.command(
        ru_doc="Установить недостающие библиотеки (py-tgcalls, yt-dlp) через терминал с автоматической проверкой",
        de_doc="Installiert fehlende Bibliotheken über das Terminal mit automatischer Verifizierung",
    )
    async def vinstall(self, message: Message):
        """Install required python libraries (py-tgcalls, yt-dlp) via terminal with verification"""
        p = self._prefix(message)
        py_ver = f"python{sys.version_info.major}.{sys.version_info.minor}"
        target_dir = f"/usr/local/lib/{py_ver}/site-packages"

        pip_cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--break-system-packages",
            "py-tgcalls",
            "yt-dlp",
        ]

        msg = await utils.answer(
            message,
            "<b>[VoiceMod]</b> 💻 <b>Запуск установки библиотек в терминале...</b>\n"
            f"<code>$ {' '.join(pip_cmd)}</code>\n\n"
            "⏳ <i>Установка в процессе, пожалуйста, подождите...</i>",
        )

        try:
            utils.ensure_child_watcher()
            proc = await asyncio.create_subprocess_exec(
                *pip_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            output_lines = []
            last_edit = time.time()
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="ignore").rstrip()
                if decoded:
                    output_lines.append(decoded)
                    if len(output_lines) > 25:
                        output_lines = output_lines[-25:]

                if time.time() - last_edit >= 2.5:
                    last_edit = time.time()
                    tail = "\n".join(output_lines[-6:])
                    with contextlib.suppress(Exception):
                        await utils.answer(
                            msg,
                            "<b>[VoiceMod]</b> 💻 <b>Установка в процессе (терминал)...</b>\n"
                            f"<code>{utils.escape_html(tail)}</code>\n\n"
                            "⏳ <i>Пожалуйста, подождите...</i>",
                        )
                await asyncio.sleep(0.01)

            await proc.wait()
            if proc.returncode != 0:
                tail = "\n".join(output_lines[-10:])
                return await utils.answer(
                    msg,
                    f"<b>[VoiceMod] ❌ Ошибка pip install (код {proc.returncode}):</b>\n"
                    f"<code>{utils.escape_html(tail)}</code>\n\n"
                    f"Попробуйте вручную через терминал:\n<code>{p}terminal {' '.join(pip_cmd)}</code>",
                )
        except Exception as e:
            return await utils.answer(
                msg,
                f"<b>[VoiceMod] ⚠️ Ошибка запуска процесса:</b> <code>{utils.escape_html(str(e))}</code>",
            )

        await utils.answer(
            msg,
            "<b>[VoiceMod]</b> 🔍 <b>Проверка импорта py-tgcalls после установки...</b>",
        )

        _ensure_site_packages()
        importlib.invalidate_caches()

        try:
            utils.ensure_child_watcher()
            verify_script = (
                "import os, sys, site; "
                f"p1 = '/root/.local/lib/{py_ver}/site-packages'; "
                f"p2 = '{target_dir}'; "
                "[site.addsitedir(p) for p in (p1, p2) if os.path.isdir(p)]; "
                "[(sys.path.insert(0, p)) for p in (p1, p2) if os.path.isdir(p) and p not in sys.path]; "
                "import pytgcalls; print('VERIFY_OK:', getattr(pytgcalls, '__version__', 'unknown'))"
            )
            v_proc = await asyncio.create_subprocess_exec(
                sys.executable,
                "-c",
                verify_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            v_stdout, v_stderr = await v_proc.communicate()
            v_out = v_stdout.decode("utf-8", errors="ignore").strip()
            v_err = v_stderr.decode("utf-8", errors="ignore").strip()

            if v_proc.returncode == 0 and "VERIFY_OK:" in v_out:
                ver = v_out.split("VERIFY_OK:", 1)[1].strip()
                _try_import_pytgcalls()
                await utils.answer(
                    msg,
                    f"<b>[VoiceMod]</b> ✅ <b>Библиотека py-tgcalls (v{ver}) успешно установлена и проверена!</b>\n\n"
                    f"🔄 <b>Сделайте рестарт по команде:</b> <code>{p}restart</code>",
                )
            else:
                err_detail = v_err or v_out or "Модуль py-tgcalls не найден в окружении Python"
                await utils.answer(
                    msg,
                    "<b>[VoiceMod] ❌ Ошибка проверки: пакет установлен, но Python не может его загрузить!</b>\n\n"
                    f"<b>Причина ошибки:</b>\n<code>{utils.escape_html(err_detail[-600:])}</code>\n\n"
                    f"💡 <b>Попробуйте принудительно установить в системную директорию:</b>\n"
                    f"<code>{p}terminal {sys.executable} -m pip install --upgrade --break-system-packages --target {target_dir} py-tgcalls yt-dlp</code>",
                )
        except Exception as e:
            await utils.answer(
                msg,
                f"<b>[VoiceMod] ⚠️ Ошибка при проверке импорта:</b> <code>{utils.escape_html(str(e))}</code>\n\n"
                f"🔄 <i>Попробуйте перезагрузить юзербота:</i> <code>{p}restart</code>",
            )

    @loader.command(
        ru_doc="[360p/480p/720p/1080p] - Настроить качество трансляции видео",
        de_doc="[360p/480p/720p/1080p] - Videoübertragungsqualität einstellen",
    )
    async def vquality(self, message: Message):
        """[360p/480p/720p/1080p] - Set video streaming quality"""
        args = (utils.get_args_raw(message) or "").strip().lower()
        valid = ["360p", "480p", "720p", "1080p"]
        p = self._prefix(message)
        if not args:
            cur = self.config["video_quality"]
            return await utils.answer(
                message,
                f"<b>[VoiceMod] 🎬 Текущее качество видео:</b> <code>{cur}</code>\n"
                f"<i>Доступные варианты:</i> <code>{' / '.join(valid)}</code>\n\n"
                f"<i>Использование:</i> <code>{p}vquality 720p</code>",
            )
        if args not in valid:
            return await utils.answer(
                message,
                f"<b>[VoiceMod] ❌ Недопустимое качество:</b> <code>{args}</code>\n"
                f"<i>Доступные варианты:</i> <code>{' / '.join(valid)}</code>",
            )
        self.config["video_quality"] = args
        await utils.answer(
            message,
            f"<b>[VoiceMod] ✅ Качество видео установлено:</b> <code>{args}</code>",
        )

    @loader.command(
        ru_doc="[start/stop/status] - Запись звука из голосового чата в MP3",
        de_doc="[start/stop/status] - Sprachchat-Audio in MP3 aufnehmen",
    )
    async def vrecord(self, message: Message):
        """[start/stop/status] - Record voice chat audio to MP3"""
        args = (utils.get_args_raw(message) or "").strip().lower()
        p = self._prefix(message)
        chat_id, _ = await self._resolve_target(message)

        if args in ("stop", "end"):
            if chat_id not in self._recordings:
                return await utils.answer(message, "<b>[VoiceMod]</b> ℹ️ В этом чате нет активной записи.")

            msg = await utils.answer(message, "<b>[VoiceMod] ⏹ Остановка и сохранение записи...</b>")
            rec_info = self._recordings.pop(chat_id)
            rec_path = rec_info.get("path")
            start_time = rec_info.get("start_time", time.time())

            if self._is_pytgcalls_client and self._tgcalls and hasattr(self._tgcalls, "record"):
                with contextlib.suppress(Exception):
                    res = self._tgcalls.record(chat_id, stream=None)
                    if inspect.isawaitable(res):
                        await res

            await asyncio.sleep(2)
            duration = int(time.time() - start_time)

            if rec_path and os.path.exists(rec_path) and os.path.getsize(rec_path) > 0:
                size_mb = os.path.getsize(rec_path) / (1024 * 1024)
                await utils.answer(msg, "<b>[VoiceMod] 📤 Отправка записи...</b>")
                try:
                    await self._client.send_file(
                        chat_id,
                        rec_path,
                        caption=(
                            "<b>[VoiceMod] 🎙 Запись голосового чата</b>\n"
                            f"⏱ <b>Длительность:</b> <code>{self._format_duration(duration)}</code>\n"
                            f"💾 <b>Размер:</b> <code>{size_mb:.2f} МБ</code>"
                        ),
                        voice_note=False,
                    )
                    with contextlib.suppress(Exception):
                        await msg.delete()
                except Exception as e:
                    await utils.answer(msg, f"<b>[VoiceMod] ⚠️ Не удалось отправить файл:</b> <code>{e}</code>")
                finally:
                    with contextlib.suppress(Exception):
                        os.remove(rec_path)
            else:
                await utils.answer(msg, "<b>[VoiceMod] ⚠️ Файл записи пуст или не был создан.</b>")
            return

        if args == "status":
            if chat_id not in self._recordings:
                return await utils.answer(message, "<b>[VoiceMod]</b> ℹ️ В этом чате сейчас нет активной записи.")
            rec_info = self._recordings[chat_id]
            dur = int(time.time() - rec_info.get("start_time", time.time()))
            rec_path = rec_info.get("path")
            size_mb = (os.path.getsize(rec_path) / (1024 * 1024)) if rec_path and os.path.exists(rec_path) else 0.0
            return await utils.answer(
                message,
                f"<b>[VoiceMod] 🎙 Идет запись голосового чата:</b>\n"
                f"⏱ <b>Длительность:</b> <code>{self._format_duration(dur)}</code>\n"
                f"💾 <b>Размер на диске:</b> <code>{size_mb:.2f} МБ</code>\n\n"
                f"<i>Остановить запись:</i> <code>{p}vrecord stop</code>",
            )

        if args in ("start", ""):
            if chat_id in self._recordings:
                return await utils.answer(
                    message,
                    f"<b>[VoiceMod] ℹ️ Запись уже идет в этом чате.</b>\n"
                    f"<i>Для остановки отправьте:</i> <code>{p}vrecord stop</code>",
                )

            vc_call = await self._get_active_call(chat_id)
            if not vc_call and chat_id not in self._calls:
                return await utils.answer(message, self.strings("no_active_vc"))

            ready = await self._ensure_backend_ready()
            if not ready or not self._tgcalls or not hasattr(self._tgcalls, "record"):
                return await utils.answer(
                    message,
                    "<b>[VoiceMod] ❌ Запись поддерживается только через PyTgCalls с поддержкой метода record().</b>",
                )

            rec_file = os.path.join(self._temp_dir, f"rec_{abs(chat_id)}_{uuid.uuid4().hex[:6]}.mp3")
            stream_obj = None
            if RecordStreamClass is not None:
                try:
                    stream_obj = RecordStreamClass(audio=rec_file)
                except Exception as e_rs:
                    logger.debug(f"[VoiceMod] RecordStream direct init failed: {e_rs}")

            if stream_obj is None:
                stream_obj = rec_file

            try:
                res = self._tgcalls.record(chat_id, stream=stream_obj)
                if inspect.isawaitable(res):
                    await res
                self._recordings[chat_id] = {
                    "path": rec_file,
                    "start_time": time.time(),
                }
                await utils.answer(
                    message,
                    f"<b>[VoiceMod] 🎙 Запись голосового чата началась!</b>\n"
                    f"<i>Чтобы остановить и получить аудиофайл:</i> <code>{p}vrecord stop</code>",
                )
            except Exception as e:
                logger.error(f"[VoiceMod] Ошибка старта записи: {e}")
                await utils.answer(
                    message,
                    f"<b>[VoiceMod] ⚠️ Ошибка запуска записи:</b> <code>{e}</code>",
                )
            return

        await utils.answer(
            message,
            f"<b>[VoiceMod] 🎙 Управление записью голосового чата:</b>\n"
            f"• <code>{p}vrecord start</code> — начать запись\n"
            f"• <code>{p}vrecord stop</code> — остановить запись и отправить файл в чат\n"
            f"• <code>{p}vrecord status</code> — текущий статус записи",
        )

    @loader.command(
        ru_doc="[clear] - Управление кешем и просмотр занятого дискового пространства",
        de_doc="[clear] - Cache-Verwaltung und Anzeige des belegten Speicherplatzes",
    )
    async def vcache(self, message: Message):
        """[clear] - Cache management and disk usage"""
        p = self._prefix(message)
        args = (utils.get_args_raw(message) or "").strip().lower()

        if args in ("clear", "clean", "purge"):
            active_files = set()
            if self._temp_dir and os.path.exists(self._temp_dir):
                silence_file = os.path.join(self._temp_dir, "silence.raw")
                active_files.add(os.path.abspath(silence_file))

                for track in self._current.values():
                    for k in ("file_path", "raw_path"):
                        path = track.get(k)
                        if path:
                            active_files.add(os.path.abspath(path))

                for q in self._queue.values():
                    for track in q:
                        for k in ("file_path", "raw_path"):
                            path = track.get(k)
                            if path:
                                active_files.add(os.path.abspath(path))

                for rec in self._recordings.values():
                    path = rec.get("path")
                    if path:
                        active_files.add(os.path.abspath(path))

                freed_bytes = 0
                deleted_count = 0
                for entry in os.scandir(self._temp_dir):
                    if entry.is_file():
                        abs_p = os.path.abspath(entry.path)
                        if abs_p not in active_files:
                            try:
                                sz = entry.stat().st_size
                                os.remove(entry.path)
                                freed_bytes += sz
                                deleted_count += 1
                            except Exception:
                                pass

                freed_mb = freed_bytes / (1024 * 1024)
                return await utils.answer(
                    message,
                    f"<b>[VoiceMod] 🧹 Кеш очищен!</b>\n"
                    f"Удалено файлов: <code>{deleted_count}</code>\n"
                    f"Освобождено: <code>{freed_mb:.2f} МБ</code>",
                )

        total_size, file_count = self._get_cache_size()
        size_mb = total_size / (1024 * 1024)
        limit_mb = self.config.get("max_cache_mb", 500)
        pct = (size_mb / limit_mb * 100) if limit_mb > 0 else 0

        await utils.answer(
            message,
            f"<b>[VoiceMod] 💾 Информация о кеше:</b>\n"
            f"📁 <b>Занято:</b> <code>{size_mb:.2f} МБ</code> / <code>{limit_mb} МБ</code> ({pct:.1f}%)\n"
            f"📄 <b>Файлов в кеше:</b> <code>{file_count}</code>\n"
            f"📍 <b>Директория:</b> <code>{self._temp_dir}</code>\n\n"
            f"<i>Очистить кеш:</i> <code>{p}vcache clear</code>",
        )
