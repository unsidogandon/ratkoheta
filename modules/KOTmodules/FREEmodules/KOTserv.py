# meta developer: @kotcheat

import contextlib
import os
import platform
import sys
import random
import psutil
from telethon.tl.types import Message
from .. import loader, utils

def bytes_to_megabytes(b: int) -> int:
    return round(b / 1024 / 1024, 1)

@loader.tds
class KOTservMod(loader.Module):
    """Показывает информацию о сервере с интересным конфигом (by @kotcheat)"""

    strings = {
        "name": "KOTserv",
        "loading": "<emoji document_id=5373310679241466020>🌀</emoji> <b>Почти готово...</b>",
        "servinfo": (
            "<blockquote><emoji document_id=5172685498350567983>💻</emoji> <b>Информация о сервере:</b></blockquote>\n\n"
            "<blockquote><emoji document_id=5172869086727635492>💻</emoji> <b>CPU: {cpu} ядер(-ро) {cpu_load}%</b>\n"
            "<emoji document_id=5174693704799093859>💻</emoji> <b>RAM: {ram} / {ram_load_mb}MB ({ram_load}%)</blockquote></b>\n\n"
            "<blockquote><emoji document_id=5172494668658639634>💻</emoji> <b>Kernel:</b> {kernel}\n"
            "<emoji document_id=5172474181664637769>💻</emoji> <b>Arch:</b> {arch}\n"
            "<emoji document_id=5172622400986022463>💻</emoji> <b>OS:</b> {os}</blockquote>\n\n"
            "<blockquote><emoji document_id=5174695263872221947>💻</emoji> <b>Python:</b> {python}</blockquote>"
        ),
        "_cls_doc": "Показывает информацию о сервере с возможностью фейковых значений",
        "_cfg_use_fake": "Использовать фейковые значения вместо реальных",
        "_cfg_fake_cpu": (
            "Количество ядер CPU. Примеры: 2 (бюджетный VPS), 4 (средний VPS), "
            "6 (хороший VPS), 8 (мощный сервер), 12 (топовый VPS), 16 (dedicated server), "
            "24 (enterprise server), 32 (high-end server), 48 (datacenter), 64 (supercomputer), "
            "96 (AMD EPYC), 128 (максимальные конфиги)"
        ),
        "_cfg_fake_cpu_load_min": (
            "Минимальная загрузка CPU в %. Примеры: 5 (почти idle), 10 (легкая нагрузка), "
            "15 (фоновые задачи), 20 (нормальная работа), 25 (активные процессы), "
            "30 (средняя нагрузка), 35 (повышенная активность), 40 (высокая нагрузка), "
            "45 (интенсивная работа), 50 (половина мощности), 60 (heavy load), 70 (перегруз)"
        ),
        "_cfg_fake_cpu_load_max": (
            "Максимальная загрузка CPU в %. Примеры: 20 (спокойный режим), 30 (легкая работа), "
            "40 (нормальная нагрузка), 50 (средняя), 60 (активная работа), 70 (высокая нагрузка), "
            "75 (интенсивная), 80 (очень высокая), 85 (критическая), 90 (перегруз), "
            "95 (максимум), 98 (предел)"
        ),
        "_cfg_fake_ram": (
            "Использованная RAM в MB. Примеры: 512 (минимальный VPS), 1024 (1GB - легкие боты), "
            "2048 (2GB - средние задачи), 3072 (3GB), 4096 (4GB - стандарт), 6144 (6GB), "
            "8192 (8GB - хороший сервер), 12288 (12GB), 16384 (16GB - мощный), 24576 (24GB), "
            "32768 (32GB - топ), 49152 (48GB - enterprise)"
        ),
        "_cfg_fake_ram_total": (
            "Общая RAM в MB. Примеры: 1024 (1GB VPS), 2048 (2GB VPS), 4096 (4GB - базовый), "
            "8192 (8GB - стандарт), 16384 (16GB - хороший), 24576 (24GB), 32768 (32GB - мощный), "
            "49152 (48GB - топ), 65536 (64GB - pro), 98304 (96GB - enterprise), "
            "131072 (128GB - datacenter), 262144 (256GB - supercomputer)"
        ),
        "_cfg_fake_ram_load_min": (
            "Минимальная загрузка RAM в %. Примеры: 10 (почти пусто), 15 (минимум), "
            "20 (легкая нагрузка), 25 (фоновые процессы), 30 (нормально), 35 (стандарт), "
            "40 (средняя загрузка), 45 (активная работа), 50 (половина), 55 (выше среднего), "
            "60 (высокая), 65 (очень высокая)"
        ),
        "_cfg_fake_ram_load_max": (
            "Максимальная загрузка RAM в %. Примеры: 30 (безопасная зона), 40 (комфортно), "
            "50 (нормально), 60 (активно), 65 (выше среднего), 70 (высокая), 75 (напряженно), "
            "80 (очень высокая), 85 (критично), 90 (перегруз), 95 (максимум), 98 (предел)"
        ),
        "_cfg_fake_kernel": (
            "Версия ядра. Примеры: 5.4.0-42-generic (Ubuntu 20.04), 5.10.0-21-amd64 (Debian 11), "
            "5.15.0-94-generic (Ubuntu 22.04), 6.1.0-18-amd64 (Debian 12), 6.2.0-39-generic (Ubuntu 23.04), "
            "6.5.0-14-generic (Ubuntu 23.10), 4.18.0-477.el8.x86_64 (CentOS 8), 5.14.0-362.el9.x86_64 (RHEL 9), "
            "6.17.4-arch2-1 (Arch Linux), 6.7.0-0.rc8.54.fc40.x86_64 (Fedora), "
            "5.19.0-32-generic (custom build), 6.8.1-1-MANJARO (Manjaro)"
        ),
        "_cfg_fake_arch": (
            "Архитектура. Примеры: 64bit (стандарт), x86_64 (альтернативное название), "
            "amd64 (Debian/Ubuntu стиль), aarch64 (ARM 64-bit), arm64 (альтернатива ARM), "
            "32bit (старые системы), i686 (32-bit Intel), armv7l (ARM 32-bit), "
            "ppc64le (PowerPC), s390x (IBM mainframe), riscv64 (RISC-V), mips64 (MIPS)"
        ),
        "_cfg_fake_os": (
            "Операционная система. Примеры: Ubuntu 20.04.6 LTS (Focal Fossa), "
            "Ubuntu 22.04.3 LTS (Jammy Jellyfish), Ubuntu 23.10 (Mantic Minotaur), "
            "Debian GNU/Linux 11 (bullseye), Debian GNU/Linux 12 (bookworm), "
            "CentOS Linux 8.5.2111, Red Hat Enterprise Linux 9.3, Fedora Linux 39, "
            "Arch Linux (rolling), openSUSE Leap 15.5, Alpine Linux v3.19, "
            "Rocky Linux 9.3 (Blue Onyx), AlmaLinux 9.3 (Shamrock Pampas Cat)"
        ),
        "_cfg_fake_python": (
            "Версия Python. Примеры: 3.8.10 (Ubuntu 20.04 default), 3.9.18 (стабильная), "
            "3.10.12 (Ubuntu 22.04 default), 3.11.5 (популярная), 3.11.8 (актуальная), "
            "3.12.0 (новая), 3.12.1 (свежая), 3.12.2 (последняя стабильная), "
            "3.13.0a3 (alpha), 3.7.17 (устаревшая), 3.6.15 (legacy), 3.13.0b1 (beta)"
        ),
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "use_fake",
                False,
                lambda: self.strings("_cfg_use_fake"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "fake_cpu",
                8,
                lambda: self.strings("_cfg_fake_cpu"),
                validator=loader.validators.Integer(minimum=1),
            ),
            loader.ConfigValue(
                "fake_cpu_load_min",
                15,
                lambda: self.strings("_cfg_fake_cpu_load_min"),
                validator=loader.validators.Integer(minimum=0, maximum=100),
            ),
            loader.ConfigValue(
                "fake_cpu_load_max",
                45,
                lambda: self.strings("_cfg_fake_cpu_load_max"),
                validator=loader.validators.Integer(minimum=0, maximum=100),
            ),
            loader.ConfigValue(
                "fake_ram",
                4096,
                lambda: self.strings("_cfg_fake_ram"),
                validator=loader.validators.Integer(minimum=1),
            ),
            loader.ConfigValue(
                "fake_ram_total",
                16384,
                lambda: self.strings("_cfg_fake_ram_total"),
                validator=loader.validators.Integer(minimum=1),
            ),
            loader.ConfigValue(
                "fake_ram_load_min",
                25,
                lambda: self.strings("_cfg_fake_ram_load_min"),
                validator=loader.validators.Integer(minimum=0, maximum=100),
            ),
            loader.ConfigValue(
                "fake_ram_load_max",
                50,
                lambda: self.strings("_cfg_fake_ram_load_max"),
                validator=loader.validators.Integer(minimum=0, maximum=100),
            ),
            loader.ConfigValue(
                "fake_kernel",
                "5.15.0-94-generic",
                lambda: self.strings("_cfg_fake_kernel"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "fake_arch",
                "64bit",
                lambda: self.strings("_cfg_fake_arch"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "fake_os",
                "Ubuntu 22.04.3 LTS",
                lambda: self.strings("_cfg_fake_os"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "fake_python",
                "3.11.5",
                lambda: self.strings("_cfg_fake_python"),
                validator=loader.validators.String(),
            ),
        )

    @loader.command(ru_doc="Показать информацию о сервере")
    async def serv(self, message: Message):
        """Показать информацию о сервере"""
        message = await utils.answer(message, self.strings("loading"))

        if self.config["use_fake"]:
            inf = self._get_fake_info()
        else:
            inf = self._get_real_info()

        await utils.answer(message, self.strings("servinfo").format(**inf))

    def _get_fake_info(self):
        cpu_load = round(random.uniform(
            self.config["fake_cpu_load_min"],
            self.config["fake_cpu_load_max"]
        ), 1)
        
        ram_load = round(random.uniform(
            self.config["fake_ram_load_min"],
            self.config["fake_ram_load_max"]
        ), 1)
        
        ram_used = round(self.config["fake_ram_total"] * ram_load / 100, 1)

        return {
            "cpu": self.config["fake_cpu"],
            "cpu_load": cpu_load,
            "ram": ram_used,
            "ram_load_mb": self.config["fake_ram_total"],
            "ram_load": ram_load,
            "kernel": self.config["fake_kernel"],
            "arch": self.config["fake_arch"],
            "os": self.config["fake_os"],
            "python": self.config["fake_python"],
        }

    def _get_real_info(self):
        inf = {
            "cpu": "n/a",
            "cpu_load": "n/a",
            "ram": "n/a",
            "ram_load_mb": "n/a",
            "ram_load": "n/a",
            "kernel": "n/a",
            "arch": "n/a",
            "os": "n/a",
            "python": "n/a",
        }

        with contextlib.suppress(Exception):
            inf["cpu"] = psutil.cpu_count(logical=True)

        with contextlib.suppress(Exception):
            inf["cpu_load"] = psutil.cpu_percent()

        with contextlib.suppress(Exception):
            inf["ram"] = bytes_to_megabytes(
                psutil.virtual_memory().total - psutil.virtual_memory().available
            )

        with contextlib.suppress(Exception):
            inf["ram_load_mb"] = bytes_to_megabytes(psutil.virtual_memory().total)

        with contextlib.suppress(Exception):
            inf["ram_load"] = psutil.virtual_memory().percent

        with contextlib.suppress(Exception):
            inf["kernel"] = utils.escape_html(platform.release())

        with contextlib.suppress(Exception):
            inf["arch"] = utils.escape_html(platform.architecture()[0])

        with contextlib.suppress(Exception):
            system = os.popen("cat /etc/*release").read()
            b = system.find('DISTRIB_DESCRIPTION="') + 21
            system = system[b : system.find('"', b)]
            inf["os"] = utils.escape_html(system)

        with contextlib.suppress(Exception):
            inf["python"] = (
                f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            )

        return inf