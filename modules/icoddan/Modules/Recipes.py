# meta developer: @coddan
from .. import loader, utils

@loader.tds
class RecipesMod(loader.Module):
    """Модуль для сохранения и удобного просмотра рецептов через инлайн-кнопки (via)"""
    strings = {
        "name": "Recipes",
        "no_args": "❌ Используй формат: <code>.addrecipe Название | Текст рецепта</code>",
        "no_name": "❌ Укажите название рецепта для удаления.",
        "saved": "✅ Рецепт <b>{}</b> успешно сохранен!",
        "deleted": "✅ Рецепт <b>{}</b> удален!",
        "not_found": "❌ Рецепт <b>{}</b> не найден!",
        "no_recipes": "❌ У вас нет сохраненных рецептов.",
        "menu": "🍽 <b>Ваши рецепты:</b>\nВыберите рецепт из списка ниже:",
        "recipe_text": "🍽 <b>Рецепт: {}</b>\n\n{}",
        "back": "🔙 Назад"
    }

    async def client_ready(self, client, db):
        self.db = db

    @loader.command(ru_doc="<название> | <рецепт> - Добавить рецепт")
    async def addrecipecmd(self, message):
        args = utils.get_args_raw(message)
        if "|" not in args:
            await utils.answer(message, self.strings("no_args"))
            return
        
        name, text = args.split("|", 1)
        name = name.strip()
        text = text.strip()
        
        recipes = self.db.get("Recipes", "recipes", {})
        recipes[name] = text
        self.db.set("Recipes", "recipes", recipes)
        
        await utils.answer(message, self.strings("saved").format(utils.escape_html(name)))

    @loader.command(ru_doc="<название> - Удалить рецепт")
    async def delrecipecmd(self, message):
        name = utils.get_args_raw(message).strip()
        if not name:
            await utils.answer(message, self.strings("no_name"))
            return

        recipes = self.db.get("Recipes", "recipes", {})
        if name in recipes:
            del recipes[name]
            self.db.set("Recipes", "recipes", recipes)
            await utils.answer(message, self.strings("deleted").format(utils.escape_html(name)))
        else:
            await utils.answer(message, self.strings("not_found").format(utils.escape_html(name)))

    @loader.command(ru_doc="- Показать все рецепты через инлайн кнопки")
    async def recipescmd(self, message):
        recipes = self.db.get("Recipes", "recipes", {})
        if not recipes:
            await utils.answer(message, self.strings("no_recipes"))
            return

        buttons = []
        row = []
        for name in recipes.keys():
            row.append({"text": name, "callback": self.inline__show_recipe, "args": (name,)})
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        await self.inline.form(
            message=message,
            text=self.strings("menu"),
            reply_markup=buttons
        )

    async def inline__show_recipe(self, call, name):
        recipes = self.db.get("Recipes", "recipes", {})
        if name not in recipes:
            await call.answer("Рецепт не найден!", show_alert=True)
            return
        
        recipe_text = recipes[name]
        back_button = [{"text": self.strings("back"), "callback": self.inline__back_to_recipes}]
        
        await call.edit(
            text=self.strings("recipe_text").format(utils.escape_html(name), utils.escape_html(recipe_text)),
            reply_markup=[back_button]
        )

    async def inline__back_to_recipes(self, call):
        recipes = self.db.get("Recipes", "recipes", {})
        if not recipes:
            await call.edit(self.strings("no_recipes"))
            return

        buttons = []
        row = []
        for name in recipes.keys():
            row.append({"text": name, "callback": self.inline__show_recipe, "args": (name,)})
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        await call.edit(
            text=self.strings("menu"),
            reply_markup=buttons
        )
