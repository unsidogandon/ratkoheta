# meta developer: @Nedo_Modules
# я гей
__version__ = (0, 2, 0)
from .. import loader, utils
from ..inline.types import InlineCall
import logging
import asyncio
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

@loader.tds
class SteamViewer(loader.Module):
    """Steam модуль - трансляция игры, библиотека, профиль, плейсхолдеры"""
    
    strings = {
        'name': 'SteamViewer',
        
        '_api_key': "<tg-emoji emoji-id=6005570495603282482>🔑</tg-emoji> Steam API Key: https://steamcommunity.com/dev/apikey",
        '_account_id': "<tg-emoji emoji-id=5967548335542767952>💳</tg-emoji> Steam ID (17 цифр, начинается с 7656...)",
        '_stream_chat': "<tg-emoji emoji-id=5447510826304959724>💬</tg-emoji> Чат для трансляции (chat_id)",
        '_stream_msg': "<tg-emoji emoji-id=5447510826304959724>💬</tg-emoji> ID сообщения для трансляции",
        '_stream_text': "<tg-emoji emoji-id=6021741567163767583>💾</tg-emoji> Текст трансляции\nПлейсхолдеры:\n{name} - ник\n{game} - игра\n{playtime} - часов в игре\n{achievements} - достижения\n{status} - статус",
        '_profile_text': "<tg-emoji emoji-id=6021741567163767583>💾</tg-emoji> Текст профиля\nПлейсхолдеры:\n{name} - ник\n{realname} - реальное имя\n{status} - статус\n{created} - дата создания\n{current_game} - текущая игра\n{total_games} - всего игр\n{total_time} - общее время\n{top_game} - топ игра\n{top_game_time} - время в топ игре",
        
        'no_api_key': '<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>API_KEY не настроен!</b>',
        'no_account_id': '<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>ACCOUNT_ID не настроен!</b>',
        'no_api_key_or_id': '<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>API_KEY или ACCOUNT_ID не настроены!</b>',
        'noGame': '<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>Игра не запущена или профиль приватный</b>',
        'gameNotFound': '<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>Игра с ID {} не найдена</b>',
        'profile_private': '<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>Профиль приватный или не найден</b>',
        'no_stream_config': '<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>Не настроен чат или сообщение для трансляции!</b>',
        
        'stream_started': '<tg-emoji emoji-id=6021486789703769089>📡</tg-emoji> <b>Трансляция запущена!</b>\nБудет обновляться в настроенном сообщении',
        'stream_stopped': '<tg-emoji emoji-id=5908934603321642637>🎙</tg-emoji> <b>Трансляция остановлена</b>',
        'stream_not_running': '<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>Трансляция не запущена</b>',
        'stream_now': (
            '<tg-emoji emoji-id=5424675936891070474>🎤</tg-emoji> <b>Сейчас играет:</b>\n\n'
            '<tg-emoji emoji-id=6006038041448156880>📝</tg-emoji> <b>Название:</b> <code>{}</code>\n'
            '<tg-emoji emoji-id=5967548335542767952>💳</tg-emoji> <b>ID игры:</b> <code>{}</code>'
        ),
        
        'gameInfo': (
            '<tg-emoji emoji-id=5258508428212445001>🎮</tg-emoji> <b>{name}</b> — {price}\n\n'
            '<tg-emoji emoji-id=5956561916573782596>📄</tg-emoji> <b>Описание:</b>\n<i>{description}</i>\n\n'
            '{stats}'
            '<tg-emoji emoji-id=5967548335542767952>💳</tg-emoji> <b>AppID:</b> <code>{appid}</code>'
        ),
        'game_stats': '<tg-emoji emoji-id=5456502069756192095>🕓</tg-emoji> <b>Время в игре:</b> {playtime}\n<tg-emoji emoji-id=6021644067111180663>🏆</tg-emoji> <b>Достижения:</b> {achievements}\n\n',
        'game_not_owned': '<tg-emoji emoji-id=5271509874038051245>❌</tg-emoji> <i>Игра не в библиотеке</i>\n\n',
        
        'profile_default': (
            '<tg-emoji emoji-id=5255835635704408236>👤</tg-emoji> <b>Профиль Steam</b>\n\n'
            '<tg-emoji emoji-id=5879770735999717115>👤</tg-emoji> <b>Имя:</b> <code>{name}</code>\n'
            '<tg-emoji emoji-id=5936017305585586269>🪪</tg-emoji> <b>Реальное имя:</b> <code>{realname}</code>\n'
            '<tg-emoji emoji-id=5877485980901971030>📊</tg-emoji> <b>Статус:</b> {status}\n'
            '<tg-emoji emoji-id=6023880246128810031>📅</tg-emoji> <b>Аккаунт создан:</b> <code>{created}</code>\n'
            '<tg-emoji emoji-id=6021525053567409034>🗃</tg-emoji> <b>Всего игр:</b> {total_games}\n'
            '<tg-emoji emoji-id=5255971360965930740>🕔</tg-emoji> <b>Общее время:</b> {total_time}\n'
            '<tg-emoji emoji-id=6021644067111180663>🏆</tg-emoji> <b>Топ игра:</b> {top_game} — {top_game_time}\n\n'
            '<tg-emoji emoji-id=5258508428212445001>🎮</tg-emoji> <b>Сейчас в игре:</b>\n'
            '<i>{current_game}</i>'
        ),
        
        'gamesLibrary': (
            '<tg-emoji emoji-id=6021767126514144698>📦</tg-emoji> <b>Библиотека игр Steam</b>\n\n'
            '<tg-emoji emoji-id=5877485980901971030>📊</tg-emoji> <b>Всего игр:</b> {}\n'
            '<tg-emoji emoji-id=5456502069756192095>🕓</tg-emoji> <b>Общее время:</b> {} ч\n\n'
            '<tg-emoji emoji-id=5444931419270839381>🏅</tg-emoji> <b>Топ-{} по времени:</b>\n\n'
            '{}\n'
            '<blockquote expandable>\n'
            '<i><tg-emoji emoji-id=5422871492281001864>📊</tg-emoji> Сортировка: По времени игры (по убыванию)</i>\n'
            '</blockquote>'
        ),
        
        'online': '<tg-emoji emoji-id=6019289243916968110>🛜</tg-emoji> В сети',
        'offline': '<tg-emoji emoji-id=6019508188464814176>🛜</tg-emoji> Не в сети',
        'busy': '<tg-emoji emoji-id=5399899739439251665>🎩</tg-emoji> Занят',
        'away': '<tg-emoji emoji-id=5339286072876614251>✋</tg-emoji> Отошёл',
        'in_game': '<tg-emoji emoji-id=5424675936891070474>🎤</tg-emoji> В игре',
        
        'not_configured': 'Не настроен',
        'not_in_game': 'Не в игре',
        'no_achievements': 'Нет достижений',
        'not_specified': 'Не указано',
        'info_button': '<tg-emoji emoji-id=5474686055049360097>🔎</tg-emoji> Подробнее',
    }
    
    strings_ru = {
        'name': 'SteamViewer',
        
        '_api_key': "<tg-emoji emoji-id=6005570495603282482>🔑</tg-emoji> Steam API Key: https://steamcommunity.com/dev/apikey",
        '_account_id': "<tg-emoji emoji-id=5967548335542767952>💳</tg-emoji> Steam ID (17 цифр, начинается с 7656...)",
        '_stream_chat': "<tg-emoji emoji-id=5447510826304959724>💬</tg-emoji> Чат для трансляции (chat_id)",
        '_stream_msg': "<tg-emoji emoji-id=5447510826304959724>💬</tg-emoji> ID сообщения для трансляции",
        '_stream_text': "<tg-emoji emoji-id=6021741567163767583>💾</tg-emoji> Текст трансляции\nПлейсхолдеры:\n{name} - ник\n{game} - игра\n{playtime} - часов в игре\n{achievements} - достижения\n{status} - статус",
        '_profile_text': "<tg-emoji emoji-id=6021741567163767583>💾</tg-emoji> Текст профиля\nПлейсхолдеры:\n{name} - ник\n{realname} - реальное имя\n{status} - статус\n{created} - дата создания\n{current_game} - текущая игра\n{total_games} - всего игр\n{total_time} - общее время\n{top_game} - топ игра\n{top_game_time} - время в топ игре",
        
        'no_api_key': '<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>API_KEY не настроен!</b>',
        'no_account_id': '<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>ACCOUNT_ID не настроен!</b>',
        'no_api_key_or_id': '<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>API_KEY или ACCOUNT_ID не настроены!</b>',
        'noGame': '<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>Игра не запущена или профиль приватный</b>',
        'gameNotFound': '<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>Игра с ID {} не найдена</b>',
        'profile_private': '<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>Профиль приватный или не найден</b>',
        'no_stream_config': '<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>Не настроен чат или сообщение для трансляции!</b>',
        
        'stream_started': '<tg-emoji emoji-id=6021486789703769089>📡</tg-emoji> <b>Трансляция запущена!</b>\nБудет обновляться в настроенном сообщении',
        'stream_stopped': '<tg-emoji emoji-id=5908934603321642637>🎙</tg-emoji> <b>Трансляция остановлена</b>',
        'stream_not_running': '<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>Трансляция не запущена</b>',
        'stream_now': (
            '<tg-emoji emoji-id=5424675936891070474>🎤</tg-emoji> <b>Сейчас играет:</b>\n\n'
            '<tg-emoji emoji-id=6006038041448156880>📝</tg-emoji> <b>Название:</b> <code>{}</code>\n'
            '<tg-emoji emoji-id=5967548335542767952>💳</tg-emoji> <b>ID игры:</b> <code>{}</code>'
        ),
        
        'gameInfo': (
            '<tg-emoji emoji-id=5258508428212445001>🎮</tg-emoji> <b>{name}</b> — {price}\n\n'
            '<tg-emoji emoji-id=5956561916573782596>📄</tg-emoji> <b>Описание:</b>\n<i>{description}</i>\n\n'
            '{stats}'
            '<tg-emoji emoji-id=5967548335542767952>💳</tg-emoji> <b>AppID:</b> <code>{appid}</code>'
        ),
        'game_stats': '<tg-emoji emoji-id=5456502069756192095>🕓</tg-emoji> <b>Время в игре:</b> {playtime}\n<tg-emoji emoji-id=6021644067111180663>🏆</tg-emoji> <b>Достижения:</b> {achievements}\n\n',
        'game_not_owned': '<tg-emoji emoji-id=5271509874038051245>❌</tg-emoji> <i>Игра не в библиотеке</i>\n\n',
        
        'profile_default': (
            '<tg-emoji emoji-id=5255835635704408236>👤</tg-emoji> <b>Профиль Steam</b>\n\n'
            '<tg-emoji emoji-id=5879770735999717115>👤</tg-emoji> <b>Имя:</b> <code>{name}</code>\n'
            '<tg-emoji emoji-id=5936017305585586269>🪪</tg-emoji> <b>Реальное имя:</b> <code>{realname}</code>\n'
            '<tg-emoji emoji-id=5877485980901971030>📊</tg-emoji> <b>Статус:</b> {status}\n'
            '<tg-emoji emoji-id=6023880246128810031>📅</tg-emoji> <b>Аккаунт создан:</b> <code>{created}</code>\n'
            '<tg-emoji emoji-id=6021525053567409034>🗃</tg-emoji> <b>Всего игр:</b> {total_games}\n'
            '<tg-emoji emoji-id=5255971360965930740>🕔</tg-emoji> <b>Общее время:</b> {total_time}\n'
            '<tg-emoji emoji-id=6021644067111180663>🏆</tg-emoji> <b>Топ игра:</b> {top_game} — {top_game_time}\n\n'
            '<tg-emoji emoji-id=5258508428212445001>🎮</tg-emoji> <b>Сейчас в игре:</b>\n'
            '<i>{current_game}</i>'
        ),
        
        'gamesLibrary': (
            '<tg-emoji emoji-id=6021767126514144698>📦</tg-emoji> <b>Библиотека игр Steam</b>\n\n'
            '<blockquote><tg-emoji emoji-id=5877485980901971030>📊</tg-emoji> <b>Всего игр:</b> {}\n'
            '<tg-emoji emoji-id=5456502069756192095>🕓</tg-emoji> <b>Общее время:</b> {} ч</blockquote>\n\n'
            '<tg-emoji emoji-id=5444931419270839381>🏅</tg-emoji> <b>Топ-{} по времени:</b>\n'
            '<blockquote>{}</blockquote>\n'
            '<blockquote expandable>\n'
            '<i><tg-emoji emoji-id=5422871492281001864>📊</tg-emoji> Сортировка: По времени игры (по убыванию)</i>\n'
            '</blockquote>'
        ),
        
        'online': '<tg-emoji emoji-id=6019289243916968110>🛜</tg-emoji> В сети',
        'offline': '<tg-emoji emoji-id=6019508188464814176>🛜</tg-emoji> Не в сети',
        'busy': '<tg-emoji emoji-id=5399899739439251665>🎩</tg-emoji> Занят',
        'away': '<tg-emoji emoji-id=5339286072876614251>✋</tg-emoji> Отошёл',
        'in_game': '<tg-emoji emoji-id=5424675936891070474>🎤</tg-emoji> В игре',
        
        'not_configured': 'Не настроен',
        'not_in_game': 'Не в игре',
        'no_achievements': 'Нет достижений',
        'not_specified': 'Не указано',
        
        'info_button': '<tg-emoji emoji-id=5474686055049360097>🔎</tg-emoji> Подробнее',
    }
    
    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                'API_KEY',
                None,
                doc=lambda: self.strings('_api_key'),
                validator=loader.validators.Hidden(),
            ),
            loader.ConfigValue(
                'ACCOUNT_ID',
                None,
                doc=lambda: self.strings('_account_id')
            ),
            loader.ConfigValue(
                'stream_chat',
                None,
                doc=lambda: self.strings('_stream_chat')
            ),
            loader.ConfigValue(
                'stream_msg',
                None,
                doc=lambda: self.strings('_stream_msg')
            ),
            loader.ConfigValue(
                'stream_text',
                "{name} сейчас играет в {game}\nНаиграно - {playtime}\n{achievements}",
                doc=lambda: self.strings('_stream_text')
            ),
            loader.ConfigValue(
                'profile_text',
                None,
                doc=lambda: self.strings('_profile_text')
            )
        )
        
        self.stream_task = None
        self._cached_player = None
        self._cached_games = None
        self._cache_time = 0
        self._cache_ttl = 60
    
    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.me = await client.get_me()
        
        self._register_placeholders()
    
    def _register_placeholders(self):
        try:
            utils.register_placeholder("steam_name", self.get_steam_name, "Steam никнейм")
            utils.register_placeholder("steam_status", self.get_steam_status, "Статус Steam")
            utils.register_placeholder("steam_game", self.get_steam_game, "Текущая игра в Steam")
            utils.register_placeholder("steam_playtime", self.get_steam_playtime, "Наиграно в текущей игре")
            utils.register_placeholder("steam_total_time", self.get_steam_total_time, "Общее время в Steam")
            utils.register_placeholder("steam_games_count", self.get_steam_games_count, "Количество игр")
            utils.register_placeholder("steam_top_game", self.get_steam_top_game, "Самая наигранная игра")
            utils.register_placeholder("steam_top_game_time", self.get_steam_top_game_time, "Время в топ игре")
            utils.register_placeholder("steam_realname", self.get_steam_realname, "Реальное имя")
            utils.register_placeholder("steam_created", self.get_steam_created, "Дата создания аккаунта")
            
            logger.info("Steam placeholders registered")
        except Exception as e:
            logger.error(f"Failed to register placeholders: {e}")
    
    
    async def _get_cached_player(self, force=False):
        now = datetime.now().timestamp()
        
        if not force and self._cached_player and (now - self._cache_time) < self._cache_ttl:
            return self._cached_player
        
        api_key = self.config['API_KEY']
        account_id = self.config['ACCOUNT_ID']
        
        if not api_key or not account_id:
            return None
        
        url = f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={api_key}&steamids={account_id}'
        
        try:
            response = await asyncio.to_thread(requests.get, url)
            data = response.json()
            
            if 'response' in data and 'players' in data['response']:
                players = data['response']['players']
                if players:
                    self._cached_player = players[0]
                    self._cache_time = now
                    return self._cached_player
        except Exception as e:
            logger.error(f"Failed to get player: {e}")
        
        return None
    
    async def _get_cached_games(self, force=False):
        now = datetime.now().timestamp()
        
        if not force and self._cached_games and (now - self._cache_time) < self._cache_ttl:
            return self._cached_games
        
        api_key = self.config['API_KEY']
        account_id = self.config['ACCOUNT_ID']
        
        if not api_key or not account_id:
            return None, []
        
        url = f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={api_key}&steamid={account_id}&format=json&include_appinfo=1&include_played_free_games=1'
        
        try:
            response = await asyncio.to_thread(requests.get, url)
            data = response.json()
            
            if 'response' in data:
                games = data['response'].get('games', [])
                game_count = data['response'].get('game_count', len(games))
                self._cached_games = (game_count, games)
                self._cache_time = now
                return self._cached_games
        except Exception as e:
            logger.error(f"Failed to get games: {e}")
        
        return None, []
    
    async def _get_top_game(self):
        _, games = await self._get_cached_games()
        if games:
            sorted_games = sorted(games, key=lambda x: x.get('playtime_forever', 0), reverse=True)
            if sorted_games:
                top = sorted_games[0]
                name = top.get('name', 'Unknown')
                minutes = top.get('playtime_forever', 0)
                return name, minutes
        return None, 0
    
    
    async def get_steam_name(self):
        player = await self._get_cached_player()
        return player.get('personaname', 'Unknown') if player else self.strings('not_configured')
    
    async def get_steam_status(self):
        player = await self._get_cached_player()
        if not player:
            return self.strings('not_configured')
        
        state = player.get('personastate', 0)
        game = player.get('gameextrainfo')
        
        if game:
            return f"{self.strings('in_game')} ({game})"
        elif state == 0:
            return self.strings('offline')
        elif state == 1:
            return self.strings('online')
        elif state == 2:
            return self.strings('busy')
        elif state == 3:
            return self.strings('away')
        return "⚪ Unknown"
    
    async def get_steam_game(self):
        player = await self._get_cached_player()
        if player:
            game = player.get('gameextrainfo')
            return game if game else self.strings('not_in_game')
        return self.strings('not_configured')
    
    async def get_steam_playtime(self):
        player = await self._get_cached_player()
        if not player:
            return self.strings('not_configured')
        
        game_id = player.get('gameid')
        if not game_id:
            return self.strings('not_in_game')
        
        _, games = await self._get_cached_games()
        for g in games:
            if g.get('appid') == game_id:
                return self._format_playtime(g.get('playtime_forever', 0))
        
        return '0 мин'
    
    async def get_steam_total_time(self):
        _, games = await self._get_cached_games()
        if games:
            total = sum(g.get('playtime_forever', 0) for g in games)
            return f"{round(total / 60, 1)} ч"
        return self.strings('not_configured')
    
    async def get_steam_games_count(self):
        count, _ = await self._get_cached_games()
        return str(count) if count is not None else self.strings('not_configured')
    
    async def get_steam_top_game(self):
        name, _ = await self._get_top_game()
        return name if name else self.strings('not_configured')
    
    async def get_steam_top_game_time(self):
        _, minutes = await self._get_top_game()
        return self._format_playtime(minutes) if minutes > 0 else '0 мин'
    
    async def get_steam_realname(self):
        player = await self._get_cached_player()
        if player:
            return player.get('realname') or self.strings('not_specified')
        return self.strings('not_configured')
    
    async def get_steam_created(self):
        player = await self._get_cached_player()
        if player and 'timecreated' in player:
            return datetime.fromtimestamp(player['timecreated']).strftime('%d.%m.%Y')
        return 'Неизвестно'
    
    
    def _format_playtime(self, minutes):
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours} ч {mins} мин"
        return f"{mins} мин"
    
    def _format_playtime_short(self, minutes):
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours}ч {mins}м"
        return f"{mins}м"
    
    async def _get_achievements(self, appid):
        api_key = self.config['API_KEY']
        account_id = self.config['ACCOUNT_ID']
        
        url = f"http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/?appid={appid}&key={api_key}&steamid={account_id}"
        
        try:
            response = await asyncio.to_thread(requests.get, url)
            data = response.json()
            
            if 'playerstats' in data:
                achievements = data['playerstats'].get('achievements', [])
                if achievements:
                    achieved = sum(1 for a in achievements if a.get('achieved', 0) == 1)
                    return achieved, len(achievements)
        except:
            pass
        
        return 0, 0
    
    async def _get_game_info(self, appid):
        url = f"http://store.steampowered.com/api/appdetails?appids={appid}&cc=ru&l=russian"
        
        try:
            response = await asyncio.to_thread(requests.get, url)
            data = response.json()
            
            if str(appid) in data and data[str(appid)]['success']:
                return data[str(appid)]['data']
        except:
            pass
        
        return None
    
    def _check_config(self):
        api_key = self.config['API_KEY']
        account_id = self.config['ACCOUNT_ID']
        
        if not api_key and not account_id:
            return False, self.strings('no_api_key_or_id')
        elif not api_key:
            return False, self.strings('no_api_key')
        elif not account_id:
            return False, self.strings('no_account_id')
        
        return True, None
    
    def _check_stream_config(self):
        return bool(self.config['stream_chat'] and self.config['stream_msg'])
    
    def _format_status(self, player):
        state = player.get('personastate', 0)
        game = player.get('gameextrainfo')
        
        if game:
            return f"{self.strings('in_game')} ({game})"
        elif state == 0:
            return self.strings('offline')
        elif state == 1:
            return self.strings('online')
        elif state == 2:
            return self.strings('busy')
        elif state == 3:
            return self.strings('away')
        return "⚪ Unknown"
    
    
    async def _update_stream_message(self):
        player = await self._get_cached_player(force=True)
        if not player:
            return False
        
        game_name = player.get('gameextrainfo')
        game_id = player.get('gameid')
        
        if not game_name:
            text = "❌ Не в игре"
        else:
            _, games = await self._get_cached_games(force=True)
            playtime = 0
            if games:
                for g in games:
                    if g.get('appid') == game_id:
                        playtime = g.get('playtime_forever', 0)
                        break
            
            achieved, total = await self._get_achievements(game_id)
            
            name = player.get('personaname', 'Unknown')
            playtime_str = self._format_playtime(playtime)
            ach_str = f"{achieved}/{total} достижений" if total > 0 else "Нет достижений"
            status = self._format_status(player)
            
            text = self.config['stream_text'].format(
                name=name,
                game=game_name,
                playtime=playtime_str,
                achievements=ach_str,
                status=status
            )
        
        try:
            chat_id = int(self.config['stream_chat'])
            msg_id = int(self.config['stream_msg'])
            await self.client.edit_message(chat_id, msg_id, text)
            return True
        except Exception as e:
            logger.error(f"Failed to update stream: {e}")
            return False
    
    async def _stream_loop(self):
        try:
            while True:
                await self._update_stream_message()
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            try:
                chat_id = int(self.config['stream_chat'])
                msg_id = int(self.config['stream_msg'])
                await self.client.edit_message(chat_id, msg_id, self.strings('stream_stopped'))
            except:
                pass
    

    
    @loader.command(ru_doc='- запустить трансляцию')
    async def startstream(self, message):
        config_ok, error_msg = self._check_config()
        if not config_ok:
            await utils.answer(message, error_msg)
            return
        
        if not self._check_stream_config():
            await utils.answer(message, self.strings('no_stream_config'))
            return
        
        if self.stream_task:
            self.stream_task.cancel()
        
        self.stream_task = asyncio.create_task(self._stream_loop())
        await utils.answer(message, self.strings('stream_started'))
    
    @loader.command(ru_doc='- остановить трансляцию')
    async def stopstream(self, message):
        if self.stream_task:
            self.stream_task.cancel()
            self.stream_task = None
            await utils.answer(message, self.strings('stream_stopped'))
        else:
            await utils.answer(message, self.strings('stream_not_running'))
    
    @loader.command(ru_doc='- обновить трансляцию вручную')
    async def updatestream(self, message):
        if not self._check_stream_config():
            await utils.answer(message, self.strings('no_stream_config'))
            return
        
        success = await self._update_stream_message()
        await utils.answer(message, "✅ <b>Сообщение обновлено!</b>" if success else "<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>Не удалось обновить</b>")
    
    @loader.command(ru_doc='- текущая игра')
    async def steamnow(self, message):
        config_ok, error_msg = self._check_config()
        if not config_ok:
            await utils.answer(message, error_msg)
            return
        
        player = await self._get_cached_player(force=True)
        
        if not player:
            await utils.answer(message, self.strings('profile_private'))
            return
        
        game_name = player.get('gameextrainfo')
        game_id = player.get('gameid')
        
        if not game_name:
            await utils.answer(message, self.strings('noGame'))
            return
        
        text = self.strings('stream_now').format(game_name, game_id)
        
        game_data = await self._get_game_info(game_id)
        if game_data and game_data.get('header_image'):
            await self.inline.form(
                message=message,
                photo=game_data['header_image'],
                text=text,
                reply_markup=[
                    {'text': self.strings('info_button'), 'callback': self.game_info_callback, 'args': (game_id,)}
                ]
            )
        else:
            await utils.answer(message, text)
    
    @loader.command(ru_doc='<id> - информация об игре')
    async def game(self, message):
        args = utils.get_args_raw(message)
        
        if not args:
            await utils.answer(message, "<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>Укажите ID игры</b>")
            return
        
        try:
            appid = int(args)
        except:
            await utils.answer(message, "<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>Неверный ID игры</b>")
            return
        
        await self._send_game_info(message, appid)
    
    async def _send_game_info(self, message, appid, edit=False):
        game_data = await self._get_game_info(appid)
        
        if not game_data:
            text = self.strings('gameNotFound').format(appid)
            if edit:
                await message.edit(text=text)
            else:
                await utils.answer(message, text)
            return
        
        name = game_data.get('name', 'Unknown')
        description = game_data.get('short_description', 'Нет описания')
        
        price = "Бесплатно"
        if 'price_overview' in game_data:
            price = game_data['price_overview'].get('final_formatted', 'Бесплатно')
        
        _, games = await self._get_cached_games()
        playtime = 0
        if games:
            for g in games:
                if g.get('appid') == appid:
                    playtime = g.get('playtime_forever', 0)
                    break
        
        achieved, total = await self._get_achievements(appid)
        
        if playtime > 0 or total > 0:
            playtime_str = self._format_playtime(playtime) if playtime > 0 else "0 мин"
            ach_str = f"{achieved}/{total}" if total > 0 else self.strings('no_achievements')
            stats = self.strings('game_stats').format(playtime=playtime_str, achievements=ach_str)
        else:
            stats = self.strings('game_not_owned')
        
        text = self.strings('gameInfo').format(
            name=name,
            price=price,
            description=description,
            stats=stats,
            appid=appid
        )
        
        photo = game_data.get('header_image')
        
        if edit:
            if photo:
                await message.edit(text=text, file=photo)
            else:
                await message.edit(text=text)
        else:
            if photo:
                await utils.answer_file(message, photo, caption=text)
            else:
                await utils.answer(message, text)
    
    async def game_info_callback(self, call, gameid: int):
        await self._send_game_info(call, gameid, edit=True)
    
    @loader.command(ru_doc='- профиль Steam')
    async def sme(self, message):
        config_ok, error_msg = self._check_config()
        if not config_ok:
            await utils.answer(message, error_msg)
            return
        
        player = await self._get_cached_player(force=True)
        
        if not player:
            await utils.answer(message, self.strings('profile_private'))
            return
        
        _, games = await self._get_cached_games()
        
        name = player.get('personaname', 'Unknown')
        realname = player.get('realname') or self.strings('not_specified')
        status = self._format_status(player)
        
        created = "Unknown"
        if 'timecreated' in player:
            created = datetime.fromtimestamp(player['timecreated']).strftime('%d.%m.%Y')
        
        current_game = player.get('gameextrainfo') or self.strings('not_in_game')
        
        total_games = len(games) if games else 0
        total_minutes = sum(g.get('playtime_forever', 0) for g in games) if games else 0
        total_time = f"{round(total_minutes / 60, 1)} ч"
        
        top_name, top_minutes = await self._get_top_game()
        top_game = top_name or self.strings('not_configured')
        top_game_time = self._format_playtime(top_minutes) if top_minutes > 0 else '0 мин'
        
        profile_text = self.config['profile_text']
        if profile_text:
            text = profile_text.format(
                name=name,
                realname=realname,
                status=status,
                created=created,
                current_game=current_game,
                total_games=total_games,
                total_time=total_time,
                top_game=top_game,
                top_game_time=top_game_time
            )
        else:
            text = self.strings('profile_default').format(
                name=name,
                realname=realname,
                status=status,
                created=created,
                current_game=current_game,
                total_games=total_games,
                total_time=total_time,
                top_game=top_game,
                top_game_time=top_game_time
            )
        
        photo = player.get('avatarfull')
        
        if photo:
            await utils.answer_file(message, photo, caption=text)
        else:
            await utils.answer(message, text)
    
    @loader.command(ru_doc='[кол-во] - библиотека игр')
    async def games(self, message):
        config_ok, error_msg = self._check_config()
        if not config_ok:
            await utils.answer(message, error_msg)
            return
        
        args = utils.get_args_raw(message)
        limit = 30
        
        if args:
            try:
                limit = min(int(args), 50)
            except:
                pass
        
        game_count, games = await self._get_cached_games(force=True)
        
        if games is None:
            await utils.answer(message, self.strings('profile_private'))
            return
        
        if not games:
            await utils.answer(message, "<tg-emoji emoji-id=5303134392548355140>❌</tg-emoji> <b>Библиотека пуста или приватна</b>")
            return
        
        sorted_games = sorted(games, key=lambda x: x.get('playtime_forever', 0), reverse=True)
        
        total_minutes = sum(g.get('playtime_forever', 0) for g in games)
        total_hours = round(total_minutes / 60, 1)
        
        games_list = []
        for i, game in enumerate(sorted_games[:limit], 1):
            name = game.get('name', 'Unknown')
            minutes = game.get('playtime_forever', 0)
            playtime = self._format_playtime_short(minutes)
            games_list.append(f"{i}. <b>{name}</b> — {playtime}")
        
        if game_count > limit:
            games_list.append(f"\n...и еще {game_count - limit} игр")
        
        games_text = '\n'.join(games_list)
        
        text = self.strings('gamesLibrary').format(game_count, total_hours, limit, games_text)
        await utils.answer(message, text)