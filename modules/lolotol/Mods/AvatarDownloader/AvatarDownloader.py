#  ██ ████ ██ ████ ████ ████ ██
#  ██ █  █ ██ █   █  ██  █   █ ██
#  ██ ████ ██ ████   ██  ████ ██

#   https://t.me/lolotol089
#   https://github.com/lolotol/Mods/raw/main/AvatarDownloader

# ---------------------------------------------------------------------------------
# Name: AvatarDownloader
# Description: Скачивает аватарку пользователя по номеру или рандомно, а также аватарку чата/канала
# meta developer: @lolotol89
# ---------------------------------------------------------------------------------

import logging
import os
import asyncio
import random
import string
from datetime import datetime as dt
from telethon.tl.types import Message, DocumentAttributeVideo, VideoSizeEmojiMarkup, User
from telethon import functions

from .. import loader, utils

__version__ = (1, 2, 1)

logger = logging.getLogger(__name__)

@loader.tds
class AvatarDownloader(loader.Module):
    """Скачивает аватарку пользователя по номеру или рандомно, а также аватарку чата/канала"""

    strings = {
        "name": "AvatarDownloader",

        "no_number": "<emoji document_id=5350734660391432462>⚠️</emoji> <b>Укажите номер аватарки!</b>",
        "invalid_number": "<emoji document_id=5350734660391432462>⚠️</emoji> <b>Номер должен быть положительным целым числом!</b>",
        "no_user": "<emoji document_id=5350734660391432462>⚠️</emoji> <b>Не удалось определить пользователя!</b>",
        "downloading": "<emoji document_id=5258419835922030550>🕔</emoji> <b>Скачиваю аватарку...</b>",
        "no_avatar": "<emoji document_id=5350734660391432462>⚠️</emoji> <b>Нет аватарки!</b>",
        "no_avatar_total_zero": "<emoji document_id=5350734660391432462>⚠️</emoji> <b>Нет аватарок вовсе! Всего: 0</b>",
        "no_avatar_number": "<emoji document_id=5350734660391432462>⚠️</emoji> <b>Нет аватарки под номером {number}! Всего: {total}</b>",
        "chat_avatar": "<emoji document_id=5258254475386167466>🖼</emoji> Аватарка чата/канала",
        "error": "<emoji document_id=5213335456841749820>❌</emoji> <b>Ошибка:</b> <code>{error}</code>",
        "video_avatar": "<emoji document_id=5258254475386167466>🖼</emoji> Видео/эмодзи аватарка #{number} из {total}",
        "photo_avatar": "<emoji document_id=5258254475386167466>🖼</emoji> Аватарка #{number} из {total}",
        "random_avatar": "<emoji document_id=5258254475386167466>🖼</emoji> Рандомная аватарка #{number} из {total}",
        "only_users": "<emoji document_id=5350734660391432462>⚠️</emoji> <b>Множественные/рандомные аватарки только для пользователей!</b>",
    }

    async def client_ready(self, client, db):
        self._client = client

    async def _send_media(self, message: Message, media_bytes: bytes, caption: str, reply_to_id=None, is_video=False):
        if message.out:
            proc_msg = await message.edit(self.strings["downloading"])
        else:
            proc_msg = await self._client.send_message(message.peer_id, self.strings["downloading"], reply_to=message.id)

        try:
            if media_bytes is None:
                await proc_msg.edit(self.strings["no_avatar"])
                return

            timestamp = str(int(dt.now().timestamp()))
            rand_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            temp_input = f"temp_input_{timestamp}_{rand_str}.mp4"
            temp_output = f"temp_output_{timestamp}_{rand_str}.mp4"
            temp_photo = f"temp_photo_{timestamp}_{rand_str}.jpg"

            if is_video:
                with open(temp_input, 'wb') as f:
                    f.write(media_bytes)

                cmd = (
                    f'ffmpeg -y -i "{temp_input}" '
                    f'-f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 '
                    f'-c:v copy -c:a aac -shortest -map 0:v:0 -map 1:a:0 '
                    f'"{temp_output}"'
                )
                process = await asyncio.create_subprocess_shell(
                    cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                if process.returncode != 0:
                    raise Exception(f"ffmpeg error: {stderr.decode()}")

                video_file = temp_output

                proc = await asyncio.create_subprocess_exec(
                    'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1', video_file,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                duration = int(float(stdout.decode().strip())) if stdout else 0

                await self._client.send_file(
                    message.chat_id,
                    file=video_file,
                    caption=caption,
                    reply_to=reply_to_id,
                    force_document=False,
                    supports_streaming=True,
                    attributes=[DocumentAttributeVideo(
                        duration=duration,
                        w=512,
                        h=512,
                        supports_streaming=True,
                        round_message=False
                    )]
                )

                for f in [temp_input, temp_output]:
                    if os.path.exists(f):
                        os.remove(f)
            else:
                with open(temp_photo, 'wb') as f:
                    f.write(media_bytes)

                await self._client.send_file(
                    message.chat_id,
                    file=temp_photo,
                    caption=caption,
                    reply_to=reply_to_id,
                    force_document=False
                )

                if os.path.exists(temp_photo):
                    os.remove(temp_photo)

            await proc_msg.delete()

        except Exception as e:
            await utils.answer(proc_msg, self.strings["error"].format(error=str(e)))

    async def _get_random_avatar(self, message: Message, user):
        if not isinstance(user, User):
            await utils.answer(message, self.strings["only_users"])
            return

        try:
            res_count = await self._client(functions.photos.GetUserPhotosRequest(
                user_id=user, offset=0, max_id=0, limit=1
            ))
            total = res_count.count

            if total == 0:
                await utils.answer(message, self.strings["no_avatar_total_zero"])
                return

            number = random.randint(1, total)

            offset = (number - 1) // 100 * 100
            res = await self._client(functions.photos.GetUserPhotosRequest(
                user_id=user, offset=offset, max_id=0, limit=100
            ))

            photos = res.photos
            local_index = (number - 1) % 100
            if local_index >= len(photos):
                await utils.answer(message, self.strings["no_avatar_number"].format(number=number, total=total))
                return

            photo = photos[local_index]
            media_bytes = await self._client.download_media(photo, file=bytes)
            if media_bytes is None:
                await utils.answer(message, self.strings["no_avatar_number"].format(number=number, total=total))
                return

            is_video = photo.video_sizes is not None and len(photo.video_sizes) > 0
            caption = self.strings["random_avatar"].format(number=number, total=total)

            await self._send_media(message, media_bytes, caption, message.reply_to_msg_id, is_video)
        except Exception as e:
            await utils.answer(message, self.strings["error"].format(error=str(e)))

    @loader.command()
    async def getava(self, message: Message):
        """ — скачать аватарку по номеру пользователя или текущую чата: .getava [номер] [пользователь/reply]"""
        args = utils.get_args_raw(message).split()
        number = None
        target_arg = ""

        if args:
            try:
                number = int(args[0])
                if number < 1:
                    raise ValueError
                if len(args) > 1:
                    target_arg = " ".join(args[1:])
            except ValueError:
                number = None
                target_arg = utils.get_args_raw(message)

        reply_to_id = None
        target = None
        if message.is_reply:
            reply = await message.get_reply_message()
            reply_to_id = reply.id
            sender = await reply.get_sender()
            if sender:
                target = sender

        if target is None:
            if target_arg:
                try:
                    target = await self._client.get_entity(target_arg)
                except Exception:
                    await utils.answer(message, self.strings["no_user"])
                    return
            else:
                target = await self._client.get_entity(message.peer_id)

        # Чат/канал — только текущая аватарка
        if not isinstance(target, User):
            media_bytes = await self._client.download_profile_photo(target, file=bytes)
            if media_bytes is None:
                await utils.answer(message, self.strings["no_avatar"])
                return

            await self._send_media(message, media_bytes, self.strings["chat_avatar"], reply_to_id, False)
            if message.out:
                await message.delete()
            return

        # Пользователь
        if number is None:
            number = 1

        try:
            count_res = await self._client(functions.photos.GetUserPhotosRequest(
                user_id=target, offset=0, max_id=0, limit=1
            ))
            total = count_res.count

            if total == 0:
                await utils.answer(message, self.strings["no_avatar_total_zero"])
                return
            if number > total:
                await utils.answer(message, self.strings["no_avatar_number"].format(number=number, total=total))
                return

            offset = (number - 1) // 100 * 100
            res = await self._client(functions.photos.GetUserPhotosRequest(
                user_id=target, offset=offset, max_id=0, limit=100
            ))

            photos = res.photos
            local_index = (number - 1) % 100
            if local_index >= len(photos):
                await utils.answer(message, self.strings["no_avatar_number"].format(number=number, total=total))
                return

            photo = photos[local_index]
            media_bytes = await self._client.download_media(photo, file=bytes)
            if media_bytes is None:
                await utils.answer(message, self.strings["no_avatar_number"].format(number=number, total=total))
                return

            is_video = photo.video_sizes is not None and len(photo.video_sizes) > 0
            caption_key = "video_avatar" if is_video else "photo_avatar"
            caption = self.strings[caption_key].format(number=number, total=total)

            await self._send_media(message, media_bytes, caption, reply_to_id, is_video)
        except Exception as e:
            await utils.answer(message, self.strings["error"].format(error=str(e)))

    @loader.command()
    async def getmyava(self, message: Message):
        """ — скачать свою аватарку по номеру: .getmyava [номер]"""
        args = utils.get_args_raw(message).strip()
        if args:
            try:
                number = int(args)
                if number < 1:
                    raise ValueError
            except ValueError:
                await utils.answer(message, self.strings["invalid_number"])
                return
        else:
            number = 1

        user = await self._client.get_me()
        reply_to_id = message.reply_to_msg_id

        try:
            count_res = await self._client(functions.photos.GetUserPhotosRequest(
                user_id=user, offset=0, max_id=0, limit=1
            ))
            total = count_res.count

            if total == 0:
                await utils.answer(message, self.strings["no_avatar_total_zero"])
                return
            if number > total:
                await utils.answer(message, self.strings["no_avatar_number"].format(number=number, total=total))
                return

            offset = (number - 1) // 100 * 100
            res = await self._client(functions.photos.GetUserPhotosRequest(
                user_id=user, offset=offset, max_id=0, limit=100
            ))

            photos = res.photos
            local_index = (number - 1) % 100
            if local_index >= len(photos):
                await utils.answer(message, self.strings["no_avatar_number"].format(number=number, total=total))
                return

            photo = photos[local_index]
            media_bytes = await self._client.download_media(photo, file=bytes)
            if media_bytes is None:
                await utils.answer(message, self.strings["no_avatar_number"].format(number=number, total=total))
                return

            is_video = photo.video_sizes is not None and len(photo.video_sizes) > 0
            caption_key = "video_avatar" if is_video else "photo_avatar"
            caption = self.strings[caption_key].format(number=number, total=total)

            await self._send_media(message, media_bytes, caption, reply_to_id, is_video)
        except Exception as e:
            await utils.answer(message, self.strings["error"].format(error=str(e)))

    @loader.command()
    async def randomava(self, message: Message):
        """ — рандомная аватарка пользователя: .randomava [пользователь/reply]"""
        args = utils.get_args_raw(message)
        target_arg = args if args else ""

        reply_to_id = None
        target = None
        if message.is_reply:
            reply = await message.get_reply_message()
            reply_to_id = reply.id
            target = await reply.get_sender()

        if target is None and target_arg:
            try:
                target = await self._client.get_entity(target_arg)
            except Exception:
                await utils.answer(message, self.strings["no_user"])
                return

        if target is None:
            target = await self._client.get_me()

        await self._get_random_avatar(message, target)

    @loader.command()
    async def randommyava(self, message: Message):
        """ — рандомная своя аватарка"""
        user = await self._client.get_me()
        await self._get_random_avatar(message, user)
