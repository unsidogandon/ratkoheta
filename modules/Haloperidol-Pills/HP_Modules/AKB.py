# name = AKB
# description = sends aneks from AKB
# Author = @hp_modules
# meta developer = @hp_modules
# Scope = AKB
__version__ = 1, 0, 0

import time
import random
import os
import logging
from herokutl.types import Message
from .. import loader, utils

logger = logging.getLogger("simplename")

entity = ("https://t.me/baneksru")

@loader.tds
class AKB(loader.Module):
	"""Sends aneks from AKB"""
	
	strings_ru = {
	    "name": "AKB", 
		"sending": "Внимание, анекдот!", 
		"error": "ааааа ашибка 00000"
			}
			
	strings = {
	    "name": "AKB",
	    "sending": "attention, anekdot!",
	    "error": "oops, that's an error"
	}
		
	@loader.command(
	ru_doc="вкинуть анекдот из АКБ",
	en_doc="Send anek from AKB",
	)
	async def akb(self, message):
	    """Вкинуть анекдотик из АКБ"""
	    otpravka = await utils.answer(message, self.strings("sending"))
	    
	    try:
	        mes = await self.client.get_messages(entity, limit=300)
	    except Exception as e:
	        return await utils.answer(message, self.strings("error"))
	        
	        
	            
	    rndm_mes = random.choice(mes)
	    await message.client.send_message(
	        message.peer_id,
	        message=rndm_mes,
	        reply_to=getattr(message, "reply_to_msg_id", None)
	        )
	    time.sleep(0.3)
	    await self.client.delete_messages(message.chat_id, otpravka)
