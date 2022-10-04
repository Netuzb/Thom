import difflib
import inspect
import logging

from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Message

from .. import loader, security, utils

logger = logging.getLogger(__name__)


@loader.tds
class MHelpMod(loader.Module):
    """Thom uchun maxsus yaratilgan MHelp moduli <3"""

    strings = {
        "name": "Infomods",
        "bad_module": "<b>🚫 <b>Modul</b> <code>{}</code> <b>topilmadi</b>",
        "single_mod_header": "💌 <b>Modul nomi:</b> {}",
        "single_cmd": "\n— <b>«{}{}»</b> {}",
        "undoc_cmd": "🦥 No docs",
        "all_header": "💌 <b>«{}» modullar mavjud \n💌 «{}» berkitilgan</b>\n<i>— Quyida siz oʻrnatgan barcha modullar roʻyxati bor karoche</i>",
        "mod_tmpl": "\n{} <b>«{}»</b>",
        "first_cmd_tmpl": " «{}»",
        "cmd_tmpl": " «{}»",
        "no_mod": "🚫 <b>Specify module to hide</b>",
        "hidden_shown": "👀 <b>«{}» modul(lar) koʻrsatildi, «{}» berkitildi:</b>\n{}\n{}",
        "ihandler": "\n✿ <code>{}</code> {}",
        "undoc_ihandler": "🦥 No docs",
        "partial_load": "⚠️ <b>Userbot is not fully loaded, so not all modules are shown</b>",
        "not_exact": "⚠️ <b>No exact match occured, so the closest result is shown instead</b>",
    }

    strings_ru = {
        "bad_module": "<b>🚫 <b>Модуль</b> <code>{}</code> <b>не найдено.<b>",
        "single_mod_header": "💌 <b>Modul nomi:</b> {}",
        "single_cmd": "\n— <b>«{}{}»</b> {}",
        "undoc_cmd": "🦥 No docs",
        "all_header": "💌 <b>«{}» модулей доступно \n💌 «{}» спрятано</b>\n<i>— Короче, тут находится все твои тупые модули</i>",
        "mod_tmpl": "\n{} <b>«{}»</b>",
        "first_cmd_tmpl": " «{}»",
        "cmd_tmpl": " «{}»",
        "no_mod": "🚫 <b>Specify module to hide</b>",
        "hidden_shown": "👀 <b>«{}» модулей не скрытно находится, «{}» скрыто/b>\n{}\n{}",
        "ihandler": "\n✿ <code>{}</code> {}",
        "undoc_ihandler": "🦥 No docs",
        "partial_load": "⚠️ <b>Userbot is not fully loaded, so not all modules are shown</b>",
        "not_exact": "⚠️ <b>No exact match occured, so the closest result is shown instead</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "core_emoji",
                "—",
                lambda: "Core module bullet",
                validator=loader.validators.String(length=1),
            ),
            loader.ConfigValue(
                "thom_emoji",
                "—",
                lambda: "thom-only module bullet",
                validator=loader.validators.String(length=1),
            ),
            loader.ConfigValue(
                "plain_emoji",
                "—",
                lambda: "Plain module bullet",
                validator=loader.validators.String(length=1),
            ),
            loader.ConfigValue(
                "empty_emoji",
                "—",
                lambda: "Empty modules bullet",
                validator=loader.validators.String(length=1),
            ),
        )

    async def hhcmd(self, message: Message):
        """<module or modules> - Hide module(-s) from help
        *Split modules by spaces"""
        modules = utils.get_args(message)
        if not modules:
            await utils.answer(message, self.strings("no_mod"))
            return

        mods = [
            i.strings["name"]
            for i in self.allmodules.modules
            if hasattr(i, "strings") and "name" in i.strings
        ]

        modules = list(filter(lambda module: module in mods, modules))
        currently_hidden = self.get("hide", [])
        hidden, shown = [], []
        for module in modules:
            if module in currently_hidden:
                currently_hidden.remove(module)
                shown += [module]
            else:
                currently_hidden += [module]
                hidden += [module]

        self.set("hide", currently_hidden)

        await utils.answer(
            message,
            self.strings("hidden_shown").format(
                len(hidden),
                len(shown),
                "\n".join([f"👁‍🗨 <i>{m}</i>" for m in hidden]),
                "\n".join([f"👁 <i>{m}</i>" for m in shown]),
            ),
        )

    async def modhelp(self, message: Message, args: str):
        exact = True

        try:
            module = next(
                mod
                for mod in self.allmodules.modules
                if mod.strings("name").lower() == args.lower()
            )
        except Exception:
            module = None

        if not module:
            args = args.lower()
            args = args[1:] if args.startswith(self.get_prefix()) else args
            if args in self.allmodules.commands:
                module = self.allmodules.commands[args].__self__

        if not module:
            module_name = next(  # skipcq: PTC-W0063
                reversed(
                    sorted(
                        [module.strings["name"] for module in self.allmodules.modules],
                        key=lambda x: difflib.SequenceMatcher(
                            None,
                            args.lower(),
                            x,
                        ).ratio(),
                    )
                )
            )

            module = next(  # skipcq: PTC-W0063
                module
                for module in self.allmodules.modules
                if module.strings["name"] == module_name
            )

            exact = False

        try:
            name = module.strings("name")
        except KeyError:
            name = getattr(module, "name", "ERROR")

        reply = self.strings("single_mod_header").format(utils.escape_html(name))
        if module.__doc__:
            reply += "\n<b>🌄 Info:</b> <i>" + utils.escape_html(inspect.getdoc(module)) + "\n</i>"

        commands = {
            name: func
            for name, func in module.commands.items()
            if await self.allmodules.check_security(message, func)
        }

        if hasattr(module, "inline_handlers"):
            for name, fun in module.inline_handlers.items():
                reply += self.strings("ihandler").format(
                    f"@{self.inline.bot_username} {name}",
                    (
                        utils.escape_html(inspect.getdoc(fun))
                        if fun.__doc__
                        else self.strings("undoc_ihandler")
                    ),
                )

        for name, fun in commands.items():
            reply += self.strings("single_cmd").format(
                self.get_prefix(),
                name,
                (
                    utils.escape_html(inspect.getdoc(fun))
                    if fun.__doc__
                    else self.strings("undoc_cmd")
                ),
            )

        await utils.answer(
            message, f"{reply}\n\n{self.strings('not_exact') if not exact else ''}"
        )

    @loader.unrestricted
    async def helpcmd(self, message: Message):
        """[module] [-f] - Show help"""
        args = utils.get_args_raw(message)
        force = False
        if "-f" in args:
            args = args.replace(" -f", "").replace("-f", "")
            force = True

        if args:
            await self.modhelp(message, args)
            return

        count = 0
        for i in self.allmodules.modules:
            try:
                if i.commands or i.inline_handlers:
                    count += 1
            except Exception:
                pass

        hidden = self.get("hide", [])

        reply = self.strings("all_header").format(
            count,
            len(hidden) if not force else 0,
        )
        shown_warn = False

        plain_ = []
        core_ = []
        inline_ = []
        no_commands_ = []

        for mod in self.allmodules.modules:
            if not hasattr(mod, "commands"):
                logger.debug(f"Module {mod.__class__.__name__} is not inited yet")
                continue

            if mod.strings["name"] in self.get("hide", []) and not force:
                continue

            tmp = ""

            try:
                name = mod.strings["name"]
            except KeyError:
                name = getattr(mod, "name", "ERROR")

            inline = (
                hasattr(mod, "callback_handlers")
                and mod.callback_handlers
                or hasattr(mod, "inline_handlers")
                and mod.inline_handlers
            )

            if not inline:
                for cmd_ in mod.commands.values():
                    try:
                        inline = "await self.inline.form(" in inspect.getsource(
                            cmd_.__code__
                        )
                    except Exception:
                        pass

            core = mod.__origin__ == "<core>"

            if core:
                emoji = self.config["core_emoji"]
            elif inline:
                emoji = self.config["thom_emoji"]
            else:
                emoji = self.config["plain_emoji"]

            if (
                not getattr(mod, "commands", None)
                and not getattr(mod, "inline_handlers", None)
                and not getattr(mod, "callback_handlers", None)
            ):
                no_commands_ += [
                    self.strings("mod_tmpl").format(self.config["empty_emoji"], name)
                ]
                continue

            tmp += self.strings("mod_tmpl").format(emoji, name)
            first = True

            commands = [
                name
                for name, func in mod.commands.items()
                if await self.allmodules.check_security(message, func) or force
            ]

            for cmd in commands:
                if first:
                    tmp += self.strings("first_cmd_tmpl").format(cmd)
                    first = False
                else:
                    tmp += self.strings("cmd_tmpl").format(cmd)

            icommands = [
                name
                for name, func in mod.inline_handlers.items()
                if await self.inline.check_inline_security(
                    func=func,
                    user=message.sender_id,
                )
                or force
            ]

            for cmd in icommands:
                if first:
                    tmp += self.strings("first_cmd_tmpl").format(f"✿ {cmd}")
                    first = False
                else:
                    tmp += self.strings("cmd_tmpl").format(f"✿ {cmd}")

            if commands or icommands:
                tmp += ""
                if core:
                    core_ += [tmp]
                elif inline:
                    inline_ += [tmp]
                else:
                    plain_ += [tmp]
            elif not shown_warn and (mod.commands or mod.inline_handlers):
                reply = f"<i>You have permissions to execute only these commands</i>\n{reply}"
                shown_warn = True

        plain_.sort(key=lambda x: x.split()[1])
        core_.sort(key=lambda x: x.split()[1])
        inline_.sort(key=lambda x: x.split()[1])
        no_commands_.sort(key=lambda x: x.split()[1])
        no_commands_ = "\n".join(no_commands_) if force else ""

        partial_load = (
            f"\n\n{self.strings('partial_load')}"
            if not self.lookup("Loader")._fully_loaded
            else ""
        )

        umod_turn = f"\n\n🌉 <b>1.4.2 modification oʻrnida qabul qilamiza.</b>"
        um_tn = "\n<i>— Never gonna give you up...</i>"
        await utils.answer(
            message,
            f"{reply}\n{''.join(core_)}{''.join(plain_)}{''.join(inline_)}{no_commands_}{partial_load}{umod_turn}{um_tn}",
        )
