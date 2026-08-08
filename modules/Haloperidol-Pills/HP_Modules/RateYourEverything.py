# Name: RateYourEverything
# Meta Developer: @HP_Modules
# Author: @HaloperidolPills
# Meta Banner: https://raw.githubusercontent.com/Haloperidol-Pills/metaassets/refs/heads/main/ratebanner.png
# Meta Pic: https://raw.githubusercontent.com/Haloperidol-Pills/metaassets/refs/heads/main/ratebanner.png
__version__ = 1,0,0
from .. import loader, utils
import random

class RateYourEverything(loader.Module):
    """Высококвалификацированный специалист по оценке всего"""
    strings = {"name": "RateYourEverything"}

    async def ratecmd(self, message):
        """Оценка от высококвалифицированного специалиста во всех областях"""
        channel_entity = "https://t.me/yahzchtopridumat"
        channel_messages = await self.client.get_messages(channel_entity, limit=1)

        possible_responses = [line.strip() for line in      channel_messages[0].raw_text.split("\n") if line.strip()]

        prediction = random.choice(possible_responses)
        
        formatted_result = (
            f"<emoji document_id=5319034516096951391>⌨️</emoji> <b>Ответ высококвалифицированного специалиста по всем вопросам:</b> {prediction}"
        )

        await message.edit(formatted_result)
