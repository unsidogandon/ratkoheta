# requires: py-tgcalls==0.9.7

#
# ░█░█░█▀▀░█▀█░█▀▀░▀█▀░█▀▄░█▀▀
# ░▄▀▄░█▀▀░█░█░▀▀█░░█░░█░█░█▀▀
# ░▀░▀░▀▀▀░▀░▀░▀▀▀░▀▀▀░▀▀░░▀▀▀
#
# 🔒 Licensed under All Rights Reserved.
# meta developer: @XenSideMOD
#
import sys
import os
if sys.version_info >= (3, 12):
    raise RuntimeError("This module is not compatible with Python 3.12+ and requires Python 3.11 or lower.")
if "userland" in os.environ.get("USER", ""):
    raise RuntimeError("This module is NOT compatible with UserLAnd.'")
import asyncio
import atexit
import contextlib
import logging
import re
import shutil
import tempfile
import telethon
# О ВЕЛИКИ БАЙПАСС
telethon.__version__ = "1.40.0"
# О ВЕЛИКИ БАЙПАСС
from pytgcalls import PyTgCalls, StreamType, types
from pytgcalls.binding import Binding
from pytgcalls.environment import Environment
from pytgcalls.exceptions import AlreadyJoinedError, NoActiveGroupCall
from pytgcalls.handlers import HandlersHolder
from pytgcalls.methods import Methods
from pytgcalls.mtproto import MtProtoClient
from pytgcalls.scaffold import Scaffold
from pytgcalls.types import Cache
from pytgcalls.types.call_holder import CallHolder
from pytgcalls.types.update_solver import UpdateSolver
from telethon.tl.functions.phone import CreateGroupCallRequest
from telethon.tl.types import DocumentAttributeFilename, Message

from .. import loader, utils
from ..inline.types import InlineCall
from ..tl_cache import CustomTelegramClient

logging.getLogger("pytgcalls").setLevel(logging.ERROR)


@loader.tds
class XenifiedVoiceChatMod(loader.Module):
    """
    Toolkit for VoiceChats handling
    """

    strings = {
        "name": "XenifiedVoiceChat",
        "already_joined": "🚫 <b>You are already in VoiceChat</b>",
        "joined": "🎙 <b>Joined VoiceChat</b>",
        "no_reply": "🚫 <b>Reply to an audio or video file</b>",
        "no_queue": "🚫 <b>Queue is empty</b>",
        "not_playing": "🚫 <b>Nothing is playing right now.</b>",
        "queue": "🎙 <b>Queue</b>:\n\n{}",
        "queueadd": "🎧 <b>{} added to queue</b>",
        "queueaddv": "🎬 <b>{} added to queue</b>",
        "downloading": "📥 <b>Downloading...</b>",
        "playing": "🎶 <b>Playing {}</b>",
        "playing_with_next": "🎶 <b>Playing {}</b>\n➡️ <b>Next: {}</b>",
        "pause": "🎵 Pause",
        "play": "🎵 Play",
        "mute": "🔇 Mute",
        "unmute": "🔈 Unmute",
        "next": "➡️ Next",
        "stopped": "🚨 <b>Stopped</b>",
        "stop": "🚨 Stop",
        "choose_delete": "♻️ <b>Choose a queue item to delete</b>",
        "loop": "🔁 Loop",
        "looping": "🔁 Looping",
    }

    _calls = {}
    _muted = {}
    _queue = {}
    _loop = {}
    _paused = {}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "silent_queue",
                False,
                "Do not notify about track changes in chat",
                validator=loader.validators.Boolean(),
            )
        )

    async def client_ready(self, client, db):
        class HikkaTLClient(MtProtoClient):
            def __init__(self, cache_duration: int, client: CustomTelegramClient):
                from pytgcalls.mtproto.telethon_client import TelethonClient
                self._bind_client = TelethonClient(cache_duration, client)

        class CustomPyTgCalls(PyTgCalls):
            def __init__(self, app: CustomTelegramClient, cache_duration: int = 120, **kwargs):
                Methods.__init__(self)
                Scaffold.__init__(self)
                self._app = HikkaTLClient(cache_duration, app)
                self._is_running = False
                self._env_checker = Environment(
                    self._REQUIRED_NODEJS_VERSION,
                    self._REQUIRED_PYROGRAM_VERSION,
                    self._REQUIRED_TELETHON_VERSION,
                    self._app.client,
                )
                self._call_holder = CallHolder()
                self._cache_user_peer = Cache()
                self._wait_result = UpdateSolver()
                self._on_event_update = HandlersHolder()
                self._binding = Binding(
                    kwargs.get("overload_quiet_mode", False),
                )
                atexit.register(
                    lambda: self._async_core.cancel()
                    if self._async_core is not None
                    else None
                )

        self._client = client
        self._app = CustomPyTgCalls(client)
        self._dir = tempfile.mkdtemp()
        await self._app.start()
        self._app._on_event_update.add_handler("STREAM_END_HANDLER", self.stream_ended)

    async def on_unload(self):
        shutil.rmtree(self._dir)
        for chat_id in self._calls:
            with contextlib.suppress(Exception):
                await self._app.leave_group_call(chat_id)

    async def stream_ended(self, client: PyTgCalls, update: types.Update):
        chat_id = update.chat_id

        if self._loop.get(chat_id) and self._queue.get(chat_id):
            try:
                await self._app.change_stream(chat_id, self._queue[chat_id][0]["stream"])
            except Exception:
                await self._play_from_queue(chat_id)
            return

        with contextlib.suppress(IndexError):
            self._queue.get(chat_id, []).pop(0)

        if not self._queue.get(chat_id):
            with contextlib.suppress(Exception):
                await client.leave_group_call(chat_id)
            self._cleanup_chat(chat_id)
            return

        await self._play_from_queue(chat_id)

    def _cleanup_chat(self, chat_id: int):
        self._queue.pop(chat_id, None)
        self._muted.pop(chat_id, None)
        self._calls.pop(chat_id, None)
        self._loop.pop(chat_id, None)
        self._paused.pop(chat_id, None)

    async def _play_raw(self, chat_id: int, stream, reattempt: bool = False):
        self._muted.setdefault(chat_id, False)
        self._paused.setdefault(chat_id, False)
        self._calls[chat_id] = True
        try:
            await self._app.join_group_call(
                chat_id, stream, stream_type=StreamType().pulse_stream
            )
        except AlreadyJoinedError:
            await self._app.change_stream(chat_id, stream)
        except NoActiveGroupCall:
            if reattempt:
                raise
            await self._client(CreateGroupCallRequest(chat_id))
            await self._play_raw(chat_id, stream, True)

    def _get_fn(self, message: Message) -> str:
        filename = "Unknown Track"
        if not hasattr(message, "document"):
            return filename
        try:
            attr = next((attr for attr in message.document.attributes if isinstance(attr, DocumentAttributeFilename)), None)
            if attr: return attr.file_name
            attr = next((attr for attr in message.document.attributes if hasattr(attr, "performer") or hasattr(attr, "title")), None)
            if attr:
                performer = getattr(attr, "performer", "")
                title = getattr(attr, "title", "")
                return f"{performer} - {title}" if performer and title else title or performer
        except (StopIteration, Exception):
            pass
        return filename

    @loader.command(ru_doc="<в ответ на аудио/видео> - Добавить трек в очередь")
    async def qadd(self, message: Message):
        """<reply to audio/video> - Add a track to the queue"""
        reply = await message.get_reply_message()
        if not reply or not reply.document:
            await utils.answer(message, self.strings("no_reply"))
            return

        mime_type = reply.document.mime_type
        is_audio = "audio" in mime_type
        is_video = "video" in mime_type

        if not is_audio and not is_video:
            await utils.answer(message, self.strings("no_reply"))
            return

        msg = await utils.answer(message, self.strings("downloading"))

        raw_data = await self._client.download_file(reply.document, bytes)
        filename = self._get_fn(reply)

        filename = re.sub(r"\(.*?\)", "", filename or "Unknown Track").strip()
        chat_id = utils.get_chat_id(message)

        self._queue.setdefault(chat_id, []).append({
            "data": raw_data, "filename": filename, "audio": is_audio, "stream": None
        })

        await utils.answer(msg, self.strings("queueadd" if is_audio else "queueaddv").format(filename))
        
        if len(self._queue[chat_id]) == 1:
            await self._play_from_queue(chat_id, message=message)

    @loader.command(ru_doc="Переключить трек")
    async def qnext(self, message: Message):
        """Skips current track in queue"""
        chat_id = utils.get_chat_id(message)
        if len(self._queue.get(chat_id, [])) < 2:
            await utils.answer(message, self.strings("no_queue"))
            return

        self._loop[chat_id] = False
        self._queue[chat_id].pop(0)
        await self._play_from_queue(chat_id)
        await message.delete()

    @loader.command(ru_doc="Показать текущую очередь")
    async def queue(self, message: Message):
        """Get current chat's queue"""
        chat_id = utils.get_chat_id(message)
        if not self._queue.get(chat_id):
            await utils.answer(message, self.strings("no_queue"))
            return

        queue_list = "\n".join(
            f"<b>{('🎶' if i == 0 else '🕓')} {'🎧' if item['audio'] else '🎬'}</b> "
            f"<code>{utils.escape_html(item['filename'])}</code>"
            for i, item in enumerate(self._queue[chat_id])
        )
        await utils.answer(message, self.strings("queue").format(queue_list))

    @loader.command(ru_doc="Удалить трек из очереди")
    async def qdel(self, message: Message):
        """Remove a track from the queue"""
        chat_id = utils.get_chat_id(message)
        if len(self._queue.get(chat_id, [])) < 2:
            await utils.answer(message, self.strings("no_queue"))
            return

        await self.inline.form(
            message=message, text=self.strings("choose_delete"),
            reply_markup=[{
                "text": f"{'🎧' if item['audio'] else '🎬'} {item['filename']}",
                "callback": self._inline_delete,
                "args": (chat_id, index + 1),
            } for index, item in enumerate(self._queue[chat_id][1:])]
        )
        
    @loader.command(ru_doc="Открыть панель управления плеером")
    async def qpanel(self, message: Message):
        """Opens the player control panel"""
        chat_id = utils.get_chat_id(message)
        if chat_id not in self._calls or not self._queue.get(chat_id):
            await utils.answer(message, self.strings("not_playing"))
            return

        await self._update_inline_form(chat_id, message=message)

    async def _inline_delete(self, call: InlineCall, chat_id: int, index: int):
        del self._queue[chat_id][index]
        await call.answer("Track removed!")
        await call.delete()

    async def _handle_stream_change(self, call, chat_id, action):
        if action == "pause":
            await self._app.pause_stream(chat_id)
            self._paused[chat_id] = True
        elif action == "resume":
            await self._app.resume_stream(chat_id)
            self._paused[chat_id] = False
        elif action == "mute":
            await self._app.mute_stream(chat_id)
            self._muted[chat_id] = True
        elif action == "unmute":
            await self._app.unmute_stream(chat_id)
            self._muted[chat_id] = False
            
        await self._update_inline_form(chat_id, call=call)

    async def _inline_toggle_loop(self, call: InlineCall, chat_id: int):
        self._loop[chat_id] = not self._loop.get(chat_id, False)
        await call.answer(f"Loop {'enabled' if self._loop[chat_id] else 'disabled'}")
        await self._update_inline_form(chat_id, call=call)

    async def _inline_stop(self, call: InlineCall, chat_id: int):
        self._cleanup_chat(chat_id)
        with contextlib.suppress(Exception):
            await self._app.leave_group_call(chat_id)
        
        await utils.answer(call, self.strings("stopped"))
        with contextlib.suppress(Exception):
            await call.delete()

    async def _inline_next(self, call: InlineCall, chat_id: int):
        self._loop[chat_id] = False
        self._queue.get(chat_id, []).pop(0)
        await self._play_from_queue(chat_id)
        await self._update_inline_form(chat_id, call=call)

    def _get_inline_info(self, chat_id: int):
        queue = self._queue.get(chat_id, [])
        if not queue: return None, None

        current_track = utils.escape_html(queue[0]["filename"])
        msg = self.strings("playing").format(current_track)
        if len(queue) > 1:
            msg = self.strings("playing_with_next").format(current_track, utils.escape_html(queue[1]["filename"]))

        is_paused = self._paused.get(chat_id, False)
        is_looping = self._loop.get(chat_id, False)
        is_muted = self._muted.get(chat_id, False)

        play_pause_btn = {"text": self.strings("play"), "callback": self._handle_stream_change, "args": (chat_id, "resume")} if is_paused else {"text": self.strings("pause"), "callback": self._handle_stream_change, "args": (chat_id, "pause")}
        mute_unmute_btn = {"text": self.strings("unmute"), "callback": self._handle_stream_change, "args": (chat_id, "unmute")} if is_muted else {"text": self.strings("mute"), "callback": self._handle_stream_change, "args": (chat_id, "mute")}
        loop_btn = {"text": self.strings("looping") if is_looping else self.strings("loop"), "callback": self._inline_toggle_loop, "args": (chat_id,)}

        markup = [[play_pause_btn, mute_unmute_btn, loop_btn], [{"text": self.strings("stop"), "callback": self._inline_stop, "args": (chat_id,)}]]
        if len(queue) > 1:
            markup[1].insert(0, {"text": self.strings("next"), "callback": self._inline_next, "args": (chat_id,)})

        return msg, markup

    async def _update_inline_form(self, chat_id: int, message: Message = None, call: InlineCall = None):
        if self.config["silent_queue"]: return

        msg, markup = self._get_inline_info(chat_id)
        if not msg: return

        try:
            if call:
                await call.edit(msg, reply_markup=markup)
            elif message:
                await utils.answer(message, msg, reply_markup=markup)
        except Exception:
            pass

    async def _play_from_queue(self, chat_id: int, message: Message = None):
        queue = self._queue.get(chat_id, [])
        if not queue: return

        self._paused[chat_id] = False
        item = queue[0]
        is_audio = item["audio"]
        suffix = "ogg" if is_audio else "mp4"
        file = os.path.join(self._dir, f"{utils.rand(8)}.{suffix}")

        with open(file, "wb") as f:
            f.write(item["data"])

        stream = (
            types.AudioPiped(file, types.HighQualityAudio())
            if is_audio
            else types.AudioVideoPiped(file, types.HighQualityAudio(), types.HighQualityVideo())
        )

        self._queue[chat_id][0]["stream"] = stream

        await self._play_raw(chat_id, stream)
        await asyncio.sleep(1)
        
        if not self.config["silent_queue"] and message:
            await self._update_inline_form(chat_id, message=message)
