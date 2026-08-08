# meta developer: @coddan

from .. import loader, utils
import logging
import json
import io
import aiohttp
import random

logger = logging.getLogger(__name__)

@loader.tds
class MusicPlaylistsMod(loader.Module):
    """Модуль для создания и управления музыкальными плейлистами, а также поиска текстов песен"""
    strings = {"name": "MusicPlaylists"}

    async def client_ready(self, client, db):
        self.client = client
        self.db = db

    async def _get_target(self):
        chat = None
        async for dialog in self.client.iter_dialogs():
            if dialog.name == "heroku-userbot" and dialog.is_group:
                chat = dialog.entity
                break

        has_forum_support = True
        try:
            from telethon.tl.functions.channels import ToggleForumRequest, GetForumTopicsRequest, CreateForumTopicRequest
        except ImportError:
            has_forum_support = False

        if not chat:
            from telethon.tl.functions.channels import CreateChannelRequest
            try:
                result = await self.client(CreateChannelRequest(
                    title="heroku-userbot",
                    about="MusicPlaylists storage",
                    megagroup=True
                ))
                chat = result.chats[0]
                if has_forum_support:
                    try:
                        await self.client(ToggleForumRequest(channel=chat, enabled=True))
                    except Exception as e:
                        logger.error(f"Failed to enable forum: {e}")
            except Exception as e:
                logger.error(f"Failed to create heroku-userbot group: {e}")
                return "me", None

        if chat != "me" and has_forum_support and not getattr(chat, 'forum', False):
            try:
                await self.client(ToggleForumRequest(channel=chat, enabled=True))
                chat = await self.client.get_entity(chat.id)
            except Exception as e:
                logger.error(f"Failed to enable forum: {e}")

        topic_id = self.db.get(self.name, "topic_id")
        topic_chat_id = self.db.get(self.name, "topic_chat_id")

        if chat != "me" and has_forum_support and (not topic_id or topic_chat_id != chat.id):
            try:
                topics_res = await self.client(GetForumTopicsRequest(
                    channel=chat,
                    offset_date=None,
                    offset_id=0,
                    offset_topic=0,
                    limit=100
                ))
                for t in topics_res.topics:
                    if t.title == "MusicPlaylists":
                        topic_id = t.id
                        break
            except Exception as e:
                logger.error(f"Failed to get forum topics: {e}")

            if not topic_id:
                try:
                    topic_res = await self.client(CreateForumTopicRequest(
                        channel=chat,
                        title="MusicPlaylists",
                        random_id=random.randint(1, 2**63 - 1)
                    ))
                    for update in topic_res.updates:
                        if hasattr(update, 'message') and hasattr(update.message, 'action'):
                            from telethon.tl.types import MessageActionTopicCreate
                            if isinstance(update.message.action, MessageActionTopicCreate):
                                topic_id = update.message.id
                                break
                    if not topic_id:
                        topics_res = await self.client(GetForumTopicsRequest(
                            channel=chat,
                            offset_date=None,
                            offset_id=0,
                            offset_topic=0,
                            limit=100
                        ))
                        for t in topics_res.topics:
                            if t.title == "MusicPlaylists":
                                topic_id = t.id
                                break
                except Exception as e:
                    logger.error(f"Failed to create forum topic: {e}")
                    topic_id = None

            if topic_id:
                self.db.set(self.name, "topic_id", topic_id)
                self.db.set(self.name, "topic_chat_id", chat.id)

        if not has_forum_support:
            topic_id = None

        return chat, topic_id

    @loader.command()
    async def plcreatecmd(self, message):
        """<название> - Создать новый плейлист"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Пожалуйста, укажите название плейлиста.")
            return
        
        playlists = self.db.get(self.name, "playlists", {})
        if args in playlists:
            await utils.answer(message, f"<b>[MusicPlaylists]</b> Плейлист <code>{args}</code> уже существует.")
            return
        
        playlists[args] = []
        self.db.set(self.name, "playlists", playlists)
        await utils.answer(message, f"<b>[MusicPlaylists]</b> Плейлист <code>{args}</code> успешно создан!")

    @loader.command()
    async def pldelcmd(self, message):
        """<название> - Удалить плейлист"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Пожалуйста, укажите название плейлиста.")
            return
        
        playlists = self.db.get(self.name, "playlists", {})
        if args not in playlists:
            await utils.answer(message, f"<b>[MusicPlaylists]</b> Плейлист <code>{args}</code> не найден.")
            return
        
        del playlists[args]
        self.db.set(self.name, "playlists", playlists)
        
        banners = self.db.get(self.name, "banners", {})
        if args in banners:
            del banners[args]
            self.db.set(self.name, "banners", banners)
            
        await utils.answer(message, f"<b>[MusicPlaylists]</b> Плейлист <code>{args}</code> удален.")

    @loader.command()
    async def pllistcmd(self, message):
        """Список всех ваших плейлистов"""
        playlists = self.db.get(self.name, "playlists", {})
        if not playlists:
            await utils.answer(message, "<b>[MusicPlaylists]</b> У вас еще нет ни одного плейлиста.")
            return
        
        banners = self.db.get(self.name, "banners", {})
        text = "<b>🎵 Ваши плейлисты:</b>\n<blockquote expandable>"
        for name, tracks in playlists.items():
            has_banner = " 🖼" if name in banners else ""
            text += f"🎧 <code>{name}</code> — {len(tracks)} треков{has_banner}\n"
        text += "</blockquote>"
        
        await utils.answer(message, text)

    @loader.command()
    async def pladdcmd(self, message):
        """<название> (реплай на аудио) - Добавить трек в плейлист"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Пожалуйста, укажите название плейлиста.")
            return
        
        reply = await message.get_reply_message()
        if not reply or not reply.audio:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Пожалуйста, ответьте на аудиосообщение.")
            return
        
        playlists = self.db.get(self.name, "playlists", {})
        if args not in playlists:
            await utils.answer(message, f"<b>[MusicPlaylists]</b> Плейлист <code>{args}</code> не найден. Сначала создайте его с помощью .plcreate")
            return
        
        title = "Неизвестный трек"
        performer = "Неизвестный исполнитель"
        if reply.document:
            for attr in reply.document.attributes:
                if hasattr(attr, 'title') and hasattr(attr, 'performer'):
                    title = attr.title or title
                    performer = attr.performer or performer
        
        chat, topic_id = await self._get_target()
        try:
            caption_text = "НЕ УДАЛЯТЬ , ИНАЧЕ ТРЕК ПЕРЕСТАНЕТ РАБОТАТЬ В ПЛЕЙЛИСТЕ"
            if topic_id:
                saved_msg = await self.client.send_file(chat, reply.media, caption=caption_text, reply_to=topic_id)
            else:
                saved_msg = await self.client.send_file(chat, reply.media, caption=caption_text)
        except Exception as e:
            await utils.answer(message, f"<b>[MusicPlaylists]</b> Ошибка при сохранении трека в избранное: {e}")
            return
        
        track_data = {
            "chat_id": saved_msg.chat_id,
            "msg_id": saved_msg.id,
            "title": title,
            "performer": performer
        }
        
        playlists[args].append(track_data)
        self.db.set(self.name, "playlists", playlists)
        
        await utils.answer(message, f"<b>[MusicPlaylists]</b> Трек <b>{performer} - {title}</b> добавлен в <code>{args}</code>!")

    @loader.command()
    async def plremcmd(self, message):
        """<название> <индекс> - Удалить трек из плейлиста по его индексу"""
        args_raw = utils.get_args_raw(message)
        args = args_raw.rsplit(maxsplit=1)
        
        if len(args) < 2:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Использование: <code>.plrem &lt;название плейлиста&gt; &lt;индекс&gt;</code>")
            return
        
        pl_name, index_str = args[0], args[1]
        if not index_str.isdigit():
            await utils.answer(message, "<b>[MusicPlaylists]</b> Индекс должен быть числом.")
            return
        
        index = int(index_str) - 1
        playlists = self.db.get(self.name, "playlists", {})
        
        if pl_name not in playlists:
            await utils.answer(message, f"<b>[MusicPlaylists]</b> Плейлист <code>{pl_name}</code> не найден.")
            return
        
        if index < 0 or index >= len(playlists[pl_name]):
            await utils.answer(message, "<b>[MusicPlaylists]</b> Неверный индекс трека.")
            return
        
        removed = playlists[pl_name].pop(index)
        self.db.set(self.name, "playlists", playlists)
        
        await utils.answer(message, f"<b>[MusicPlaylists]</b> Трек <b>{removed['performer']} - {removed['title']}</b> удален из <code>{pl_name}</code>.")

    @loader.command()
    async def plrencmd(self, message):
        """<название> <индекс> <Новый исполнитель> - <Новое название> - Изменить название трека в плейлисте"""
        args_raw = utils.get_args_raw(message)
        if not args_raw:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Укажите аргументы: <code>&lt;название&gt; &lt;индекс&gt; &lt;Новый исполнитель&gt; - &lt;Новое название&gt;</code>")
            return
            
        playlists = self.db.get(self.name, "playlists", {})
        
        pl_name = None
        for name in sorted(playlists.keys(), key=len, reverse=True):
            if args_raw.startswith(name + " "):
                pl_name = name
                break
                
        if not pl_name:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Плейлист не найден. Проверьте правильность названия.")
            return
            
        remaining = args_raw[len(pl_name):].strip()
        parts = remaining.split(maxsplit=1)
        
        if len(parts) < 2:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Укажите индекс и новое название трека.")
            return
            
        index_str, new_name = parts
        
        if not index_str.isdigit():
            await utils.answer(message, "<b>[MusicPlaylists]</b> Индекс должен быть числом.")
            return
            
        index = int(index_str) - 1
        
        if index < 0 or index >= len(playlists[pl_name]):
            await utils.answer(message, "<b>[MusicPlaylists]</b> Неверный индекс трека.")
            return
            
        if " - " in new_name:
            performer, title = new_name.split(" - ", maxsplit=1)
        else:
            performer = "Неизвестный исполнитель"
            title = new_name
            
        old_performer = playlists[pl_name][index].get("performer", "Неизвестный исполнитель")
        old_title = playlists[pl_name][index].get("title", "Неизвестный трек")
        
        playlists[pl_name][index]["performer"] = performer.strip()
        playlists[pl_name][index]["title"] = title.strip()
        
        self.db.set(self.name, "playlists", playlists)
        
        await utils.answer(message, f"<b>[MusicPlaylists]</b> Трек <b>{old_performer} - {old_title}</b> переименован в <b>{performer.strip()} - {title.strip()}</b> в плейлисте <code>{pl_name}</code>.")

    @loader.command()
    async def plbannercmd(self, message):
        """<название> (реплай на медиа) - Установить баннер для плейлиста"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Пожалуйста, укажите название плейлиста.")
            return
        
        reply = await message.get_reply_message()
        if not reply or not reply.media:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Пожалуйста, ответьте на медиасообщение (фото/видео/гиф).")
            return
        
        playlists = self.db.get(self.name, "playlists", {})
        if args not in playlists:
            await utils.answer(message, f"<b>[MusicPlaylists]</b> Плейлист <code>{args}</code> не найден.")
            return
        
        banners = self.db.get(self.name, "banners", {})
        banners[args] = {
            "chat_id": reply.chat_id,
            "msg_id": reply.id
        }
        self.db.set(self.name, "banners", banners)
        
        await utils.answer(message, f"<b>[MusicPlaylists]</b> Баннер для плейлиста <code>{args}</code> успешно установлен!")

    @loader.command()
    async def plrmbannercmd(self, message):
        """<название> - Удалить баннер плейлиста"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Пожалуйста, укажите название плейлиста.")
            return
        
        banners = self.db.get(self.name, "banners", {})
        if args not in banners:
            await utils.answer(message, f"<b>[MusicPlaylists]</b> У плейлиста <code>{args}</code> нет баннера.")
            return
        
        del banners[args]
        self.db.set(self.name, "banners", banners)
        
        await utils.answer(message, f"<b>[MusicPlaylists]</b> Баннер плейлиста <code>{args}</code> удален.")

    @loader.command()
    async def playlistcmd(self, message):
        """<название> - Просмотр треков в плейлисте"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Пожалуйста, укажите название плейлиста.")
            return
        
        playlists = self.db.get(self.name, "playlists", {})
        if args not in playlists:
            await utils.answer(message, f"<b>[MusicPlaylists]</b> Плейлист <code>{args}</code> не найден.")
            return
        
        tracks = playlists[args]
        if not tracks:
            await utils.answer(message, f"<b>[MusicPlaylists]</b> Плейлист <code>{args}</code> пуст.")
            return
        
        text = f"<b>🎵 Плейлист: <code>{args}</code></b>\n<blockquote expandable>"
        for i, track in enumerate(tracks, 1):
            text += f"<b>{i}.</b> {track['performer']} — {track['title']}\n"
        text += "</blockquote>"
        
        banners = self.db.get(self.name, "banners", {})
        if args in banners:
            banner_data = banners[args]
            try:
                msg = await self.client.get_messages(banner_data["chat_id"], ids=banner_data["msg_id"])
                if msg and msg.media:
                    if len(text) <= 1024:
                        await self.client.send_file(message.peer_id, msg.media, caption=text)
                        await message.delete()
                        return
                    else:
                        await self.client.send_file(message.peer_id, msg.media, caption=f"<b>🎵 Плейлист: <code>{args}</code></b>")
            except Exception as e:
                logger.error(f"Failed to load banner: {e}")
        
        await utils.answer(message, text)

    @loader.command()
    async def plplaycmd(self, message):
        """<название> - Отправить все треки из плейлиста в текущий чат"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Пожалуйста, укажите название плейлиста.")
            return
        
        playlists = self.db.get(self.name, "playlists", {})
        if args not in playlists:
            await utils.answer(message, f"<b>[MusicPlaylists]</b> Плейлист <code>{args}</code> не найден.")
            return
        
        tracks = playlists[args]
        if not tracks:
            await utils.answer(message, f"<b>[MusicPlaylists]</b> Плейлист <code>{args}</code> пуст.")
            return
        
        banners = self.db.get(self.name, "banners", {})
        if args in banners:
            banner_data = banners[args]
            try:
                msg = await self.client.get_messages(banner_data["chat_id"], ids=banner_data["msg_id"])
                if msg and msg.media:
                    await self.client.send_file(message.peer_id, msg.media, caption=f"<b>🎵 Воспроизведение плейлиста: <code>{args}</code></b>")
            except Exception as e:
                logger.error(f"Failed to load banner: {e}")
        
        msg_status = await utils.answer(message, f"<b>[MusicPlaylists]</b> Воспроизведение <code>{args}</code>...")
        
        for track in tracks:
            try:
                msg = await self.client.get_messages(track["chat_id"], ids=track["msg_id"])
                if msg and msg.media:
                    await self.client.send_file(message.peer_id, msg.media)
                else:
                    await self.client.send_message(
                        message.peer_id, 
                        f"<i>❌ Не удалось загрузить трек (удален или недоступен): {track['performer']} - {track['title']}</i>"
                    )
            except Exception as e:
                logger.error(f"Failed to play track {track['title']}: {e}")
                await self.client.send_message(
                    message.peer_id, 
                    f"<i>❌ Не удалось загрузить трек: {track['performer']} - {track['title']}</i>"
                )
        
        if msg_status:
            await utils.answer(msg_status, f"<b>[MusicPlaylists]</b> Воспроизведение плейлиста <code>{args}</code> завершено.")

    @loader.command()
    async def pltrackcmd(self, message):
        """<название> <индекс1> [индекс2] ... - Отправить определенные треки из плейлиста в текущий чат по индексам"""
        args_raw = utils.get_args_raw(message).replace(',', ' ')
        parts = args_raw.split()
        
        indices = []
        while parts and parts[-1].isdigit():
            indices.insert(0, int(parts.pop()) - 1)
        
        if not parts or not indices:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Использование: <code>.pltrack &lt;название плейлиста&gt; &lt;индекс1&gt; [индекс2] ...</code>")
            return
        
        pl_name = " ".join(parts)
        playlists = self.db.get(self.name, "playlists", {})
        
        if pl_name not in playlists:
            await utils.answer(message, f"<b>[MusicPlaylists]</b> Плейлист <code>{pl_name}</code> не найден.")
            return
        
        playlist_tracks = playlists[pl_name]
        valid_indices = [idx for idx in indices if 0 <= idx < len(playlist_tracks)]
        
        if not valid_indices:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Неверные индексы треков.")
            return
        
        msg_status = await utils.answer(message, f"<b>[MusicPlaylists]</b> Загрузка треков...")
        
        for index in valid_indices:
            track = playlist_tracks[index]
            try:
                msg = await self.client.get_messages(track["chat_id"], ids=track["msg_id"])
                if msg and msg.media:
                    await self.client.send_file(message.peer_id, msg.media)
                else:
                    await self.client.send_message(
                        message.peer_id,
                        f"<i>❌ Не удалось загрузить трек (удален или недоступен): {track['performer']} - {track['title']}</i>"
                    )
            except Exception as e:
                logger.error(f"Failed to play track {track['title']}: {e}")
                await self.client.send_message(
                    message.peer_id,
                    f"<i>❌ Не удалось загрузить трек: {track['performer']} - {track['title']}</i>"
                )
                
        if msg_status:
            await msg_status.delete()

    @loader.command()
    async def plsendcmd(self, message):
        """<название> - Найти и отправить трек по названию (или части) из всех плейлистов"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Пожалуйста, укажите название трека для поиска.")
            return
        
        playlists = self.db.get(self.name, "playlists", {})
        if not playlists:
            await utils.answer(message, "<b>[MusicPlaylists]</b> У вас еще нет ни одного плейлиста.")
            return

        search_query = args.lower()
        found_tracks = []

        for pl_name, tracks in playlists.items():
            for track in tracks:
                title = track.get("title", "").lower()
                performer = track.get("performer", "").lower()
                if search_query in title or search_query in performer:
                    if not any(t["msg_id"] == track["msg_id"] and t["chat_id"] == track["chat_id"] for t in found_tracks):
                        found_tracks.append(track)
                    if len(found_tracks) >= 5:
                        break
            if len(found_tracks) >= 5:
                break
        
        if not found_tracks:
            await utils.answer(message, f"<b>[MusicPlaylists]</b> Трек по запросу <code>{args}</code> не найден.")
            return

        msg_status = await utils.answer(message, f"<b>[MusicPlaylists]</b> Найдено треков: {len(found_tracks)}. Отправка...")
        
        for track in found_tracks:
            try:
                msg = await self.client.get_messages(track["chat_id"], ids=track["msg_id"])
                if msg and msg.media:
                    await self.client.send_file(message.peer_id, msg.media)
                else:
                    await self.client.send_message(
                        message.peer_id, 
                        f"<i>❌ Не удалось загрузить трек (удален или недоступен): {track['performer']} - {track['title']}</i>"
                    )
            except Exception as e:
                logger.error(f"Failed to play track {track['title']}: {e}")
                await self.client.send_message(
                    message.peer_id, 
                    f"<i>❌ Не удалось загрузить трек: {track['performer']} - {track['title']}</i>"
                )
        
        if msg_status:
            await msg_status.delete()

    @loader.command()
    async def plexportcmd(self, message):
        """<название> - Экспортировать плейлист в файл"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Пожалуйста, укажите название плейлиста.")
            return
        
        playlists = self.db.get(self.name, "playlists", {})
        if args not in playlists:
            await utils.answer(message, f"<b>[MusicPlaylists]</b> Плейлист <code>{args}</code> не найден.")
            return
        
        banners = self.db.get(self.name, "banners", {})
        
        data = {
            "tracks": playlists[args],
            "banner": banners.get(args)
        }
        
        file = io.BytesIO(json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8'))
        file.name = f"{args}_playlist.json"
        
        await self.client.send_file(
            message.peer_id,
            file,
            caption=f"<b>[MusicPlaylists]</b> Плейлист <code>{args}</code>",
            reply_to=message.reply_to_msg_id
        )
        await message.delete()

    @loader.command()
    async def plimportcmd(self, message):
        """<название> (реплай на файл) - Импортировать плейлист из файла"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Пожалуйста, укажите название для нового плейлиста.")
            return
        
        reply = await message.get_reply_message()
        if not reply or not reply.document:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Пожалуйста, ответьте на файл плейлиста (.json).")
            return
        
        try:
            content = await reply.download_media(bytes)
            data = json.loads(content.decode('utf-8'))
            
            if isinstance(data, list):
                tracks = data
                banner = None
            elif isinstance(data, dict) and "tracks" in data:
                tracks = data["tracks"]
                banner = data.get("banner")
            else:
                await utils.answer(message, "<b>[MusicPlaylists]</b> Неверный формат файла.")
                return
            
            for track in tracks:
                if not isinstance(track, dict) or not all(k in track for k in ["chat_id", "msg_id", "title", "performer"]):
                    await utils.answer(message, "<b>[MusicPlaylists]</b> Неверный формат файла: отсутствуют необходимые ключи трека.")
                    return
                    
        except Exception as e:
            await utils.answer(message, f"<b>[MusicPlaylists]</b> Ошибка при чтении файла: {e}")
            return
            
        playlists = self.db.get(self.name, "playlists", {})
        playlists[args] = tracks
        self.db.set(self.name, "playlists", playlists)
        
        if banner:
            banners = self.db.get(self.name, "banners", {})
            banners[args] = banner
            self.db.set(self.name, "banners", banners)
        
        await utils.answer(message, f"<b>[MusicPlaylists]</b> Плейлист <code>{args}</code> успешно импортирован! ({len(tracks)} треков)")

    @loader.command()
    async def pllyricscmd(self, message):
        """(реплай на аудио) - Найти текст песни"""
        reply = await message.get_reply_message()
        if not reply or not reply.audio:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Пожалуйста, ответьте на аудиосообщение.")
            return
        
        title = ""
        performer = ""
        file_name = ""
        
        if reply.document:
            for attr in reply.document.attributes:
                if hasattr(attr, 'title') and hasattr(attr, 'performer'):
                    title = attr.title or ""
                    performer = attr.performer or ""
                if hasattr(attr, 'file_name'):
                    file_name = attr.file_name or ""
        
        query = f"{performer} {title}".strip()
        if not query and file_name:
            query = file_name.rsplit('.', 1)[0]
            
        if not query:
            await utils.answer(message, "<b>[MusicPlaylists]</b> Не удалось определить название трека.")
            return

        msg_status = await utils.answer(message, f"<b>[MusicPlaylists]</b> Поиск текста для <b>{query}</b>...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://lrclib.net/api/search", params={"q": query}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data and isinstance(data, list) and len(data) > 0:
                            track_name = data[0].get("trackName", title)
                            artist_name = data[0].get("artistName", performer)
                            lyrics = data[0].get("plainLyrics") or data[0].get("syncedLyrics")
                            
                            if lyrics:
                                text = f"<b>🎵 Текст песни: {artist_name} — {track_name}</b>\n\n<blockquote expandable>{lyrics}</blockquote>"
                                if len(text) > 4096:
                                    file = io.BytesIO(lyrics.encode('utf-8'))
                                    file.name = f"{artist_name} - {track_name}.txt"
                                    await self.client.send_file(
                                        message.peer_id,
                                        file,
                                        caption=f"<b>[MusicPlaylists]</b> Текст песни <b>{artist_name} — {track_name}</b>",
                                        reply_to=reply.id
                                    )
                                    if msg_status:
                                        await msg_status.delete()
                                else:
                                    await utils.answer(msg_status, text)
                                return
        except Exception as e:
            logger.error(f"Error fetching lyrics: {e}")

        await utils.answer(msg_status, f"<b>[MusicPlaylists]</b> Текст песни для <b>{query}</b> не найден.")
