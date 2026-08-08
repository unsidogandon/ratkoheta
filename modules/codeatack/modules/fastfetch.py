# 🔒    Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta developer: @VibeCodermodules

__version__ = (1, 0, 0)

import asyncio, re, shlex, shutil, subprocess, traceback
from telethon.tl.types import Message, PeerUser, PeerChat, PeerChannel, InputPeerUser, InputPeerChat, InputPeerChannel
from .. import loader, utils

class OutputFormatter:
    ANSI_PATTERN = re.compile(r"\x1B\[[0-9;?]*[a-zA-Z]")
    HOST_PATTERN = re.compile(r"([`\"']+)([A-Za-z0-9._-]+@[^ \t]+)")

    @staticmethod
    def format(text: str) -> str:
        return OutputFormatter.HOST_PATTERN.sub(r"\1\n\2", OutputFormatter.ANSI_PATTERN.sub("", text)).strip()

class OutputCensor:
    VAMHOST_PATTERN = re.compile(r"vamhost", re.IGNORECASE)

    @staticmethod
    def censor(text: str, chat_id: int, restricted_chats: list[int]) -> str:
        return OutputCensor.VAMHOST_PATTERN.sub(
            lambda m: ("M" if m.group(0)[0].isupper() else "m") + "utehost", text
        ) if chat_id in restricted_chats else text

class FastfetchRunner:
    TIMEOUT = 5

    @staticmethod
    async def run(args: list) -> tuple[bool, str, str]:
        try:
            proc = subprocess.run(
                ["fastfetch"] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=FastfetchRunner.TIMEOUT
            )
            return proc.returncode == 0, proc.stdout.strip(), proc.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "", "Fastfetch execution timed out."
        except Exception as e:
            return False, "", utils.escape_html("".join(traceback.format_exception(e)))

class FastfetchPresenter:
    @staticmethod
    def present(ok: bool, output: str, error: str, strings: dict) -> str:
        if not ok:
            return strings["error"].format(error=error or strings["unknown_error"])
        if not output:
            return strings["no_data"]
        return f'<pre><code class="language-fastfetch">{utils.escape_html(output)}</code></pre>'

@loader.tds
class FastfetchMod(loader.Module):
    """Fastfetch system information display"""

    strings = {
        "name": "Fastfetch",
        "error": "<emoji document_id=5350477112677515642>⚠️</emoji> <b>Failed to execute fastfetch...</b>\n\n"
                 "<pre><code class='language-stderr'>{error}</code></pre>",
        "no_data": "<emoji document_id=5449875850046481967>🤔</emoji> <b>No output from fastfetch.</b>",
        "not_installed": "<emoji document_id=5449875850046481967>🤔</emoji> <b>Fastfetch is not installed.</b>",
        "unknown_error": "An unexpected error occurred.",
        "invalid_chat_id": "<emoji document_id=5350477112677515642>⚠️</emoji> <b>Invalid chat ID.</b>",
        "_cfg_arguments": "Custom arguments for fastfetch.",
        "_cfg_restricted_chats": "Chat IDs to replace 'vhost' with 'mutehost'",
        "refresh_button": "🔄 Refresh",
    }

    strings_ru = {
        "error": "<emoji document_id=5350477112677515642>⚠️</emoji> <b>Ошибка выполнения fastfetch...</b>\n\n"
                 "<pre><code class='language-stderr'>{error}</code></pre>",
        "no_data": "<emoji document_id=5449875850046481967>🤔</emoji> <b>Fastfetch не вернул данных.</b>",
        "not_installed": "<emoji document_id=5449875850046481967>🤔</emoji> <b>Fastfetch не установлен.</b>",
        "unknown_error": "Произошла неизвестная ошибка.",
        "invalid_chat_id": "<emoji document_id=5350477112677515642>⚠️</emoji> <b>Недопустимый ID чата.</b>",
        "_cfg_arguments": "Аргументы для fastfetch.",
        "_cfg_restricted_chats": "ID чатов для замены 'vhost' на 'mutehost'.",
        "refresh_button": "🔄 Обновить",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue("arguments", None, lambda: self.strings["_cfg_arguments"], validator=loader.validators.Union(loader.validators.String(), loader.validators.NoneType())),
            loader.ConfigValue("restricted_chats", [2341345589, 1697279580], lambda: self.strings["_cfg_restricted_chats"], validator=loader.validators.Series(loader.validators.Integer())),
        )
        self.formatter = OutputFormatter()
        self.censor = OutputCensor()
        self.runner = FastfetchRunner()
        self.presenter = FastfetchPresenter()

    @loader.command(alias="f", en_doc="Display system info using fastfetch.", ru_doc="Показать информацию о системе с помощью fastfetch.")
    async def fastfetch(self, message: Message):
        if not shutil.which("fastfetch"):
            await utils.answer(message, self.strings["not_installed"])
            return

        raw_args = utils.get_args_raw(message) or self.config["arguments"] or ""
        args = shlex.split(raw_args) if raw_args else []
        inline_mode = args and args[0].lower() == "inline"
        if inline_mode:
            args = args[1:]

        chat_id = self._resolve_chat_id(message.peer_id)
        if chat_id is None:
            await utils.answer(message, self.strings["invalid_chat_id"])
            return

        result = await self._execute_fastfetch(args, chat_id)

        if inline_mode:
            await self.inline.form(
                message=message, text=result, reply_markup=[[{"text": self.strings["refresh_button"], "callback": self._refresh_inline, "args": (args, chat_id)}]] if "language-fastfetch" in result else None
            )
        else:
            await utils.answer(message, result)

    async def _refresh_inline(self, call, args: list, chat_id: int):
        result = await self._execute_fastfetch(args, chat_id)
        await call.edit(result, reply_markup=[[{"text": self.strings["refresh_button"], "callback": self._refresh_inline, "args": (args, chat_id)}]] if "language-fastfetch" in result else None)

    async def _execute_fastfetch(self, args: list, chat_id: int) -> str:
        ok, output, error = await self.runner.run(args)
        if not ok or not output:
            return self.presenter.present(ok, output, error, self.strings)
        formatted_output = self.formatter.format(output)
        censored_output = self.censor.censor(formatted_output, chat_id, self.config["restricted_chats"])
        return self.presenter.present(True, censored_output, "", self.strings)

    def _resolve_chat_id(self, peer) -> int | None:
        try:
            if isinstance(peer, (PeerUser, PeerChat, PeerChannel, InputPeerUser, InputPeerChat, InputPeerChannel)):
                return peer.user_id if isinstance(peer, (PeerUser, InputPeerUser)) else peer.chat_id if isinstance(peer, (PeerChat, InputPeerChat)) else peer.channel_id
            return int(peer)
        except (AttributeError, ValueError, TypeError):
            return None
