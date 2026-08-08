# ====================================================================================================================
#   ██████╗  ██████╗ ██╗   ██╗███╗   ███╗ ██████╗ ██████╗ ██╗   ██╗██╗     ███████╗███████╗
#  ██╔════╝ ██╔═══██╗╚██╗ ██╔╝████╗ ████║██╔═══██╗██╔══██╗██║   ██║██║     ██╔════╝██╔════╝
#  ██║  ███╗██║   ██║ ╚████╔╝ ██╔████╔██║██║   ██║██║  ██║██║   ██║██║     █████╗  ███████╗
#  ██║   ██║██║   ██║  ╚██╔╝  ██║╚██╔╝██║██║   ██║██║  ██║██║   ██║██║     ██╔══╝  ╚════██║
#  ╚██████╔╝╚██████╔╝   ██║   ██║ ╚═╝ ██║╚██████╔╝██████╔╝╚██████╔╝███████╗███████╗███████║
#   ╚═════╝  ╚═════╝    ╚═╝   ╚═╝     ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚══════╝
#
#   OFFICIAL USERNAMES: @goymodules | @samsepi0l_ovf
#   MODULE: doom
# ====================================================================================================================

# requires: herokutl
# meta developer: @GoyModules
# meta tags: game, doom, shooter, inline, entertainment, offline, игра, дум, шутер, инлайн, развлечение, офлайн
# authors: @goymodules
# Description: Inline DOOM mini-game module.
# meta banner: https://raw.githubusercontent.com/sepiol026-wq/goypulse/main/assets/doom.png

"""Inline DOOM with waves, boss, shop, profile and daily run."""

__version__ = (1, 4, 0)

import asyncio
import math
import random
import re
import time
import traceback
from herokutl.types import Message
from .. import loader, utils


@loader.tds
class Doom(loader.Module):
    """Inline DOOM mini-game."""

    strings = {
        "name": "Doom",
        "_cls_doc": "Inline DOOM mini-game.",
    }
    strings_ru = {"_cls_doc": "Мини-игра DOOM в инлайне."}
    strings_uk = {"_cls_doc": "Міні-гра DOOM в інлайні."}
    strings_de = {"_cls_doc": "DOOM-Minispiel im Inline-Modus."}
    strings_jp = {"_cls_doc": "インラインDOOMミニゲーム。"}
    strings_neofit = {"_cls_doc": "Дум-модуль с меню и волнами."}
    strings_tiktok = {"_cls_doc": "DOOM модуль: волны, босс, шоп."}
    strings_leet = {"_cls_doc": "1nl1n3 D00M m1n1-g4m3."}
    strings_uwu = {"_cls_doc": "inline doom mini gami uwu."}
    strings_ru = {**strings, **locals().get("strings_ru", {})}
    strings_uk = {**strings, **locals().get("strings_ua", {}), **locals().get("strings_uk", {})}
    strings_de = {**strings, **locals().get("strings_de", {})}
    strings_jp = {**strings, **locals().get("strings_jp", {})}
    strings_neofit = {**strings, **locals().get("strings_neofit", {})}
    strings_tiktok = {**strings, **locals().get("strings_tiktok", {})}
    strings_leet = {**strings, **locals().get("strings_leet", {})}
    strings_uwu = {**strings, **locals().get("strings_uwu", {})}

    def __init__(self):
        self.sessions = {}
        self.game_config = {
            "scr_w": 24,
            "scr_h": 12,
            "fov": math.pi / 3,
            "depth": 10.0,
            "shades": [" ", "░", "▒", "▓", "█"],
        }
        self.base_map = [
            "##################",
            "#....A...........#",
            "#.####.E..####.R.#",
            "#.#..#....#..#...#",
            "#.#..######..#.A.#",
            "#........E...H...#",
            "######...........#",
            "#...A........D...#",
            "#.######...#..S..#",
            "#......#...#..H..#",
            "#.####.#.E.#.....#",
            "#..H..............#",
            "##################",
        ]
        self.map_h = len(self.base_map)
        self.map_w = len(self.base_map[0])

    async def client_ready(self, client, db):
        self.client = client
        self.db = db

    def _today_key(self):
        return time.strftime("%Y-%m-%d", time.localtime())

    def _settings(self):
        return self.db.get(
            "Doom",
            "settings",
            {
                "difficulty": "normal",
                "autosave": 15,
                "lang": "ru",
            },
        )

    def _save_settings(self, value):
        self.db.set("Doom", "settings", value)

    def _profile(self):
        return self.db.get(
            "Doom",
            "profile",
            {
                "games": 0,
                "kills": 0,
                "deaths": 0,
                "best_score": 0,
                "shots": 0,
                "hits": 0,
                "daily_best": 0,
                "daily_last": "",
                "ach": [],
            },
        )

    def _save_profile(self, value):
        self.db.set("Doom", "profile", value)

    def _lang(self, st=None):
        if st and st.get("settings", {}).get("lang"):
            return st["settings"]["lang"]
        return self._settings().get("lang", "ru")

    def _t(self, key, st=None, **fmt):
        ru = {
            "menu": "📛 <b>DOOM</b>\n\nВыбери действие:",
            "new": "🟢 Новая игра",
            "cont": "🟡 Продолжить",
            "profile": "🏆 Профиль",
            "settings": "⚙️ Настройки",
            "help": "📖 Помощь",
            "daily": "☣️ Daily Run",
            "back": "↩️ Назад",
            "exit": "🚪 Выход",
            "shop": "🛒 Магазин",
            "dead": "💀 <b>ВЫ ПОГИБЛИ</b>\n\nСчет: {score}",
            "loaded": "Игра загружена.",
            "nosave": "Нет сохранений!",
            "saved": "Сохранено.",
            "autosaved": "Автосохранение.",
            "welcome": "Добро пожаловать в Ад.",
            "hit": "🔥 Монстр уничтожен!",
            "hit_boss": "🔥 Босс уничтожен!",
            "wall": "Упёрлись в стену.",
            "noammo": "Клик! Нет патронов.",
            "reload": "Перезарядка +{n}",
            "noreload": "Нет патронов в запасе.",
            "med": "Аптечка использована.",
            "nomed": "Нет аптечек.",
            "enemy_hit": "Удар вблизи прошёл.",
            "enemy_miss": "Рядом нет цели.",
            "enemy_attack": "Враг атакует! -{n} HP",
            "pickup_ammo": "Патроны +6",
            "pickup_hp": "Лечение +20 HP",
            "pickup_armor": "Броня +15",
            "pickup_secret": "Секретка: патроны +8, аптечка +1",
            "wave_start": "Волна {w}",
            "wave_boss": "Босс-волна {w}",
            "daily_done": "Daily Run уже сыгран сегодня.",
            "daily_start": "Daily Run начат.",
            "shop_title": "🛒 <b>Магазин</b>\nКредиты: <b>{c}</b>",
            "buy_ok": "Куплено: {name}",
            "buy_no": "Не хватает кредитов.",
            "buy_max": "Лимит апгрейда.",
            "p_text": "<b>Профиль</b>\nИгр: <b>{games}</b>\nКиллов: <b>{kills}</b>\nСмертей: <b>{deaths}</b>\nЛучший счёт: <b>{best}</b>\nТочность: <b>{acc}%</b>\nDaily best: <b>{daily}</b>\nАчивки: <b>{ach}</b>",
            "help_text": "<b>DOOM</b>\n\nP — ты\nM — враг\nB — босс\nA — патроны\nH — хилка\nR — броня\nS — секретка\n\nЗапуск: <code>{pref}doom</code>",
            "set_text": "<b>Настройки</b>\nСложность: <b>{d}</b>\nАвтосейв: <b>{a}s</b>\nЯзык: <b>{l}</b>",
            "set_ok": "Настройки обновлены.",
            "start_pick": "Выбери сложность:",
            "ach_unlock": "🏆 Ачивка: {name}",
            "inline_fail": "Не удалось открыть inline-меню. Проверь inline-бота.",
        }
        en = {
            "menu": "📛 <b>DOOM</b>\n\nChoose action:",
            "new": "🟢 New game",
            "cont": "🟡 Continue",
            "profile": "🏆 Profile",
            "settings": "⚙️ Settings",
            "help": "📖 Help",
            "daily": "☣️ Daily Run",
            "back": "↩️ Back",
            "exit": "🚪 Exit",
            "shop": "🛒 Shop",
            "dead": "💀 <b>YOU DIED</b>\n\nScore: {score}",
            "loaded": "Game loaded.",
            "nosave": "No save found!",
            "saved": "Saved.",
            "autosaved": "Autosaved.",
            "welcome": "Welcome to Hell.",
            "hit": "🔥 Enemy down!",
            "hit_boss": "🔥 Boss down!",
            "wall": "Wall hit.",
            "noammo": "Click! No ammo.",
            "reload": "Reload +{n}",
            "noreload": "No reserve ammo.",
            "med": "Medkit used.",
            "nomed": "No medkits.",
            "enemy_hit": "Melee hit.",
            "enemy_miss": "No enemy nearby.",
            "enemy_attack": "Enemy attacks! -{n} HP",
            "pickup_ammo": "Ammo +6",
            "pickup_hp": "Heal +20 HP",
            "pickup_armor": "Armor +15",
            "pickup_secret": "Secret: ammo +8, medkit +1",
            "wave_start": "Wave {w}",
            "wave_boss": "Boss wave {w}",
            "daily_done": "Daily Run already played today.",
            "daily_start": "Daily Run started.",
            "shop_title": "🛒 <b>Shop</b>\nCredits: <b>{c}</b>",
            "buy_ok": "Bought: {name}",
            "buy_no": "Not enough credits.",
            "buy_max": "Upgrade cap reached.",
            "p_text": "<b>Profile</b>\nGames: <b>{games}</b>\nKills: <b>{kills}</b>\nDeaths: <b>{deaths}</b>\nBest score: <b>{best}</b>\nAccuracy: <b>{acc}%</b>\nDaily best: <b>{daily}</b>\nAchievements: <b>{ach}</b>",
            "help_text": "<b>DOOM</b>\n\nP — player\nM — enemy\nB — boss\nA — ammo\nH — heal\nR — armor\nS — secret\n\nStart: <code>{pref}doom</code>",
            "set_text": "<b>Settings</b>\nDifficulty: <b>{d}</b>\nAutosave: <b>{a}s</b>\nLang: <b>{l}</b>",
            "set_ok": "Settings updated.",
            "start_pick": "Pick difficulty:",
            "ach_unlock": "🏆 Achievement: {name}",
            "inline_fail": "Inline menu failed. Check inline bot.",
        }
        loc = en if self._lang(st) == "en" else ru
        return (loc.get(key) or ru.get(key) or key).format(**fmt)

    def _main_buttons(self):
        return [
            [{"text": self._t("new"), "callback": self.action_new_menu}],
            [{"text": self._t("cont"), "callback": self.action_cont}, {"text": self._t("daily"), "callback": self.action_daily}],
            [{"text": self._t("profile"), "callback": self.action_profile}, {"text": self._t("settings"), "callback": self.action_settings}],
            [{"text": self._t("help"), "callback": self.action_help}],
        ]

    def _difficulty_table(self):
        return {
            "easy": {"hp": 120, "ammo": 18, "enemy_dmg": 6, "ai": 0.95},
            "normal": {"hp": 100, "ammo": 14, "enemy_dmg": 8, "ai": 0.75},
            "hard": {"hp": 90, "ammo": 12, "enemy_dmg": 10, "ai": 0.62},
            "nightmare": {"hp": 82, "ammo": 10, "enemy_dmg": 12, "ai": 0.5},
        }

    def _new_map(self):
        m = []
        for row in self.base_map:
            m.append(list(row.replace(".", " ")))
        return m

    async def safe_edit(self, call, text, reply_markup):
        try:
            await call.edit(text, reply_markup=reply_markup)
            return True
        except Exception as e:
            wait_s = getattr(e, "seconds", 0) or getattr(e, "value", 0)
            if not wait_s:
                m = re.search(r"(\d+)\s*seconds", str(e))
                if m:
                    wait_s = int(m.group(1))
            if wait_s:
                await asyncio.sleep(wait_s + 0.1)
                try:
                    await call.edit(text, reply_markup=reply_markup)
                    return True
                except Exception:
                    return False
            return False

    def _unlock(self, st, name):
        if name not in st["ach"]:
            st["ach"].add(name)
            st["log"] = self._t("ach_unlock", st, name=name)
            st["dirty"] = True

    def _spawn_wave(self, st, wave):
        st["wave"] = wave
        for y in range(self.map_h):
            for x in range(self.map_w):
                if st["map"][y][x] in ["E", "D"]:
                    st["map"][y][x] = " "

        spots = []
        px, py = int(st["x"]), int(st["y"])
        for y in range(1, self.map_h - 1):
            for x in range(1, self.map_w - 1):
                if st["map"][y][x] != " ":
                    continue
                if abs(px - x) + abs(py - y) < 6:
                    continue
                spots.append((x, y))
        random.shuffle(spots)

        enemies = min(2 + wave, 12)
        boss = wave % 5 == 0
        used = 0
        for x, y in spots:
            if used >= enemies:
                break
            if boss and used == 0:
                st["map"][y][x] = "D"
            else:
                st["map"][y][x] = "E"
            used += 1

        st["log"] = self._t("wave_boss" if boss else "wave_start", st, w=wave)
        st["dirty"] = True

    @loader.command(
        ru_doc="Справка по игре DOOM",
        uk_doc="Довідка по грі DOOM",
        de_doc="Hilfe zum DOOM-Spiel",
        jp_doc="DOOMゲームのヘルプ",
        neofit_doc="Справка по doom",
        tiktok_doc="Гайд по doom-модулю",
        leet_doc="D00M h3lp",
        uwu_doc="DOOM hewp",
    )
    async def hdoomcmd(self, message: Message):
        pref = getattr(self, "get_prefix", lambda: ".")()
        await utils.answer(message, self._t("help_text", pref=pref))

    @loader.command(
        ru_doc="Запуск меню DOOM",
        uk_doc="Запуск меню DOOM",
        de_doc="DOOM-Menü starten",
        jp_doc="DOOMメニューを開く",
        neofit_doc="Запуск doom меню",
        tiktok_doc="Открыть doom меню",
        leet_doc="0p3n d00m m3nu",
        uwu_doc="open doom menu",
    )
    async def doomcmd(self, message: Message):
        try:
            await self.inline.form(
                text=self._t("menu"),
                message=message,
                reply_markup=self._main_buttons(),
            )
        except Exception:
            await utils.answer(message, self._t("inline_fail"))

    def render_3d_frame(self, state):
        w = self.game_config["scr_w"]
        h = self.game_config["scr_h"]
        fov = self.game_config["fov"]
        depth = self.game_config["depth"]
        shades = self.game_config["shades"]

        px, py, pa = state["x"], state["y"], state["a"]
        screen = []

        for x in range(w):
            ray_a = (pa - fov / 2.0) + (x / float(w)) * fov
            dist_w = 0.0
            hit_w = False
            cell_hit = " "

            eye_x = math.sin(ray_a)
            eye_y = math.cos(ray_a)

            while not hit_w and dist_w < depth:
                dist_w += 0.1
                test_x = int(px + eye_x * dist_w)
                test_y = int(py + eye_y * dist_w)

                if test_x < 0 or test_x >= self.map_w or test_y < 0 or test_y >= self.map_h:
                    hit_w = True
                    dist_w = depth
                else:
                    cell = state["map"][test_y][test_x]
                    if cell in ["#", "E", "D", "A", "H", "R", "S"]:
                        hit_w = True
                        cell_hit = cell

            ceil = float(h / 2.0) - h / max(dist_w, 0.01)
            floor = h - ceil

            shade = " "
            if cell_hit not in ["E", "D", "A", "H", "R", "S"]:
                if dist_w <= depth / 5.0:
                    shade = shades[4]
                elif dist_w <= depth / 4.0:
                    shade = shades[3]
                elif dist_w <= depth / 3.0:
                    shade = shades[2]
                elif dist_w <= depth / 1.5:
                    shade = shades[1]
                elif dist_w < depth:
                    shade = shades[0]

            col = []
            for y in range(h):
                if y <= ceil:
                    col.append(" ")
                elif ceil < y <= floor:
                    if cell_hit == "E":
                        col.append("👾")
                    elif cell_hit == "D":
                        col.append("💀")
                    elif cell_hit == "A":
                        col.append("A" if y == int(floor) else " ")
                    elif cell_hit == "H":
                        col.append("+" if y == int(floor) else " ")
                    elif cell_hit == "R":
                        col.append("R" if y == int(floor) else " ")
                    elif cell_hit == "S":
                        col.append("$" if y == int(floor) else " ")
                    else:
                        col.append(shade)
                else:
                    b = 1.0 - ((float(y) - h / 2.0) / (h / 2.0))
                    if b < 0.25:
                        col.append(".")
                    elif b < 0.5:
                        col.append("-")
                    elif b < 0.75:
                        col.append("=")
                    else:
                        col.append(" ")
            screen.append(col)

        out = []
        for y in range(h):
            row = "".join([screen[x][y] for x in range(w)])
            out.append(row)
        cx = w // 2
        cy = h // 2
        if 0 <= cy < len(out) and 0 <= cx < len(out[cy]):
            r = list(out[cy])
            r[cx] = "✚"
            out[cy] = "".join(r)
        return "\n".join(out)

    def get_mini_map(self, state):
        px, py = int(state["x"]), int(state["y"])
        m = []
        for y, row in enumerate(state["map"]):
            r = ["." if c == " " else c for c in row]
            r = ["M" if c == "E" else c for c in r]
            if y == py and 0 <= px < len(r):
                r[px] = "P"
            m.append("".join(r))
        return "\n".join(m)

    def _hud(self, st):
        frame = self.render_3d_frame(st)
        mmap = self.get_mini_map(st)
        acc = round((st["hits"] / st["shots"] * 100.0), 1) if st["shots"] else 0.0
        return (
            f"📍 <b>Mini-Map</b>:\n"
            f"<pre>{mmap}</pre>\n"
            f"📟 <b>Action</b>:\n"
            f"<pre>{frame}</pre>\n"
            f"🔋 HP: <b>{st['hp']}</b> | AR: <b>{st['armor']}</b> | 📦 Ammo: <b>{st['ammo']}</b>/<b>{st['reserve']}</b> | 🩹 <b>{st['medkits']}</b>\n"
            f"📛 Kills: <b>{st['score']}</b> | 🌊 Wave: <b>{st['wave']}</b> | 💳 Credits: <b>{st['credits']}</b> | 🎯 {acc}%\n"
            f"💬 <i>{st['log']}</i>"
        )

    async def do_render(self, call, st):
        if st["hp"] <= 0:
            st["running"] = False
            p = self._profile()
            p["deaths"] += 1
            p["kills"] += st["score"]
            p["best_score"] = max(p["best_score"], st["score"])
            p["shots"] += st["shots"]
            p["hits"] += st["hits"]
            all_ach = set(p.get("ach", [])) | st["ach"]
            p["ach"] = sorted(all_ach)
            if st.get("daily"):
                p["daily_best"] = max(p.get("daily_best", 0), st["score"])
                p["daily_last"] = self._today_key()
            self._save_profile(p)

            dead_text = self._t("dead", st, score=st["score"])
            btn = [
                [{"text": self._t("new", st), "callback": self.action_new_menu}],
                [{"text": self._t("back", st), "callback": self.action_main_menu}],
            ]
            await self.safe_edit(call, dead_text, btn)
            return

        hud = self._hud(st)
        btn = [
            [{"text": "🔄 L", "callback": self.action_rot_l}, {"text": "⬆️", "callback": self.action_fw}, {"text": "🔄 R", "callback": self.action_rot_r}],
            [{"text": "⬅️", "callback": self.action_m_l}, {"text": "💥", "callback": self.action_shoot}, {"text": "➡️", "callback": self.action_m_r}],
            [{"text": "🤜", "callback": self.action_melee}, {"text": "🔁", "callback": self.action_reload}, {"text": "🩹", "callback": self.action_medkit}],
            [{"text": self._t("shop", st), "callback": self.action_shop}, {"text": "💾", "callback": self.action_save}, {"text": self._t("exit", st), "callback": self.action_exit}],
        ]

        if st.get("last_hud") == hud:
            return
        if await self.safe_edit(call, hud, btn):
            st["last_hud"] = hud

    def _snapshot(self, st):
        sv = st.copy()
        sv["ach"] = sorted(list(st["ach"]))
        return sv

    async def game_loop(self, call):
        user_id = "doom_user"
        while user_id in self.sessions and self.sessions[user_id].get("running"):
            st = self.sessions[user_id]
            now = time.time()
            dmg_base = self._difficulty_table()[st["difficulty"]]["enemy_dmg"]
            ai_tick = self._difficulty_table()[st["difficulty"]]["ai"]

            enemies_count = 0
            for row in st["map"]:
                for c in row:
                    if c in ["E", "D"]:
                        enemies_count += 1
            if enemies_count == 0:
                self._spawn_wave(st, st["wave"] + 1)
                if st["wave"] >= 3:
                    self._unlock(st, "Slayer III")
                if st["wave"] >= 7:
                    self._unlock(st, "Slayer VII")

            if now - st.get("last_ai", 0) > ai_tick:
                moved = False
                enemies = []
                for y in range(self.map_h):
                    for x in range(self.map_w):
                        if st["map"][y][x] in ["E", "D"]:
                            enemies.append((x, y, st["map"][y][x]))

                for ex, ey, et in enemies:
                    if st["map"][ey][ex] != et:
                        continue
                    dist = math.hypot(st["x"] - ex, st["y"] - ey)
                    if dist < 1.5:
                        dmg = dmg_base + (4 if et == "D" else 0)
                        if st["armor"] > 0:
                            blocked = min(st["armor"], int(dmg * 0.45))
                            st["armor"] -= blocked
                            dmg -= blocked
                        st["hp"] -= max(1, dmg)
                        st["log"] = self._t("enemy_attack", st, n=max(1, dmg))
                        moved = True
                    else:
                        dx = 1 if st["x"] > ex else (-1 if st["x"] < ex else 0)
                        dy = 1 if st["y"] > ey else (-1 if st["y"] < ey else 0)

                        options = [(ex + dx, ey), (ex, ey + dy), (ex + dx, ey + dy)]
                        random.shuffle(options)
                        for nx, ny in options:
                            if nx < 1 or nx >= self.map_w - 1 or ny < 1 or ny >= self.map_h - 1:
                                continue
                            if st["map"][ny][nx] != " ":
                                continue
                            st["map"][ey][ex] = " "
                            st["map"][ny][nx] = et
                            moved = True
                            break

                if moved:
                    st["dirty"] = True
                st["last_ai"] = now

            if now - st.get("last_save", 0) >= st["settings"]["autosave"]:
                sv = self._snapshot(st)
                sv["running"] = False
                self.db.set("Doom", "save", sv)
                st["last_save"] = now
                st["log"] = self._t("autosaved", st)
                st["dirty"] = True

            if st.get("dirty") and now - st.get("last_render", 0) >= 0.58:
                try:
                    await self.do_render(call, st)
                    st["last_render"] = time.time()
                    st["dirty"] = False
                except Exception:
                    pass

            await asyncio.sleep(0.12)

    def update_player(self, dx, dy, dr):
        if "doom_user" not in self.sessions:
            return
        st = self.sessions["doom_user"]
        if st["hp"] <= 0:
            return

        def is_walkable(x, y):
            r = 0.17
            points = [(x - r, y - r), (x + r, y - r), (x - r, y + r), (x + r, y + r)]
            for px, py in points:
                tx, ty = int(px), int(py)
                if tx < 0 or tx >= self.map_w or ty < 0 or ty >= self.map_h:
                    return False
                if st["map"][ty][tx] in ["#", "E", "D"]:
                    return False
            return True

        st["a"] += dr
        if dx or dy:
            old_x, old_y = st["x"], st["y"]
            nx = st["x"] + dx
            if is_walkable(nx, st["y"]):
                st["x"] = nx
            ny = st["y"] + dy
            if is_walkable(st["x"], ny):
                st["y"] = ny

            cell_x, cell_y = int(st["x"]), int(st["y"])
            if 0 <= cell_x < self.map_w and 0 <= cell_y < self.map_h:
                cell = st["map"][cell_y][cell_x]
                if cell == "A":
                    st["ammo"] += 6
                    st["reserve"] += 6
                    st["log"] = self._t("pickup_ammo", st)
                    st["map"][cell_y][cell_x] = " "
                elif cell == "H":
                    st["hp"] = min(st["max_hp"], st["hp"] + 20)
                    st["log"] = self._t("pickup_hp", st)
                    st["map"][cell_y][cell_x] = " "
                elif cell == "R":
                    st["armor"] = min(100, st["armor"] + 15)
                    st["log"] = self._t("pickup_armor", st)
                    st["map"][cell_y][cell_x] = " "
                elif cell == "S":
                    st["reserve"] += 8
                    st["medkits"] += 1
                    st["log"] = self._t("pickup_secret", st)
                    st["map"][cell_y][cell_x] = " "
            if old_x == st["x"] and old_y == st["y"] and (dx or dy):
                st["log"] = self._t("wall", st)
        st["dirty"] = True

    async def action_shoot(self, call):
        st = self.sessions.get("doom_user")
        if not st or st["hp"] <= 0:
            return

        if st["ammo"] <= 0:
            st["log"] = self._t("noammo", st)
            st["dirty"] = True
            return

        st["ammo"] -= 1
        st["shots"] += 1
        hit = False
        rx, ry = math.sin(st["a"]), math.cos(st["a"])
        d = 0.0

        while d < self.game_config["depth"]:
            d += 0.1
            fx, fy = st["x"] + rx * d, st["y"] + ry * d
            tx, ty = int(fx), int(fy)
            if 0 <= tx < self.map_w and 0 <= ty < self.map_h:
                cell = st["map"][ty][tx]
                if cell in ["E", "D"]:
                    st["map"][ty][tx] = " "
                    st["score"] += 3 if cell == "D" else 1
                    st["credits"] += 20 if cell == "D" else 7
                    st["hits"] += 1
                    st["log"] = self._t("hit_boss" if cell == "D" else "hit", st)
                    if st["score"] >= 30:
                        self._unlock(st, "Hell Cleaner")
                    if cell == "D":
                        self._unlock(st, "Boss Killer")
                    hit = True
                    break
                if cell == "#":
                    break
            else:
                break

        if not hit:
            st["log"] = "Выстрел в стену." if self._lang(st) != "en" else "Shot into wall."
        st["dirty"] = True

    async def action_melee(self, call):
        st = self.sessions.get("doom_user")
        if not st or st["hp"] <= 0:
            return
        best = None
        best_d = 999
        for y in range(self.map_h):
            for x in range(self.map_w):
                if st["map"][y][x] in ["E", "D"]:
                    d = math.hypot(st["x"] - x, st["y"] - y)
                    if d < best_d:
                        best = (x, y)
                        best_d = d
        if best and best_d < 1.4:
            x, y = best
            cell = st["map"][y][x]
            st["map"][y][x] = " "
            st["score"] += 2 if cell == "D" else 1
            st["credits"] += 16 if cell == "D" else 6
            st["hits"] += 1
            st["log"] = self._t("enemy_hit", st)
            if cell == "D":
                self._unlock(st, "Boss Punch")
        else:
            st["log"] = self._t("enemy_miss", st)
        st["dirty"] = True

    async def action_reload(self, call):
        st = self.sessions.get("doom_user")
        if not st or st["hp"] <= 0:
            return
        if st["reserve"] <= 0:
            st["log"] = self._t("noreload", st)
        else:
            need = st["mag_size"] - st["ammo"]
            add = min(need, st["reserve"]) if need > 0 else 0
            st["ammo"] += add
            st["reserve"] -= add
            st["log"] = self._t("reload", st, n=add)
        st["dirty"] = True

    async def action_medkit(self, call):
        st = self.sessions.get("doom_user")
        if not st or st["hp"] <= 0:
            return
        if st["medkits"] <= 0:
            st["log"] = self._t("nomed", st)
        else:
            st["medkits"] -= 1
            st["hp"] = min(st["max_hp"], st["hp"] + 30)
            st["log"] = self._t("med", st)
        st["dirty"] = True

    async def action_new_menu(self, call):
        btn = [
            [{"text": "🟢 EASY", "callback": self.action_new_easy}, {"text": "🟡 NORMAL", "callback": self.action_new_normal}],
            [{"text": "🟠 HARD", "callback": self.action_new_hard}, {"text": "🔴 NIGHTMARE", "callback": self.action_new_nightmare}],
            [{"text": self._t("back"), "callback": self.action_main_menu}],
        ]
        await self.safe_edit(call, self._t("start_pick"), btn)

    async def _start(self, call, difficulty, daily=False):
        try:
            settings = self._settings()
            settings["difficulty"] = difficulty
            self._save_settings(settings)

            dif = self._difficulty_table()[difficulty]
            m = self._new_map()
            p = self._profile()
            p["games"] += 1
            self._save_profile(p)

            st = {
                "x": 1.5,
                "y": 1.5,
                "a": 0.0,
                "hp": dif["hp"],
                "max_hp": dif["hp"],
                "armor": 0,
                "ammo": min(dif["ammo"], 12),
                "reserve": max(0, dif["ammo"] - 12),
                "mag_size": 12,
                "medkits": 1,
                "score": 0,
                "shots": 0,
                "hits": 0,
                "credits": 0,
                "wave": 0,
                "upg": {"dmg": 0, "hp": 0, "ammo": 0},
                "ach": set(p.get("ach", [])),
                "daily": daily,
                "difficulty": difficulty,
                "settings": settings,
                "log": self._t("daily_start") if daily else self._t("welcome"),
                "last_render": 0,
                "last_ai": 0,
                "last_save": 0,
                "dirty": True,
                "running": True,
                "map": m,
                "last_hud": "",
            }
            self._spawn_wave(st, 1)
            self.sessions["doom_user"] = st
            asyncio.create_task(self.game_loop(call))
        except Exception:
            err = traceback.format_exc()
            await self.safe_edit(call, f"<b>CRITICAL ERROR:</b>\n<pre>{err}</pre>", [])

    async def action_new_easy(self, call):
        await self._start(call, "easy")

    async def action_new_normal(self, call):
        await self._start(call, "normal")

    async def action_new_hard(self, call):
        await self._start(call, "hard")

    async def action_new_nightmare(self, call):
        await self._start(call, "nightmare")

    async def action_daily(self, call):
        p = self._profile()
        if p.get("daily_last") == self._today_key():
            await self.safe_edit(call, self._t("daily_done"), [[{"text": self._t("back"), "callback": self.action_main_menu}]])
            return
        await self._start(call, "hard", daily=True)

    async def action_cont(self, call):
        try:
            sv = self.db.get("Doom", "save", None)
            if sv:
                sv.setdefault("credits", 0)
                sv.setdefault("wave", 1)
                sv.setdefault("upg", {"dmg": 0, "hp": 0, "ammo": 0})
                sv.setdefault("ach", [])
                sv.setdefault("daily", False)
                sv["ach"] = set(sv.get("ach", []))
                sv["running"] = True
                sv["dirty"] = True
                sv["log"] = self._t("loaded", sv)
                sv["last_hud"] = ""
                sv["last_save"] = time.time()
                self.sessions["doom_user"] = sv
                asyncio.create_task(self.game_loop(call))
            else:
                await self.safe_edit(call, self._t("nosave"), [[{"text": self._t("back"), "callback": self.action_main_menu}]])
        except Exception:
            err = traceback.format_exc()
            await self.safe_edit(call, f"<b>CRITICAL ERROR:</b>\n<pre>{err}</pre>", [])

    async def action_shop(self, call):
        st = self.sessions.get("doom_user")
        if not st:
            return
        txt = self._t("shop_title", st, c=st["credits"])
        btn = [
            [{"text": "💥 Урон +12% (25)", "callback": self.action_buy_dmg}],
            [{"text": "🔋 +20 max HP (28)", "callback": self.action_buy_hp}],
            [{"text": "📦 +2 магазин (24)", "callback": self.action_buy_ammo}],
            [{"text": self._t("back", st), "callback": self.action_refresh}],
        ]
        if self._lang(st) == "en":
            btn[0][0]["text"] = "💥 Damage +12% (25)"
            btn[1][0]["text"] = "🔋 +20 max HP (28)"
            btn[2][0]["text"] = "📦 +2 mag size (24)"
        await self.safe_edit(call, txt, btn)

    async def _buy(self, call, key, cost, cap):
        st = self.sessions.get("doom_user")
        if not st:
            return
        lvl = st["upg"].get(key, 0)
        if lvl >= cap:
            st["log"] = self._t("buy_max", st)
            st["dirty"] = True
            await self.action_shop(call)
            return
        if st["credits"] < cost:
            st["log"] = self._t("buy_no", st)
            st["dirty"] = True
            await self.action_shop(call)
            return
        st["credits"] -= cost
        st["upg"][key] = lvl + 1
        if key == "dmg":
            st["log"] = self._t("buy_ok", st, name=("урон" if self._lang(st) != "en" else "damage"))
        elif key == "hp":
            st["max_hp"] += 20
            st["hp"] += 20
            st["log"] = self._t("buy_ok", st, name=("HP" if self._lang(st) != "en" else "HP"))
        elif key == "ammo":
            st["mag_size"] += 2
            st["ammo"] += 2
            st["log"] = self._t("buy_ok", st, name=("магазин" if self._lang(st) != "en" else "mag"))
        if sum(st["upg"].values()) >= 6:
            self._unlock(st, "Doom Engineer")
        st["dirty"] = True
        await self.action_shop(call)

    async def action_buy_dmg(self, call):
        await self._buy(call, "dmg", 25, 6)

    async def action_buy_hp(self, call):
        await self._buy(call, "hp", 28, 4)

    async def action_buy_ammo(self, call):
        await self._buy(call, "ammo", 24, 5)

    async def action_profile(self, call):
        p = self._profile()
        acc = round((p["hits"] / p["shots"] * 100.0), 1) if p["shots"] else 0.0
        txt = self._t(
            "p_text",
            games=p["games"],
            kills=p["kills"],
            deaths=p["deaths"],
            best=p["best_score"],
            acc=acc,
            daily=p.get("daily_best", 0),
            ach=len(p.get("ach", [])),
        )
        ach = p.get("ach", [])
        if ach:
            txt += "\n\n" + "\n".join([f"• {x}" for x in ach[-8:]])
        btn = [[{"text": self._t("back"), "callback": self.action_main_menu}]]
        if "doom_user" in self.sessions and self.sessions["doom_user"].get("running"):
            btn.insert(0, [{"text": "🕹️" if self._lang(self.sessions["doom_user"]) != "en" else "🕹️ In-game", "callback": self.action_refresh}])
        await self.safe_edit(call, txt, btn)

    async def action_settings(self, call):
        s = self._settings()
        txt = self._t("set_text", d=s["difficulty"], a=s["autosave"], l=s["lang"])
        btn = [
            [{"text": f"difficulty: {s['difficulty']}", "callback": self.action_cycle_diff}],
            [{"text": f"autosave: {s['autosave']}s", "callback": self.action_cycle_autosave}],
            [{"text": f"lang: {s['lang']}", "callback": self.action_cycle_lang}],
            [{"text": self._t("back"), "callback": self.action_main_menu}],
        ]
        await self.safe_edit(call, txt, btn)

    async def action_cycle_diff(self, call):
        s = self._settings()
        seq = ["easy", "normal", "hard", "nightmare"]
        s["difficulty"] = seq[(seq.index(s["difficulty"]) + 1) % len(seq)]
        self._save_settings(s)
        st = self.sessions.get("doom_user")
        if st:
            st["settings"] = s
            st["difficulty"] = s["difficulty"]
            st["log"] = self._t("set_ok", st)
            st["dirty"] = True
        await self.action_settings(call)

    async def action_cycle_autosave(self, call):
        s = self._settings()
        seq = [10, 15, 20, 30, 45]
        s["autosave"] = seq[(seq.index(s["autosave"]) + 1) % len(seq)] if s["autosave"] in seq else 15
        self._save_settings(s)
        st = self.sessions.get("doom_user")
        if st:
            st["settings"] = s
            st["log"] = self._t("set_ok", st)
            st["dirty"] = True
        await self.action_settings(call)

    async def action_cycle_lang(self, call):
        s = self._settings()
        seq = ["ru", "en"]
        s["lang"] = seq[(seq.index(s.get("lang", "ru")) + 1) % len(seq)]
        self._save_settings(s)
        st = self.sessions.get("doom_user")
        if st:
            st["settings"] = s
            st["log"] = self._t("set_ok", st)
            st["dirty"] = True
        await self.action_settings(call)

    async def action_help(self, call):
        pref = getattr(self, "get_prefix", lambda: ".")()
        txt = self._t("help_text", pref=pref)
        await self.safe_edit(call, txt, [[{"text": self._t("back"), "callback": self.action_main_menu}]])

    async def action_save(self, call):
        if "doom_user" in self.sessions:
            st = self.sessions["doom_user"]
            sv = self._snapshot(st)
            sv["running"] = False
            self.db.set("Doom", "save", sv)
            st["log"] = self._t("saved", st)
            st["dirty"] = True
            p = self._profile()
            p["ach"] = sorted(set(p.get("ach", [])) | st["ach"])
            self._save_profile(p)

    async def action_exit(self, call):
        if "doom_user" in self.sessions:
            st = self.sessions["doom_user"]
            p = self._profile()
            p["ach"] = sorted(set(p.get("ach", [])) | st["ach"])
            self._save_profile(p)
            st["running"] = False
            del self.sessions["doom_user"]
        await self.safe_edit(call, self._t("exit"), [[{"text": self._t("back"), "callback": self.action_main_menu}]])

    async def action_main_menu(self, call):
        await self.safe_edit(call, self._t("menu"), self._main_buttons())

    async def action_refresh(self, call):
        st = self.sessions.get("doom_user")
        if st and st.get("running"):
            st["dirty"] = True
            await self.do_render(call, st)
        else:
            await self.action_main_menu(call)

    async def action_rot_l(self, call):
        self.update_player(0, 0, -0.4)

    async def action_rot_r(self, call):
        self.update_player(0, 0, 0.4)

    async def action_fw(self, call):
        a = self.sessions.get("doom_user", {}).get("a", 0)
        self.update_player(math.sin(a) * 0.45, math.cos(a) * 0.45, 0)

    async def action_bw(self, call):
        a = self.sessions.get("doom_user", {}).get("a", 0)
        self.update_player(-math.sin(a) * 0.45, -math.cos(a) * 0.45, 0)

    async def action_m_l(self, call):
        a = self.sessions.get("doom_user", {}).get("a", 0) - math.pi / 2
        self.update_player(math.sin(a) * 0.4, math.cos(a) * 0.4, 0)

    async def action_m_r(self, call):
        a = self.sessions.get("doom_user", {}).get("a", 0) + math.pi / 2
        self.update_player(math.sin(a) * 0.4, math.cos(a) * 0.4, 0)
