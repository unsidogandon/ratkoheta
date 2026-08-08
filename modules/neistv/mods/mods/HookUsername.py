# Name: HookUsername
# Description: хук юзернейма
# authors: @neistv
# version: 1.0.1
# meta developer: @latexmods
# meta banner: https://github.com/neistv/mods/raw/main/assets/HookUsername.png
import io
import logging
import re
import requests
from bs4 import BeautifulSoup
from telethon.tl import functions
from telethon.tl.types import InputChatUploadedPhoto
from herokutl.types import Message

from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class HookUsernameMod(loader.Module):
    """хук юзернейма"""

    strings = {"name": "HookUsername"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "channel_title",
                "Этот юзернейм зарезервирован.",
                "название канала при захвате юзернейма",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "channel_about",
                "",
                "описание канала при захвате юзернейма",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "channel_avatar_url",
                "https://raw.githubusercontent.com/neistv/mods/main/assets/rezerv.png",
                "ссылка на аватарку канала",
                validator=loader.validators.String(),
            ),
        )

    async def client_ready(self, client, db):
        self._db = db
        self._client = client

    async def _check(self, username: str) -> bool:
        try:
            return await self._client(
                functions.account.CheckUsernameRequest(username=username)
            )
        except Exception as e:
            err_name = type(e).__name__
            if "UsernamePurchaseAvailable" in err_name or "UsernameInvalid" in err_name:
                return False
            logger.exception(f"ошибка при проверке юзернейма {username}: {e}")
            return False

    async def _check_fragment(self, username: str) -> tuple[bool, str, str | None]:
        try:
            response = await utils.run_sync(
                requests.get,
                f"https://fragment.com/username/{username}",
                timeout=10,
            )
            if response.status_code != 200:
                return False, "none", None

            soup = BeautifulSoup(response.content, "html.parser")
            header_status = soup.find(class_="tm-section-header-status")
            status_text = header_status.text.strip().lower() if header_status else ""

            if "sold" in status_text:
                price_el = soup.select_one(".tm-value")
                price = price_el.text.strip() if price_el else None
                return True, "sold", price
            elif "available" in status_text or "auction" in status_text:
                price_el = soup.select_one(".tm-value")
                price = price_el.text.strip() if price_el else None
                return True, "available", price
            else:
                return False, "none", None

        except Exception as e:
            logger.warning(f"ошибка при проверке fragment @{username}: {e}")
            return False, "none", None

    async def _grab_username(self, username: str) -> tuple[bool, str]:
        try:
            result = await self._client(
                functions.channels.CreateChannelRequest(
                    title=self.config["channel_title"],
                    about=self.config["channel_about"],
                    megagroup=False,
                )
            )
            channel = result.chats[0]

            await self._client(
                functions.channels.UpdateUsernameRequest(
                    channel=channel,
                    username=username,
                )
            )

            avatar_url = self.config["channel_avatar_url"].strip()
            if avatar_url:
                try:
                    resp = await utils.run_sync(requests.get, avatar_url, allow_redirects=True)
                    img_bytes = resp.content
                    buf = io.BytesIO(img_bytes)
                    buf.name = "avatar.png"
                    uploaded = await self._client.upload_file(buf)
                    await self._client(
                        functions.channels.EditPhotoRequest(
                            channel=channel,
                            photo=InputChatUploadedPhoto(file=uploaded),
                        )
                    )

                    async for msg in self._client.iter_messages(channel, limit=10):
                        if msg.action:
                            await msg.delete()

                except Exception as e:
                    logger.warning(f"ошибка с аватаркой: {e}")

            return True, f"t.me/{username}"
        except Exception as e:
            logger.exception(f"ошибка при захвате: {e}")
            return False, str(e)

    @loader.command(ru_doc="<юзернейм> — проверяет доступность юзернейма с возможностью занять его")
    async def uz(self, message: Message):
        """<юзернейм> - проверяет доступность юзернейма с возможностью занять его."""
        args = utils.get_args_raw(message).strip().lstrip("@")

        if not args:
            await utils.answer(
                message,
                "<b><tg-emoji emoji-id='5220197908342648622'>❗️</tg-emoji> укажи юзак!!</b>"
            )
            return

        if len(args) < 4:
            await utils.answer(
                message,
                "<b><tg-emoji emoji-id='5220197908342648622'>❗️</tg-emoji> минимум 4 символа!!</b>"
            )
            return

        if re.search(r'[а-яА-ЯёЁ]', args):
            await utils.answer(
                message,
                "<b><tg-emoji emoji-id='5220197908342648622'>❗️</tg-emoji> "
                "в юзернейме не может быть русских букв!!</b>"
            )
            return

        available = await self._check(args)

        if available:
            await self.inline.form(
                text=(
                    f"юзак <b>@{args}</b> — свободен!!!\n\n"
                    f"хочешь занять этот юзернейм?"
                ),
                message=message,
                reply_markup=[
                    [
                        {"text": "✔ занять", "callback": self._grab_cb, "args": (args,)},
                        {"text": "✖", "callback": self._close_cb},
                    ]
                ],
            )
        else:
            loading_msg = await self.inline.form(
                text=(
                    f"<b>проверяю.. @{args}...</b>"
                ),
                message=message,
                reply_markup=[
                    [{"text": "✖ закрыть", "callback": self._close_cb}]
                ],
            )

            found_on_fragment, frag_status, price = await self._check_fragment(args)

            if found_on_fragment:
                price_line = f"<tg-emoji emoji-id='6039802097916974085'>🪙</tg-emoji> <b>цена:</b> <code>{price}</code> TON\n" if price else ""
                fragment_url = f"https://fragment.com/username/{args}"

                if frag_status == "sold":
                    status_title = f"<tg-emoji emoji-id='5220197908342648622'>❗️</tg-emoji> <b>@{args}</b> — продан на Fragment.\n\n"
                else:
                    status_title = f"<tg-emoji emoji-id='5220197908342648622'>❗️</tg-emoji> <b>@{args}</b> — занят.\n\n"

                await loading_msg.edit(
                    text=(
                        f"{status_title}"
                        f"<tg-emoji emoji-id='5219943216781995020'>⚡️</tg-emoji> <b>найден на Fragment:</b>\n"
                        f"{price_line}"
                        f"<tg-emoji emoji-id='5902449142575141204'>🔗</tg-emoji> <b>ссылка:</b> <a href=\"{fragment_url}\">{fragment_url}</a>"
                    ),
                    reply_markup=[
                        [{"text": "✖ закрыть", "callback": self._close_cb}]
                    ]
                )
            else:
                is_banned = False
                try:
                    await self._client(functions.contacts.ResolveUsernameRequest(username=args))
                except Exception as e:
                    err_name = type(e).__name__
                    if "UsernameNotOccupied" in err_name or "UsernameInvalid" in err_name:
                        is_banned = True

                if is_banned:
                    await loading_msg.edit(
                        text=(
                            f"<tg-emoji emoji-id='5208663713539704322'>👎</tg-emoji> "
                            f"<b>@{args}</b> — в бане или недопустим"
                        ),
                        reply_markup=[
                            [{"text": "✖ закрыть", "callback": self._close_cb}]
                        ]
                    )
                else:
                    await loading_msg.edit(
                        text=(
                            f"<tg-emoji emoji-id='5220197908342648622'>❗️</tg-emoji> "
                            f"<b>@{args}</b> — занят."
                        ),
                        reply_markup=[
                            [{"text": "✖ закрыть", "callback": self._close_cb}]
                        ]
                    )

    async def _grab_cb(self, call, username: str):
        await call.answer("захватываю...", show_alert=False)
        success, info = await self._grab_username(username)

        if success:
            await call.edit(
                text=(
                    f"<tg-emoji emoji-id='5219901967916084166'>💥</tg-emoji> "
                    f"<b>@{username}</b> успешно занят!\n\n"
                    f"Канал: {info}"
                ),
                reply_markup=[[{"text": "✖ закрыть", "callback": self._close_cb}]],
            )
        else:
            await call.edit(
                text=(
                    f"<tg-emoji emoji-id='5220197908342648622'>❗️</tg-emoji> "
                    f"<b>Ошибка:</b>\n<code>{info}</code>"
                ),
                reply_markup=[[{"text": "✖ закрыть", "callback": self._close_cb}]],
            )

    async def _close_cb(self, call):
        await call.delete()
