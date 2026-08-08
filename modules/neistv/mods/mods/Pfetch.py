# Name: pfetch
# Description: показывает инфу краткую о системе
# authors: @neistv
# version: 1.0.1
# meta developer: @latexmods
# meta banner: https://github.com/neistv/mods/raw/main/assets/banners/pfetch.png
import logging
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from html import escape

from herokutl.types import Message
from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class PfetchMod(loader.Module):
    """информация о системе с помощью pfetch"""

    strings = {
        "name": "Pfetch",
        "installing": "<b>устанавливаю pfetch...</b>",
        "trying_install": "<b>пробую:</b> <code>{}</code>",
        "install_error": "<b>не смог установить pfetch:</b> <code>{}</code>",
        "run_error": "<b>pfetch упал:</b> <code>{}</code>",
    }

    def __init__(self):
        self._bin_dir = os.path.expanduser("~/.local/bin")
        self._pfetch_path = os.path.join(self._bin_dir, "pfetch")
        os.makedirs(self._bin_dir, exist_ok=True)

        current_path = os.environ.get("PATH", "")
        if self._bin_dir not in current_path.split(os.pathsep):
            os.environ["PATH"] = f"{self._bin_dir}{os.pathsep}{current_path}"

    def _find_pfetch(self) -> str | None:
        return shutil.which("pfetch") or (
            self._pfetch_path if os.path.exists(self._pfetch_path) else None
        )

    async def _install_pfetch(self, message: Message | None = None) -> str:
        distro = self._os_release().get("ID", "").lower()
        commands = self._install_commands(distro)

        for label, command in commands:
            if not shutil.which(command[0]):
                continue

            if message:
                await utils.answer(message, self.strings("trying_install").format(label))

            try:
                result = await utils.run_sync(
                    subprocess.run,
                    command,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
            except (OSError, subprocess.SubprocessError):
                continue

            if result.returncode == 0:
                installed = self._find_pfetch()
                if installed:
                    return installed

        if message:
            await utils.answer(message, self.strings("trying_install").format("github"))

        return await self._install_from_github()

    def _install_commands(self, distro: str) -> list[tuple[str, list[str]]]:
        commands = []

        if distro in {"arch", "endeavouros", "manjaro"}:
            commands += [
                ("pacman", ["pacman", "-S", "--noconfirm", "pfetch"]),
                ("yay", ["yay", "-S", "--noconfirm", "pfetch"]),
                ("paru", ["paru", "-S", "--noconfirm", "pfetch"]),
            ]
        elif distro in {"debian", "ubuntu", "linuxmint", "pop", "popos"}:
            commands += [
                ("apt-get", ["apt-get", "install", "-y", "pfetch"]),
                ("apt", ["apt", "install", "-y", "pfetch"]),
            ]
        elif distro in {"fedora", "rhel", "centos", "rocky", "almalinux"}:
            commands += [
                ("dnf", ["dnf", "install", "-y", "pfetch"]),
                ("yum", ["yum", "install", "-y", "pfetch"]),
            ]
        elif distro in {"opensuse", "opensuse-tumbleweed"}:
            commands.append(("zypper", ["zypper", "install", "-y", "pfetch"]))
        elif distro == "alpine":
            commands.append(("apk", ["apk", "add", "pfetch"]))
        elif distro == "void":
            commands.append(("xbps-install", ["xbps-install", "-Sy", "pfetch"]))

        commands += [
            ("pacman", ["pacman", "-S", "--noconfirm", "pfetch"]),
            ("yay", ["yay", "-S", "--noconfirm", "pfetch"]),
            ("paru", ["paru", "-S", "--noconfirm", "pfetch"]),
            ("apt-get", ["apt-get", "install", "-y", "pfetch"]),
            ("apt", ["apt", "install", "-y", "pfetch"]),
            ("dnf", ["dnf", "install", "-y", "pfetch"]),
            ("zypper", ["zypper", "install", "-y", "pfetch"]),
            ("apk", ["apk", "add", "pfetch"]),
            ("xbps-install", ["xbps-install", "-Sy", "pfetch"]),
        ]

        seen = set()
        unique = []
        for label, command in commands:
            key = tuple(command)
            if key in seen:
                continue
            seen.add(key)
            unique.append((label, command))

        return unique

    async def _install_from_github(self) -> str:
        url = "https://raw.githubusercontent.com/dylanaraps/pfetch/master/pfetch"
        try:
            await utils.run_sync(urllib.request.urlretrieve, url, self._pfetch_path)
            await utils.run_sync(os.chmod, self._pfetch_path, 0o755)
        except (urllib.error.URLError, OSError) as e:
            raise RuntimeError(str(e)) from e

        return self._pfetch_path

    @staticmethod
    def _read_first(paths: list[str]) -> str:
        for path in paths:
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as file:
                    value = file.read().strip()
                    if value:
                        return value
            except OSError:
                continue

        return ""

    @staticmethod
    def _os_release() -> dict[str, str]:
        data = {}
        try:
            with open("/etc/os-release", "r", encoding="utf-8", errors="ignore") as file:
                for line in file:
                    if "=" not in line:
                        continue

                    key, value = line.rstrip().split("=", 1)
                    data[key] = value.strip('"')
        except OSError:
            pass

        return data

    def _get_host(self) -> str:
        product = self._read_first(
            [
                "/sys/devices/virtual/dmi/id/product_name",
                "/sys/class/dmi/id/product_name",
            ]
        )
        version = self._read_first(
            [
                "/sys/devices/virtual/dmi/id/product_version",
                "/sys/class/dmi/id/product_version",
            ]
        )

        host = " ".join(part for part in [product, version] if part and part != "None")
        return host or os.uname().machine

    @staticmethod
    def _get_uptime() -> str:
        try:
            with open("/proc/uptime", "r", encoding="utf-8") as file:
                seconds = int(float(file.read().split()[0]))
        except (OSError, ValueError, IndexError):
            seconds = int(time.monotonic())

        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes = seconds // 60

        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        parts.append(f"{minutes}m")
        return " ".join(parts)

    @staticmethod
    def _get_packages() -> str:
        checks = [
            ("pacman", ["pacman", "-Qq"]),
            ("dpkg-query", ["dpkg-query", "-f", "${binary:Package}\n", "-W"]),
            ("rpm", ["rpm", "-qa"]),
            ("apk", ["apk", "info"]),
        ]

        for binary, command in checks:
            if not shutil.which(binary):
                continue

            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=8,
                )
            except (subprocess.SubprocessError, OSError):
                continue

            if result.returncode == 0:
                count = len([line for line in result.stdout.splitlines() if line.strip()])
                if count:
                    return str(count)

        return "unknown"

    @staticmethod
    def _get_memory() -> str:
        meminfo = {}
        try:
            with open("/proc/meminfo", "r", encoding="utf-8") as file:
                for line in file:
                    key, value = line.split(":", 1)
                    meminfo[key] = int(value.strip().split()[0])
        except (OSError, ValueError, IndexError):
            return "unknown"

        total = meminfo.get("MemTotal", 0)
        available = meminfo.get("MemAvailable", 0)
        used = max(total - available, 0)
        return f"{used // 1024}M / {total // 1024}M"

    @staticmethod
    def _clip(value: str, limit: int = 36) -> str:
        value = " ".join(str(value).split())
        if len(value) <= limit:
            return value

        return value[: max(limit - 1, 1)].rstrip() + "."

    @staticmethod
    def _compact_os(os_release: dict[str, str]) -> str:
        os_id = os_release.get("ID", "").lower()
        pretty_name = os_release.get("PRETTY_NAME", "")
        name = (
            pretty_name
            or os_release.get("NAME")
            or os_id
            or "unknown"
        )
        name = re.sub(r"\s*\([^)]*\)", "", name).strip()

        if os_id == "debian" and "VERSION_ID" in os_release:
            return f"Debian {os_release['VERSION_ID']}"
        if os_id == "ubuntu" and "VERSION_ID" in os_release:
            return f"Ubuntu {os_release['VERSION_ID']}"
        if os_id in {"arch", "archlinux"}:
            return "Arch"
        if os_id == "endeavouros":
            return "EndeavourOS"
        if os_id == "linuxmint" and "VERSION_ID" in os_release:
            return f"Mint {os_release['VERSION_ID']}"
        if os_id == "fedora" and "VERSION_ID" in os_release:
            return f"Fedora {os_release['VERSION_ID']}"
        if os_id == "manjaro":
            return "Manjaro"
        if os_id == "opensuse-tumbleweed":
            return "openSUSE TW"
        if os_id in {"rhel", "centos", "rocky", "almalinux"} and "VERSION_ID" in os_release:
            label = {
                "rhel": "RHEL",
                "centos": "CentOS",
                "rocky": "Rocky",
                "almalinux": "Alma",
            }.get(os_id, os_id)
            return f"{label} {os_release['VERSION_ID']}"

        name = name.replace(" GNU/Linux", "").replace(" Linux", "")
        return PfetchMod._clip(name, 16)

    @staticmethod
    def _compact_host(host: str) -> str:
        host = re.sub(r"\s*\([^)]*\)", "", host)
        host = host.replace("RHEL 7.6.0 PC", "")
        host = re.sub(r"\s+", " ", host).strip()

        if "kvm" in host.lower():
            return "kvm"
        if "virtualbox" in host.lower():
            return "virtualbox"
        if "vmware" in host.lower():
            return "vmware"

        return PfetchMod._clip(host or "unknown", 22)

    @staticmethod
    def _compact_kernel(kernel: str) -> str:
        kernel = re.sub(r"([0-9]+\.[0-9]+\.[0-9]+).*", r"\1", kernel)
        kernel = re.sub(r"([0-9]+\.[0-9]+)-.*", r"\1", kernel)
        return PfetchMod._clip(kernel, 10)

    @staticmethod
    def _compact_identity(username: str, hostname: str) -> str:
        host = hostname.split(".", 1)[0]
        return PfetchMod._clip(f"{username}@{host}", 18)

    def _logo_key(self, os_release: dict[str, str]) -> str:
        distro_id = os_release.get("ID", "").lower().strip('"')
        
        id_map = {
            "ubuntu": "ubuntu",
            "linuxmint": "mint",
            "debian": "debian",
            "fedora": "fedora",
            "arch": "arch",
            "archlinux": "arch",
            "manjaro": "manjaro",
            "endeavouros": "endeavour",
            "alpine": "alpine",
            "void": "void",
            "nixos": "nixos",
            "gentoo": "gentoo",
            "freebsd": "freebsd",
            "pop": "pop",
        }
        
        if distro_id in id_map:
            return id_map[distro_id]

        distro_full = " ".join(os_release.values()).lower()

        for name in (
            "endeavour",
            "manjaro",
            "mint",
            "ubuntu",
            "arch",
            "debian",
            "fedora",
            "alpine",
            "void",
            "nixos",
            "gentoo",
            "freebsd",
        ):
            if name in distro_full:
                return name

        if "suse" in distro_full:
            return "opensuse"
        if "pop!_os" in distro_full or "pop os" in distro_full:
            return "pop"

        return "linux"

    def _logo(self, os_release: dict[str, str]) -> list[str]:
        logos = {
            "linux": [
                "    ___",
                "   (.. |",
                "   (<> |",
                "  / __  \\",
                " ( /  \\ /|",
                "_/\\ __)/_)",
            ],
            "debian": [
                "  _____",
                " /  __ \\",
                "|  /    |",
                "|  \\___-",
                "-_",
                "  --_",
            ],
            "endeavour": [
                "      /\\",
                "    //  \\\\",
                "   //    \\ \\",
                " / /     _) )",
                "/_/___-- __-",
                " /____--",
            ],
            "arch": [
                "      /\\",
                "     /  \\",
                "    /\\   \\",
                "   /  __  \\",
                "  /  /  \\  \\",
                " /__/    \\__\\",
            ],
            "ubuntu": [
                "         _",
                "     ---(_) ",
                " _/  ---  \\",
                "(_) |   |",
                "  \\  --- _/",
                "     ---(_)",
            ],
            "fedora": [
                "      _____",
                "     /   __)",
                "     |  /",
                "  ___|  |__",
                " /  _    _/",
                " |_/ |__/",
            ],
            "alpine": [
                "    /\\ /\\",
                "   / /  \\",
                "  / /    \\",
                " / / /\\   \\",
                "/_/ /  \\___\\",
                "   /_/",
            ],
            "void": [
                "    _______",
                " _ \\______ -",
                "| \\  ___  \\ |",
                "| | /   \\ | |",
                "| | \\___/ | |",
                " \\_\\______/ ",
            ],
            "nixos": [
                "  \\\\  \\\\ //",
                " ==\\\\__\\\\/ /",
                "   //   \\\\",
                "==//     //==",
                " //\\___//",
                "//  // \\\\",
            ],
            "gentoo": [
                " _-----_",
                "(       \\",
                "\\    0   \\",
                " \\        )",
                " /      _/",
                "(     _-",
                "\\____-",
            ],
            "manjaro": [
                "|||||||||",
                "|||||||||",
                "||||",
                "||||  |||",
                "||||  |||",
                "||||  |||",
            ],
            "opensuse": [
                "  _______",
                "__|   __ \\",
                "     / .\\ \\",
                "     \\__/ |",
                "   _______|",
                "   \\_______",
            ],
            "mint": [
                " __________",
                "|_          \\",
                "  | | _____ |",
                "  | | | | | |",
                "  | \\_____/ |",
                "  \\________/",
            ],
            "pop": [
                "  ______",
                " / ____ \\",
                "| |    | |",
                "| |____| |",
                " \\______/ ",
                "  POP!_OS",
            ],
            "freebsd": [
                "  /\\,-'''''-,/\\",
                "  \\_)       (_/",
                "  |           |",
                "  |           |",
                "   ;         ;",
                "    '-_____-'",
            ],
        }
        return logos.get(self._logo_key(os_release), logos["linux"])

    def _build_output(self) -> str:
        os_release = self._os_release()
        username = os.environ.get("USER") or "user"
        hostname = os.uname().nodename
        logo = self._logo(os_release)

        info = [
            f"   {self._compact_identity(username, hostname)}",
            f"os     {self._compact_os(os_release)}",
            f"host   {self._compact_host(self._get_host())}",
            f"kernel {self._compact_kernel(os.uname().release)}",
            f"uptime {self._get_uptime()}",
            f"pkgs   {self._get_packages()}",
            f"memory {self._get_memory()}",
        ]

        rows = max(len(logo), len(info))
        output = []
        logo_width = max(len(line) for line in logo) if logo else 0

        for index in range(rows):
            left = logo[index].ljust(logo_width) if index < len(logo) else " " * logo_width
            right = info[index] if index < len(info) else ""
            output.append(f"{left}  {right}".rstrip())

        return "\n".join(output)

    @staticmethod
    def _escape_pre(text: str) -> str:
        return escape(text)

    async def _answer_pre(self, message: Message, text: str):
        html = f"<blockquote><pre>&#8203;{self._escape_pre(text)}</pre></blockquote>"

        if message.out and not message.via_bot_id and not message.fwd_from:
            return await message.edit(html, parse_mode="html", link_preview=False)

        return await message.respond(
            html,
            parse_mode="html",
            reply_to=getattr(message, "reply_to_msg_id", None),
            link_preview=False,
        )

    @loader.command(ru_doc="- показать краткую информацию о системе")
    async def pfetchcmd(self, message: Message):
        """- показать краткую информацию о системе"""
        pfetch = self._find_pfetch()

        if not pfetch:
            await utils.answer(message, self.strings("installing"))
            try:
                pfetch = await self._install_pfetch(message)
            except RuntimeError as e:
                return await utils.answer(
                    message,
                    self.strings("install_error").format(utils.escape_html(str(e))),
                )

        output = self._build_output()
        await self._answer_pre(message, output)
