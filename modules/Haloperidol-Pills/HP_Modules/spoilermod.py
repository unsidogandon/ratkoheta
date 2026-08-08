# name: Spoilermod
# meta developer: @hp_modules
# author: @haloperidolpills
from .. import loader, utils
from telethon import types
import io
__version__ = 1,0,0

@loader.tds
class SpoilerMod(loader.Module):
    strings = {
        "name": "Spoilermod",
        "no_reply": "<emoji document_id=5278578973595427038>🚫</emoji> <b>Ошибка: необходимо ответить на сообщение с медиафайлом</b>",
        "no_media": "<emoji document_id=5278578973595427038>🚫</emoji> <b>Ошибка: данное медиа не поддерживает спойлер</b>",
        "processing": "<emoji document_id=5276412364458059956>🕓</emoji> <b>Обработка медиафайла...</b>"
    }

    @loader.command()
    async def spmcmd(self, message):
        """Наложить спойлер на фото"""
        reply = await message.get_reply_message()
        
        if not reply or not reply.media:
            await utils.answer(message, self.strings["no_reply"])
            return

        is_photo = hasattr(reply, "photo") and reply.photo
        is_document = hasattr(reply, "document") and reply.document
        
        if not is_photo and not is_document:
            await utils.answer(message, self.strings["no_media"])
            return

        status_message = await utils.answer(message, self.strings["processing"])
        
        media_bytes = await self._client.download_media(reply, bytes)
        
        file_name = "media_spoiler"
        mime_type = None
        attributes = []

        if is_photo:
            file_name += ".jpg"
        elif is_document:
            mime_type = reply.document.mime_type
            attributes = reply.document.attributes
            if mime_type == "video/mp4":
                file_name += ".mp4"
            elif mime_type == "image/gif":
                file_name += ".gif"
            else:
                file_name += ".bin"

        uploaded_file = await self._client.upload_file(media_bytes, file_name=file_name)
        
        if is_photo:
            media = types.InputMediaUploadedPhoto(
                file=uploaded_file,
                spoiler=True
            )
        else:
            media = types.InputMediaUploadedDocument(
                file=uploaded_file,
                mime_type=mime_type,
                attributes=attributes,
                spoiler=True
            )
        
        if reply.out:
            await self._client.edit_message(
                message.peer_id,
                reply.id,
                file=media
            )
        else:
            await self._client.send_file(
                message.peer_id,
                file=media,
                reply_to=reply.id
            )
        
        await status_message.delete()
        if message.out:
            await message.delete()
