#                © Copyright 2025
#            ✈ https://t.me/json1c_modules
# 🆓 Released into the public domain under The Unlicense.
#
# This is free and unencumbered software released into the public domain.
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, for any purpose, commercial or non-commercial.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

# meta developer: @json1c_modules
# requires: aiohttp requests git+https://github.com/MarshalX/yandex-music-api mutagen

import tempfile
from typing import Optional

from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, ID3, error

from yandex_music import ClientAsync
from yandex_music.exceptions import UnauthorizedError

from .. import loader, utils


class TracksNotFoundError(Exception): ...


@loader.tds
class YandexMusicMod(loader.Module):
    strings = {
        "name": "Yandex Music",
        "not_enough_args": ".dlt [название]",
        "downloading": "<emoji document_id=5386367538735104399>⌛</emoji> <b>Загрузка...</b>",
        "not_found_tracks": "По вашему запросу треков не найдено",
        "no_yandex_music_token": (
            "Получите токен Yandex Music и укажите его в конфиге\n\n"

            "<a href='https://github.com/MarshalX/yandex-music-api/discussions/513#discussion-3903521'>Как получить токен</a>"
        ),
        "unauthorized": "🚫 Невалидный токен Yandex Music",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            *(
                "YANDEX_MUSIC_TOKEN",
                "",
                "Токен Yandex Music",
            ),
        )


    async def init_yandex_music_client(self):
        if hasattr(self, "yandex_music_client"):
            return

        self.yandex_music_client = ClientAsync(
            token=self.config["YANDEX_MUSIC_TOKEN"]
        )

        await self.yandex_music_client.init()

    async def dltcmd(self, message):
        """Скачать трек по названию"""

        args = utils.get_args_raw(message)

        if not self.config["YANDEX_MUSIC_TOKEN"]:
            return await utils.answer(
                message,
                self.strings("no_yandex_music_token")
            )

        if not args:
            return await utils.answer(
                message,
                self.strings("not_enough_args")
            )

        try:
            track_id = await self.search_track(args)
        except TracksNotFoundError:
            return await utils.answer(
                message,
                self.strings("not_found_tracks")
            )
        except UnauthorizedError:
            return await utils.answer(
                message,
                self.strings("unauthorized")
            )

        response = await utils.answer(
            message,
            self.strings("downloading")
        )

        with (
            tempfile.NamedTemporaryFile("wb+", suffix=".mp3") as tmp_track,
            tempfile.NamedTemporaryFile("wb+", suffix=".jpg") as tmp_cover
        ):
            await self.direct_download(track_id, tmp_track.name, tmp_cover.name)

            if isinstance(response, list): # GeekTG
                await response[0].delete()
            else:
                await response.delete()

            with open(tmp_track.name, "rb") as track_file:
                await utils.answer(
                    message,
                    track_file
                )

    async def search_track(self, query: str):
        await self.init_yandex_music_client()

        search_result = await self.yandex_music_client.search(query, type_="track")

        if not search_result.tracks:
            raise TracksNotFoundError(f"No tracks found for query {query}")

        return search_result.tracks.results[0].track_id

    async def add_mp3_metadata(self, file_path, track, cover_path: Optional[str] = None):
        try:
            audio = EasyID3(file_path)
        except error:
            audio = ID3()
            audio.save(file_path)
            audio = EasyID3(file_path)

        if track.artists:
            audio['artist'] = ', '.join(artist.name for artist in track.artists)

        audio['title'] = track.title or "Без названия"

        if track.albums:
            audio['album'] = track.albums[0].title

        audio.save()

        if cover_path:
            with open(cover_path, 'rb') as img:
                img_data = img.read()
                audio = ID3(file_path)
                audio.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc='Cover',
                    data=img_data
                ))
                audio.save()

    async def direct_download(self, track_id: int, track_path: str, cover_path: str):
        await self.init_yandex_music_client()

        tracks = await self.yandex_music_client.tracks(track_id, with_positions=False)
        track = tracks[0]

        await track.download_async(track_path)

        if track.cover_uri is not None:
            await track.download_cover_async(cover_path)
            await self.add_mp3_metadata(track_path, track, cover_path)

        else:
            await self.add_mp3_metadata(track_path, track)