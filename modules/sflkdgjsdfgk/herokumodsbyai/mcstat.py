import asyncio
import time
import json
import struct
import base64
import io
import socket
from herokutl.types import Message
from .. import loader, utils
# meta developer: @modsbyai

@loader.tds
class MCStatMod(loader.Module):
    """Получить информацию о сервере Майнкрафт не заходя в игру. Поддерживает оба Бэдрок и Джава издания."""
    
    strings = {
        "name": "MCStat",
        "pinging": "<b>🔍 Опрашиваю сервер...</b>",
        "error": "<b>❌ Ошибка:</b> <code>{}</code>",
        "invalid_args": "<b>⚠️ Укажите адрес:</b> <code>.mcstat play.hypixel.net</code>",
        "result": (
            "<b>🎮 Minecraft:</b> <code>{}</code>\n\n"
            "<b>✅ Статус:</b> Онлайн ({})\n"
            "<b>👥 Игроки:</b> <code>{}/{}</code>\n"
            "<b>🎲 Версия:</b> <code>{}</code>\n"
            "<b>💬 MOTD:</b>\n<i>{}</i>\n\n"
            "<b>⚡ Задержка:</b> <code>{} мс</code>"
        )
    }

    def __init__(self):
        self._cache = {}

    @loader.command(ru_doc="Отправить запрос.")
    async def mcstat(self, message: Message):
        """<ip:port> - Статистика Java/Bedrock серверов"""
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, self.strings["invalid_args"])

        target = args.strip()
        
        if target in self._cache and time.time() - self._cache[target]['time'] < 30:
            data = self._cache[target]['data']
        else:
            message = await utils.answer(message, self.strings["pinging"])
            try:
                # Пробуем Java, если упало — пробуем Bedrock
                try:
                    data = await asyncio.wait_for(self._ping_java(target), timeout=4)
                    data['type'] = "Java"
                except:
                    data = await asyncio.wait_for(self._ping_bedrock(target), timeout=4)
                    data['type'] = "Bedrock"
                
                self._cache[target] = {'data': data, 'time': time.time()}
            except Exception as e:
                return await utils.answer(message, self.strings["error"].format("Сервер недоступен или неверный адрес"))

        # Чистка MOTD
        motd_raw = data.get('description', '...')
        if isinstance(motd_raw, dict):
            clean_motd = motd_raw.get('text', '')
            if 'extra' in motd_raw:
                clean_motd += "".join([ex.get('text', '') for ex in motd_raw['extra']])
        else:
            clean_motd = "".join(str(motd_raw).split('§')[::2])

        caption = self.strings["result"].format(
            target, data['type'], data['players']['online'], data['players']['max'],
            data['version']['name'], clean_motd.strip()[:200], data['latency']
        )

        if data.get("favicon"):
            try:
                img_data = base64.b64decode(data["favicon"].split(",")[1])
                photo = io.BytesIO(img_data)
                photo.name = "favicon.png"
                await self._client.send_file(message.peer_id, photo, caption=caption, reply_to=message.reply_to_msg_id)
                await message.delete()
            except:
                await utils.answer(message, caption)
        else:
            await utils.answer(message, caption)

    async def _ping_java(self, address):
        host, port = self._parse_addr(address, 25565)
        start = time.perf_counter()
        reader, writer = await asyncio.open_connection(host, port)
        try:
            host_b = host.encode('utf-8')
            packet = b'\x00' + self._encode_varint(47) + self._encode_varint(len(host_b)) + host_b + struct.pack('>H', port) + b'\x01' 
            writer.write(self._encode_varint(len(packet)) + packet + b'\x01\x00')
            await writer.drain()
            await self._read_varint(reader) 
            await self._read_varint(reader)
            data_len = await self._read_varint(reader)
            raw_data = b""
            while len(raw_data) < data_len:
                raw_data += await reader.read(data_len - len(raw_data))
            res = json.loads(raw_data.decode('utf-8'))
            res['latency'] = round((time.perf_counter() - start) * 1000)
            return res
        finally:
            writer.close()

    async def _ping_bedrock(self, address):
        host, port = self._parse_addr(address, 19132)
        start = time.perf_counter()
        
        # RakNet Unconnected Ping
        ping_packet = bytearray.fromhex("01000000000000000000ffff00fe fefefefdfdfdfd12345678")
        ping_packet[1:9] = struct.pack(">Q", int(time.time()))
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        loop = asyncio.get_event_loop()
        await loop.sock_connect(sock, (host, port))
        await loop.sock_sendall(sock, ping_packet)
        
        data = await asyncio.wait_for(loop.sock_recv(sock, 1024), timeout=3)
        latency = round((time.perf_counter() - start) * 1000)
        
        # Парсинг ответа Bedrock
        decoded = data[35:].decode("utf-8", errors="ignore").split(";")
        return {
            "version": {"name": decoded[3] if len(decoded) > 3 else "Unknown"},
            "players": {"online": decoded[4], "max": decoded[5]},
            "description": decoded[1],
            "latency": latency
        }

    def _parse_addr(self, addr, default_port):
        if ':' in addr:
            parts = addr.split(':')
            return parts[0], int(parts[1])
        return addr, default_port

    def _encode_varint(self, d):
        o = b""
        while True:
            b = d & 0x7F
            d >>= 7
            o += struct.pack("B", b | (0x80 if d > 0 else 0))
            if d == 0: break
        return o

    async def _read_varint(self, reader):
        d = 0
        for i in range(5):
            b = ord(await reader.read(1))
            d |= (b & 0x7F) << 7 * i
            if not b & 0x80: break
        return d
