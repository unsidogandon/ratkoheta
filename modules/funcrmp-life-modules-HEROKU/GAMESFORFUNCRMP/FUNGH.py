"""
    🔧 FUNGH - GitHub управление (оптимизированный)
"""

__version__ = (2, 0, 0)

# meta developer: @zymoyhold
# requires: aiohttp

import aiohttp, asyncio, time, base64
from .. import loader, utils

@loader.tds
class FunGithubMod(loader.Module):
    """FUNGH - GitHub управление"""
    strings = {"name": "FUNGH"}
    
    def __init__(self):
        self.cfg = loader.ModuleConfig(
            loader.ConfigValue("github_token", "", "GitHub API токен"),
            loader.ConfigValue("monitor_channel", "", "Канал для уведомлений"),
        )
        self.monitoring = False
        self.repos = {}
        self.sess = None

    async def client_ready(self, client, db):
        self._client, self._db = client, db
        self.me = await client.get_me()
        self.repos = self._db.get(__name__, "repos", {})
        
        h = {"User-Agent": "Mozilla/5.0"}
        if token := self.cfg['github_token']:
            h["Authorization"] = f"token {token}"
        self.sess = aiohttp.ClientSession(headers=h)

    def _save(self):
        self._db.set(__name__, "repos", self.repos)

    # ==================== ОСНОВНЫЕ КОМАНДЫ ====================
    @loader.command()
    async def funghapi(self, m):
        """Установить GitHub API токен"""
        a = utils.get_args_raw(m)
        if not a:
            t = self.cfg['github_token']
            await utils.answer(m, f"🔑 <b>Токен:</b> {'✅' if t else '❌'}")
            return
        self.cfg["github_token"] = a.strip()
        if self.sess:
            self.sess.headers["Authorization"] = f"token {a.strip()}"
        await utils.answer(m, "✅ <b>Токен установлен</b>")

    @loader.command()
    async def ghchannel(self, m):
        """Установить канал для уведомлений"""
        a = utils.get_args_raw(m)
        if not a:
            c = self.cfg['monitor_channel']
            await utils.answer(m, f"📢 <b>Канал:</b> {'@' + c if c else '❌'}")
            return
        self.cfg["monitor_channel"] = a.strip().replace('@', '')
        await utils.answer(m, f"✅ <b>Канал:</b> @{self.cfg['monitor_channel']}")

    @loader.command()
    async def startgh(self, m):
        """Запустить мониторинг"""
        if not self.cfg['github_token']:
            await utils.answer(m, "❌ <b>Установите токен</b>")
            return
        if self.monitoring:
            await utils.answer(m, "❌ <b>Уже активно</b>")
            return
        self.monitoring = True
        await utils.answer(m, "🚀 <b>Мониторинг запущен</b>")
        asyncio.create_task(self._monitor_loop())

    @loader.command()
    async def stopgh(self, m):
        """Остановить мониторинг"""
        if not self.monitoring:
            await utils.answer(m, "❌ <b>Не активно</b>")
            return
        self.monitoring = False
        await utils.answer(m, "🛑 <b>Мониторинг остановлен</b>")

    @loader.command()
    async def funall(self, m):
        """Добавить репозиторий для отслеживания"""
        if not self.cfg['github_token']:
            await utils.answer(m, "❌ <b>Установите токен</b>")
            return
        a = utils.get_args_raw(m)
        if not a:
            await utils.answer(m, "🔍 .funall owner/repo")
            return
        repo = a.strip()
        info = await self._get_repo_info(repo)
        if not info:
            await utils.answer(m, f"❌ <b>Не найден:</b> {repo}")
            return
        files = await self._get_repo_files(repo)
        self.repos[repo] = {
            "last_commit": info.get("pushed_at", ""),
            "files": {f["path"]: f.get("sha", "") for f in files[:50]},
            "last_check": time.time()
        }
        self._save()
        await utils.answer(m, f"✅ <b>Добавлен:</b> {repo}")

    @loader.command()
    async def funlist(self, m):
        """Список отслеживаемых репозиториев"""
        if not self.repos:
            await utils.answer(m, "📭 <b>Нет репозиториев</b>")
            return
        text = "📋 <b>Репозитории:</b>\n"
        for repo in self.repos:
            text += f"• <b>{repo}</b>\n"
        await utils.answer(m, text)

    @loader.command()
    async def funremove(self, m):
        """Удалить репозиторий"""
        a = utils.get_args_raw(m)
        if not a:
            await utils.answer(m, "🗑️ .funremove owner/repo")
            return
        repo = a.strip()
        if repo in self.repos:
            del self.repos[repo]
            self._save()
            await utils.answer(m, f"✅ <b>Удален:</b> {repo}")
        else:
            await utils.answer(m, f"❌ <b>Не найден:</b> {repo}")

    # ==================== РЕДАКТИРОВАНИЕ ====================
    @loader.command()
    async def ghedit(self, m):
        """Изменить/создать файл"""
        if not self.cfg['github_token']:
            await utils.answer(m, "❌ <b>Установите токен</b>")
            return
        a = utils.get_args_raw(m)
        if not a:
            await utils.answer(m, "✏️ .ghedit repo path/file [commit]")
            return
        if not m.is_reply:
            await utils.answer(m, "❌ <b>Ответьте на файл</b>")
            return
        reply = await m.get_reply_message()
        if not reply.media:
            await utils.answer(m, "❌ <b>Нет файла</b>")
            return
        
        p = a.split()
        if len(p) < 2:
            await utils.answer(m, "❌ .ghedit repo path/file")
            return
        
        repo, path = p[0], p[1]
        msg = " ".join(p[2:]) if len(p) > 2 else "Update"
        
        await utils.answer(m, f"📝 <b>Загружаю...</b>\n{path}")
        
        try:
            data = await reply.download_media(bytes)
            if not data:
                await utils.answer(m, "❌ <b>Ошибка загрузки</b>")
                return
            
            content = base64.b64encode(data).decode()
            file_info = await self._get_file_info(repo, path)
            
            if file_info:
                sha = file_info.get("sha")
                res = await self._update_file(repo, path, sha, content, msg)
                action = "обновлен"
            else:
                res = await self._create_file(repo, path, content, msg)
                action = "создан"
            
            if res:
                url = f"https://github.com/{repo}/blob/main/{path}"
                if c := self.cfg['monitor_channel']:
                    await self._send_msg(c, f"✅ <b>Файл {action}</b>\n{repo}\n{path}")
                await utils.answer(m, f"✅ <b>Файл {action}!</b>\n🔗 {url}")
            else:
                await utils.answer(m, f"❌ <b>Ошибка</b>")
                
        except Exception as e:
            await utils.answer(m, f"❌ <b>Ошибка:</b>\n{str(e)[:100]}")

    @loader.command()
    async def ghdelete(self, m):
        """Удалить файл"""
        if not self.cfg['github_token']:
            await utils.answer(m, "❌ <b>Установите токен</b>")
            return
        a = utils.get_args_raw(m)
        if not a:
            await utils.answer(m, "🗑️ .ghdelete repo path/file [commit]")
            return
        
        p = a.split()
        if len(p) < 2:
            await utils.answer(m, "❌ .ghdelete repo path/file")
            return
        
        repo, path = p[0], p[1]
        msg = " ".join(p[2:]) if len(p) > 2 else f"Remove {path}"
        
        await utils.answer(m, f"🗑️ <b>Удаляю...</b>\n{path}")
        
        try:
            file_info = await self._get_file_info(repo, path)
            if not file_info:
                await utils.answer(m, f"❌ <b>Файл не найден</b>")
                return
            
            sha = file_info.get("sha")
            res = await self._delete_file(repo, path, sha, msg)
            
            if res:
                if c := self.cfg['monitor_channel']:
                    await self._send_msg(c, f"🗑️ <b>Файл удален</b>\n{repo}\n{path}")
                await utils.answer(m, f"✅ <b>Файл удален!</b>\n{path}")
            else:
                await utils.answer(m, "❌ <b>Ошибка удаления</b>")
                
        except Exception as e:
            await utils.answer(m, f"❌ <b>Ошибка:</b>\n{str(e)[:100]}")

    @loader.command()
    async def ghrename(self, m):
        """Переименовать файл"""
        if not self.cfg['github_token']:
            await utils.answer(m, "❌ <b>Установите токен</b>")
            return
        a = utils.get_args_raw(m)
        if not a:
            await utils.answer(m, "📝 .ghrename repo old/path new/path [commit]")
            return
        
        p = a.split()
        if len(p) < 3:
            await utils.answer(m, "❌ .ghrename repo old/path new/path")
            return
        
        repo, old, new = p[0], p[1], p[2]
        msg = " ".join(p[3:]) if len(p) > 3 else f"Rename {old} to {new}"
        
        await utils.answer(m, f"📝 <b>Переименовываю...</b>\n{old} → {new}")
        
        try:
            file_info = await self._get_file_info(repo, old)
            if not file_info:
                await utils.answer(m, f"❌ <b>Файл не найден:</b> {old}")
                return
            
            # Копируем содержимое
            content = file_info.get("content", "")
            sha = file_info.get("sha")
            
            # Создаем новый файл
            create = await self._create_file(repo, new, content, msg)
            if not create:
                await utils.answer(m, "❌ <b>Ошибка создания</b>")
                return
            
            # Удаляем старый
            await self._delete_file(repo, old, sha, msg)
            
            if c := self.cfg['monitor_channel']:
                await self._send_msg(c, f"📝 <b>Файл переименован</b>\n{repo}\n{old} → {new}")
            
            await utils.answer(m, f"✅ <b>Переименовано!</b>\n{old} → {new}")
            
        except Exception as e:
            await utils.answer(m, f"❌ <b>Ошибка:</b>\n{str(e)[:100]}")

    @loader.command()
    async def ghdebug(self, m):
        """Проверить доступ"""
        a = utils.get_args_raw(m)
        if not a:
            await utils.answer(m, "🔍 .ghdebug owner/repo")
            return
        
        repo = a.strip()
        await utils.answer(m, f"🔍 <b>Проверяю {repo}...</b>")
        
        try:
            info = await self._get_repo_info(repo)
            if not info:
                await utils.answer(m, f"❌ <b>Не найден:</b> {repo}")
                return
            
            # Тест записи
            test_url = f"https://api.github.com/repos/{repo}/contents/.fungh_test"
            test_data = {"message": "Test", "content": "dGVzdA==", "branch": "main"}
            
            async with self.sess.put(test_url, json=test_data) as r:
                if r.status == 201:
                    # Очистка
                    await self.sess.delete(test_url, json={"message": "Clean", "sha": "test", "branch": "main"})
                    await utils.answer(m, f"✅ <b>Доступ есть!</b>\n{repo}")
                else:
                    await utils.answer(m, f"❌ <b>Нет прав записи</b> (статус: {r.status})")
                    
        except Exception as e:
            await utils.answer(m, f"❌ <b>Ошибка:</b>\n{str(e)[:100]}")

    # ==================== МОНИТОРИНГ ====================
    async def _monitor_loop(self):
        while self.monitoring:
            for repo in list(self.repos.keys()):
                if not self.monitoring:
                    break
                await self._check_repo(repo)
                await asyncio.sleep(2)
            if self.monitoring:
                await asyncio.sleep(60)

    async def _check_repo(self, repo):
        try:
            info = await self._get_repo_info(repo)
            if not info:
                return
            
            data = self.repos[repo]
            last = info.get("pushed_at")
            
            if last != data.get("last_commit"):
                commits = await self._get_repo_commits(repo)
                if commits and (c := self.cfg['monitor_channel']):
                    msg = commits[0].get("commit", {}).get("message", "")[:50]
                    await self._send_msg(c, f"🔄 <b>Новые коммиты</b>\n{repo}\n💬 {msg}...")
                data["last_commit"] = last
            
            files = await self._get_repo_files(repo)
            old = data.get("files", {})
            
            new_files = []
            for f in files[:30]:
                path, sha = f.get("path"), f.get("sha", "")
                if path not in old:
                    new_files.append(path)
                elif old.get(path) != sha and (c := self.cfg['monitor_channel']):
                    await self._send_msg(c, f"✏️ <b>Файл изменен</b>\n{repo}\n📝 {path}")
            
            if new_files and (c := self.cfg['monitor_channel']):
                for path in new_files[:3]:
                    await self._send_msg(c, f"📁 <b>Новый файл</b>\n{repo}\n➕ {path}")
            
            data["files"] = {f["path"]: f.get("sha", "") for f in files[:30]}
            data["last_check"] = time.time()
            self._save()
            
        except:
            pass

    # ==================== API МЕТОДЫ ====================
    async def _get_repo_info(self, repo):
        try:
            async with self.sess.get(f"https://api.github.com/repos/{repo}") as r:
                if r.status == 200:
                    return await r.json()
        except:
            pass
        return None

    async def _get_repo_files(self, repo):
        try:
            async with self.sess.get(f"https://api.github.com/repos/{repo}/contents") as r:
                if r.status == 200:
                    return await r.json()
        except:
            pass
        return []

    async def _get_repo_commits(self, repo):
        try:
            async with self.sess.get(f"https://api.github.com/repos/{repo}/commits?per_page=3") as r:
                if r.status == 200:
                    return await r.json()
        except:
            pass
        return []

    async def _get_file_info(self, repo, path):
        try:
            async with self.sess.get(f"https://api.github.com/repos/{repo}/contents/{path}") as r:
                if r.status == 200:
                    return await r.json()
        except:
            pass
        return None

    async def _create_file(self, repo, path, content, msg):
        try:
            url = f"https://api.github.com/repos/{repo}/contents/{path}"
            data = {"message": msg, "content": content, "branch": "main"}
            async with self.sess.put(url, json=data) as r:
                return r.status in [200, 201]
        except:
            return False

    async def _update_file(self, repo, path, sha, content, msg):
        try:
            url = f"https://api.github.com/repos/{repo}/contents/{path}"
            data = {"message": msg, "content": content, "sha": sha, "branch": "main"}
            async with self.sess.put(url, json=data) as r:
                return r.status in [200, 201]
        except:
            return False

    async def _delete_file(self, repo, path, sha, msg):
        try:
            url = f"https://api.github.com/repos/{repo}/contents/{path}"
            data = {"message": msg, "sha": sha, "branch": "main"}
            async with self.sess.delete(url, json=data) as r:
                return r.status in [200, 204]
        except:
            return False

    async def _send_msg(self, channel, text):
        try:
            await self._client.send_message(f"@{channel}", text)
        except:
            pass

    async def on_unload(self):
        if self.sess:
            await self.sess.close()
        self.monitoring = False