__version__ = (0, 3, 4)


#░█░█░█▀▀░█▀█░█▀▀░▀█▀░█▀▄░█▀▀
#░▄▀▄░█▀▀░█░█░▀▀█░░█░░█░█░█▀▀
#░▀░▀░▀▀▀░▀░▀░▀▀▀░▀▀▀░▀▀░░▀▀▀

# 🔒 Licensed under All Rights Reserved.
# meta developer: @XenSideMOD

from .. import loader, utils

import asyncio
from telethon.tl.types import Message


@loader.tds
class XenAnims(loader.Module):

    strings = {"name": "😼Анимки @XenSide"}

    async def podkatcmd(self, message: Message):
        "😏Анимация подката"
        for _ in range(1):
            for anim in ["😏Привет😏", "🧡Ты красивая🧡", "♥️Я тебя люблю♥️", "💓💓💓", "☺️", "🧡Пошли домой моя конфетка♥️♥️♥️"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(1.0)

    async def rasstatcmd(self, message: Message):
        "🤬Анимация расставания"
        for _ in range(1):
            for anim in ["🤬Ну привет блядина🤬🤬", "🤬Ты тупая шлюха я расстаюсь🤬", "⚰️Я расстаюсь тварь ты ебаная!⚰️", "🗿Уезжай нахуй блять безмамная🤬", "👿👿👿👿👿"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(1.0)
                
    async def oskcmd(self, message: Message):
        "👿Оскарбления(жоские)"
        for _ in range(1):
            for anim in ["🤬Ты ебаная блядина🤬🤬", "🤬Ты хуесос(ка) блять безмамная!🤬", "👿Живи на улице тварь безмамная👿", "🤬Иди нахуй пидорасина блять СУКА!🤬", "👿Ты гей👿", "🤬Пускай тебя бомбы взровут нахуй блядина🤬"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(3.0)

    async def ipxcmd(self, message: Message):
        "😎Анимация вычисления по айпи"
        for _ in range(1):
            for anim in ["😼 Вычисляю по айпи...", "8%◆◇◇◇◇◇◇◇◇◇", "15%◆◆◇◇◇◇◇◇◇◇", "23%◆◆◆◇◇◇◇◇◇◇", "34%◆◆◆◆◇◇◇◇◇◇", "47%◆◆◆◆◆◇◇◇◇◇", "58%◆◆◆◆◆◆◇◇◇◇", "64%◆◆◆◆◆◆◆◇◇◇", "75%◆◆◆◆◆◆◆◆◇◇", "86%◆◆◆◆◆◆◆◆◆◇", "100%◆◆◆◆◆◆◆◆◆◆", "😨Теперь я знаю твой адрес мухахаах👿", "🙀Я могу прийти к тебе ууу🙀", "🗿Ну все тебе крышка!🗿"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(1.0)
                
    async def mumcmd(self, message: Message):
        "😎Анимация вычисления мамашки"
        for _ in range(1):
            for anim in ["🔍 Ищу твою мамашку на авито...", "✅ Успешно!", "🛒 Покупаю адрес...", "✅ Успешно!", "🔍 Ищу твою мамаху в канаве", "✅ Успешно найдено!"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(3.0)
                
    async def oxmcmd(self, message: Message):
        "🤬Анимация маты (Oxxxymiron)"
        for _ in range(1):
            for anim in ["Говно", "залупа", "пенис", "хер", "давалка", "хуй", "блядина", "головка", "шлюха", "жопа", "член", "еблан", "петух", "мудила", "рукоблуд", "ссанина", "очко", "блядун", "вагина", "сука", "ебланище", "влагалище", "пердун", "дрочила"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(1.0)
                
    async def huicmd(self, message: Message):
        "🍆Анимация делает хуй из сердечек"
        for _ in range(1):
            for anim in ["       💗💗💗\n", "       💗💗💗\n       💗⬜💗\n", "       💗💗💗\n       💗⬜💗\n       💗💗💗\n", "       💗💗💗\n       💗⬜💗\n       💗💗💗\n       💗💗💗\n", "       💗💗💗\n       💗⬜💗\n       💗💗💗\n       💗💗💗\n       💗💗💗\n", "       💗💗💗\n       💗⬜💗\n       💗💗💗\n       💗💗💗\n       💗💗💗\n💗💗💗💗💗💗💗\n", "       💗💗💗\n       💗⬜💗\n       💗💗💗\n       💗💗💗\n       💗💗💗\n💗💗💗💗💗💗💗\n💗    💗💗💗    💗\n", "       💗💗💗\n       💗⬜💗\n       💗💗💗\n       💗💗💗\n       💗💗💗\n💗💗💗💗💗💗💗\n💗    💗💗💗    💗\n💗💗💗💗💗💗💗\n"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(1.0)
                
    async def vzlomcmd(self, message: Message):
        "🦕Анимация взлома пентагона"
        for _ in range(1):
            for anim in ["👮‍♂️ Взлом пентагона...", "8%◆◇◇◇◇◇◇◇◇◇", "15%◆◆◇◇◇◇◇◇◇◇", "23%◆◆◆◇◇◇◇◇◇◇", "34%◆◆◆◆◇◇◇◇◇◇", "47%◆◆◆◆◆◇◇◇◇◇", "58%◆◆◆◆◆◆◇◇◇◇", "64%◆◆◆◆◆◆◆◇◇◇", "75%◆◆◆◆◆◆◆◆◇◇", "86%◆◆◆◆◆◆◆◆◆◇", "100%◆◆◆◆◆◆◆◆◆◆", "✅ Успешно!", "🛸Поиск секретных данных об НЛО!", "8%◆◇◇◇◇◇◇◇◇◇", "15%◆◆◇◇◇◇◇◇◇◇", "23%◆◆◆◇◇◇◇◇◇◇", "34%◆◆◆◆◇◇◇◇◇◇", "47%◆◆◆◆◆◇◇◇◇◇", "58%◆◆◆◆◆◆◇◇◇◇", "64%◆◆◆◆◆◆◆◇◇◇", "75%◆◆◆◆◆◆◆◆◇◇", "86%◆◆◆◆◆◆◆◆◆◇", "100%◆◆◆◆◆◆◆◆◆◆", "✅ Успешно!", "🦕 Также мне удалось найти данные об динозаврах они существуют!"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(1.0)
                
    async def rickcmd(self, message: Message):
        "☺️Анимация рикролла"
        for _ in range(100):
            for anim in ["⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣻⣿⣿⣿\n⣿⣿⣿⠀⠀⠀⠀⢀⣴⣦⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿\n⣿⣿⣿⠀⠀⠀⠀⠘⣿⡯⠀⠀⠀⠀⠀⠀⠀⣻⣿⣿\n⣿⣿⣿⠀⠀⢰⣶⣿⣟⣴⣶⡀⢀⠀⠀⠀⠀⣼⣿⣿\n⣿⣿⣿⠀⠐⣿⣿⣿⣿⣿⣿⡇⠘⠀⠀⠀⠀⢹⣿⣿\n⣿⣿⣿⠀⢀⠛⣿⣿⣿⣿⡿⣷⣶⠦⠀⠀⠀⣿⣿⣿\n⣿⣿⣟⣛⣛⣀⣿⣿⣿⣿⣿⣀⣀⣀⣀⣀⣀⣿⣿⣿\n⡿⣿⣿⡿⢿⣯⣯⣯⣯⣽⣯⣿⣿⣯⣿⣯⣽⣿⣿⣿\n\nNever Gonna Give You UP\n", "⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣻⣿⣿⣿\n⣿⣿⣿⠀⠀⠀⠀⠀⠀⣀⡀⠀⠀⠀⠀⠀⠀⣿⣿⣿\n⣿⣿⣿⠀⠀⠀⠀⠀⠐⣿⡗⠀⠀⠀⠀⠀⠀⣻⣿⣿\n⣿⣿⣿⠀⠀⠀⠀⣀⣤⢿⢷⣤⣀⠀⠀⠀⠀⣼⣿⣿\n⣿⣿⣿⠀⠀⠐⠀⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⢹⣿⣿\n⣿⣿⣿⠀⠀⠀⢠⣿⣿⣿⣿⣿⡿⠂⠀⠀⠀⣿⣿⣿\n⣿⣿⣿⣒⣈⣛⣊⣿⣿⣿⣿⣿⣀⣀⣀⣀⣀⣿⣿⣿\n⡿⣿⣿⡿⢿⣯⣯⣯⣯⣽⣯⣿⣿⣯⣿⣯⣽⣿⣿⣿\n\nNever Gonna Give You UP\n"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(0.6)
                
    async def unocmd(self, message: Message):
        "🧿Анимация UNO REV. CARD"
        for _ in range(1):
            for anim in ["⣿⣿⣿⡿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⡟⡴⠛⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⡏⠴⠞⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n", "⣿⣿⣿⡿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⡟⡴⠛⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⡏⠴⠞⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⣿⣿⡏⠩⣭⣭⢹⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⣿⠟⣵⣾⠟⠟⣼⣿⣿⣿⣿⡇\n", "⣿⣿⣿⡿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⡟⡴⠛⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⡏⠴⠞⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⣿⣿⡏⠩⣭⣭⢹⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⣿⠟⣵⣾⠟⠟⣼⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⠿⠀⢛⣵⡆⣶⣿⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⡏⢸⣶⡿⢋⣴⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣇⣈⣉⣉⣼⣿⣿⣿⣿⣿⣿⣿⡇\n", "⣿⣿⣿⡿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⡟⡴⠛⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⡏⠴⠞⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⣿⣿⡏⠩⣭⣭⢹⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⣿⠟⣵⣾⠟⠟⣼⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⠿⠀⢛⣵⡆⣶⣿⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⡏⢸⣶⡿⢋⣴⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣇⣈⣉⣉⣼⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢣⠞⢺⣿⡇\n⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢡⡴⣣⣿⣿⡇\n", "⣿⣿⣿⡿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⡟⡴⠛⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⡏⠴⠞⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⣿⣿⡏⠩⣭⣭⢹⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⣿⠟⣵⣾⠟⠟⣼⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⠿⠀⢛⣵⡆⣶⣿⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⡏⢸⣶⡿⢋⣴⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣇⣈⣉⣉⣼⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇\n⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢣⠞⢺⣿⡇\n⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢡⡴⣣⣿⣿⡇\n⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣶⣿⣿⣿⡇\n"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(1.0)
                
    async def kekscmd(self, message: Message):
        "🔞18+🍆👄"
        for _ in range(80):
            for anim in ["ㅤㅤㅤㅤ＼○／\n＼○  𓂸 /\n   /      ノ)\nノ)𐨸 𐨸 𐨸 𐨸 𐨸 𐨸 𐨸 𐨸 𐨸 \n", "ㅤㅤㅤ＼○／\n＼○𓂸 /\n   /    ノ)\nノ)𐨸 𐨸 𐨸 𐨸 𐨸 𐨸 𐨸 𐨸 𐨸 \n"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(0.7)
                
    async def grancmd(self, message: Message):
        "💣Анимация взрыва гранаты"
        for _ in range(1):
            for anim in ["─▄▀▀███═◯\n▐▌▄▀▀█▀▀▄\n█▐▌─────▐▌\n█▐█▄───▄█▌\n▀─▀██▄██▀\n\nЯ ВЗРЫВАЮ ТЕБЯ НАХУЙ!\n", "──███\n─▄▀▀█▀▀▄\n▐▌─────▐▌\n▐█▄───▄█▌\n─▀██▄██▀\n", "💥💥💥💥💥💥💥💥💥\n💥💥💥💥💥💥💥💥💥\n💥💥💥💥💥💥💥💥💥\n💥💥💥💥💥💥💥💥💥\n💥💥💥💥💥💥💥💥💥\n💥💥💥💥💥💥💥💥💥\n"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(3.0)
                
    async def kotcmd(self, message: Message):
        "🧙Анимация кота с палкой"
        for _ in range(80):
            for anim in ["∧＿∧\n( ･ω･｡)つ━☆・*。・゜ .¨¸.·'* ☆   ＼○／\n⊂  ノ ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ /\nしーＪㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤノ)\n", "∧＿∧\n( ･ω･｡)つ━☆*´¨・*゜  *゜ .°  ☆ ＼○／\n⊂  ノ ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ /\nしーＪㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤノ)\n"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(0.7)
                
    async def drochcmd(self, message: Message):
        "😉Анимация дрочения"
        for _ in range(80):
            for anim in ["ㅤ ╱○／\n  𓂸/\nㅤノ)\n", "╱○／\n𓂸/\nㅤノ)\n"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(0.7)
                
    async def muhacmd(self, message: Message):
        "😉Анимация а муха тоже вертолет"
        for _ in range(1):
            for anim in ["А муха тоже вертолет🪰🚁", "Но без коробки передач🕹️", "А по стене ползет пельмень🥟", "Он волосатый как трамвай🚊", "И деревянный как кирпич🧱", "А это песня про любовь🧡", "И ты ее не забывай🏮"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(3.5)
                
    async def ilovecmd(self, message: Message):
        "🖤Анимация любви"
        for _ in range(1):
            for anim in ["🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍❤️❤️❤️🤍🤍🤍❤️❤️❤️🤍\n🤍❤️❤️❤️❤️🤍❤️❤️❤️❤️🤍\n🤍🤍❤️❤️❤️❤️❤️❤️❤️🤍🤍\n🤍🤍🤍❤️❤️❤️❤️❤️🤍🤍🤍\n🤍🤍🤍🤍❤️❤️❤️🤍🤍🤍🤍\n🤍🤍🤍🤍❤️❤️🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍\n", "🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍💙💙💙🤍🤍🤍💙💙💙🤍\n🤍💙💙💙💙🤍💙💙💙💙🤍\n🤍🤍💙💙💙💙💙💙💙🤍🤍\n🤍🤍🤍💙💙💙💙💙🤍🤍🤍\n🤍🤍🤍🤍💙💙💙🤍🤍🤍🤍\n🤍🤍🤍🤍💙💙🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍\n", "🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍💚💚💚🤍🤍🤍💚💚💚🤍\n🤍💚💚💚💚🤍💚💚💚💚🤍\n🤍🤍💚💚💚💚💚💚💚🤍🤍\n🤍🤍🤍💚💚💚💚💚🤍🤍🤍\n🤍🤍🤍🤍💚💚💚🤍🤍🤍🤍\n🤍🤍🤍🤍💚💚🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍\n", "🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍💜💜💜🤍🤍🤍💜💜💜🤍\n🤍💜💜💜💜🤍💜💜💜💜🤍\n🤍🤍💜💜💜💜💜💜💜🤍🤍\n🤍🤍🤍💜💜💜💜💜🤍🤍🤍\n🤍🤍🤍🤍💜💜💜🤍🤍🤍🤍\n🤍🤍🤍🤍💜💜🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍\n", "🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍💛💛💛🤍🤍🤍💛💛💛🤍\n🤍💛💛💛💛🤍💛💛💛💛🤍\n🤍🤍💛💛💛💛💛💛💛🤍🤍\n🤍🤍🤍💛💛💛💛💛🤍🤍🤍\n🤍🤍🤍🤍💛💛💛🤍🤍🤍🤍\n🤍🤍🤍🤍💛💛🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍\n", "🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🧡🧡🧡🤍🤍🤍🧡🧡🧡🤍\n🤍🧡🧡🧡🧡🤍🧡🧡🧡🧡🤍\n🤍🤍🧡🧡🧡🧡🧡🧡🧡🤍🤍\n🤍🤍🤍🧡🧡🧡🧡🧡🤍🤍🤍\n🤍🤍🤍🤍🧡🧡🧡🤍🤍🤍🤍\n🤍🤍🤍🤍🧡🧡🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍\n", "🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍\n🤍🖤🖤🖤🤍🤍🤍🖤🖤🖤🤍\n🤍🖤🖤🖤🖤🤍🖤🖤🖤🖤🤍\n🤍🤍🖤🖤🖤🖤🖤🖤🖤🤍🤍\n🤍🤍🤍🖤🖤🖤🖤🖤🤍🤍🤍\n🤍🤍🤍🤍🖤🖤🖤🤍🤍🤍🤍\n🤍🤍🤍🤍🖤🖤🤍🤍🤍🤍🤍\n🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍🤍\n", "🖤🧡💛💜💚💙❤️\nЯ Тебя Люблю❤️\n❤️💙💚💜💛🧡🖤\n"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(1.0)
                
    async def vzlomacmd(self, message: Message):
        "😈Анимация взлома админки[PREMIUM]"
        for _ in range(1):
            for anim in ["<emoji document_id=5192765204898783881>💜</emoji><emoji document_id=5195311729663286630>💜</emoji><emoji document_id=5195045669324201904>💜</emoji>: Начинаю получение прав администратора...<emoji document_id=5789844634901417073>💜</emoji>", "8%◆◇◇◇◇◇◇◇◇◇", "15%◆◆◇◇◇◇◇◇◇◇", "23%◆◆◆◇◇◇◇◇◇◇", "75%◆◆◆◆◆◆◆◆◇◇", "86%◆◆◆◆◆◆◆◆◆◇", "100%◆◆◆◆◆◆◆◆◆◆", "<emoji document_id=5192765204898783881>💜</emoji><emoji document_id=5195311729663286630>💜</emoji><emoji document_id=5195045669324201904>💜</emoji>: Лог успешно получен, начинаю редактирование manifest.json<emoji document_id=5789764439272066504>💜</emoji>", "38%◆◇◇◇◇◇◇◇◇◇", "64%◆◆◆◆◆◆◆◇◇◇", "75%◆◆◆◆◆◆◆◆◇◇", "86%◆◆◆◆◆◆◆◆◆◇", "100%◆◆◆◆◆◆◆◆◆◆", "<emoji document_id=5192765204898783881>💜</emoji><emoji document_id=5195311729663286630>💜</emoji><emoji document_id=5195045669324201904>💜</emoji>: Редактирую admins.js<emoji document_id=5789853954980449405>💜</emoji>", "38%◆◇◇◇◇◇◇◇◇◇", "64%◆◆◆◆◆◆◆◇◇◇", "75%◆◆◆◆◆◆◆◆◇◇", "86%◆◆◆◆◆◆◆◆◆◇", "100%◆◆◆◆◆◆◆◆◆◆", "✅ Успешно!", "<emoji document_id=5192765204898783881>💜</emoji><emoji document_id=5195311729663286630>💜</emoji><emoji document_id=5195045669324201904>💜</emoji>: Загружаю файлы в датабазу...<emoji document_id=5789844634901417073>💜</emoji>", "<emoji document_id=5192765204898783881>💜</emoji><emoji document_id=5195311729663286630>💜</emoji><emoji document_id=5195045669324201904>💜</emoji>: Чтобы получить права, перейдите на  https://clck.ru/9TFat После чего введите в чат полученный PIN-КОД<emoji document_id=5789844634901417073>💜</emoji>"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(2.0)
                
    async def zigacmd(self, message: Message):
        "卍 вы пон крч"
        for _ in range(80):
            for anim in ["卍卍卍卍卍卍卍卍ㅤㅤㅤㅤㅤ卍\nㅤㅤㅤㅤㅤㅤㅤ卍ㅤㅤㅤㅤㅤㅤ卍\nㅤㅤㅤㅤㅤㅤㅤ卍ㅤㅤㅤㅤㅤㅤ卍\n", "卍卍卍卍卍卍卍卍ㅤㅤㅤㅤㅤ卍\nㅤㅤㅤㅤㅤㅤㅤ卍ㅤㅤㅤㅤㅤㅤ卍\nㅤㅤㅤㅤㅤㅤㅤ卍ㅤㅤㅤㅤㅤㅤ卍\nㅤㅤㅤㅤㅤㅤㅤ卍ㅤㅤㅤㅤㅤㅤ卍\nㅤㅤㅤㅤㅤㅤㅤ卍ㅤㅤㅤㅤㅤㅤ卍\n卍卍卍卍卍卍卍卍卍卍卍卍卍卍\n卍ㅤㅤㅤㅤㅤㅤ卍\n", "卍卍卍卍卍卍卍卍ㅤㅤㅤㅤㅤ卍\nㅤㅤㅤㅤㅤㅤㅤ卍ㅤㅤㅤㅤㅤㅤ卍\nㅤㅤㅤㅤㅤㅤㅤ卍ㅤㅤㅤㅤㅤㅤ卍\nㅤㅤㅤㅤㅤㅤㅤ卍ㅤㅤㅤㅤㅤㅤ卍\nㅤㅤㅤㅤㅤㅤㅤ卍ㅤㅤㅤㅤㅤㅤ卍\n卍卍卍卍卍卍卍卍卍卍卍卍卍卍\n卍ㅤㅤㅤㅤㅤㅤ卍\n卍ㅤㅤㅤㅤㅤㅤ卍\n卍ㅤㅤㅤㅤㅤㅤ卍\n卍ㅤㅤㅤㅤㅤㅤ卍\n卍ㅤㅤㅤㅤㅤㅤ卍卍卍卍卍卍卍卍\n"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(0.7)
                
    async def umnekcmd(self, message: Message):
        "🌲Анимация умника"
        for _ in range(1):
            for anim in ["💊", "🥱", "🤓", "🥸", "🥶", "🐻"]:
                message = await utils.answer(message, anim)
                await asyncio.sleep(5.0)
