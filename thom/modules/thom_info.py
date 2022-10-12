#            ▀█▀ █ █ █▀█ █▀▄▀█ ▄▀█ █▀
#             █  █▀█ █▄█ █ ▀ █ █▀█ ▄█  
#             https://t.me/netuzb
#
# 🔒 Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

import logging
import git
from telethon.tl.types import Message
from telethon.utils import get_display_name
from .. import loader, utils, version
from ..inline.types import InlineQuery

logger = logging.getLogger(__name__)

@loader.tds
class ThomInfoMod(loader.Module):
    """Show userbot info"""

    strings = {
        "name": "ThomInfo",
        "owner": "Asoschi",
        "version": "Version",
        "build": "Build",
        "prefix": "Prefix",
        "uptime": "Uptime",
        "branch": "Branch",
        "send_info": "Thom’ boʻyicha maʼlumot",
        "description": "👀 Bo‘tta faqat Thom haqida maʼlumot boʻladi",
        "up-to-date": "<b>😎 Sizda uje barqaror versiya</b>",
        "update_required": "<b>😕 Brat! Yangilavoling, eskisida oʻtiribsiz: </b><code>.update</code>",
        "_cfg_cst_msg": (
            "Karoche, maxsus yutillar: {me}, {version}, {build}, {prefix},"
            " {platform}, {upd}, {uptime}, {branch}"
        ),
        "_cfg_cst_btn": "Tugmachani yozuvi hamda havolasini vergul bilan ajratib yozish kere, oka.",
        "_cfg_banner": "Banner uchun havola kere",
    }

    strings_ru = {
        "owner": "Владелец",
        "version": "Версия",
        "build": "Сборка",
        "prefix": "Префикс",
        "uptime": "Аптайм",
        "branch": "Ветка",
        "send_info": "Отправить информацию о юзерботе",
        "description": "ℹ Это не раскроет никакой личной информации",
        "_ihandle_doc_info": "Отправить информацию о юзерботе",
        "up-to-date": "<b>😌 Актуальная версия</b>",
        "update_required": "<b>😕 Требуется обновление </b><code>.update</code>",
        "_cfg_cst_msg": (
            "Кастомный текст сообщения в info. Может содержать ключевые слова {me},"
            " {version}, {build}, {prefix}, {platform}, {upd}, {uptime}, {branch}"
        ),
        "_cfg_cst_btn": (
            "Кастомная кнопка в сообщении в info. Оставь пустым, чтобы убрать кнопку"
        ),
        "_cfg_banner": "Ссылка на баннер-картинку",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "custom_message",
                doc=lambda: self.strings("_cfg_cst_msg"),
            ),
            loader.ConfigValue(
                "custom_button",
                ["💌 UMod fed.", "https://t.me/umodules"],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Union(
                    loader.validators.Series(fixed_len=2),
                    loader.validators.NoneType(),
                ),
            ),
            loader.ConfigValue(
                "banner_url",
                "https://te.legra.ph/file/aaa7bc16209157e7aa3c9.jpg",
                lambda: self.strings("_cfg_banner"),
                validator=loader.validators.Link(),
            ),
        )

    async def client_ready(self):
        self._me = await self._client.get_me()

    def _render_info(self) -> str:
        try:
            repo = git.Repo(search_parent_directories=True)
            diff = repo.git.log([f"HEAD..origin/{version.branch}", "--oneline"])
            upd = (
                self.strings("update_required") if diff else self.strings("up-to-date")
            )
        except Exception:
            upd = ""

        me = (
            "<b><a"
            f' href="tg://user?id={self._me.id}">{utils.escape_html(get_display_name(self._me))}</a></b>'
        )
        build = utils.get_commit_url()
        _version = f'<i>{".".join(list(map(str, list(version.__version__))))}</i>'
        prefix = f"«<code>{utils.escape_html(self.get_prefix())}</code>»"
        platform = utils.get_named_platform()

        return (
            (
                "<b>🌘 Thom</b> userbot\n"
                if "thom" not in self.config["custom_message"].lower()
                else ""
            )
            + self.config["custom_message"].format(
                me=me,
                version=_version,
                build=build,
                prefix=prefix,
                platform=platform,
                upd=upd,
                uptime=utils.formatted_uptime(),
                branch=version.branch,
            )
            if self.config["custom_message"]
            else (
                "<b>🌘 Thom</b> userbot\n"
                f'<b>🤴 {self.strings("owner")}: </b>{me}\n\n'
                f"<b>🔮 {self.strings('version')}: </b>{_version} {build}\n"
                f"<b>🌳 {self.strings('branch')}: </b><code>{version.branch}</code>\n"
                f"{upd}\n\n"
                f"<b>📼 {self.strings('prefix')}: </b>{prefix}\n"
                f"<b>⌚️ {self.strings('uptime')}: </b>{utils.formatted_uptime()}\n"
                f"<b>{platform}</b>\n"
            )
        )

    def _get_mark(self):
        return (
            {
                "text": self.config["custom_button"][0],
                "url": self.config["custom_button"][1],
            }
            if self.config["custom_button"]
            else None
        )

    @loader.inline_everyone
    async def info_inline_handler(self, _: InlineQuery) -> dict:
        """Send userbot info"""

        return {
            "title": self.strings("send_info"),
            "description": self.strings("description"),
            "message": self._render_info(),
            "thumb": (
                "https://te.legra.ph/file/6c9471456effd1bd018b0.jpg"
            ),
            "reply_markup": self._get_mark(),
        }

    @loader.unrestricted
    async def infocmd(self, message: Message):
        """Send userbot info"""
        await self.inline.form(
            message=message,
            text=self._render_info(),
            reply_markup=self._get_mark(),
            **(
                {"photo": self.config["banner_url"]}
                if self.config["banner_url"]
                else {}
            ),
        )

    @loader.unrestricted
    async def thominfocmd(self, message: Message):
        """[en/ru - default en] - Send info aka 'What is Thom?'"""
        args = utils.get_args_raw(message)
        args = args if args in {"en", "ru"} else "en"

        await utils.answer(
            message,
            "<emoji document_id=6318565919471699564>🌌</emoji>"
            " <b>Thom</b>\n\nTelegram userbot with a lot of features, like inline"
            " galleries, forms, lists and animated emojis support. Userbot - software,"
            " running on your Telegram account. If you write a command to any chat, it"
            " will get executed right there. Check out live examples at <a"
            ' href="https://github.com/hikariatama/Hikka">GitHub</a>'
            if args == "en"
            else (
                "<emoji document_id=6318565919471699564>🌌</emoji>"
                " <b>Hikka</b>\n\nTelegram юзербот с огромным количеством функций, из"
                " которых: инлайн галереи, формы, списки, а также поддержка"
                " анимированных эмодзи. Юзербот - программа, которая запускается на"
                " твоем Telegram-аккаунте. Когда ты пишешь команду в любом чате, она"
                " сразу же выполняется. Обрати внимание на живые примеры на <a"
                ' href="https://github.com/hikariatama/Hikka">GitHub</a>'
            ),
        )
