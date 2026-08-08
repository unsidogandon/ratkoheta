"""

    🌑 ShadowTikTok - Извлекатель медиа из Бездны

    Модуль для скачивания контента из TikTok (видео/фото) без водяных знаков.

"""



from .. import loader, utils

import aiohttp

import io

import asyncio

import logging



logger = logging.getLogger(__name__)



# 🛡️ Сакральная Структура

version = (1, 6, 0) # Обновленная версия

# meta developer: @HarutyaModules

# scope: hikka_only

# meta fhsdesc: #ShadowTikTok #tiktok #видео #фото #без_вм #скачивание #альбомы



@loader.tds

class ShadowTikTokMod(loader.Module):

    """

    Скачивает видео или фото из TikTok без водяного знака,

    автоматически определяя тип контента. Фото отправляются альбомом.

    Команда: .tt <ссылка>

    """



    strings = {

        "name": "ShadowTikTok",

        "loading": "<b>🌑 Подключаюсь к потоку данных...</b>",

        "downloading_video": "<b>📥 Извлекаю материю (Скачивание видео)...</b>",

        "downloading_photos": "<b>📸 Извлекаю материю (Скачивание {count} фото)...</b>",

        "uploading_photos": "<b>📤 Материализация (Отправка альбома)...</b>", # NEW

        "no_args": "<b>❌ Хозяйка, Вы не дали мне цель (Ссылку).</b>",

        "error_api": "<b>⚠️ Эфир отверг запрос. Возможно, ссылка мертва или сервис недоступен.</b>",

        "error_net": "<b>🚫 Ошибка соединения с Бездной.</b>",

        "no_media_found": "<b>❌ В Бездне не найдено ни видео, ни фото по этой ссылке.</b>",

    }



    strings_ru = {

        "loading": "<b>🌑 Подключаюсь к потоку данных...</b>",

        "downloading_video": "<b>📥 Извлекаю материю (Скачивание видео)...</b>",

        "downloading_photos": "<b>📸 Извлекаю материю (Скачивание {count} фото)...</b>",

        "uploading_photos": "<b>📤 Материализация (Отправка альбома)...</b>",

        "no_args": "<b>❌ Хозяйка, Вы не дали мне цель (Ссылку).</b>",

        "error_api": "<b>⚠️ Эфир отверг запрос. Возможно, ссылка мертва или сервис недоступен.</b>",

        "error_net": "<b>🚫 Ошибка соединения с Бездной.</b>",

        "no_media_found": "<b>❌ В Бездне не найдено ни видео, ни фото по этой ссылке.</b>",

    }



    async def client_ready(self, client, db):

        self.client = client

        self.db = db



    async def _fetch_tiktok_api_data(self, url, session, headers):

        """Внутренний ритуал: запрос метаданных у теневых шлюзов TikTok."""

        async with session.post(

            "https://www.tikwm.com/api/", 

            data={"url": url}, 

            headers=headers

        ) as response:

            data = await response.json()



        if "data" not in data:

            err_msg = data.get('msg', 'Unknown Error')

            raise ValueError(f"{self.strings('error_api')}\nLog: {err_msg}")

        

        video_url = data["data"].get("play")

        image_urls = data["data"].get("images")

        title = data["data"].get("title", "ShadowTikTok Media")

        author = data["data"].get("author", {}).get("nickname", "Unknown")

        

        return video_url, image_urls, title, author



    async def _send_video(self, message, status_msg, video_url, title, author, reply_to, session, headers):

        """Внутренний ритуал: отправка видео."""

        await utils.answer(status_msg, self.strings("downloading_video"))

        

        async with session.get(video_url, headers=headers) as vid_stream:

            video_bytes = await vid_stream.read()



        file = io.BytesIO(video_bytes)

        file.name = f"TikTok_{author}.mp4"

        

        caption_base = (

            f"<b>🎥 Author:</b> {utils.escape_html(author)}\n"

            f"<b>📝 Title:</b> {utils.escape_html(title)}"

        )

        

        await self.client.send_file(

            message.chat_id,

            file,

            caption=caption_base,

            reply_to=reply_to,

            parse_mode="HTML"

        )

        await status_msg.delete()



    async def _send_photos(self, message, status_msg, image_urls, title, author, reply_to, session, headers):

        """Внутренний ритуал: отправка фото (альбомами)."""

        await utils.answer(status_msg, self.strings("downloading_photos").format(count=len(image_urls)))



        caption_base = (

            f"<b>🎥 Author:</b> {utils.escape_html(author)}\n"

            f"<b>📝 Title:</b> {utils.escape_html(title)}"

        )



        media_files = []



        # 1. Скачивание всех изображений в память

        for idx, img_url in enumerate(image_urls):

            async with session.get(img_url, headers=headers) as img_stream:

                content_type = img_stream.headers.get('Content-Type')

                image_bytes = await img_stream.read()



            file = io.BytesIO(image_bytes)

            

            # Определение расширения

            file_ext = 'jpg'

            if content_type:

                if 'jpeg' in content_type or 'jpg' in content_type: file_ext = 'jpg'

                elif 'png' in content_type: file_ext = 'png'

                elif 'gif' in content_type: file_ext = 'gif'

                elif 'webp' in content_type: file_ext = 'webp'

                else: file_ext = img_url.split('.')[-1] if '.' in img_url else 'jpg'

            else:

                file_ext = img_url.split('.')[-1] if '.' in img_url else 'jpg'



            file.name = f"TikTok_{author}_{idx+1}.{file_ext}"

            media_files.append(file)



        # 2. Отправка альбомами (группировка по 10 штук, так как это лимит Telegram)

        await utils.answer(status_msg, self.strings("uploading_photos"))

        

        chunk_size = 10

        chunks = [media_files[i:i + chunk_size] for i in range(0, len(media_files), chunk_size)]



        for i, chunk in enumerate(chunks):

            # Подпись добавляем только к первому альбому, чтобы не спамить текстом

            caption = caption_base if i == 0 else ""

            

            await self.client.send_file(

                message.chat_id,

                file=chunk,

                caption=caption,

                reply_to=reply_to,

                parse_mode="HTML"

            )

            

            # Небольшая задержка между альбомами, если их несколько

            if len(chunks) > 1:

                await asyncio.sleep(1)



        await status_msg.delete()



    async def _process_command(self, message):

        """Единый механизм обработки ссылки для команды .tt"""

        args = utils.get_args_raw(message)

        reply = await message.get_reply_message()



        url = None

        reply_to = None



        if args:

            url = args

            reply_to = message.reply_to_msg_id

        elif reply:

            url = reply.raw_text

            reply_to = reply.id

        

        if not url:

            await utils.answer(message, self.strings("no_args"))

            return



        status_msg = await utils.answer(message, self.strings("loading"))



        headers = {

            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",

            "Accept-Encoding": "gzip, deflate",

            "Accept-Language": "en-US,en;q=0.9",

        }



        try:

            async with aiohttp.ClientSession() as session:

                video_url, image_urls, title, author = await self._fetch_tiktok_api_data(url, session, headers)



                if image_urls and isinstance(image_urls, list) and image_urls:

                    await self._send_photos(message, status_msg, image_urls, title, author, reply_to, session, headers)

                elif video_url:

                    await self._send_video(message, status_msg, video_url, title, author, reply_to, session, headers)

                else:

                    await utils.answer(status_msg, self.strings("no_media_found"))

                    await status_msg.delete()



                if not reply and message.is_private:

                     await message.delete()



        except ValueError as ve:

            logger.exception(f"Ошибка API в ShadowTikTok: {ve}") 

            await utils.answer(status_msg, f"{ve}")

        except Exception as e:

            logger.exception(f"Непредвиденная ошибка в ShadowTikTok: {e}") 

            await utils.answer(status_msg, f"{self.strings('error_net')}\n<code>{utils.escape_html(str(e))}</code>")



    @loader.command(name="tt", ru_doc="<ссылка> - Скачать видео или фото из TikTok")

    async def ttcmd(self, message):

        """<ссылка> - Скачать видео или фото из TikTok"""

        await self._process_command(message)