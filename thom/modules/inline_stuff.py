#            ▀█▀ █ █ █▀█ █▀▄▀█ ▄▀█ █▀
#             █  █▀█ █▄█ █ ▀ █ █▀█ ▄█  
#             https://t.me/netuzb
#
# 🔒 Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import logging
import re
import string
from thom.inline.types import BotInlineMessage

from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.functions.contacts import UnblockRequest
from telethon.tl.types import Message

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class InlineStuffMod(loader.Module):
    """Provides support for inline stuff"""

    strings = {
        "name": "InlineStuff",
        "bot_username_invalid": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Brat! Neto qivossizu."
            " Karoche, oxirida </b><code>bot</code><b> bilan yakunlanishi kere, keyin"
            " 4 simvoldan koʻpro boʻsin.</b>"
        ),
        "bot_username_occupied": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Oka! Bu yuzerbot"
            " band ekan-ku.</b>"
        ),
        "bot_updated": (
            "<emoji document_id=6318792204118656433>🎉</emoji> <b>Tayyor brat!))"
            " Bitta restart bersangiz zoʻr boʻb ketadi</b>"
        ),
        "this_is_thom": (
            "💌 <b>Thom</b> - userbot maxsuli sanaladi."
            " Agarda sizni qiziqtirsa <a href='https://t.me/netuzb'>"
            "rasmiy manba</a>dan oʻrnatish qoʻllanmasini"
            " koʻrishingiz mumkin. 😎"
        ),
    }

    strings_ru = {
        "bot_username_invalid": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Неправильный ник"
            " бота. Он должен заканчиваться на </b><code>bot</code><b> и быть не короче"
            " чем 5 символов</b>"
        ),
        "bot_username_occupied": (
            "<emoji document_id=5415905755406539934>🚫</emoji> <b>Такой ник бота уже"
            " занят</b>"
        ),
        "bot_updated": (
            "<emoji document_id=6318792204118656433>🎉</emoji> <b>Готов братик!))"
            " Для их применения нужно перезагрузить юзербот</b>"
        ),
        "this_is_thom": (
             "💌 <b>Thom</b> - актуальный источник юзербота."
             " Если вам интересно <a href='https://t.me/netuzb'>"
             "руководство по установке</a> из официального источника,"
             " то можете заглянуть. 😎"
         ),
    }

    async def watcher(self, message: Message):
        if (
            getattr(message, "out", False)
            and getattr(message, "via_bot_id", False)
            and message.via_bot_id == self.inline.bot_id
            and "This message will be deleted automatically"
            in getattr(message, "raw_text", "")
        ):
            await message.delete()
            return

        if (
            not getattr(message, "out", False)
            or not getattr(message, "via_bot_id", False)
            or message.via_bot_id != self.inline.bot_id
            or "Opening gallery..." not in getattr(message, "raw_text", "")
        ):
            return

        id_ = re.search(r"#id: ([a-zA-Z0-9]+)", message.raw_text)[1]

        await message.delete()

        m = await message.respond("🌘 <b>Opening gallery...</b>")

        await self.inline.gallery(
            message=m,
            next_handler=self.inline._custom_map[id_]["handler"],
            caption=self.inline._custom_map[id_].get("caption", ""),
            force_me=self.inline._custom_map[id_].get("force_me", False),
            disable_security=self.inline._custom_map[id_].get(
                "disable_security", False
            ),
            silent=True,
        )

    async def _check_bot(self, username: str) -> bool:
        async with self._client.conversation("@BotFather", exclusive=False) as conv:
            try:
                m = await conv.send_message("/token")
            except YouBlockedUserError:
                await self._client(UnblockRequest(id="@BotFather"))
                m = await conv.send_message("/token")

            r = await conv.get_response()

            await m.delete()
            await r.delete()

            if not hasattr(r, "reply_markup") or not hasattr(r.reply_markup, "rows"):
                return False

            for row in r.reply_markup.rows:
                for button in row.buttons:
                    if username != button.text.strip("@"):
                        continue

                    m = await conv.send_message("/cancel")
                    r = await conv.get_response()

                    await m.delete()
                    await r.delete()

                    return True

    @loader.command(ru_doc="<юзернейм> - Изменить юзернейм инлайн бота")
    async def newbot(self, message: Message):
        """<yuzerneym> - Yangi inline bot yaratish"""
        args = utils.get_args_raw(message).strip("@")
        if (
            not args
            or not args.lower().endswith("bot")
            or len(args) <= 4
            or any(
                litera not in (string.ascii_letters + string.digits + "_")
                for litera in args
            )
        ):
            await utils.answer(message, self.strings("bot_username_invalid"))
            return

        try:
            await self._client.get_entity(f"@{args}")
        except ValueError:
            pass
        else:
            if not await self._check_bot(args):
                await utils.answer(message, self.strings("bot_username_occupied"))
                return

        self._db.set("thom.inline", "custom_bot", args)
        self._db.set("thom.inline", "bot_token", None)
        await utils.answer(message, self.strings("bot_updated"))

    async def aiogram_watcher(self, message: BotInlineMessage):
        if message.text != "/start":
            return

        await message.answer_photo(
            "https://te.legra.ph/file/aaa7bc16209157e7aa3c9.jpg",
            caption=self.strings("this_is_thom"),
        )
