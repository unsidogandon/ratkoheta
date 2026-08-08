# meta developer: @coddan
# requires: qrcode pillow

import io
import qrcode
from .. import loader, utils

@loader.tds
class QRCode(loader.Module):
    """Generates QR codes from text or links"""
    
    strings = {
        "name": "QRCode",
        "no_args": "<b>❌ Please provide a link or text (or reply to a message) to generate a QR code.</b>",
        "generating": "<b>⏳ Generating QR code...</b>",
        "error": "<b>❌ Error generating QR code:</b> <code>{}</code>"
    }

    @loader.command(
        ru_doc="Сгенерировать QR код по ссылке или тексту. Использование: .qr <текст/ссылка> или реплай"
    )
    async def qrcmd(self, message):
        """Generates a QR code from the provided text/link"""
        args = utils.get_args_raw(message)
        
        if not args:
            reply = await message.get_reply_message()
            if reply and reply.text:
                args = reply.text
            else:
                await utils.answer(message, self.strings("no_args", message))
                return
        
        await utils.answer(message, self.strings("generating", message))
        
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(args)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            out = io.BytesIO()
            out.name = "qrcode.png"
            img.save(out, 'PNG')
            out.seek(0)
            
            caption = f"<b>✅ QR Code generated</b>\n<b>📝 Data:</b> <code>{args[:100]}{'...' if len(args) > 100 else ''}</code>"
            await utils.answer_file(message, out, caption=caption)
            
            if message.out:
                await message.delete()
                
        except Exception as e:
            await utils.answer(message, self.strings("error", message).format(str(e)))