# meta developer: @coddan
import base64
import os
import re
import aiohttp
from .. import loader, utils

@loader.tds
class GitHubUploaderMod(loader.Module):
    """Загружает файлы и модули напрямую в ваш репозиторий GitHub."""
    
    strings = {"name": "GitHubUploader"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "github_token",
                "",
                lambda: "Персональный токен доступа GitHub (требуются права repo)",
                validator=loader.validators.Hidden(),
            ),
            loader.ConfigValue(
                "github_repo",
                "",
                lambda: "Репозиторий GitHub (например, 'username/repo')",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "github_branch",
                "main",
                lambda: "Целевая ветка (например, 'main' или 'master')",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "github_path",
                "",
                lambda: "Путь к директории внутри репозитория (например, 'modules', оставьте пустым для корня)",
                validator=loader.validators.String(),
            )
        )

    async def _upload_to_github(self, filename: str, content: bytes) -> tuple:
        """Внутренний метод для обработки запросов к API GitHub"""
        token = self.config["github_token"].strip()
        repo = self.config["github_repo"].strip()
        branch = self.config["github_branch"].strip()
        base_path = self.config["github_path"].strip().strip("/")
        
        # Очистка строки репозитория, если пользователь вставил полную ссылку
        repo = repo.replace("https://", "").replace("http://", "").replace("github.com/", "")
        repo_parts = [p for p in repo.split("/") if p]
        if len(repo_parts) >= 2:
            repo = f"{repo_parts[0]}/{repo_parts[1]}"
        repo = repo.replace(".git", "")
        
        filename = filename.strip("/")
        path = f"{base_path}/{filename}" if base_path else filename
        path = re.sub(r"/+", "/", path)
        
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with aiohttp.ClientSession() as session:
            # 1. Проверка существования файла для получения его SHA (нужно для обновления)
            sha = None
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    sha = data.get("sha")
            
            # 2. Загрузка или обновление файла
            payload = {
                "message": f"Загрузка {filename} через Heroku Userbot",
                "content": base64.b64encode(content).decode('utf-8'),
                "branch": branch
            }
            if sha:
                payload["sha"] = sha
                
            async with session.put(url, headers=headers, json=payload) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    return True, data.get("content", {}).get("html_url", "Успешно")
                else:
                    err = await resp.text()
                    if resp.status == 404:
                        err += "\n\nПодсказка: 404 обычно означает, что репозиторий/ветка не существует, или у вашего токена нет прав 'repo'."
                    return False, f"Ошибка API {resp.status}: {err}"

    @loader.command()
    async def ghupcmd(self, message):
        """<реплай на файл | путь_к_файлу> [имя_файла] - Загрузить файл/модуль на GitHub"""
        if not self.config["github_token"] or not self.config["github_repo"]:
            await utils.answer(
                message,
                "<b>[GitHubUploader]</b> Пожалуйста, настройте <code>github_token</code> и <code>github_repo</code> в настройках модуля."
            )
            return

        reply = await message.get_reply_message()
        args = utils.get_args_raw(message)
        
        content = None
        filename = None

        if reply and reply.media and reply.document:
            filename = args if args else reply.file.name
            if not filename:
                filename = "uploaded_module.py"
            
            await utils.answer(message, f"<b>[GitHubUploader]</b> Скачивание <code>{filename}</code>...")
            content = await reply.download_media(bytes)
            
        elif args:
            parts = args.split(maxsplit=1)
            file_path = parts[0]
            
            if os.path.isfile(file_path):
                filename = parts[1] if len(parts) > 1 else os.path.basename(file_path)
                await utils.answer(message, f"<b>[GitHubUploader]</b> Чтение локального файла <code>{file_path}</code>...")
                with open(file_path, "rb") as f:
                    content = f.read()
            else:
                await utils.answer(message, f"<b>[GitHubUploader]</b> Файл <code>{file_path}</code> не найден локально.")
                return
        else:
            await utils.answer(message, "<b>[GitHubUploader]</b> Пожалуйста, ответьте на файл или укажите путь к локальному файлу.")
            return

        if not content:
            await utils.answer(message, "<b>[GitHubUploader]</b> Не удалось получить содержимое файла.")
            return

        await utils.answer(message, f"<b>[GitHubUploader]</b> Загрузка <code>{filename}</code> в репозиторий GitHub <code>{self.config['github_repo']}</code>...")
        
        success, result = await self._upload_to_github(filename, content)
        
        if success:
            await utils.answer(message, f"<b>[GitHubUploader]</b> Успешно загружено!\n<a href='{result}'>Посмотреть на GitHub</a>")
        else:
            if len(result) > 1000:
                result = result[:1000] + "..."
            await utils.answer(message, f"<b>[GitHubUploader]</b> Ошибка при загрузке:\n<code>{result}</code>")
