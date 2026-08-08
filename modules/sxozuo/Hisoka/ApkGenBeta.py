"""
🤖 ApkGen - Генерирует Android-приложение через OpenAI и собирает APK

Команда: .apkgen <идея приложения>
Отправит готовый .apk в тот же чат, где вызвана команда.
Требует java/gradle/android sdk на сервере.
"""

version = (0, 0, 0)

# meta developer: @xyecoder
# meta banner: https://files.catbox.moe/2s9dvz.jpg
# scope: hikka_only
# requires:

#  ██╗  ██╗██╗███████╗ ██████╗ ██╗  ██╗ █████╗
#  ██║  ██║██║██╔════╝██╔═══██╗██║ ██╔╝██╔══██╗
#  ███████║██║███████╗██║   ██║█████╔╝ ███████║
#  ██╔══██║██║╚════██║██║   ██║██╔═██╗ ██╔══██║
#  ██║  ██║██║███████║╚██████╔╝██║  ██╗██║  ██║
#  ╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
#                HISOKA
# © 2026 @xyecoder | All rights reserved
# ⛔ Копирование без разрешения запрещено

import asyncio
import json
import os
import shutil
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from hikkatl.tl.types import Message

from .. import loader, utils


@loader.tds
class ApkGenMod(loader.Module):
    """Generate Android project via OpenAI and build APK in the same chat"""

    strings = {
        "name": "ApkGen",
        "no_args": "❌ <b>Usage:</b> <code>.apkgen app idea</code>",
        "no_key": "❌ <b>OPENAI_API_KEY is empty.</b> Set it in module config.",
        "busy": "⏳ <b>Generating project...</b>",
        "building": "🏗 <b>Building APK...</b>",
        "build_failed": "❌ <b>Build failed.</b>\n<code>{}</code>",
        "gen_failed": "❌ <b>Generation failed:</b>\n<code>{}</code>",
        "bad_json": "❌ <b>Model returned invalid JSON.</b>",
        "no_files": "❌ <b>No files in generated payload.</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "OPENAI_API_KEY",
                "",
                "OpenAI API key",
                validator=loader.validators.Hidden(loader.validators.String()),
            ),
            loader.ConfigValue(
                "OPENAI_MODEL",
                "gpt-5.3-codex",
                "OpenAI model",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "ANDROID_SDK_ROOT",
                "/opt/android-sdk",
                "Path to Android SDK root",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "JAVA_HOME",
                "/usr/lib/jvm/java-17-openjdk-amd64",
                "Path to JAVA_HOME (optional)",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "BUILD_VARIANT",
                "debug",
                "debug or release",
                validator=loader.validators.Choice(["debug", "release"]),
            ),
            loader.ConfigValue(
                "TIMEOUT_SEC",
                1200,
                "Build timeout (seconds)",
                validator=loader.validators.Integer(minimum=60),
            ),
        )

    async def _run(self, cmd, cwd=None, env=None, timeout=1200):
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return 124, "", "Timeout"
        return proc.returncode, out.decode("utf-8", "ignore"), err.decode("utf-8", "ignore")

    def _extract_json(self, text: str):
        text = text.strip()
        if text.startswith("```"):
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                text = text[start : end + 1]
        return json.loads(text)

    async def _openai_generate(self, idea: str):
        system_prompt = (
            "You are a senior Android engineer. "
            "Return ONLY valid JSON with keys: project_name, files, build_notes. "
            "files is array of {path, content}. "
            "Use Kotlin + Gradle Kotlin DSL, minSdk 24, compileSdk 34, targetSdk 34, Material3. "
            "Use Android Gradle Plugin (AGP) version 8.1.x. "
            "In build.gradle.kts plugins block use: id 'com.android.application' version '8.1.1'. "
            "Use Gradle 8.5+ compatible dependencies (androidx.activity:activity:1.8.0, androidx.core:core-ktx:1.12.0). "
            "IMPORTANT: Include local.properties file with: sdk.dir=/opt/android-sdk "
            "Include all required files for successful assembleDebug build. "
            "No markdown, no explanations, JSON only."
        )

        body = {
            "model": self.config["OPENAI_MODEL"],
            "reasoning": {"effort": "low"},
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": f"Build Android app idea:\n{idea}"}],
                },
            ],
            "max_output_tokens": 32000,
        }

        req = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config['OPENAI_API_KEY']}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        loop = asyncio.get_running_loop()

        def _do_request():
            with urllib.request.urlopen(req, timeout=180) as response:
                return response.read().decode("utf-8", "ignore")

        raw = await loop.run_in_executor(None, _do_request)
        data = json.loads(raw)

        text = ""
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in ("output_text", "text"):
                    text += content.get("text", "")

        if not text and isinstance(data.get("output_text"), str):
            text = data["output_text"]

        if not text:
            raise RuntimeError("Empty model output")

        return self._extract_json(text)

    def _write_project(self, root: Path, payload: dict):
        files = payload.get("files", [])
        if not files:
            raise ValueError("No files")

        for file_item in files:
            rel = file_item.get("path", "").strip().replace("\\", "/")
            content = file_item.get("content", "")

            if not rel or rel.startswith("/") or ".." in rel:
                continue

            file_path = root / rel
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

    @loader.command()
    async def apkgen(self, message: Message):
        """<idea> - generate Android app and upload APK here"""
        idea = utils.get_args_raw(message)
        if not idea:
            await utils.answer(message, self.strings("no_args"))
            return

        if not self.config["OPENAI_API_KEY"]:
            await utils.answer(message, self.strings("no_key"))
            return

        status = await utils.answer(message, self.strings("busy"))
        started = time.time()
        workdir = Path(tempfile.mkdtemp(prefix="apkgen_"))

        try:
            try:
                payload = await self._openai_generate(idea)
            except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, RuntimeError) as error:
                await utils.answer(status, self.strings("gen_failed").format(utils.escape_html(str(error))))
                return
            except Exception as error:
                await utils.answer(status, self.strings("gen_failed").format(utils.escape_html(repr(error))))
                return

            try:
                self._write_project(workdir, payload)
            except ValueError:
                await utils.answer(status, self.strings("no_files"))
                return
            except json.JSONDecodeError:
                await utils.answer(status, self.strings("bad_json"))
                return

            await utils.answer(status, self.strings("building"))

            env = os.environ.copy()
            if self.config["ANDROID_SDK_ROOT"]:
                env["ANDROID_SDK_ROOT"] = self.config["ANDROID_SDK_ROOT"]
            if self.config["JAVA_HOME"]:
                env["JAVA_HOME"] = self.config["JAVA_HOME"]

            task = "assembleDebug" if self.config["BUILD_VARIANT"] == "debug" else "assembleRelease"
            gradlew = workdir / "gradlew"

            if gradlew.exists():
                await self._run(["chmod", "+x", "gradlew"], cwd=str(workdir), env=env)
                cmd = ["./gradlew", task]
            else:
                cmd = ["gradle", task]

            rc, out, err = await self._run(
                cmd,
                cwd=str(workdir),
                env=env,
                timeout=int(self.config["TIMEOUT_SEC"]),
            )
            if rc != 0:
                tail = (out + "\n" + err)[-3500:]
                await utils.answer(status, self.strings("build_failed").format(utils.escape_html(tail)))
                return

            apks = list(workdir.glob("**/build/outputs/apk/**/*.apk"))
            if not apks:
                await utils.answer(status, self.strings("build_failed").format("APK not found in outputs"))
                return

            apk = max(apks, key=lambda path: path.stat().st_mtime)
            elapsed = round(time.time() - started, 1)
            caption = f"✅ Built in {elapsed}s\n<code>{apk.name}</code>"
            await utils.answer_file(message, str(apk), caption=caption)
        finally:
            shutil.rmtree(workdir, ignore_errors=True)
