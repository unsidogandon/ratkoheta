#meta developer: @dev_angel_7553
#requires: matplotlib

import io
import time
import datetime
import asyncio
import aiohttp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches

from .. import loader, utils
from herokutl.tl.types import Message


@loader.tds
class TonAnalyzer(loader.Module):
    """Анализ оборота TON в кошельке"""

    strings = {"name": "TonAnalyzer"}

    strings_ru = {
        "no_key": (
            "<b>API ключ не задан!</b>\n\n"
            "Получи бесплатный ключ у <a href='https://t.me/tonapibot'>@tonapibot</a> "
            "в боте, затем пропиши:\n"
            "<code>.cfg TonAnalyzer</code> поле <b>api_key</b>"
        ),
        "no_addr": "Укажи адрес: <code>.tonscan UQ...</code>",
        "not_found": "Транзакций не найдено",
        "err": "<b>Ошибка:</b> <code>{}</code>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "api_key", "", "API ключ от @tonapibot.",
                validator=loader.validators.Hidden(),
            ),
            loader.ConfigValue(
                "currencies", "usd,rub", "Валюты для конвертации через запятую (usd, rub, eur, ...)",
            ),
        )

    BASE_URL = "https://toncenter.com/api/v3"
    LIMIT = 256
    MIN_VAL = 10_000_000

    EMOJI_LOADING = '<tg-emoji emoji-id="5350773074578916842">🙏</tg-emoji>'
    EMOJI_IN = '<tg-emoji emoji-id="5350700390847365132">⏬</tg-emoji>'
    EMOJI_OUT = '<tg-emoji emoji-id="5350305520144106741">⏫</tg-emoji>'
    EMOJI_STATS = '<tg-emoji emoji-id="5350613306090482956">📊</tg-emoji>'
    EMOJI_FEE = '<tg-emoji emoji-id="5280479668422610048">⚜️</tg-emoji>'
    EMOJI_RATE = '<tg-emoji emoji-id="5350815453021234828">💱</tg-emoji>'
    EMOJI_HISTORY = '<tg-emoji emoji-id="5350667865060043135">💼</tg-emoji>'

    CURRENCY_SYMBOLS = {
        "usd": "$", "rub": "₽", "eur": "€", "gbp": "£", "cny": "¥", "kzt": "₸",
    }

    WEEKDAYS_RU = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]

    def nano_to_ton(self, nano) -> float:
        return int(nano or 0) / 1e9

    def get_currencies(self):
        raw = self.config["currencies"] or "usd"
        return [c.strip().lower() for c in raw.split(",") if c.strip()]

    def fmt_amount(self, amount: float, currency: str) -> str:
        symbol = self.CURRENCY_SYMBOLS.get(currency, currency.upper() + " ")
        if symbol.endswith(" "):
            return f"{amount:,.2f} {symbol.strip()}"
        return f"{symbol}{amount:,.2f}"

    def usd_block(self, ton: float, rates: dict) -> str:
        if ton < 0.001 or not rates:
            return ""
        parts = []
        for cur in self.get_currencies():
            price = rates.get(cur, 0)
            if price > 0:
                parts.append(f"<b>{self.fmt_amount(ton * price, cur)}</b>")
        return "≈ " + " / ".join(parts) if parts else ""

    def _headers(self):
        h = {}
        if self.config["api_key"]:
            h["X-Api-Key"] = self.config["api_key"]
        return h

    def build_daily_spend(self, all_txs):
        daily = {}
        for tx in all_txs:
            ts = tx.get("now") or tx.get("utime") or 0
            if not ts:
                continue
            day = datetime.date.fromtimestamp(ts)
            out_val = sum(int(m.get("value") or 0) for m in (tx.get("out_msgs") or []))
            if out_val >= self.MIN_VAL:
                daily[day] = daily.get(day, 0) + out_val
        return dict(sorted(daily.items()))

    def render_spend_chart(self, daily: dict, address: str, rates: dict,
                            ton_in: float, ton_out: float, ton_fees: float,
                            count_in: int, count_out: int):
        if not daily:
            return None

        first_day = min(daily.keys())
        last_day = max(daily.keys())
        span = (last_day - first_day).days
        days, values = [], []
        d = first_day
        while d <= last_day:
            days.append(d)
            values.append(daily.get(d, 0) / 1e9)
            d += datetime.timedelta(days=1)

        total = sum(values)
        active_days = [v for v in values if v > 0]
        avg = sum(active_days) / len(active_days) if active_days else 0
        peak_val = max(values) if values else 0
        peak_day = days[values.index(peak_val)] if values else None

        BG = "#0b0f19"
        CARD_BG = "#131a2a"
        CARD_BORDER = "#1e293b"
        ACCENT = "#f97316"
        BLUE = "#3b82f6"
        GREEN = "#22c55e"
        RED = "#ef4444"
        GRAY = "#8b93a3"
        WHITE = "#f5f5f7"

        fig = plt.figure(figsize=(16, 9), dpi=100)
        fig.patch.set_facecolor(BG)

        overlay = fig.add_axes([0, 0, 1, 1])
        overlay.set_xlim(0, 1)
        overlay.set_ylim(0, 1)
        overlay.axis("off")
        overlay.set_zorder(5)

        overlay.text(0.045, 0.945, "TonAnalyzer", color=ACCENT, fontsize=15,
                     fontweight="bold", family="sans-serif")
        overlay.text(0.955, 0.945, "ALL TIME", color=GRAY, fontsize=11,
                     fontweight="bold", ha="right")

        overlay.text(0.045, 0.885, "Расходы кошелька", color=WHITE, fontsize=30,
                     fontweight="bold")
        overlay.text(0.045, 0.835, "История трат за всё время", color=GRAY, fontsize=13)

        stats = [
            ("ВСЕГО ПОТРАЧЕНО", f"{ton_out:,.2f}", BLUE),
            ("ТРАНЗАКЦИЙ", f"{count_out}", GREEN),
            ("СРЕДНЕЕ/ДЕНЬ", f"{avg:,.2f}", RED),
            ("КОМИССИИ", f"{ton_fees:,.2f}", ACCENT),
        ]
        sx = 0.045
        for label, value, color in stats:
            overlay.add_patch(plt.Rectangle((sx, 0.735), 0.0035, 0.05,
                                             color=color, transform=overlay.transData))
            overlay.text(sx + 0.014, 0.765, label, color=GRAY, fontsize=9.5,
                         fontweight="bold")
            overlay.text(sx + 0.014, 0.735, value, color=WHITE, fontsize=20,
                         fontweight="bold")
            sx += 0.165

        overlay.text(0.045, 0.665, "ЕЖЕДНЕВНЫЕ ТРАТЫ", color=GRAY, fontsize=10,
                     fontweight="bold")

        card_x0, card_y0, card_w, card_h = 0.775, 0.115, 0.18, 0.715
        overlay.add_patch(mpatches.FancyBboxPatch(
            (card_x0, card_y0), card_w, card_h,
            boxstyle="round,pad=0,rounding_size=0.012",
            linewidth=1, edgecolor=CARD_BORDER, facecolor=CARD_BG, zorder=1,
        ))

        overlay.text(card_x0 + 0.02, card_y0 + card_h - 0.05, "Структура", color=WHITE,
                     fontsize=14, fontweight="bold")

        total_flow = ton_in + ton_out + ton_fees or 1
        rows = [
            ("Исходящие", ton_out, ACCENT),
            ("Входящие", ton_in, GREEN),
            ("Комиссии", ton_fees, RED),
        ]
        ry = card_y0 + card_h - 0.115
        for label, val, color in rows:
            pct = val / total_flow * 100
            overlay.add_patch(plt.Circle((card_x0 + 0.028, ry + 0.006), 0.006, color=color, zorder=2))
            overlay.text(card_x0 + 0.05, ry, label, color=GRAY, fontsize=10.5, va="center")
            overlay.text(card_x0 + card_w - 0.02, ry, f"{pct:.0f}%", color=WHITE,
                         fontsize=11, fontweight="bold", ha="right", va="center")
            ry -= 0.06

        overlay.plot([card_x0 + 0.02, card_x0 + card_w - 0.02], [ry + 0.02, ry + 0.02],
                     color=CARD_BORDER, linewidth=1)

        overlay.text(card_x0 + 0.02, ry - 0.03, "Самый крупный день", color=WHITE,
                     fontsize=13, fontweight="bold")
        if peak_day:
            overlay.text(card_x0 + 0.02, ry - 0.075, peak_day.strftime("%d.%m.%Y"),
                         color=GRAY, fontsize=10)
            overlay.text(card_x0 + card_w - 0.02, ry - 0.075, f"{peak_val:,.2f}",
                         color=WHITE, fontsize=12, fontweight="bold", ha="right")
            bar_w = card_w - 0.04
            overlay.add_patch(plt.Rectangle((card_x0 + 0.02, ry - 0.105), bar_w, 0.012,
                                             color="#2a3345", zorder=2))
            frac = max(peak_val / total, 0.12) if total > 0 else 0.12
            overlay.add_patch(plt.Rectangle((card_x0 + 0.02, ry - 0.105), bar_w * min(frac, 1.0), 0.012,
                                             color=ACCENT, zorder=2))

        ax = fig.add_axes([0.045, 0.14, 0.70, 0.49])
        ax.set_facecolor(BG)

        glow_layers = [(9, 0.04), (6, 0.07), (3.5, 0.14)]
        for lw, alpha in glow_layers:
            ax.plot(days, values, color=ACCENT, linewidth=lw, alpha=alpha, zorder=2)
        ax.plot(days, values, color="#fdba74", linewidth=1.8, zorder=3)

        n_bands = 25
        for i in range(n_bands):
            f0 = 1 - i / n_bands
            f1 = 1 - (i + 1) / n_bands
            ax.fill_between(days, [v * f1 for v in values], [v * f0 for v in values],
                             color=ACCENT, alpha=0.02, zorder=1, linewidth=0)

        if days:
            ax.scatter([days[-1]], [values[-1]], color="#86efac", s=28, zorder=4,
                       edgecolors=BG, linewidths=1.5)

        ax.grid(axis="y", color="#1c2231", linewidth=0.7, zorder=0)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(colors=GRAY, labelsize=9.5)
        ax.set_ylim(bottom=0)

        n_ticks = min(4, max(2, span // 10 + 1)) if span else 1
        step = max(span // (n_ticks - 1), 1) if n_ticks > 1 else 1
        tick_days = [first_day + datetime.timedelta(days=i * step) for i in range(n_ticks)]
        min_gap = max(span * 0.06, 1)
        if not tick_days or (last_day - tick_days[-1]).days < min_gap:
            if len(tick_days) > 1:
                tick_days[-1] = last_day
            else:
                tick_days.append(last_day)
        else:
            tick_days.append(last_day)
        ax.set_xticks(tick_days)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
        for label in ax.get_xticklabels():
            label.set_ha("center")

        addr_short = address[:14] + "…" + address[-6:] if len(address) > 24 else address
        overlay.text(0.045, 0.04, f"TONANALYZER  /  {addr_short}", color="#4b5563",
                     fontsize=9, family="monospace")

        buf = io.BytesIO()
        buf.name = "spend_chart.png"
        fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return buf

    def build_historical_summary(self, daily: dict, hist_prices: dict, current_usd: float, top_n: int = 5):
        if not daily:
            return "", 0.0, 0.0

        known_days = sorted(hist_prices.keys())
        entries = []
        for day, nano in sorted(daily.items()):
            ton_val = nano / 1e9
            price = hist_prices.get(day)
            if price is None and known_days:
                nearest = min(known_days, key=lambda d: abs((d - day).days))
                price = hist_prices.get(nearest)
            if price is None:
                price = current_usd
            entries.append((day, ton_val, price, ton_val * price))

        hist_total = sum(e[3] for e in entries)
        current_total = sum(e[1] for e in entries) * current_usd

        top_entries = sorted(entries, key=lambda e: e[3], reverse=True)[:top_n]
        top_entries.sort(key=lambda e: e[0])

        lines = []
        for day, ton_val, price, usd_val in top_entries:
            weekday = self.WEEKDAYS_RU[day.weekday()]
            lines.append(
                f"  <tg-emoji emoji-id=\"5872889730240089575\">🗓</tg-emoji> <b>{weekday}, {day.strftime('%d.%m')}</b> — "
                f"<code>{ton_val:.2f}</code> TON по <code>${price:.2f}</code> "
                f"= <b>${usd_val:,.2f}</b>"
            )

        return "\n".join(lines), hist_total, current_total

    async def fetch_transactions(self, session, address: str, form):
        all_txs = []
        offset = 0
        while True:
            params = {"account": address, "limit": self.LIMIT, "offset": offset, "sort": "desc"}
            async with session.get(
                f"{self.BASE_URL}/transactions",
                params=params, headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                data = await resp.json()
            if "transactions" not in data:
                raise Exception(data.get("error") or str(data)[:200])
            batch = data["transactions"]
            if not batch:
                break
            all_txs.extend(batch)
            if len(batch) < self.LIMIT:
                break
            offset += len(batch)

            await form.edit(
                text=(
                    f"{self.EMOJI_LOADING} "
                    f"<b>Загружено:</b> {len(all_txs)} транзакций...\n"
                ),
                reply_markup=[[{"text": "Закрыть", "action": "close", "style": "danger"}]]
            )
            await asyncio.sleep(0.15)
        return all_txs

    async def fetch_ton_rates(self, session) -> dict:
        currencies = ",".join(self.get_currencies())
        try:
            async with session.get(
                "https://tonapi.io/v2/rates",
                params={"tokens": "ton", "currencies": currencies},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
            prices = data["rates"]["TON"]["prices"]
            return {k.lower(): float(v) for k, v in prices.items()}
        except Exception:
            return {}

    async def fetch_historical_prices(self, session, start_day: datetime.date, end_day: datetime.date) -> dict:
        start_ts = int(datetime.datetime.combine(start_day, datetime.time.min).timestamp())
        end_ts = int(datetime.datetime.combine(end_day, datetime.time.max).timestamp())
        try:
            async with session.get(
                "https://tonapi.io/v2/rates/chart",
                params={
                    "token": "ton",
                    "currency": "usd",
                    "start_date": start_ts,
                    "end_date": end_ts,
                    "points_count": 200,
                },
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                data = await resp.json()
            by_day = {}
            for ts, price in data.get("points") or []:
                day = datetime.date.fromtimestamp(ts)
                by_day[day] = float(price)
            return by_day
        except Exception:
            return {}

    @loader.command()
    async def tonscan(self, message: Message):
        """<адрес> — полный оборот GRAM кошелька"""

        if not self.config["api_key"]:
            await self.inline.form(
                message=message,
                text=self.strings_ru["no_key"],
                reply_markup=[[{"text": "Закрыть", "action": "close", "style": "danger"}]]
            )
            return

        address = utils.get_args_raw(message)
        if not address:
            await self.inline.form(
                message=message,
                text=self.strings_ru["no_addr"],
                reply_markup=[[{"text": "Закрыть", "action": "close", "style": "danger"}]]
            )
            return

        address = address.strip()

        form = await self.inline.form(
            message=message,
            text=(
                f'<b>Загружаю транзакции...</b>\n'
                f"<code>{address}</code>"
            ),
            reply_markup=[[{"text": "Закрыть", "action": "close", "style": "danger"}]]
        )

        try:
            async with aiohttp.ClientSession() as session:
                all_txs, rates = await asyncio.gather(
                    self.fetch_transactions(session, address, form),
                    self.fetch_ton_rates(session),
                )
                daily_spend = self.build_daily_spend(all_txs)
                hist_prices = (
                    await self.fetch_historical_prices(session, min(daily_spend), max(daily_spend))
                    if daily_spend else {}
                )
        except Exception as e:
            await form.edit(
                text=self.strings_ru["err"].format(utils.escape_html(str(e))),
                reply_markup=[[{"text": "Закрыть", "action": "close", "style": "danger"}]]
            )
            return

        if not all_txs:
            await form.edit(
                text=self.strings_ru["not_found"],
                reply_markup=[[{"text": "Закрыть", "action": "close", "style": "danger"}]]
            )
            return

        total_in = total_out = 0
        count_in = count_out = 0
        fees_total = 0

        for tx in all_txs:
            in_msg = tx.get("in_msg") or {}
            out_msgs = tx.get("out_msgs") or []
            in_val = int(in_msg.get("value") or 0)
            if in_val >= self.MIN_VAL:
                total_in += in_val
                count_in += 1
            for m in out_msgs:
                out_val = int(m.get("value") or 0)
                if out_val >= self.MIN_VAL:
                    total_out += out_val
                    count_out += 1
            fees_total += int(tx.get("total_fees") or 0)

        ton_in = self.nano_to_ton(total_in)
        ton_out = self.nano_to_ton(total_out)
        ton_fees = self.nano_to_ton(fees_total)

        recent_lines = []
        for tx in all_txs:
            if len(recent_lines) >= 10:
                break
            in_msg = tx.get("in_msg") or {}
            out_msgs = tx.get("out_msgs") or []
            in_val = int(in_msg.get("value") or 0)
            out_val = sum(int(m.get("value") or 0) for m in out_msgs)

            if in_val < self.MIN_VAL and out_val < self.MIN_VAL:
                continue

            ts = tx.get("now") or tx.get("utime") or 0
            dt = time.strftime("%d.%m.%y %H:%M", time.localtime(ts))

            if in_val >= self.MIN_VAL:
                usd = self.usd_block(in_val / 1e9, rates)
                src = (in_msg.get("source") or "—")[:16]
                recent_lines.append(
                    f'  {self.EMOJI_IN} '
                    f"<code>+{in_val / 1e9:.3f}</code> GRAM {usd}\n"
                    f"      {dt} · <code>{src}</code>"
                )

            if out_val >= self.MIN_VAL:
                dst = (out_msgs[0].get("destination") or "—")[:16] if out_msgs else "—"
                usd = self.usd_block(out_val / 1e9, rates)
                recent_lines.append(
                    f'  {self.EMOJI_OUT} '
                    f"<code>-{out_val / 1e9:.3f}</code> GRAM {usd}\n"
                    f"      {dt} · <code>{dst}</code>"
                )

        recent_block = "\n\n".join(recent_lines) if recent_lines else "  —"

        chart_buf = self.render_spend_chart(
            daily_spend, address, rates,
            ton_in, ton_out, ton_fees, count_in, count_out,
        )
        if chart_buf:
            await message.client.send_file(
                message.peer_id,
                chart_buf,
                caption=f"{self.EMOJI_STATS} <b>Расходы кошелька</b>",
                parse_mode="html",
                reply_to=getattr(message, "reply_to_msg_id", None),
            )

        rate_line = ""
        if rates:
            rate_parts = [
                self.fmt_amount(rates[cur], cur)
                for cur in self.get_currencies() if rates.get(cur)
            ]
            if rate_parts:
                rate_line = f"\n{self.EMOJI_RATE} <b>Курс GRAM:</b> " + " / ".join(rate_parts)

        hist_lines, hist_total, current_total = self.build_historical_summary(
            daily_spend, hist_prices, rates.get("usd", 0)
        )
        hist_block = ""
        if hist_lines and hist_prices:
            diff = current_total - hist_total
            diff_sign = "+" if diff >= 0 else "−"
            hist_block = (
                f"\n\n{self.EMOJI_HISTORY} <b>Траты по курсу на день покупки:</b>\n"
                f"{hist_lines}\n\n"
                f"  <b>Итого по курсам покупки:</b> ${hist_total:,.2f}\n"
                f"  <b>Итого по текущему курсу:</b> ${current_total:,.2f}\n"
                f"  <b>Разница:</b> {diff_sign}${abs(diff):,.2f}"
            )

        stats_text = (
            f'{self.EMOJI_STATS} <b>Статистика кошелька</b>\n'
            f"<code>{address}</code>"
            f"{rate_line}\n\n"
            f'<blockquote>{self.EMOJI_IN} <b>Пришло:</b>\n'
            f"  <code>+{ton_in:.4f}</code> GRAM  {self.usd_block(ton_in, rates)}\n"
            f"  ({count_in} транзакций)</blockquote>\n"
            f'<blockquote>{self.EMOJI_OUT} <b>Ушло:</b>\n'
            f"  <code>-{ton_out:.4f}</code> GRAM  {self.usd_block(ton_out, rates)}\n"
            f"  ({count_out} транзакций)</blockquote>\n"
            f'{self.EMOJI_FEE} <b>Комиссии:</b>\n'
            f"  <code>-{ton_fees:.4f}</code> GRAM  {self.usd_block(ton_fees, rates)}\n\n"
            f'{self.EMOJI_STATS} '
            f"<b>Всего транзакций:</b> {len(all_txs)}"
            f"{hist_block}"
            f"\n\n"
            f'{self.EMOJI_HISTORY} <b>Последние операции:</b>\n'
            f"<blockquote expandable>{recent_block}</blockquote>"
        )

        await form.edit(
            text=stats_text,
            reply_markup=[
                [
                    {
                        "text": "Закрыть",
                        "action": "close",
                        "style": "danger",
                    }
                ]
            ]
        )
