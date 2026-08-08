#---------------------------------------------------------------------
#   __        __ __  __           _     
#   \ \      / /|  \/  | ___   __| |___ 
#    \ \ /\ / (_) |\/| |/ _ \ / _` / __|
#     \ V  V / _| |  | | (_) | (_| \__ \
#      \_/\_/ (_)_|  |_|\___/ \__,_|___/
#---------------------------------------------------------------------
# 🌐 Repository of Modules:https://github.com/sawwnapix/Heroku
# 👤 Developer: @zerixgod
# 🪧 Channel with modules: @wizardmodules / old channel @angellmodules
#---------------------------------------------------------------------
# 🔒 Licensed under GNU GPLv3
# 🧾 https://www.gnu.org/licenses/gpl-3.0.html#license-text
#--------------------------------------------------------------------- 
# Developer: @zerixgod
# Module Name: CoinFlip
# Description: Head or Tails/Орёл или Решка 
# meta developer: @wizardmodules
#---------------------------------------------------------------------  
__version__ = (1, 0, 1)

from hikka import loader, utils
import random

@loader.tds
class CoinFlipMod(loader.Module):
    """Орел или Решка!"""
    strings = {"name": "CoinFlip"}

    async def flipcmd(self, message):
        """Подбросить монетку"""
        sides = ["Орёл 🦅", "Решка 🪙"]
        result = random.choice(sides)
        await utils.answer(message, f"Выпало: {result}!")
