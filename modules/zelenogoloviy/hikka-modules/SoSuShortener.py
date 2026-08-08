# MIT License
# Copyright (c) 2025 zelenogoloviy
# ---------------------------------------------------------------------------------
# Name: SoSuShortener
# Description: Модуль для сокращения ссылок в сервисе So.Su
# Author: @zelenogoloviy_m
# ---------------------------------------------------------------------------------
# meta developer: @zelenogoloviy_m
__version__ = (0, 1, 0)
from .. import loader, utils
import string
import random
import requests

class Short:

    def __init__(self):
        self.base_url = "https://so.su/shorten.php"
        
    def generate_random_keyword(self, length=10):
        chars = string.ascii_letters + string.digits * 5
        return ''.join(random.choice(chars) for _ in range(length))
    def shorten_url(self, long_url):
        keyword = self.generate_random_keyword()
        data = {
            "url": long_url,
            "keyword": keyword
        }
        try:
            response = requests.post(self.base_url, data=data)
            if response.status_code == 200:
                return response.text.strip()
            return None
        except Exception as e:
            print(f"Произошла ошибка при запросе: {e}")
            return None
            
@loader.tds
class Sosumodule(loader.Module):
    """Модуль для сокращения ссылок в сервисе So.Su"""
    
    strings_en = {
        "name": "SoSuShortener",
        "no_args": "No args",
        "shorten": "<emoji document_id=5769289093221454192>🔗</emoji> <b>Shorten link:</b>",
        "fail": "Failed to shorten URL",
    }
    
    strings = {
        "name": "SoSuShortener",
        "no_args": "Нет Аргументов",
        "shorten": "<emoji document_id=5769289093221454192>🔗</emoji> <b>Ваша ссылка:</b>",
        "fail": "Не удалось сократить ссылку",
    }
    @loader.command(
    en_doc="Short the url \n .short <https://your.link>."
    )
    async def shortcmd(self, message):
        """Сокращает ссылку \n .short <https://твоя.ссылка>."""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(
                message,
                self.strings["no_args"]
            )
            return
        shortener = Short()
        shortened_url = shortener.shorten_url(long_url=args)
        if shortened_url:
            await utils.answer(message, f"{self.strings['shorten']} {shortened_url}")
        else:
            await utils.answer(message, f"{self.strings['fail']}")
