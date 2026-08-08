__version__ = (1, 0, 6)

"""
  __  ___  _____  ____________  ______ ___ 
 / / / / |/ / _ \/ __/ __<  / |/ /_  // _ \
/ /_/ /    / // / _// _/ / /    //_ </ // /
\____/_/|_/____/___/_/  /_/_/|_/____/____/

©️ 2025 — licensed under Apache 2.0 

🌐 https://www.apache.org/licenses/LICENSE-2.0

"""

#meta developer: @undef1n3dd
#requires: Pillow opencv-python numpy pytesseract

from PIL import Image, ImageEnhance
import cv2
import numpy as np
from io import BytesIO
import pytesseract
import re
import typing
from urllib.parse import urlparse, parse_qs, unquote
import asyncio
import logging
import subprocess

from telethon.tl.types import Message

from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class HHFarmMod(loader.Module):
  strings = {
    "name": "HHFarm",
    "activated": "<emoji document_id=5316561083085895267>✅</emoji> <b>Module activated</b>",
    "deactivated": "<emoji document_id=5388785832956016892>❌</emoji>  <b>Module deactivated</b>",
    "post_install": "<emoji document_id=5879785854284599288>ℹ️</emoji> <b>This module requires</b> <code>tesseract-ocr</code>\n\n<emoji document_id=6024106569430472546>📦</emoji><b>Installation command:</b> <code>apt install tesseract-ocr -y</code>"
  }

  strings_ru = {
    "activated": "<emoji document_id=5316561083085895267>✅</emoji> <b>Модуль активирован</b>",
    "deactivated": "<emoji document_id=5388785832956016892>❌</emoji>  <b>Модуль деактивирован</b>",
    "post_install": "<emoji document_id=5879785854284599288>ℹ️</emoji> <b>Для работы данного модуля требуется</b> <code>tesseract-ocr</code>\n\n<emoji document_id=6024106569430472546>📦</emoji><b>Команда для установки:</b> <code>apt install tesseract-ocr -y</code>"
  }

  async def client_ready(self, client, db):
    self._client = client
    self._db = db

  def _enhance_image(self, image_bytes: bytes) -> bytes:
    """
    Enhance the image's color and brightness from the given bytes and return the modified image as bytes

    :param image_bytes: The original image data in bytes
    :return: The modified image data as bytes in PNG format
    """
    image = Image.open(BytesIO(image_bytes))

    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(50)

    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(2.8)

    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)

    return buffer.read()

  def _prepare_image(self, image_bytes: bytes) -> bytes:
    """
    Preprocess and enhance the image by converting it to grayscale, applying thresholding, 
    morphological transformations, and adjusting contrast. The result is a PNG-encoded byte stream

    :param image_bytes: The original image data in bytes
    :return: The processed image data as bytes in PNG format
    """
    np_arr = np.frombuffer(image_bytes, np.uint8)

    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    _, thresh = cv2.threshold(grayscale, 75, 255, cv2.THRESH_BINARY_INV)

    kernel = np.ones((5, 5), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    image_alpha = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
    image_alpha[:, :, 3] = thresh 

    h, w = grayscale.shape[:2]
    grayscale = grayscale[(h-200)//2:(h+200)//2, (w-200)//2:(w+200)//2]

    grayscale = cv2.convertScaleAbs(grayscale, alpha=1.5, beta=0)

    _, thresh =  cv2.threshold(grayscale, 40, 255, cv2.THRESH_BINARY_INV)

    thresh = cv2.medianBlur(thresh, 3)

    thresh = cv2.morphologyEx(thresh, cv2.MORPH_GRADIENT, kernel)
    
    thresh = cv2.bitwise_not(thresh)

    _, buffer = cv2.imencode('.png', thresh)

    return buffer.tobytes()
  
  def _parse_text(self, image_bytes: bytes, ocr_config: str = '') -> str:
    """
    Extract text from an image using Optical Character Recognition (OCR)

    :param image_bytes: The image data in bytes to extract text from
    :param ocr_config: Optional configuration string for Tesseract OCR (default is empty)
    :return: The extracted text from the image
    """
    image = Image.open(BytesIO(image_bytes))

    text = pytesseract.image_to_string(image, config=ocr_config, lang='eng')

    return text
  
  def _find_urls(self, text: str) -> typing.Optional[typing.List[str]]:
    """
    Find all HikkaHost bot URLs in a given text using a regular expression

    :param text: The text to search for Telegram bot URLs
    :return: A list of found URLs or `None` if no URLs are found
    """
    pattern = r"(?:https?://)?t\.me/hikkahost_bot/?\?[^\s]*\bstart=[A-Za-z0-9%._\-+]*"

    matches = re.findall(pattern, text)

    return matches if matches else None
  
  def _extract_param(self, url: str) -> typing.Optional[str]:
    """
    Extract the 'start' parameter from a URL

    :param url: The URL to extract the 'start' parameter from
    :return: The value of the 'start' parameter, or `None` if the URL is invalid or the parameter is not found
    """
    url = url if url.startswith(('http://', 'https://')) else 'https://' + url
    p = urlparse(url)

    if p.netloc.lower() != 't.me':
      return None
    if p.path not in ('/hikkahost_bot', '/hikkahost_bot/'):
      return None
    
    qs = parse_qs(p.query)
    vals = qs.get('start')

    return unquote(vals[0] if vals else None)

  async def solve_captcha(self, param_val: str) -> bool:
    try:
      async with self._client.conversation(6150092944, timeout=120) as conv:
        await conv.send_message(f'/start {param_val}')

        bot_resp = await conv.get_response()

        if not bot_resp.media or not bot_resp.media.photo:
          if bot_resp.reply_markup and bot_resp.reply_markup.rows[0].buttons[0].data == 'not_robot':
              await bot_resp.click(0)

          return False
        
        captcha_img_bytes = await self._client.download_media(bot_resp.media, bytes)
        captcha = await utils.run_sync(self._enhance_image, captcha_img_bytes)
        captcha = await utils.run_sync(self._prepare_image, captcha)

        ocr_cfg = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789+-*/='

        text = await utils.run_sync(self._parse_text, captcha, ocr_config=ocr_cfg)

        pattern = r'[0-9.+\-*/()]'
        matches = re.findall(pattern, text)

        normalized_text = "".join(matches)

        try:
          result = eval(normalized_text)
        except Exception:
          logger.error("Failed to solve the captcha")
          return False
        
        await conv.mark_read(bot_resp)
        
        await asyncio.sleep(1)
        
        await conv.send_message(str(result))

        try:
          bot_resp = await asyncio.wait_for(conv.get_response(), timeout=5)
          await conv.mark_read(bot_resp)
        except asyncio.TimeoutError:
          await conv.send_message(str(result))
          bot_resp = await conv.get_response()
          await conv.mark_read(bot_resp)

        return True
    except Exception:
      logger.exception("Something went wrong")
      return False

  @loader.command(en_doc="- Activate/Deactivate module", ru_doc="- Активировать/Деактивировать модуль")
  async def hhfarm(self, message: Message):
    try:
      subprocess.run(['tesseract', '--version'], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
      await utils.answer(message, self.strings("post_install"))
      return
    
    self.set('status', not self.get('status', False))

    await utils.answer(message, self.strings(("activated" if self.get('status', False) else "deactivated")))
  
  @loader.watcher(out=False, only_messages=True)
  async def hh_watcher(self, message: Message):
    if not self.get('status', False):
      return
    if message.out:
      return
    
    urls = self._find_urls(message.message)

    if urls:
      for url in urls:
        param_val = self._extract_param(url)
        await self.solve_captcha(param_val)
        await asyncio.sleep(5)
      return
    elif message.via_bot_id == 6150092944 and message.reply_markup:
      if url := message.reply_markup.rows[0].buttons[0].get('url', None):
        param_val = self._extract_param(url)
        await self.solve_captcha(param_val)
        return
    else:
      return
    

