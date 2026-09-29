from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from config import ADMIN_ID
from database import Database
from states import AddProjectState, EditProjectState
from keyboards import main_menu_kb, project_list_kb, project_menu_kb, confirm_delete_kb

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    if not vis_admin(message.from_user.id):
        return await message.answer("Доступ запрещён.")
    await message.answer("Привет, Сенпай! 🐾 Добро пожаловать в CRM.", reply_markup=main_menu_kb())


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    help_text = """
📖 *Помощь по CRM-боту*

🔹 *Основные команды:*
/start — Главное меню
/help — Эта справка
/projects — Быстрый переход к списку проектов
/cancel — Отменить текущее действие

🔹 *Как пользоваться:*

*1. Создание проекта:*
   • Нажми "➕ Добавить проект" или отправь /projects
   • Введи название проекта

*2. Добавление источника рекламы:*
   • Открой проект из списка
   • Нажми "➕ Добавить источник"
   • Заполни данные: название, ссылка, площадка, тип размещения

*3. Управление статусами:*
   • В списке источников нажми на нужный
   • Меняй статус кнопками: ⏳ В работу → ✅ Оплачено / ❌ Отмена

*4. Редактирование:*
   • В меню источника можно изменить заметку или удалить его
   • В меню проекта можно переименовать или удалить проект

💡 *Совет:* Используй inline-кнопки — это быстрее, чем вводить команды вручную!
    """

    await message.answer(help_text, parse_mode="Markdown", reply_markup=main_menu_kb())


@router.callback_query(F.data == "help")
async def callback_help(callback: types.CallbackQuery):
    help_text = """
📖 *Помощь по CRM-боту*

🔹 *Основные команды:*
/start — Главное меню
/help — Эта справка
/projects — Быстрый переход к списку проектов
/cancel — Отменить текущее действие

🔹 *Как пользоваться:*

*1. Создание проекта:*
   • Нажми "➕ Добавить проект"
   • Введи название проекта

*2. Добавление источника рекламы:*
   • Открой проект из списка
   • Нажми "➕ Добавить источник"
   • Заполни данные

*3. Управление статусами:*
   • В списке источников нажми на нужный
   • Меняй статус кнопками

💡 Используй inline-кнопки — это быстрее команд!
    """

    await callback.message.edit_text(help_text, parse_mode="Markdown", reply_markup=main_menu_kb())
    await callback.answer()


@router.message(Command("projects"))
async def cmd_projects(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    projects = await Database.get_all_projects()
    if not projects:
        await message.answer("Пока нет проектов. Создадим первый?", reply_markup=main_menu_kb())
        return

    await message.answer("Выбери проект:", reply_markup=project_list_kb(projects))


@router.callback_query(F.data == "start")
async def back_to_start(callback: types.CallbackQuery):
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "add_project_prompt")
async def prompt_add_project(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddProjectState.name)
    await callback.message.answer("Введи название нового проекта:\n\n_Отправь /cancel для отмены_",
                                  parse_mode="Markdown")
    await callback.answer()


@router.message(AddProjectState.name)
async def process_add_project(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return

    project_id = await Database.create_project(message.text)
    await state.clear()

    # Сразу показываем меню нового проекта
    await message.answer(
        f"✅ Проект *'{message.text}'* создан!",
        parse_mode="Markdown",
        reply_markup=project_menu_kb(project_id)
    )


@router.callback_query(F.data == "list_projects")
async def list_projects(callback: types.CallbackQuery):
    projects = await Database.get_all_projects()
    if not projects:
        await callback.message.edit_text("Пока нет проектов. Создадим первый?")
        return
    await callback.message.edit_text("Выбери проект:", reply_markup=project_list_kb(projects))
    await callback.answer()


@router.callback_query(F.data.startswith("project_menu:"))
async def project_menu(callback: types.CallbackQuery, state: FSMContext):
    project_id = int(callback.data.split(":")[1])
    await state.update_data(project_id=project_id)

    project = await Database.get_project(project_id)
    if project is None:
        await callback.answer("⚠️ Проект не найден", show_alert=True)
        await callback.message.edit_text("Этот проект больше не существует.", reply_markup=main_menu_kb())
        return
    sources = await Database.get_sources_by_project(project_id)

    text = f"📂 Проект: *{project[1]}*\n📌 Источников: {len(sources)}"
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=project_menu_kb(project_id))
    await callback.answer()


@router.callback_query(F.data.startswith("edit_project:"))
async def prompt_edit_project(callback: types.CallbackQuery, state: FSMContext):
    project_id = int(callback.data.split(":")[1])
    await state.update_data(project_id=project_id)
    await state.set_state(EditProjectState.new_name)
    await callback.message.answer("Введи новое название проекта:")
    await callback.answer()


@router.message(EditProjectState.new_name)
async def process_edit_project(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    data = await state.get_data()
    project_id = data['project_id']

    await Database.update_project_name(project_id, message.text)
    await state.clear()

    # Возвращаемся в меню проекта с новым именем
    sources = await Database.get_sources_by_project(project_id)
    text = f"✅ Проект переименован в *'{message.text}'*\n📌 Источников: {len(sources)}"
    await message.answer(text, parse_mode="Markdown", reply_markup=project_menu_kb(project_id))


@router.callback_query(F.data.startswith("delete_project:"))
async def prompt_delete_project(callback: types.CallbackQuery):
    project_id = int(callback.data.split(":")[1])
    project = await Database.get_project(project_id)

    # Защита от None
    if project is None:
        await callback.answer("⚠️ Проект уже не существует", show_alert=True)
        await callback.message.edit_text("Этот проект уже удалён.", reply_markup=main_menu_kb())
        return

    await callback.message.answer(
        f"⚠️ Ты точно хочешь удалить проект *{project[1]}*?\nВсе источники тоже удалятся!",
        parse_mode="Markdown",
        reply_markup=confirm_delete_kb("project", project_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete:project:"))
async def confirm_delete_project(callback: types.CallbackQuery):
    project_id = int(callback.data.split(":")[2])
    project = await Database.get_project(project_id)

    if project is None:
        await callback.answer("⚠️ Проект уже удалён", show_alert=True)
        await callback.message.edit_text("Проект уже не существует.", reply_markup=main_menu_kb())
        return

    await Database.delete_project(project_id)
    await callback.message.edit_text("✅ Проект удалён", reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_delete:"))
async def cancel_delete(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer("Удаление отменено")