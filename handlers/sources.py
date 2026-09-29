from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from config import ADMIN_ID
from database import Database
from states import AddSourceState, EditSourceState
from keyboards import platform_kb, posting_type_kb, source_actions_kb, sources_list_kb, confirm_delete_kb, project_menu_kb
from utils import escape_md, make_clickable

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

@router.callback_query(F.data.startswith("add_source_start:"))
async def start_add_source(callback: types.CallbackQuery, state: FSMContext):
    project_id = int(callback.data.split(":")[1])
    # Сохраняем project_id в state — теперь он точно будет
    await state.update_data(project_id=project_id)
    await state.set_state(AddSourceState.name)
    await callback.message.answer("Введи название источника:\n\n_Отправь /cancel для отмены_", parse_mode="Markdown")
    await callback.answer()

@router.message(AddSourceState.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddSourceState.url)
    await message.answer("Отправь ссылку (или 'skip'):")

@router.message(AddSourceState.url)
async def process_url(message: types.Message, state: FSMContext):
    url = message.text if message.text.lower() != "skip" else None
    await state.update_data(url=url)
    await state.set_state(AddSourceState.platform)
    await message.answer("Выбери площадку:", reply_markup=platform_kb())

@router.callback_query(F.data.startswith("platform:"), AddSourceState.platform)
async def process_platform(callback: types.CallbackQuery, state: FSMContext):
    platform = callback.data.split(":")[1]
    await state.update_data(platform=platform)
    await state.set_state(AddSourceState.posting_type)
    await callback.message.edit_text("Как будем размещать?", reply_markup=posting_type_kb())
    await callback.answer()

@router.callback_query(F.data.startswith("posting:"), AddSourceState.posting_type)
async def process_posting(callback: types.CallbackQuery, state: FSMContext):
    posting_type = "Сам постю" if callback.data.split(":")[1] == "self" else "Пишу админу"
    await state.update_data(posting_type=posting_type)
    await state.set_state(AddSourceState.note)
    await callback.message.edit_text("Добавь заметку или 'skip':")
    await callback.answer()


@router.message(AddSourceState.note)
async def process_note(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return

    data = await state.get_data()

    # Защита от потери project_id
    if 'project_id' not in data:
        await state.clear()
        await message.answer("⚠️ Что-то пошло не так. Проект не определён. Возвращаюсь в главное меню.")
        from keyboards import main_menu_kb
        return await message.answer("Главное меню:", reply_markup=main_menu_kb())

    note = message.text if message.text.lower() != "пропустить" else ""
    project_id = data['project_id']

    await Database.create_source(project_id, data['name'], data['url'], data['platform'], data['posting_type'], note)
    await state.clear()

    project = await Database.get_project(project_id)
    sources = await Database.get_sources_by_project(project_id)

    text = f"✅ Источник *'{data['name']}'* добавлен!\n\n📂 Проект: *{project[1]}*\n📌 Всего источников: {len(sources)}"
    await message.answer(text, parse_mode="Markdown", reply_markup=project_menu_kb(project_id))


@router.callback_query(F.data.startswith("show_sources:"))
async def show_sources(callback: types.CallbackQuery, state: FSMContext):
    project_id = int(callback.data.split(":")[1])
    # Сохраняем project_id в state, чтобы он не терялся
    await state.update_data(project_id=project_id)

    sources = await Database.get_sources_by_project(project_id)

    if not sources:
        await callback.message.answer("В этом проекте пока нет источников.")
        await callback.answer()
        return

    text = "📊 Источники:\n\n"
    status_emojis = {"new": "🆕", "in_progress": "⏳", "paid": "✅", "rejected": "❌"}

    for src in sources:
        src_id, name, url, platform, p_type, status, note = src
        emoji = status_emojis.get(status, "📌")
        text += f"{emoji} {name} ({platform})\n"
        text += f"   Тип: {p_type} | Статус: {status}\n"
        if note:
            text += f"   📝 {note}\n\n"

    await callback.message.edit_text(text, reply_markup=sources_list_kb(project_id, sources))
    await callback.answer()

@router.callback_query(F.data.startswith("source_menu:"))
async def source_menu(callback: types.CallbackQuery):
    source_id = int(callback.data.split(":")[1])
    source = await Database.get_source(source_id)

    if source is None:
        await callback.answer("⚠️ Источник не найден", show_alert=True)
        return

    # ИСПРАВЛЕНО: теперь здесь 8 элементов (добавлен project_id на позицию 1)
    src_id, project_id, name, url, platform, p_type, status, note = source
    status_emojis = {"new": "🆕", "in_progress": "⏳", "paid": "✅", "rejected": "❌"}
    emoji = status_emojis.get(status, "📌")

    text = f"{emoji} *{escape_md(name)}*\n\n"
    text += f"🌐 Площадка: {platform}\n"
    text += f"📌 Тип: {p_type}\n"
    if url:
        text += f"🔗 Ссылка: {make_clickable(url)}\n"
    if note:
        text += f"📝 Заметка: {escape_md(note)}\n"

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=source_actions_kb(source_id, status)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("status:"))
async def change_status(callback: types.CallbackQuery):
    _, src_id, new_status = callback.data.split(":")
    await Database.update_source_status(int(src_id), new_status)
    await callback.answer("Статус обновлён!")

    source = await Database.get_source(int(src_id))
    if source is None:
        return

    # ИСПРАВЛЕНО: 8 элементов
    src_id, project_id, name, url, platform, p_type, status, note = source
    status_emojis = {"new": "🆕", "in_progress": "⏳", "paid": "✅", "rejected": "❌"}
    emoji = status_emojis.get(status, "📌")

    text = f"{emoji} *{escape_md(name)}*\n\n"
    text += f"🌐 Площадка: {platform}\n"
    text += f"📌 Тип: {p_type}\n"
    if url:
        text += f"🔗 Ссылка: {make_clickable(url)}\n"
    if note:
        text += f"📝 Заметка: {escape_md(note)}\n"

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=source_actions_kb(int(src_id), status)
    )

@router.callback_query(F.data.startswith("edit_note:"))
async def prompt_edit_note(callback: types.CallbackQuery, state: FSMContext):
    source_id = int(callback.data.split(":")[1])
    await state.update_data(source_id=source_id)
    await state.set_state(EditSourceState.new_value)
    await callback.message.answer("Введи новую заметку:")
    await callback.answer()

@router.message(EditSourceState.new_value)
async def process_edit_note(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    data = await state.get_data()
    source_id = data['source_id']

    await Database.update_source_note(source_id, message.text)
    await state.clear()

    source = await Database.get_source(source_id)
    if source:
        src_id, proj_id, name, url, platform, p_type, status, note = source
        status_emojis = {"new": "🆕", "in_progress": "⏳", "paid": "✅", "rejected": "❌"}
        emoji = status_emojis.get(status, "📌")

        text = f"✅ Заметка обновлена!\n\n{emoji} *{escape_md(name)}*\n\n"
        text += f"🌐 Площадка: {platform}\n"
        text += f"📌 Тип: {p_type}\n"
        if url:
            text += f"🔗 Ссылка: {make_clickable(url)}\n"
        if note:
            text += f"📝 Заметка: {escape_md(note)}\n"

        await message.answer(text, parse_mode="Markdown", reply_markup=source_actions_kb(src_id, status))

@router.callback_query(F.data.startswith("delete_source:"))
async def prompt_delete_source(callback: types.CallbackQuery):
    source_id = int(callback.data.split(":")[1])
    source = await Database.get_source(source_id)

    if source is None:
        await callback.answer("⚠️ Источник уже не существует", show_alert=True)
        return

    # ИСПРАВЛЕНО: source[2] - это имя, source[1] - это project_id
    await callback.message.answer(
        f"⚠️ Удалить источник *{source[2]}*?",
        parse_mode="Markdown",
        reply_markup=confirm_delete_kb("source", source_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_delete:source:"))
async def confirm_delete_source(callback: types.CallbackQuery):
    source_id = int(callback.data.split(":")[2])

    source = await Database.get_source(source_id)
    if source is None:
        await callback.answer("⚠️ Источник уже удалён", show_alert=True)
        return

    project_id = source[1]

    await Database.delete_source(source_id)

    sources = await Database.get_sources_by_project(project_id)
    await callback.message.edit_text(
        "✅ Источник удалён.",
        reply_markup=sources_list_kb(project_id, sources) if sources else project_menu_kb(project_id)
    )
    await callback.answer()