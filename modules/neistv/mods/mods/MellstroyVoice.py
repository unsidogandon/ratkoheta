# Name: MellstroyVoice
# Description: голосовые Мелстроя
# authors: @neistv 
# version: 1.3.1
# meta developer: @latexmods
# requires: pydub audioop-lts
# meta banner: https://github.com/neistv/mods/raw/main/assets/MellstroyVoice.png

import io
import os

import requests
from pydub import AudioSegment
try:
    from telethon import functions, types
except ImportError:
    try:
        from herokutl.tl import functions, types
    except ImportError:
        functions = None
        types = None

from .. import loader, utils

url = "https://raw.githubusercontent.com/neistv/mods/main/assets%20mellstroy/"
cache = os.path.expanduser("~/.heroku/mellstroy_cache")


def _reply_target(message, reply):
    if not reply:
        return None

    header = getattr(message, "reply_to", None)
    quote_text = getattr(header, "quote_text", None)
    if not quote_text or types is None:
        return reply.id

    quote_offset = getattr(header, "quote_offset", None)
    return types.InputReplyToMessage(
        reply_to_msg_id=getattr(header, "reply_to_msg_id", None) or reply.id,
        top_msg_id=getattr(header, "reply_to_top_id", None),
        quote_text=quote_text,
        quote_entities=getattr(header, "quote_entities", None),
        quote_offset=quote_offset,
    )


async def _send_voice_file(client, chat, buf, reply_to, duration):
    if (
        functions is not None
        and types is not None
        and isinstance(reply_to, types.InputReplyToMessage)
    ):
        entity = await client.get_input_entity(chat)
        uploaded = await client.upload_file(buf)
        media = types.InputMediaUploadedDocument(
            file=uploaded,
            mime_type="audio/ogg",
            attributes=[
                types.DocumentAttributeAudio(duration=duration, voice=True),
            ],
        )
        return await client(
            functions.messages.SendMediaRequest(
                entity,
                media,
                reply_to=reply_to,
                message="",
            )
        )

    return await client.send_file(
        chat,
        buf,
        voice_note=True,
        reply_to=reply_to,
    )


async def _send_voice(module, message, fn):
    reply = await message.get_reply_message()
    if message.out:
        await message.delete()

    os.makedirs(cache, exist_ok=True)
    path = os.path.join(cache, fn)

    if os.path.exists(path):
        data = open(path, "rb").read()
    else:
        r = await utils.run_sync(requests.get, url + fn, timeout=15)
        r.raise_for_status()
        data = r.content
        open(path, "wb").write(data)

    sound = AudioSegment.from_file(io.BytesIO(data))
    duration = max(1, round(len(sound) / 1000))

    buf = io.BytesIO()
    sound.export(buf, format="ogg")
    buf.name = "voice.ogg"
    buf.seek(0)

    await _send_voice_file(
        message.client,
        message.to_id,
        buf,
        _reply_target(message, reply),
        duration,
    )


@loader.tds
class MellstroyVoiceMod(loader.Module):
    """голосовые Мелстроя!!!"""

    strings = {"name": "MellstroyVoice"}

    async def бананcmd(self, message):
        """​"""
        await _send_voice(self, message, "1банан.ogg")

    async def быстрееcmd(self, message):
        """​"""
        await _send_voice(self, message, "BISTREE.mp3")

    async def ааасmd(self, message):
        """​"""
        await _send_voice(self, message, "aaa.ogg")

    async def амамамcmd(self, message):
        """​"""
        await _send_voice(self, message, "amamam.mp3")

    async def бембембемcmd(self, message):
        """​"""
        await _send_voice(self, message, "bembembem.mp3")

    async def блятьcmd(self, message):
        """​"""
        await _send_voice(self, message, "bluat.mp3")

    async def бравоcmd(self, message):
        """​"""
        await _send_voice(self, message, "bravoo.mp3")

    async def щавельcmd(self, message):
        """​"""
        await _send_voice(self, message, "chavel.mp3")

    async def чтотыдумалcmd(self, message):
        """​"""
        await _send_voice(self, message, "chotidumal.mp3")

    async def эхтыcmd(self, message):
        """​"""
        await _send_voice(self, message, "extisuka.mp3")

    async def идинахуйcmd(self, message):
        """​"""
        await _send_voice(self, message, "idinaxyu.mp3")

    async def посидимcmd(self, message):
        """​"""
        await _send_voice(self, message, "posidim.mp3")

    async def раздваcmd(self, message):
        """​"""
        await _send_voice(self, message, "razdva.mp3")

    async def скольконахуйcmd(self, message):
        """​"""
        await _send_voice(self, message, "skolkanaxuy.mp3")

    async def стопстопстопcmd(self, message):
        """​"""
        await _send_voice(self, message, "stopstopstop.mp3")

    async def свистcmd(self, message):
        """​"""
        await _send_voice(self, message, "svist.mp3")

    async def виноградcmd(self, message):
        """​"""
        await _send_voice(self, message, "vinpgrad.mp3")

    async def хамамcmd(self, message):
        """​"""
        await _send_voice(self, message, "xamamm.ogg")

    async def хахахаcmd(self, message):
        """​"""
        await _send_voice(self, message, "xaxaxaxa.mp3")

    async def ухуcmd(self, message):
        """​"""
        await _send_voice(self, message, "yxyyy.mp3")

    async def аоаоcmd(self, message):
        """​"""
        await _send_voice(self, message, "аоао.ogg")

    async def бабкаcmd(self, message):
        """​"""
        await _send_voice(self, message, "бабка.ogg")

    async def брбрбрcmd(self, message):
        """​"""
        await _send_voice(self, message, "брбрбр.ogg")

    async def бурмофиксикиcmd(self, message):
        """​"""
        await _send_voice(self, message, "бурмофиксики.ogg")

    async def буяяcmd(self, message):
        """​"""
        await _send_voice(self, message, "буяя.ogg")

    async def возняафриканскаяcmd(self, message):
        """​"""
        await _send_voice(self, message, "возняафриканская.ogg")

    async def закинь5миллионовcmd(self, message):
        """​"""
        await _send_voice(self, message, "закинь5милионов.ogg")

    async def зевсятинаcmd(self, message):
        """​"""
        await _send_voice(self, message, "зевсятина.ogg")

    async def кислыйcmd(self, message):
        """​"""
        await _send_voice(self, message, "кислый.ogg")

    async def милицияcmd(self, message):
        """​"""
        await _send_voice(self, message, "милиция.ogg")

    async def нормалдыcmd(self, message):
        """​"""
        await _send_voice(self, message, "нормалды.ogg")

    async def омайгадcmd(self, message):
        """​"""
        await _send_voice(self, message, "омайгад.ogg")

    async def отказаноcmd(self, message):
        """​"""
        await _send_voice(self, message, "отказано.ogg")

    async def подразбитьбыcmd(self, message):
        """​"""
        await _send_voice(self, message, "подразбитьбы.ogg")

    async def реальноcmd(self, message):
        """​"""
        await _send_voice(self, message, "реально.ogg")

    async def тишеcmd(self, message):
        """​"""
        await _send_voice(self, message, "тише.ogg")

    async def учисьcmd(self, message):
        """​"""
        await _send_voice(self, message, "учись.ogg")

    async def чеcmd(self, message):
        """​"""
        await _send_voice(self, message, "че.ogg")

    async def элджиевкаcmd(self, message):
        """​"""
        await _send_voice(self, message, "элджеевка.ogg")

    async def этоктоcmd(self, message):
        """​"""
        await _send_voice(self, message, "этокто.ogg")

    async def яблокоcmd(self, message):
        """​"""
        await _send_voice(self, message, "яблоко.ogg")

    async def яужекрасныйcmd(self, message):
        """​"""
        await _send_voice(self, message, "яужекрасный.ogg")

    async def бурмалдаcmd(self, message):
        """​"""
        await _send_voice(self, message, "бурмалда.ogg")

    async def салатикcmd(self, message):
        """​"""
        await _send_voice(self, message, "салатик.ogg")

    async def стоитcmd(self, message):
        """​"""
        await _send_voice(self, message, "стоит.ogg")
