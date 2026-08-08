# ====================================================================================================================
#   ██████╗  ██████╗ ██╗   ██╗███╗   ███╗ ██████╗ ██████╗ ██╗   ██╗██╗     ███████╗███████╗
#  ██╔════╝ ██╔═══██╗╚██╗ ██╔╝████╗ ████║██╔═══██╗██╔══██╗██║   ██║██║     ██╔════╝██╔════╝
#  ██║  ███╗██║   ██║ ╚████╔╝ ██╔████╔██║██║   ██║██║  ██║██║   ██║██║     █████╗  ███████╗
#  ██║   ██║██║   ██║  ╚██╔╝  ██║╚██╔╝██║██║   ██║██║  ██║██║   ██║██║     ██╔══╝  ╚════██║
#  ╚██████╔╝╚██████╔╝   ██║   ██║ ╚═╝ ██║╚██████╔╝██████╔╝╚██████╔╝███████╗███████╗███████║
#   ╚═════╝  ╚═════╝    ╚═╝   ╚═╝     ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚══════╝
#
#   OFFICIAL USERNAMES: @goymodules | @samsepi0l_ovf
#   MODULE: recon
#
#   THIS MODULE IS LICENSED UNDER GNU AGPLv3, PROTECTED AGAINST UNAUTHORIZED COPYING/RESALE,
#   AND ITS ORIGINAL AUTHORSHIP BELONGS TO @samsepi0l_ovf.
#   ALL OFFICIAL UPDATES, RELEASE NOTES, AND PATCHES ARE PUBLISHED IN THE TELEGRAM CHANNEL @goymodules.
# ====================================================================================================================

# meta banner: https://raw.githubusercontent.com/sepiol026-wq/goypulse/main/assets/recon.png
# meta developer: @goymodules
# meta tags: osint, network-recon, dns, host-info, scanner, infosec, осінт, сетевая-разведка, днс, информация-о-хосте, сканер, инфобез
# requires: aiohttp beautifulsoup4
__version__ = (1, 2, 1)

import aiohttp
import asyncio
import re
import os
import shutil
import ssl
import tempfile
from urllib.parse import urlparse, urljoin, quote_plus, quote
from collections import deque
from herokutl.types import Message
from .. import loader, utils

HDRS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

WAF_SIGS = {
    "Cloudflare": ["cf-ray", "cloudflare", "__cfduid"],
    "Sucuri": ["x-sucuri-id", "x-sucuri-cache"],
    "Fastly": ["x-fastly-request-id", "fastly"],
    "Akamai": ["x-akamai-request-id", "akamai"],
    "DDoS-Guard": ["ddos-guard"],
    "Imperva": ["incap_ses", "visid_incap", "imperva"],
    "AWS WAF": ["x-amzn-requestid", "x-amz-cf-id"],
    "Barracuda": ["barra", "bni__"],
    "F5 BIG-IP": ["f5", "bigip", "ts01"],
    "BitNinja": ["bitninja"],
}

SEC_HEADERS = [
    "Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options",
    "X-Content-Type-Options", "X-XSS-Protection", "Referrer-Policy",
    "Permissions-Policy", "Cross-Origin-Opener-Policy", "Cross-Origin-Resource-Policy",
]

@loader.tds
class Recon(loader.Module):
    """scan toolkit."""
    strings = {
        "name": "Recon",
        "no_args": "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> Specify target.</b>",
        "processing": "<b><tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> Scanning: <code>{}</code>...</b>\n<i>Working...</i>",
        "stopped": "<b><tg-emoji emoji-id=5253832566036770389>🚮</tg-emoji> Process killed.</b>",
        "no_active": "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> No active processes.</b>",
        "not_owner": "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> Not your task.</b>",
    }
    strings_ru = {
        "no_args": "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> Укажи таргет.</b>",
        "processing": "<b><tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> Сканирую: <code>{}</code>...</b>\n<i>Работаю...</i>",
        "stopped": "<b><tg-emoji emoji-id=5253832566036770389>🚮</tg-emoji> Процесс убит.</b>",
        "no_active": "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> Нет активных процессов.</b>",
        "not_owner": "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> Не твоя таска.</b>",
    }
    strings_uz = {
        "no_args": "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> Targetni kiriting.</b>",
        "processing": "<b><tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> Skanerlash: <code>{}</code>...</b>\n<i>Ishlamoqda...</i>",
        "stopped": "<b><tg-emoji emoji-id=5253832566036770389>🚮</tg-emoji> Jarayon to'xtatildi.</b>",
        "no_active": "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> Faol jarayonlar yo'q.</b>",
        "not_owner": "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> Bu sizning vazifangiz emas.</b>",
    }
    strings_de = {
        "no_args": "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> Ziel angeben.</b>",
        "processing": "<b><tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> Scanne: <code>{}</code>...</b>\n<i>Arbeite...</i>",
        "stopped": "<b><tg-emoji emoji-id=5253832566036770389>🚮</tg-emoji> Prozess beendet.</b>",
        "no_active": "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> Keine aktiven Prozesse.</b>",
        "not_owner": "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> Nicht deine Aufgabe.</b>",
    }
    strings_es = {
        "no_args": "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> Indica el objetivo.</b>",
        "processing": "<b><tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> Escaneando: <code>{}</code>...</b>\n<i>Trabajando...</i>",
        "stopped": "<b><tg-emoji emoji-id=5253832566036770389>🚮</tg-emoji> Proceso eliminado.</b>",
        "no_active": "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> No hay procesos activos.</b>",
        "not_owner": "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> No es tu tarea.</b>",
    }
    if "_cls_doc" not in strings and __doc__:
        strings["_cls_doc"] = (__doc__ or "").strip()
    strings_ru = {**strings, **locals().get("strings_ru", {})}
    strings_uk = {**strings, **locals().get("strings_ua", {}), **locals().get("strings_uk", {})}
    strings_de = {**strings, **locals().get("strings_de", {})}
    strings_jp = {**strings, **locals().get("strings_jp", {})}
    strings_neofit = {**strings, **locals().get("strings_neofit", {})}
    strings_tiktok = {**strings, **locals().get("strings_tiktok", {})}
    strings_leet = {**strings, **locals().get("strings_leet", {})}
    strings_uwu = {**strings, **locals().get("strings_uwu", {})}

    def __init__(self):
        self.active_tasks = {}
        self.active_processes = {}
        self.config = loader.ModuleConfig(
            loader.ConfigValue("shodan_key", "", "API ключ Shodan", validator=loader.validators.Hidden()),
            loader.ConfigValue("use_shodan", False, "Юзать Shodan API в .rc", validator=loader.validators.Boolean()),
        )

    SVG_ICON_MAP = {
        "🔥": ("⚡", "#ef4444"),
        "📟": ("◉", "#3b82f6"),
        "🛡": ("🛡", "#10b981"),
        "🏳️": ("◎", "#14b8a6"),
        "⤵️": ("↘", "#6366f1"),
        "📝": ("✎", "#f59e0b"),
        "📂": ("▣", "#f97316"),
        "🎞": ("◫", "#8b5cf6"),
        "🐢": ("◔", "#22c55e"),
        "📧": ("✉", "#06b6d4"),
        "🖼": ("◱", "#0ea5e9"),
        "⚙️": ("⚙", "#64748b"),
        "❗️": ("!", "#f43f5e"),
        "👌": ("✓", "#22c55e"),
        "📍": ("⌖", "#ec4899"),
        "🕔": ("◴", "#a855f7"),
        "📛": ("◆", "#e11d48"),
        "✅": ("✔", "#16a34a"),
        "🔓": ("⌂", "#f59e0b"),
        "🔗": ("⛓", "#0ea5e9"),
        "🔃": ("↻", "#2563eb"),
    }

    def _svg_icon(self, char):
        symbol, color = self.SVG_ICON_MAP.get(char, ("•", "#64748b"))
        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' width='15' height='15' viewBox='0 0 24 24'>"
            f"<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop stop-color='{color}'/>"
            f"<stop offset='1' stop-color='#0ea5e9'/></linearGradient></defs>"
            "<circle cx='12' cy='12' r='10' fill='url(#g)'/>"
            f"<text x='12' y='16' text-anchor='middle' fill='white' font-size='11' font-weight='700'>{symbol}</text>"
            "</svg>"
        )
        return f"<img src='data:image/svg+xml;utf8,{quote(svg)}' style='width:15px;height:15px;vertical-align:-2px;margin-right:4px'/>"

    def _svgify_line(self, line):
        for em in sorted(self.SVG_ICON_MAP, key=len, reverse=True):
            if em in line:
                line = line.replace(em, self._svg_icon(em))
        return line

    async def fetch(self, s, url, t="text"):
        try:
            async with s.get(url, headers=HDRS, timeout=aiohttp.ClientTimeout(total=15), ssl=False) as r:
                if r.status == 200:
                    return await r.json() if t == "json" else await r.text()
        except Exception:
            pass
        return {} if t == "json" else ""

    async def fetch_full(self, target):
        url = f"http://{target}" if not target.startswith("http") else target
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, headers=HDRS, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True, ssl=False) as r:
                    text = await r.text()
                    title = ""
                    m = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
                    if m: title = m.group(1).strip()[:100]
                    return {"status": r.status, "headers": dict(r.headers), "title": title, "body": text}
        except Exception:
            return {}

    async def detect_waf(self, target):
        url = f"http://{target}" if not target.startswith("http") else target
        try:
            async with aiohttp.ClientSession() as s:
                async with s.head(url, headers=HDRS, timeout=aiohttp.ClientTimeout(total=8), allow_redirects=True, ssl=False) as r:
                    h = str(r.headers).lower()
                    for name, sigs in WAF_SIGS.items():
                        if any(sig in h for sig in sigs):
                            return name
        except Exception:
            pass
        return None

    def check_sec_headers(self, headers):
        found, missing = [], []
        for h in SEC_HEADERS:
            if h in headers: found.append((h, headers[h][:60]))
            else: missing.append(h)
        return found, missing

    def extract_tech(self, headers, body):
        tech = set()
        srv = headers.get("Server", "")
        if srv: tech.add(f"Server: {srv}")
        pw = headers.get("X-Powered-By", "")
        if pw: tech.add(f"Powered: {pw}")
        patterns = {
            "WordPress": [r"wp-content", r"wp-includes", r"wordpress"],
            "Joomla": [r"Joomla", r"/components/com_"],
            "Drupal": [r"Drupal", r"sites/default/files"],
            "Laravel": [r"laravel_session"],
            "Django": [r"csrfmiddlewaretoken", r"__admin"],
            "React": [r"react\.production", r"_reactRoot"],
            "Vue.js": [r"vue\.js", r"__vue__"],
            "Angular": [r"ng-version", r"angular"],
            "jQuery": [r"jquery[\.-][\d]"],
            "Bootstrap": [r"bootstrap\.min"],
            "Nginx": [r"nginx"],
            "Apache": [r"apache"],
            "PHP": [r"\.php", r"PHPSESSID"],
            "ASP.NET": [r"asp\.net", r"__VIEWSTATE"],
        }
        for name, pats in patterns.items():
            for p in pats:
                if re.search(p, body, re.IGNORECASE) or re.search(p, str(headers), re.IGNORECASE):
                    tech.add(name)
                    break
        return list(tech)

    def extract_js(self, body, base_url):
        scripts = re.findall(r'src=["\']([^"\']*\.js[^"\']*)["\']', body, re.IGNORECASE)
        return list(set(urljoin(base_url, s) for s in scripts))[:30]

    def extract_emails(self, text):
        return list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)))

    def extract_params_from_urls(self, urls):
        params = set()
        for u in urls:
            try:
                q = urlparse(u).query
                if q:
                    for p in q.split("&"):
                        if "=" in p: params.add(p.split("=")[0])
            except: pass
        return sorted(params)[:50]

    async def parse_robots(self, s, target):
        text = await self.fetch(s, f"https://{target}/robots.txt")
        if not text or "<!DOCTYPE" in text[:50].upper(): return None
        return text[:2000]

    async def parse_sitemap(self, s, target):
        text = await self.fetch(s, f"https://{target}/sitemap.xml")
        if not text or "<!DOCTYPE html" in text[:100].lower(): return []
        urls = re.findall(r"<loc>(.*?)</loc>", text)
        return urls[:50]

    async def whois_full(self, s, target, target_ip):
        result = {}
        is_ip = bool(re.match(r"^[\d.]+$", target))
        ipw = await self.fetch(s, f"https://ipwhois.app/json/{target_ip}", "json")
        if isinstance(ipw, dict) and ipw.get("success", True) is not False:
            result["ip"] = ipw.get("ip", target_ip)
            result["country"] = ipw.get("country", "N/A")
            result["region"] = ipw.get("region", "N/A")
            result["city"] = ipw.get("city", "N/A")
            result["isp"] = ipw.get("isp", "N/A")
            result["org"] = ipw.get("org", "N/A")
            result["asn"] = ipw.get("asn", "N/A")
            result["type"] = ipw.get("type", "N/A")
            result["timezone"] = ipw.get("timezone", "N/A")
        if not is_ip:
            rdap = await self.fetch(s, f"https://rdap.org/domain/{target}", "json")
            if isinstance(rdap, dict) and rdap.get("ldhName"):
                result["domain"] = rdap.get("ldhName", target)
                result["status"] = ", ".join(rdap.get("status", [])[:3]) or "N/A"
                for ev in rdap.get("events", []):
                    if ev.get("eventAction") == "registration": result["created"] = ev.get("eventDate", "")[:10]
                    if ev.get("eventAction") == "expiration": result["expires"] = ev.get("eventDate", "")[:10]
                    if ev.get("eventAction") == "last changed": result["updated"] = ev.get("eventDate", "")[:10]
                ns = [n.get("ldhName", "") for n in rdap.get("nameservers", [])]
                result["ns"] = ns
                for ent in rdap.get("entities", []):
                    roles = ent.get("roles", [])
                    vc = ent.get("vcardArray", [None, []])
                    if isinstance(vc, list) and len(vc) > 1:
                        for item in vc[1]:
                            if isinstance(item, list) and len(item) > 3 and item[0] == "fn":
                                if "registrar" in roles: result["registrar"] = item[3]
                                if "registrant" in roles: result["registrant"] = item[3]
                                if "abuse" in roles: result["abuse"] = item[3]
                            if isinstance(item, list) and len(item) > 3 and item[0] == "email":
                                result["contact_email"] = item[3]
        return result

    async def send_report(self, message, text, title="report"):
        if len(text) <= 4096:
            await utils.answer(message, text)
            return
        plain = re.sub(r"<[^>]+>", "", text)
        html = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<style>"
            "body{background:#0d1117;color:#c9d1d9;font-family:'Courier New',monospace;padding:20px 30px;font-size:13px;line-height:1.6}"
            "h1{color:#58a6ff;border-bottom:1px solid #30363d;padding-bottom:10px;font-size:20px}"
            "h2{color:#79c0ff;margin-top:20px;font-size:16px}"
            ".section{background:#161b22;padding:14px;border-radius:6px;margin:10px 0;border:1px solid #30363d}"
            ".ok{color:#7ee787}.bad{color:#ff7b72}.warn{color:#d29922}"
            "code{color:#a5d6ff;background:#1c2128;padding:2px 5px;border-radius:3px}"
            "a{color:#58a6ff}"
            "</style>"
            f"<title>{title}</title></head><body>"
            f"<h1>{self._svg_icon('🖼')} {title}</h1>"
        )
        heading_icons = tuple(self.SVG_ICON_MAP.keys())
        for line in plain.split("\n"):
            line = line.strip()
            if not line: continue
            is_heading = line.startswith(heading_icons)
            line = self._svgify_line(line)
            if is_heading:
                html += f"<h2>{line}</h2><div class='section'>"
            elif line.startswith("├") or line.startswith("└"):
                html += f"<div>{line}</div>"
            else:
                html += f"<div>{line}</div>"
        html += "</div></body></html>"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", prefix=f"rc_", delete=False, encoding="utf-8") as f:
            f.write(html)
            path = f.name
        try:
            await self._client.send_file(message.peer_id, path, caption=f"<b><tg-emoji emoji-id=5255917867148257511>🖼</tg-emoji> {title}</b>\n<i>Полный отчёт в файле</i>")
        except Exception:
            await utils.answer(message, text[:4096])
        finally:
            try: os.unlink(path)
            except: pass

    async def crawl_site(self, s, target, depth=3, mx=150):
        base = f"https://{target}" if not target.startswith("http") else target
        visited, urls, forms, emails = set(), [], [], set()
        q = deque([(base, 0)])
        while q and len(visited) < mx:
            url, lvl = q.popleft()
            if lvl > depth or url in visited: continue
            visited.add(url)
            try:
                async with s.get(url, headers=HDRS, timeout=aiohttp.ClientTimeout(total=8), allow_redirects=True, ssl=False) as r:
                    if r.status != 200 or "text/html" not in r.headers.get("Content-Type", ""): continue
                    html = await r.text()
            except Exception: continue
            urls.append(url)
            emails.update(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html))
            for f in re.findall(r'<form[^>]*action=["\']?([^"\'>\s]*)', html, re.IGNORECASE):
                a = urljoin(url, f) if f else url
                if a not in forms: forms.append(a)
            if lvl < depth:
                for link in re.findall(r'href=["\']?(https?://[^"\'>\s]*|/[^"\'>\s]*)', html, re.IGNORECASE):
                    full = urljoin(url, link)
                    if target in urlparse(full).netloc and full not in visited:
                        q.append((full, lvl + 1))
            await asyncio.sleep(0.2)
        return {"urls": urls, "forms": forms, "emails": list(emails), "total": len(visited)}

    async def parse_dorks(self, s, target):
        dorks = [
            f"site:{target} filetype:php | filetype:env | filetype:log | filetype:bak",
            f"site:{target} inurl:admin | inurl:login | inurl:dashboard",
            f"site:{target} filetype:sql | filetype:conf | filetype:cfg | filetype:ini",
            f"site:{target} inurl:api | inurl:token | inurl:key | inurl:secret",
            f"site:{target} intitle:index of",
            f"site:{target} filetype:xml | filetype:json | filetype:yaml",
        ]
        found = []
        for dork in dorks:
            for engine_url in [
                f"https://html.duckduckgo.com/html/?q={quote_plus(dork)}",
                f"https://www.bing.com/search?q={quote_plus(dork)}&count=20",
            ]:
                try:
                    async with s.get(engine_url, headers=HDRS, timeout=aiohttp.ClientTimeout(total=12)) as r:
                        if r.status == 200:
                            text = await r.text()
                            urls = re.findall(r'href="(https?://[^"]+)"', text)
                            for u in urls:
                                if target in u and not any(x in u for x in ["duckduckgo", "bing.com", "microsoft.com", "google.com", "webcache"]):
                                    if u not in found:
                                        found.append(u)
                except Exception: pass
                await asyncio.sleep(1)
        return found

    SENSITIVE_PATHS = [
        "/.env", "/.git/config", "/.git/HEAD", "/.svn/entries", "/.DS_Store",
        "/wp-config.php.bak", "/wp-config.php.old", "/wp-login.php", "/wp-admin/",
        "/admin/", "/administrator/", "/login/", "/panel/", "/dashboard/",
        "/phpmyadmin/", "/adminer.php", "/server-status", "/server-info",
        "/.htaccess", "/.htpasswd", "/web.config", "/crossdomain.xml",
        "/elmah.axd", "/trace.axd", "/info.php", "/phpinfo.php",
        "/backup/", "/backup.sql", "/backup.zip", "/db.sql", "/dump.sql",
        "/.well-known/security.txt", "/security.txt", "/humans.txt",
        "/api/", "/api/v1/", "/api/v2/", "/swagger.json", "/api-docs",
        "/graphql", "/graphiql", "/.dockerenv", "/Dockerfile",
        "/composer.json", "/package.json", "/.npmrc", "/config.yml",
        "/config.json", "/config.php", "/config.inc.php", "/.config",
        "/debug/", "/test/", "/temp/", "/tmp/", "/log/", "/logs/",
        "/error.log", "/access.log", "/debug.log",
        "/.aws/credentials", "/.ssh/id_rsa", "/id_rsa",
    ]

    TAKEOVER_SIGS = {
        "github.io": "There isn't a GitHub Pages site here",
        "herokuapp.com": "no such app",
        "s3.amazonaws.com": "NoSuchBucket",
        "cloudfront.net": "Bad request",
        "azure": "404 Web Site not found",
        "shopify.com": "Sorry, this shop is currently unavailable",
        "tumblr.com": "There's nothing here",
        "wordpress.com": "Do you want to register",
        "ghost.io": "The thing you were looking for is no longer here",
        "surge.sh": "project not found",
        "bitbucket.io": "Repository not found",
        "pantheon.io": "404 error unknown site",
        "readme.io": "Project doesnt exist",
        "zendesk.com": "Help Center Closed",
    }

    SECRET_PATTERNS = [
        (r'(?:api[_-]?key|apikey)["\s:=]+["\']([a-zA-Z0-9_\-]{20,60})["\']', "API Key"),
        (r'(?:secret|token|password|passwd|pwd)["\s:=]+["\']([a-zA-Z0-9_\-]{8,60})["\']', "Secret/Token"),
        (r'(?:aws_access_key_id)["\s:=]+["\']([A-Z0-9]{20})["\']', "AWS Key"),
        (r'(?:aws_secret_access_key)["\s:=]+["\']([a-zA-Z0-9/+=]{40})["\']', "AWS Secret"),
        (r'(?:AKIA)[A-Z0-9]{16}', "AWS Access Key"),
        (r'sk_live_[a-zA-Z0-9]{24,}', "Stripe Secret Key"),
        (r'pk_live_[a-zA-Z0-9]{24,}', "Stripe Public Key"),
        (r'ghp_[a-zA-Z0-9]{36}', "GitHub Token"),
        (r'glpat-[a-zA-Z0-9_\-]{20}', "GitLab Token"),
        (r'xox[baprs]-[a-zA-Z0-9\-]+', "Slack Token"),
        (r'(?:firebase|firebaseio\.com)[^\s"]{5,}', "Firebase URL"),
        (r'eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}', "JWT Token"),
        (r'(?:mysql|postgres|mongodb)://[^\s"<>]{10,}', "DB Connection String"),
        (r'(?:smtp|ftp)://[^\s"<>]{10,}', "Protocol Credential"),
    ]

    async def path_bruteforce(self, s, target):
        found = []
        base = f"https://{target}"
        tasks = []
        for path in self.SENSITIVE_PATHS:
            tasks.append(self._check_path(s, base, path))
        results = await asyncio.gather(*tasks)
        for r in results:
            if r: found.append(r)
        return found

    async def _check_path(self, s, base, path):
        try:
            url = f"{base}{path}"
            async with s.get(url, headers=HDRS, timeout=aiohttp.ClientTimeout(total=5), ssl=False, allow_redirects=False) as r:
                if r.status in (200, 301, 302, 403):
                    size = int(r.headers.get("Content-Length", 0))
                    return {"path": path, "status": r.status, "size": size}
        except Exception:
            pass
        return None

    async def check_cors(self, s, target):
        issues = []
        url = f"https://{target}"
        origins = ["https://evil.com", "null", f"https://{target}.evil.com"]
        for origin in origins:
            try:
                h = {**HDRS, "Origin": origin}
                async with s.get(url, headers=h, timeout=aiohttp.ClientTimeout(total=5), ssl=False) as r:
                    acao = r.headers.get("Access-Control-Allow-Origin", "")
                    acac = r.headers.get("Access-Control-Allow-Credentials", "")
                    if acao == "*":
                        issues.append(f"Wildcard CORS: {acao}")
                    elif origin in acao:
                        msg = f"Reflects origin: {origin}"
                        if acac.lower() == "true": msg += " + credentials"
                        issues.append(msg)
            except Exception:
                pass
        return issues

    async def check_http_methods(self, s, target):
        url = f"https://{target}"
        allowed = []
        for method in ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "TRACE", "HEAD"]:
            try:
                async with s.request(method, url, headers=HDRS, timeout=aiohttp.ClientTimeout(total=4), ssl=False) as r:
                    if r.status < 500:
                        allowed.append(f"{method}:{r.status}")
            except Exception:
                pass
        return allowed

    async def get_ssl_info(self, target):
        try:
            ctx = ssl.create_default_context()
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(target, 443, ssl=ctx), timeout=5
            )
            cert = writer.get_extra_info('peercert')
            writer.close()
            await writer.wait_closed()
            if cert:
                subj = dict(x[0] for x in cert.get("subject", []))
                issuer = dict(x[0] for x in cert.get("issuer", []))
                san = []
                for t2, v in cert.get("subjectAltName", []):
                    if t2 == "DNS": san.append(v)
                return {
                    "cn": subj.get("commonName", "N/A"),
                    "issuer": issuer.get("organizationName", issuer.get("commonName", "N/A")),
                    "not_before": cert.get("notBefore", "N/A"),
                    "not_after": cert.get("notAfter", "N/A"),
                    "san": san[:20],
                    "serial": cert.get("serialNumber", "N/A"),
                }
        except Exception:
            pass
        return None

    def extract_secrets(self, text):
        found = []
        for pattern, name in self.SECRET_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches[:3]:
                val = m if isinstance(m, str) else m[0]
                found.append({"type": name, "value": val[:40] + "..." if len(val) > 40 else val})
        return found[:20]

    async def check_takeover(self, s, subdomains):
        vulnerable = []
        for sub in list(subdomains)[:30]:
            try:
                async with s.get(f"http://{sub}", headers=HDRS, timeout=aiohttp.ClientTimeout(total=4), ssl=False) as r:
                    body = await r.text()
                    for service, sig in self.TAKEOVER_SIGS.items():
                        if sig.lower() in body.lower():
                            vulnerable.append({"sub": sub, "service": service})
                            break
            except Exception:
                pass
        return vulnerable

    def analyze_spf_dmarc(self, dns_txt):
        result = {"spf": None, "dmarc": None, "issues": []}
        for t in dns_txt:
            if "v=spf1" in t:
                result["spf"] = t[:100]
                if "+all" in t: result["issues"].append("SPF: +all (allows any sender)")
                if "~all" in t: result["issues"].append("SPF: ~all (softfail, weak)")
                if "?all" in t: result["issues"].append("SPF: ?all (neutral, no protection)")
                if "-all" not in t and "~all" not in t and "+all" not in t:
                    result["issues"].append("SPF: no -all (missing strict reject)")
            if "v=DMARC" in t.upper():
                result["dmarc"] = t[:100]
                if "p=none" in t.lower(): result["issues"].append("DMARC: p=none (no enforcement)")
        if not result["spf"]: result["issues"].append("No SPF record found")
        if not result["dmarc"]: result["issues"].append("No DMARC record found")
        return result

    def extract_social(self, body):
        socials = {}
        patterns = {
            "Twitter/X": r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]{1,30})',
            "Facebook": r'facebook\.com/([a-zA-Z0-9._-]+)',
            "LinkedIn": r'linkedin\.com/(?:company|in)/([a-zA-Z0-9_-]+)',
            "Instagram": r'instagram\.com/([a-zA-Z0-9._]+)',
            "GitHub": r'github\.com/([a-zA-Z0-9_-]+)',
            "YouTube": r'youtube\.com/(?:c/|channel/|@)([a-zA-Z0-9_-]+)',
            "Telegram": r't\.me/([a-zA-Z0-9_]+)',
        }
        for name, pat in patterns.items():
            m = re.findall(pat, body, re.IGNORECASE)
            if m:
                vals = list(set(m))[:3]
                filtered = [v for v in vals if v not in ["share", "sharer", "intent", "dialog", "plugins"]]
                if filtered: socials[name] = filtered
        return socials

    def clean_out(self, text):
        lines = text.split('\n')
        out = []
        skip = ["___", "sqlmap.org", "[)]", "legal disclaimer", "starting @", "ending @",
                "multiple targets mode", "output/results", "fetched random",
                "using '/", "CSV results", "testing connection", "unable to connect",
                "skipping to the next", "if the problem persists", "is going to retry", "redirecting"]
        for l in lines:
            if any(x in l for x in skip): continue
            l = re.sub(r'\[\d{2}:\d{2}:\d{2}\]\s+', '', l)
            l = l.replace("[INFO]", "<tg-emoji emoji-id=5253590213917158323>💬</tg-emoji>").replace("[CRITICAL]", "<tg-emoji emoji-id=5253877736207821121>🔥</tg-emoji>").replace("[WARNING]", "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji>").replace("[ERROR]", "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji>")
            l = l.replace("is vulnerable", "ДЫРЯВЫЙ!").replace("sql injection", "SQL ИНЪЕКЦИЯ")
            if l.strip(): out.append(l.strip())
        return "\n".join(out)

    async def rtc(self, chat_id, uid, message, cmd, title):
        process = await asyncio.create_subprocess_shell(cmd, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
        self.active_processes[chat_id] = {"p": process, "u": uid, "o": ""}
        async def read():
            while True:
                c = await process.stdout.read(1)
                if not c: break
                self.active_processes[chat_id]["o"] += c.decode('utf-8', 'ignore')
        task = asyncio.create_task(read())
        while process.returncode is None:
            await asyncio.sleep(2.5)
            if chat_id not in self.active_processes: break
            raw = self.active_processes[chat_id]["o"]
            clean = self.clean_out(raw[-5000:])[-3500:]
            try: await utils.answer(message, f"<b>{title} (Live...):</b>\n<code>{clean}</code>\n\n<i>[.rcin для ввода]</i>")
            except: pass
        await task
        if chat_id in self.active_processes:
            raw = self.active_processes[chat_id]["o"]
            clean = self.clean_out(raw[-5000:])[-3800:]
            await utils.answer(message, f"<b>{title} (Done):</b>\n<code>{clean}</code>")
            self.active_processes.pop(chat_id, None)

    @loader.command(
        ru_doc="Убить процесс",
        uz_doc="Jarayonni to'xtatish",
        de_doc="Prozess beenden",
        es_doc="Matar proceso",
    )
    async def rcstop(self, message: Message):
        cid = utils.get_chat_id(message)
        if cid in self.active_processes:
            try: self.active_processes[cid]["p"].kill()
            except: pass
            self.active_processes.pop(cid, None)
        t = self.active_tasks.get(cid)
        if t and not t.done(): t.cancel()
        await utils.answer(message, self.strings("stopped"))

    @loader.command(
        ru_doc="<текст> - Ввод в консоль",
        uz_doc="<matn> - Konsolga kiritish",
        de_doc="<text> - Konsoleneingabe",
        es_doc="<texto> - Entrada en consola",
    )
    async def rcin(self, message: Message):
        cid = utils.get_chat_id(message)
        uid = message.sender_id
        if cid not in self.active_processes: return await utils.answer(message, self.strings("no_active"))
        if self.active_processes[cid]["u"] != uid: return await utils.answer(message, self.strings("not_owner"))
        pr = self.active_processes[cid]["p"]
        pr.stdin.write((utils.get_args_raw(message) + "\n").encode())
        await pr.stdin.drain()
        await message.delete()

    @loader.command(
        ru_doc="<IP> - Shodan",
        uz_doc="<IP> - Shodan",
        de_doc="<IP> - Shodan",
        es_doc="<IP> - Shodan",
    )
    async def shodan(self, message: Message):
        arg = utils.get_args_raw(message).strip()
        key = self.config["shodan_key"]
        if not arg or not key: return await utils.answer(message, "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> Укажи IP + shodan_key в .cfg</b>")
        await utils.answer(message, "<b><tg-emoji emoji-id=5255835635704408236>👤</tg-emoji> Shodan...</b>")
        async with aiohttp.ClientSession() as s:
            data = await self.fetch(s, f"https://api.shodan.io/shodan/host/{arg}?key={key}", "json")
        if "error" in data: return await utils.answer(message, f"<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji></b> <code>{data['error']}</code>")
        if not data: return await utils.answer(message, "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> Пусто.</b>")
        ports = ", ".join(map(str, data.get("ports", [])))
        vulns = "\n".join([f" ├ <code>{v}</code>" for v in data.get("vulns", [])[:15]]) if "vulns" in data else " └ Чисто"
        r = f"<tg-emoji emoji-id=5255835635704408236>👤</tg-emoji> <b>Shodan:</b> <code>{arg}</code>\n<tg-emoji emoji-id=5256094480498436162>📦</tg-emoji> {data.get('org','N/A')}\n<tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> OS: {data.get('os','N/A')}\n<tg-emoji emoji-id=5256182535917940722>⤵️</tg-emoji> <code>{ports}</code>\n<tg-emoji emoji-id=5253877736207821121>🔥</tg-emoji> CVE:\n{vulns}"
        await self.send_report(message, r, f"shodan_{arg}")

    @loader.command(
        ru_doc="<домен/IP> - WHOIS",
        uz_doc="<domen/IP> - WHOIS",
        de_doc="<Domain/IP> - WHOIS",
        es_doc="<dominio/IP> - WHOIS",
    )
    async def wh(self, message: Message):
        args = utils.get_args_raw(message).strip()
        if not args: return await utils.answer(message, self.strings("no_args"))
        await utils.answer(message, f"<b><tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> WHOIS: {args}...</b>")
        async with aiohttp.ClientSession() as s:
            ip_data = await self.fetch(s, f"http://ip-api.com/json/{args}?fields=query", "json")
            tip = ip_data.get("query", args) if isinstance(ip_data, dict) else args
            data = await self.whois_full(s, args, tip)
        if not data: return await utils.answer(message, f"<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> Нет данных: {args}</b>")
        r = f"<b>WHOIS {args}:</b>\n"
        for k, v in data.items():
            if isinstance(v, list): v = ", ".join(v[:5])
            if v and v != "N/A": r += f"├ <b>{k}:</b> <code>{v}</code>\n"
        await self.send_report(message, r, f"whois_{args}")

    @loader.command(
        ru_doc="<домен> - Google Dorks",
        uz_doc="<domen> - Google Dorks",
        de_doc="<Domain> - Google Dorks",
        es_doc="<dominio> - Google Dorks",
    )
    async def dork(self, message: Message):
        args = utils.get_args_raw(message).strip()
        if not args: return await utils.answer(message, self.strings("no_args"))
        await utils.answer(message, f"<b><tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> Dorks: {args}...</b>")
        async with aiohttp.ClientSession() as s:
            res = await self.parse_dorks(s, args)
        if not res: return await utils.answer(message, f"<b><tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> Dorks <code>{args}</code>:</b> ничего (Google block?)")
        r = f"<b><tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> Dorks: <code>{args}</code> ({len(res)}):</b>\n"
        for u in res[:40]: r += f"├ <code>{u[:80]}</code>\n"
        if len(res) > 40: r += f"└ <i>...ещё {len(res)-40}</i>\n"
        await self.send_report(message, r, f"dorks_{args}")

    @loader.command(
        ru_doc="<домен> [глубина] - Краулер (default 3)",
        uz_doc="<domen> [chuqurlik] - Crawler (default 3)",
        de_doc="<Domain> [Tiefe] - Crawler (Standard 3)",
        es_doc="<dominio> [profundidad] - Crawler (default 3)",
    )
    async def crawl(self, message: Message):
        raw = utils.get_args_raw(message).strip().split()
        if not raw: return await utils.answer(message, self.strings("no_args"))
        target, depth = raw[0], 3
        if len(raw) > 1:
            try: depth = min(int(raw[1]), 5)
            except: pass
        await utils.answer(message, f"<b><tg-emoji emoji-id=5256025060942031560>🐢</tg-emoji> Crawl: <code>{target}</code> (depth {depth})...</b>")
        async with aiohttp.ClientSession() as s:
            d = await self.crawl_site(s, target, depth)
        r = f"<b><tg-emoji emoji-id=5256025060942031560>🐢</tg-emoji> Crawl: <code>{target}</code></b>\nDepth: {depth} | Visited: {d['total']}\n\n"
        if d["urls"]:
            r += f"<b><tg-emoji emoji-id=5255917867148257511>🖼</tg-emoji> URLs ({len(d['urls'])}):</b>\n"
            for u in d["urls"][:30]: r += f"├ <code>{u[:80]}</code>\n"
            if len(d["urls"]) > 30: r += f"└ ...ещё {len(d['urls'])-30}\n"
        if d["forms"]:
            r += f"\n<b><tg-emoji emoji-id=5256230583717079814>📝</tg-emoji> Forms ({len(d['forms'])}):</b>\n"
            for f in d["forms"][:15]: r += f"├ <code>{f[:80]}</code>\n"
        if d["emails"]:
            r += f"\n<b><tg-emoji emoji-id=5256100953014152571>📧</tg-emoji> Emails ({len(d['emails'])}):</b>\n"
            for e in d["emails"][:15]: r += f"├ <code>{e}</code>\n"
        await self.send_report(message, r, f"crawl_{target}")

    @loader.command(
        ru_doc="<домен/IP> - Полный рекон",
        uz_doc="<domen/IP> - To'liq razvedka",
        de_doc="<Domain/IP> - Vollständige Aufklärung",
        es_doc="<dominio/IP> - Reconocimiento completo",
    )
    async def rc(self, message: Message):
        cid = utils.get_chat_id(message)
        self.active_tasks[cid] = asyncio.current_task()
        try:
            args = utils.get_args_raw(message)
            if not args: return await utils.answer(message, self.strings("no_args"))
            target = args.strip().lower()
            is_ip = bool(re.match(r"^(?:\d{1,3}\.){3}\d{1,3}$", target))
            await utils.answer(message, self.strings("processing").format(target))

            async with aiohttp.ClientSession() as s:
                geo = await self.fetch(s, f"http://ip-api.com/json/{target}?fields=status,query,isp,as,country,city,org,regionName,lat,lon,timezone", "json")
                tip = geo.get("query", target) if isinstance(geo, dict) and geo.get("status") == "success" else target
                isp = geo.get("isp", "N/A") if isinstance(geo, dict) and geo.get("status") == "success" else "N/A"

                waf = await self.detect_waf(target)
                if any(w in isp.lower() for w in ["cloudflare", "fastly", "akamai", "sucuri"]):
                    if not waf: waf = "CDN/WAF (ASN)"
                http = await self.fetch_full(target)

                api_tasks = [
                    self.fetch(s, f"https://api.hackertarget.com/dnslookup/?q={target}"),
                    self.fetch(s, f"https://ipwhois.app/json/{tip}", "json"),
                    self.fetch(s, f"https://otx.alienvault.com/api/v1/indicators/domain/{target}/general", "json"),
                    self.fetch(s, f"https://urlscan.io/api/v1/search/?q=domain:{target}&size=10", "json"),
                    self.fetch(s, f"https://api.hackertarget.com/reverseiplookup/?q={tip}"),
                ]
                key = self.config["shodan_key"]
                if self.config["use_shodan"] and key:
                    api_tasks.append(self.fetch(s, f"https://api.shodan.io/shodan/host/{tip}?key={key}", "json"))
                else:
                    api_tasks.append(self.fetch(s, f"https://internetdb.shodan.io/{tip}", "json"))

                if not is_ip:
                    api_tasks.extend([
                        self.fetch(s, f"https://crt.sh/?q=%25.{target}&output=json", "json"),
                        self.fetch(s, f"https://api.hackertarget.com/hostsearch/?q={target}"),
                        self.fetch(s, f"http://web.archive.org/cdx/search/cdx?url=*.{target}/*&output=json&limit=300", "json"),
                        self.fetch(s, f"https://rapiddns.io/subdomain/{target}?full=1"),
                        self.parse_robots(s, target),
                        self.parse_sitemap(s, target),
                    ])

                whois_task = asyncio.create_task(self.whois_full(s, target, tip))
                dork_task = asyncio.create_task(self.parse_dorks(s, target)) if not is_ip else None
                ssl_task = asyncio.create_task(self.get_ssl_info(target)) if not is_ip else None
                cors_task = asyncio.create_task(self.check_cors(s, target))
                methods_task = asyncio.create_task(self.check_http_methods(s, target))
                paths_task = asyncio.create_task(self.path_bruteforce(s, target))

                res = await asyncio.gather(*api_tasks)
                dns_res = res[0] if isinstance(res[0], str) and "error" not in res[0].lower()[:30] else ""
                ipw = res[1] if isinstance(res[1], dict) and res[1].get("success", True) is not False else {}
                otx = res[2] if isinstance(res[2], dict) and "pulse_info" in res[2] else {}
                urlscan = res[3] if isinstance(res[3], dict) and "results" in res[3] else {}
                rev_ip = res[4] if isinstance(res[4], str) and "error" not in str(res[4]).lower()[:30] else ""
                shodan_d = res[5] if isinstance(res[5], dict) and "error" not in str(res[5]) else {}

                whois_data = await whois_task
                ssl_info = await ssl_task if ssl_task else None
                cors_issues = await cors_task
                http_methods = await methods_task
                exposed_paths = await paths_task

                subdomains, wb_urls = set(), []
                dns_txt, dns_mx, dns_a, dns_ns, dns_cname = [], [], [], [], []
                real_ip = ""
                if dns_res:
                    for line in dns_res.split("\n"):
                        if "TXT :" in line: dns_txt.append(line.split("TXT :")[1].strip())
                        elif "MX :" in line: dns_mx.append(line.split("MX :")[1].strip())
                        elif "A :" in line: dns_a.append(line.split("A :")[1].strip())
                        elif "NS :" in line: dns_ns.append(line.split("NS :")[1].strip())
                        elif "CNAME :" in line: dns_cname.append(line.split("CNAME :")[1].strip())
                        if not is_ip and any(k in line for k in ["mail.", "ftp.", "direct.", "cpanel.", "dev."]):
                            parts = line.split(":")
                            if len(parts) > 1 and "cloudflare" not in parts[1].lower():
                                real_ip = parts[1].strip()

                rev_hosts = [h.strip() for h in rev_ip.split("\n") if h.strip()][:20] if rev_ip else []

                robots_txt, sitemap_urls = None, []
                if not is_ip and len(res) > 6:
                    bi = 6
                    crt_r = res[bi] if len(res) > bi and isinstance(res[bi], list) else []
                    ht_h = res[bi+1] if len(res) > bi+1 and isinstance(res[bi+1], str) and "error" not in str(res[bi+1]).lower()[:30] else ""
                    wb_r = res[bi+2] if len(res) > bi+2 and isinstance(res[bi+2], list) else []
                    rd_html = res[bi+3] if len(res) > bi+3 and isinstance(res[bi+3], str) else ""
                    robots_txt = res[bi+4] if len(res) > bi+4 and res[bi+4] else None
                    sitemap_urls = res[bi+5] if len(res) > bi+5 and isinstance(res[bi+5], list) else []

                    if isinstance(crt_r, list):
                        for e in crt_r:
                            n = e.get("name_value", "") if isinstance(e, dict) else ""
                            if n:
                                for x in n.split("\n"): subdomains.add(x.replace("*.", "").strip())
                    if ht_h:
                        for line in ht_h.split("\n"):
                            p = line.split(",")
                            if p and target in p[0]: subdomains.add(p[0].replace("*.", "").strip())
                    if rd_html:
                        for sd in re.findall(r'<td>([a-zA-Z0-9._-]+\.' + re.escape(target) + r')</td>', rd_html):
                            subdomains.add(sd.strip())
                    if isinstance(wb_r, list) and len(wb_r) > 1:
                        for entry in wb_r[1:]:
                            if isinstance(entry, list) and len(entry) > 2:
                                u = entry[2]
                                wb_urls.append(u)
                                try:
                                    h = urlparse(u).netloc.split(":")[0]
                                    if target in h: subdomains.add(h.replace("*.", "").strip())
                                except: pass
                    if isinstance(otx, dict):
                        for e in otx.get("passive_dns", []):
                            if isinstance(e, dict):
                                h = e.get("hostname", "")
                                if h and target in h: subdomains.add(h)

                ports = shodan_d.get("ports", [])
                vulns = shodan_d.get("vulns", [])
                if isinstance(vulns, dict): vulns = list(vulns.keys())
                tags = shodan_d.get("tags", [])
                cpes = shodan_d.get("cpes", [])

                otx_pulses = otx.get("pulse_info", {}).get("count", 0) if otx else 0
                otx_names = [p.get("name", "") for p in otx.get("pulse_info", {}).get("pulses", [])[:5]] if otx else []

                us_results = []
                if urlscan:
                    for r2 in urlscan.get("results", [])[:8]:
                        if isinstance(r2, dict):
                            pg = r2.get("page", {})
                            us_results.append({"url": pg.get("url", ""), "server": pg.get("server", ""), "ip": pg.get("ip", "")})

                tech, sec_found, sec_missing, js_files, page_emails, secrets, socials = [], [], [], [], [], [], {}
                if http:
                    body = http.get("body", "")
                    hdrs = http.get("headers", {})
                    tech = self.extract_tech(hdrs, body)
                    sec_found, sec_missing = self.check_sec_headers(hdrs)
                    js_files = self.extract_js(body, f"https://{target}")
                    page_emails = self.extract_emails(body)
                    secrets = self.extract_secrets(body)
                    socials = self.extract_social(body)

                if js_files:
                    js_bodies = await asyncio.gather(*[self.fetch(s, j) for j in js_files[:10]])
                    for jb in js_bodies:
                        if isinstance(jb, str) and jb:
                            secrets.extend(self.extract_secrets(jb))
                    seen = set()
                    secrets = [x for x in secrets if (k := f"{x['type']}:{x['value']}") not in seen and not seen.add(k)][:25]

                wb_params = self.extract_params_from_urls(wb_urls) if wb_urls else []
                spf_dmarc = self.analyze_spf_dmarc(dns_txt) if dns_txt else {"spf": None, "dmarc": None, "issues": ["No SPF record found", "No DMARC record found"]}

                takeover = []
                if not is_ip and subdomains:
                    takeover = await self.check_takeover(s, subdomains)

                R = f"<tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> <b>Recon:</b> <code>{target}</code>\n"
                R += f"<tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> <b>IP:</b> <code>{tip}</code>\n"
                if waf: R += f"<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> <b>WAF:</b> <code>{waf}</code>\n"
                if real_ip: R += f"<tg-emoji emoji-id=5253617001628181935>👌</tg-emoji> <b>Real IP (bypass):</b> <code>{real_ip}</code>\n"
                R += f"<tg-emoji emoji-id=5256094480498436162>📦</tg-emoji> <b>ISP:</b> {isp}\n"
                if isinstance(geo, dict) and geo.get("status") == "success":
                    R += f"<tg-emoji emoji-id=5253830568876977751>🏳️</tg-emoji> <b>Geo:</b> {geo.get('country','')}, {geo.get('regionName','')}, {geo.get('city','')}\n"
                    R += f"<tg-emoji emoji-id=5253713110111365241>📍</tg-emoji> <b>Coords:</b> <code>{geo.get('lat','')}, {geo.get('lon','')}</code>\n"
                    R += f"<tg-emoji emoji-id=5255971360965930740>🕔</tg-emoji> <b>TZ:</b> {geo.get('timezone','')}\n"
                    R += f"<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>ASN:</b> <code>{geo.get('as','')}</code>\n"
                R += "\n"

                if whois_data:
                    R += "<tg-emoji emoji-id=5256230583717079814>📝</tg-emoji> <b>WHOIS:</b>\n"
                    for k, v in whois_data.items():
                        if isinstance(v, list): v = ", ".join(v[:5])
                        if v and str(v) != "N/A": R += f" ├ <b>{k}:</b> <code>{v}</code>\n"
                    R += "\n"

                if ssl_info:
                    R += "<tg-emoji emoji-id=5253780051471642059>🛡</tg-emoji> <b>SSL/TLS:</b>\n"
                    R += f" ├ CN: <code>{ssl_info['cn']}</code>\n"
                    R += f" ├ Issuer: <code>{ssl_info['issuer']}</code>\n"
                    R += f" ├ Valid: {ssl_info['not_before']} → {ssl_info['not_after']}\n"
                    R += f" ├ Serial: <code>{ssl_info['serial'][:20]}</code>\n"
                    if ssl_info.get("san"):
                        R += f" └ SAN: <code>{', '.join(ssl_info['san'][:8])}</code>\n"
                    R += "\n"

                if http:
                    srv = http.get("headers", {}).get("Server", "Hidden")
                    pw = http.get("headers", {}).get("X-Powered-By", "Hidden")
                    R += f"<tg-emoji emoji-id=5253830568876977751>🏳️</tg-emoji> <b>HTTP:</b>\n ├ Status: <code>{http.get('status')}</code>\n ├ Title: <code>{http.get('title','')}</code>\n ├ Server: <code>{srv}</code>\n └ Powered: <code>{pw}</code>\n\n"

                if http_methods:
                    R += f"<tg-emoji emoji-id=5253952855185829086>⚙️</tg-emoji> <b>HTTP Methods:</b> <code>{', '.join(http_methods)}</code>\n\n"

                if tech:
                    R += f"<tg-emoji emoji-id=5253952855185829086>⚙️</tg-emoji> <b>Tech Stack ({len(tech)}):</b>\n"
                    for t2 in tech: R += f" ├ <code>{t2}</code>\n"
                    R += "\n"

                R += f"<tg-emoji emoji-id=5256182535917940722>⤵️</tg-emoji> <b>Ports:</b> <code>{', '.join(map(str, ports)) if ports else 'N/A'}</code>\n"
                if tags: R += f"<tg-emoji emoji-id=5256054975389247793>📛</tg-emoji> <b>Tags:</b> <code>{', '.join(tags)}</code>\n"
                if cpes: R += f"<tg-emoji emoji-id=5256094480498436162>📦</tg-emoji> <b>CPE:</b>\n" + "".join([f" ├ <code>{c}</code>\n" for c in cpes[:8]])
                R += "\n"

                if dns_a or dns_ns or dns_mx or dns_txt or dns_cname:
                    R += "<tg-emoji emoji-id=5256230583717079814>📝</tg-emoji> <b>DNS:</b>\n"
                    if dns_a: R += f" ├ <b>A:</b> <code>{', '.join(dns_a[:5])}</code>\n"
                    if dns_cname: R += f" ├ <b>CNAME:</b> <code>{', '.join(dns_cname[:3])}</code>\n"
                    if dns_ns: R += f" ├ <b>NS:</b> <code>{', '.join(dns_ns[:5])}</code>\n"
                    if dns_mx: R += f" ├ <b>MX:</b> <code>{', '.join(dns_mx[:3])}</code>\n"
                    for t2 in dns_txt[:3]: R += f" ├ <b>TXT:</b> <code>{t2[:70]}</code>\n"
                    R += "\n"

                if spf_dmarc["issues"]:
                    R += "<tg-emoji emoji-id=5256100953014152571>📧</tg-emoji> <b>SPF/DMARC:</b>\n"
                    if spf_dmarc["spf"]: R += f" ├ SPF: <code>{spf_dmarc['spf'][:60]}</code>\n"
                    if spf_dmarc["dmarc"]: R += f" ├ DMARC: <code>{spf_dmarc['dmarc'][:60]}</code>\n"
                    for issue in spf_dmarc["issues"]: R += f" ├ <tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> {issue}\n"
                    R += "\n"

                if sec_found or sec_missing:
                    R += f"<tg-emoji emoji-id=5253780051471642059>🛡</tg-emoji> <b>Security Headers:</b>\n"
                    for h2, v in sec_found: R += f" ├ <tg-emoji emoji-id=5255813619702049821>✅</tg-emoji> <code>{h2}</code>\n"
                    for h2 in sec_missing: R += f" ├ <tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> <code>{h2}</code>\n"
                    R += "\n"

                if cors_issues:
                    R += "<tg-emoji emoji-id=5253877736207821121>🔥</tg-emoji> <b>CORS Issues:</b>\n"
                    for ci in cors_issues: R += f" ├ <tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> <code>{ci}</code>\n"
                    R += "\n"

                if vulns:
                    R += f"<tg-emoji emoji-id=5253877736207821121>🔥</tg-emoji> <b>CVE ({len(vulns)}):</b>\n"
                    for cve in vulns[:20]: R += f" ├ <code>{cve}</code>\n"
                    if len(vulns) > 20: R += f" └ ...+{len(vulns)-20}\n"
                    R += "\n"

                if exposed_paths:
                    R += f"<tg-emoji emoji-id=5253647062104287098>🔓</tg-emoji> <b>Exposed Paths ({len(exposed_paths)}):</b>\n"
                    for ep in exposed_paths[:25]:
                        icon = "<tg-emoji emoji-id=5255813619702049821>✅</tg-emoji>" if ep["status"] == 200 else "<tg-emoji emoji-id=5255813619702049821>✅</tg-emoji>" if ep["status"] in (301,302) else "<tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji>"
                        R += f" ├ {icon} <code>{ep['path']}</code> [{ep['status']}] {ep['size']}b\n"
                    if len(exposed_paths) > 25: R += f" └ ...+{len(exposed_paths)-25}\n"
                    R += "\n"

                if secrets:
                    R += f"<tg-emoji emoji-id=5253490441826870592>🔗</tg-emoji> <b>Leaked Secrets ({len(secrets)}):</b>\n"
                    for sec in secrets[:15]: R += f" ├ {sec['type']}: <code>{sec['value']}</code>\n"
                    R += "\n"

                if otx_pulses > 0:
                    R += f"<tg-emoji emoji-id=5253780051471642059>🛡</tg-emoji> <b>OTX Threats:</b> {otx_pulses}\n"
                    for n in otx_names[:3]: R += f" ├ <code>{n[:60]}</code>\n"
                    R += "\n"

                if us_results:
                    R += f"<tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> <b>URLScan ({len(us_results)}):</b>\n"
                    for r2 in us_results[:5]: R += f" ├ <code>{r2['url'][:55]}</code> | {r2['server']}\n"
                    R += "\n"

                if rev_hosts:
                    R += f"<tg-emoji emoji-id=5253464392850221514>🔃</tg-emoji> <b>Reverse IP ({len(rev_hosts)}):</b>\n"
                    for h2 in rev_hosts[:10]: R += f" ├ <code>{h2}</code>\n"
                    if len(rev_hosts) > 10: R += f" └ ...+{len(rev_hosts)-10}\n"
                    R += "\n"

                if not is_ip:
                    subs = sorted([x for x in subdomains if target in x and x])
                    R += f"<tg-emoji emoji-id=5253526631221307799>📂</tg-emoji> <b>Subdomains ({len(subs)}):</b>\n"
                    for x in subs[:50]: R += f" ├ <code>{x}</code>\n"
                    if len(subs) > 50: R += f" └ ...+{len(subs)-50}\n"
                    R += "\n"

                    if takeover:
                        R += f"<tg-emoji emoji-id=5253877736207821121>🔥</tg-emoji> <b>Subdomain Takeover ({len(takeover)}):</b>\n"
                        for tk in takeover: R += f" ├ <tg-emoji emoji-id=5253877736207821121>🔥</tg-emoji> <code>{tk['sub']}</code> → {tk['service']}\n"
                        R += "\n"

                    if wb_urls:
                        R += f"<tg-emoji emoji-id=5253651477330667400>🎞</tg-emoji> <b>Wayback URLs ({len(wb_urls)}):</b>\n"
                        for u in wb_urls[:20]: R += f" ├ <code>{u[:65]}</code>\n"
                        if len(wb_urls) > 20: R += f" └ ...+{len(wb_urls)-20}\n"
                        R += "\n"

                    if wb_params:
                        R += f"<tg-emoji emoji-id=5253775593295588000>📝</tg-emoji> <b>URL Params ({len(wb_params)}):</b>\n └ <code>{', '.join(wb_params[:40])}</code>\n\n"

                if js_files:
                    R += f"<tg-emoji emoji-id=5255917867148257511>🖼</tg-emoji> <b>JS Files ({len(js_files)}):</b>\n"
                    for j in js_files[:15]: R += f" ├ <code>{j[:70]}</code>\n"
                    if len(js_files) > 15: R += f" └ ...+{len(js_files)-15}\n"
                    R += "\n"

                if page_emails:
                    R += f"<tg-emoji emoji-id=5256100953014152571>📧</tg-emoji> <b>Emails ({len(page_emails)}):</b>\n"
                    for e in page_emails[:15]: R += f" ├ <code>{e}</code>\n"
                    R += "\n"

                if socials:
                    R += "<tg-emoji emoji-id=5253830568876977751>🏳️</tg-emoji> <b>Socials:</b>\n"
                    for name, vals in socials.items(): R += f" ├ {name}: <code>{', '.join(vals)}</code>\n"
                    R += "\n"

                if robots_txt:
                    R += f"<tg-emoji emoji-id=5256025060942031560>🐢</tg-emoji> <b>robots.txt:</b>\n<code>{robots_txt[:500]}</code>\n\n"

                if sitemap_urls:
                    R += f"<tg-emoji emoji-id=5253961389285845297>📌</tg-emoji> <b>Sitemap ({len(sitemap_urls)}):</b>\n"
                    for u in sitemap_urls[:10]: R += f" ├ <code>{u[:65]}</code>\n"
                    if len(sitemap_urls) > 10: R += f" └ ...+{len(sitemap_urls)-10}\n"
                    R += "\n"

                if not is_ip:
                    dork_res = await dork_task if dork_task else []
                    if dork_res:
                        R += f"<tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> <b>Dorks ({len(dork_res)}):</b>\n"
                        for u in dork_res[:15]: R += f" ├ <code>{u[:65]}</code>\n"
                        if len(dork_res) > 15: R += f" └ ...+{len(dork_res)-15}\n"
                    else:
                        R += f"<tg-emoji emoji-id=5256079005731271025>📟</tg-emoji> <b>Dorks (manual):</b>\n"
                        R += f" ├ <code>site:{target} ext:php | ext:env | ext:log</code>\n"
                        R += f" ├ <code>site:{target} inurl:admin | inurl:login</code>\n"
                        R += f" └ <code>site:{target} ext:sql | ext:bak | ext:conf</code>\n"

                await self.send_report(message, R, f"recon_{target}")

        except asyncio.CancelledError: pass
        except Exception as e: await utils.answer(message, f"<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji></b> <code>{str(e)}</code>")
        finally: self.active_tasks.pop(cid, None)
    @loader.command(
        ru_doc="[аргументы] - Nmap",
        uz_doc="[argumentlar] - Nmap",
        de_doc="[Argumente] - Nmap",
        es_doc="[argumentos] - Nmap",
    )
    async def nmap(self, message: Message):
        cid = utils.get_chat_id(message)
        uid = message.sender_id
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, (
                "> <tg-emoji emoji-id=5249019346512008974>▶️</tg-emoji> **.nmap guide**\n"
                "> ` .nmap example.com ` - quick\n"
                "> ` .nmap -p 80,443 example.com ` - ports\n"
                "> ` .nmap -sV -O 8.8.8.8 ` - versions+OS\n\n"
                "> `-sS` stealth | `-sV` versions | `-p-` all ports\n"
                "> `-T4` fast | `-A` aggressive | `-Pn` no ping"
            ))
        if not shutil.which("nmap"):
            return await utils.answer(message, "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> nmap не найден. Установи вручную и повтори.</b>")
        await self.rtc(cid, uid, message, f"nmap {args}", "<tg-emoji emoji-id=5249019346512008974>▶️</tg-emoji> Nmap")

    @loader.command(
        ru_doc="[аргументы] - SQLMap",
        uz_doc="[argumentlar] - SQLMap",
        de_doc="[Argumente] - SQLMap",
        es_doc="[argumentos] - SQLMap",
    )
    async def sqlmap(self, message: Message):
        cid = utils.get_chat_id(message)
        uid = message.sender_id
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, (
                "> <tg-emoji emoji-id=5256054356913957552>🎙</tg-emoji> **.sqlmap guide**\n"
                "> ` .sqlmap -u \"site.com/page.php?id=1\" `\n"
                "> ` .sqlmap -u \"...\" --dbs ` - databases\n"
                "> ` .sqlmap -u \"...\" -D db --tables `\n\n"
                "> `--level=5` max | `--risk=3` aggressive\n"
                "> `--dump` extract | `--os-shell` shell\n"
                "> `--tamper=space2comment` waf bypass"
            ))
        sp = "sqlmap-dev/sqlmap.py"
        if not os.path.exists("sqlmap-dev"):
            return await utils.answer(message, "<b><tg-emoji emoji-id=5253864872780769235>❗️</tg-emoji> sqlmap-dev не найден. Клонируй sqlmap вручную в папку sqlmap-dev.</b>")
        await self.rtc(cid, uid, message, f"python3 {sp} {args}", "<tg-emoji emoji-id=5256054356913957552>🎙</tg-emoji> SQLMap")

    @loader.watcher(ignore_edited=True)
    async def watcher(self, message: Message):
        if hasattr(message, "message") and not hasattr(message, "get_sender"):
            message = getattr(message, "message", message)
        if not hasattr(message, "chat_id"):
            return
        sender_id = getattr(message, "sender_id", None)

        if sender_id is None:
            getter = getattr(message, "get_sender", None)
            if callable(getter):
                try:
                    sender = await getter()
                except Exception:
                    sender = None
                else:
                    sender_id = getattr(sender, "id", None)

        if sender_id is None:
            return

        if sender_id == self._tg_id:
            return


