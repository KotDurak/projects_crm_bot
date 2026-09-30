import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Update

import config
import google_sheets
from keyboards import (
    ProjectCD, PaginationCD, SourceCardCD, EditStatusCD, EditFieldCD,
    DeleteSourceCD, ShowStatusCD,
    get_pagination_keyboard, get_source_card_keyboard,
    get_status_keyboard, get_project_select_keyboard
)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

class AdminAccessMiddleware(BaseMiddleware):
    """Пропускает к обработчикам только администратора"""
    async def __call__(self, handler, event: Update, data: dict):
        user = event.from_user
        # Если пользователь есть и его ID совпадает с ADMIN_ID — пропускаем
        if user and user.id == config.ADMIN_ID:
            return await handler(event, data)
        # Иначе просто ничего не делаем (бот молча игнорирует чужака)
        return

# --- FSM СОСТОЯНИЯ ---
class AddSourceStates(StatesGroup):
    project = State()
    name = State()
    link = State()
    admin = State()
    type = State()
    stage = State()
    price = State()


class EditSourceStates(StatesGroup):
    waiting_for_value = State()


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def escape_html(text):
    if not text: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def get_main_menu() -> ReplyKeyboardMarkup:
    """Создает статичное нижнее меню"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Источники"), KeyboardButton(text="➕ Добавить")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True,  # Уменьшает размер кнопок
        input_field_placeholder="Выберите действие..."
    )
    return keyboard


async def render_source_card(chat_id: int, source_id: str, project: str, message_to_edit=None):
    sheet = google_sheets.get_sheet()
    records = sheet.get_all_records()
    item = next((r for r in records if str(r.get('id')) == str(source_id)), None)

    if not item:
        text = "Источник не найден."
        keyboard = get_project_select_keyboard(google_sheets.get_projects())
        if message_to_edit:
            await message_to_edit.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")
        return

    name = escape_html(item.get('source_name'))
    stage = escape_html(item.get('stage'))
    link = item.get('link', '')
    price = escape_html(item.get('price', '0'))
    notes = escape_html(item.get('notes', ''))
    admin = escape_html(item.get('admin_contact', ''))
    type_ = escape_html(item.get('type', ''))

    link_html = f'\n <a href="{escape_html(link)}">Ссылка</a>' if link else ""

    text = (f"📂 <b>{name}</b> [{stage}]{link_html}\n\n"
            f"👤 Админ: <code>{admin}</code>\n"
            f"🏷 Тип: <code>{type_}</code> | 💰 Цена: <code>{price}</code>\n"
            f"📝 Заметки: {notes}\n"
            f"ID: <code>{source_id}</code>")

    keyboard = get_source_card_keyboard(source_id, project)

    if message_to_edit:
        await message_to_edit.edit_text(text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
    else:
        await bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)


# --- КОМАНДЫ И МЕНЮ ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет, Сенпай! 🌸\n\n"
        "Я ваш ассистент по маркетингу. Используйте меню ниже или команды.",
        reply_markup=get_main_menu()
    )


@dp.message(Command("help"))
@dp.message(F.text == "❓ Помощь")  # <-- Исправили на точное совпадение с кнопкой
async def cmd_help(message: Message):
    text = (
        "📖 <b>Справка по боту:</b>\n\n"
        "📊 <b>Источники</b> — просмотр и управление базой рекламы.\n"
        "➕ <b>Добавить</b> — пошаговое добавление нового источника.\n"
        "❓ <b>Помощь</b> — это сообщение.\n\n"
        "💡 <b>Советы:</b>\n"
        "• В карточке источника можно менять любое поле.\n"
        "• Удаление переносит вас обратно в меню.\n"
        "• Пагинация позволяет быстро прыгать по страницам."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu())


@dp.message(Command("sources"))
@dp.message(F.text == "📊 Источники")
async def cmd_sources(message: Message):
    projects = google_sheets.get_projects()
    text = " <b>Выберите проект:</b>\n\n"
    for proj, count in projects.items():
        text += f"🔹 <b>{escape_html(proj)}</b>: {count} ист.\n"
    keyboard = get_project_select_keyboard(projects)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@dp.message(Command("add"))
@dp.message(F.text == "➕ Добавить")  # <-- Исправили на точное совпадение с кнопкой
async def cmd_add(message: Message, state: FSMContext):
    projects = google_sheets.get_projects()
    await message.answer("Выберите проект:", reply_markup=get_project_select_keyboard(projects))
    await state.set_state(AddSourceStates.project)


# --- ОБРАБОТКА ПРОЕКТОВ ---
@dp.callback_query(ProjectCD.filter())
async def handle_project_select(callback: CallbackQuery, callback_data: ProjectCD, state: FSMContext):
    project = callback_data.name
    current_state = await state.get_state()

    if current_state == AddSourceStates.project.state:
        await state.update_data(project=project)
        await callback.message.edit_text("Введите название источника:")
        await state.set_state(AddSourceStates.name)
        await callback.answer()
        return

    page = 1
    items, total_pages, total_items = google_sheets.get_sources_by_project(project, page, config.ITEMS_PER_PAGE)

    if not items:
        await callback.answer("Пока пусто", show_alert=True)
        return

    text = f"📊 <b>{escape_html(project)}</b>\n(Стр. {page}/{total_pages})\n\n"
    source_ids = []
    for item in items:
        name = escape_html(item.get('source_name'))
        stage = escape_html(item.get('stage'))
        source_ids.append((str(item.get('id')), name))
        text += f"• {name} [{stage}]\n"

    keyboard = get_pagination_keyboard(page, total_pages, project, source_ids)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# --- FSM ДОБАВЛЕНИЯ (Сокращено, логика та же) ---
@dp.message(AddSourceStates.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(source_name=message.text)
    await message.answer("Ссылку (или -):")
    await state.set_state(AddSourceStates.link)


@dp.message(AddSourceStates.link)
async def process_link(message: Message, state: FSMContext):
    link = message.text if message.text != '-' else ''
    await state.update_data(link=link)
    await message.answer("Админа (или -):")
    await state.set_state(AddSourceStates.admin)


@dp.message(AddSourceStates.admin)
async def process_admin(message: Message, state: FSMContext):
    admin = message.text if message.text != '-' else ''
    await state.update_data(admin_contact=admin)
    await message.answer("Тип (organic/paid):")
    await state.set_state(AddSourceStates.type)


@dp.message(AddSourceStates.type)
async def process_type(message: Message, state: FSMContext):
    await state.update_data(type=message.text.lower())
    await message.answer("Статус (active/lead/negotiation):")
    await state.set_state(AddSourceStates.stage)


@dp.message(AddSourceStates.stage)
async def process_stage(message: Message, state: FSMContext):
    await state.update_data(stage=message.text.lower())
    await message.answer("Цену (0 если бесплатно):")
    await state.set_state(AddSourceStates.price)


@dp.message(AddSourceStates.price)
async def process_price(message: Message, state: FSMContext):
    data = await state.get_data()
    data['price'] = message.text
    data['date_added'] = datetime.now().strftime("%Y-%m-%d")

    new_id = google_sheets.add_source(data)
    project = data.get('project', '')

    await message.answer(f"✅ Добавлен ID {new_id}.", reply_markup=get_main_menu())
    await state.clear()

    if project:
        items, total_pages, total_items = google_sheets.get_sources_by_project(project, 1, config.ITEMS_PER_PAGE)
        text = f" <b>{escape_html(project)}</b>\n(Стр. 1/{total_pages})\n\n"
        source_ids = [(str(item.get('id')), escape_html(item.get('source_name'))) for item in items]
        for item in items:
            text += f"• {escape_html(item.get('source_name'))} [{escape_html(item.get('stage'))}]\n"
        keyboard = get_pagination_keyboard(1, total_pages, project, source_ids)
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# --- РЕДАКТИРОВАНИЕ ---
@dp.callback_query(EditFieldCD.filter())
async def start_edit_field(callback: CallbackQuery, callback_data: EditFieldCD, state: FSMContext):
    await state.update_data(id=callback_data.id, field=callback_data.field, project=callback_data.project)
    field_names = {
        'source_name': 'название', 'link': 'ссылку', 'admin_contact': 'контакт админа',
        'type': 'тип (organic/paid)', 'price': 'цену', 'notes': 'заметки'
    }
    await callback.message.edit_text(
        f"Введите новое значение для поля '{field_names[callback_data.field]}':\n(или /cancel для отмены)")
    await state.set_state(EditSourceStates.waiting_for_value)
    await callback.answer()


@dp.message(Command("cancel"), EditSourceStates.waiting_for_value)
async def cancel_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    await message.answer("Отменено.", reply_markup=get_main_menu())
    await state.clear()
    await render_source_card(message.chat.id, data['id'], data['project'])


@dp.message(EditSourceStates.waiting_for_value)
async def process_edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    success = google_sheets.update_source_field(data['id'], data['field'], message.text)
    if success:
        await message.answer("✅ Обновлено!")
        await render_source_card(message.chat.id, data['id'], data['project'])
    else:
        await message.answer("❌ Ошибка.")
    await state.clear()


# --- КАРТОЧКА И СТАТУСЫ ---
@dp.callback_query(SourceCardCD.filter())
async def open_source_card(callback: CallbackQuery, callback_data: SourceCardCD):
    await render_source_card(callback.message.chat.id, callback_data.id, callback_data.project, callback.message)
    await callback.answer()


@dp.callback_query(ShowStatusCD.filter())
async def show_statuses(callback: CallbackQuery, callback_data: ShowStatusCD):
    keyboard = get_status_keyboard(callback_data.id, callback_data.project)
    await callback.message.edit_text("Выберите новый статус:", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(EditStatusCD.filter())
async def change_status(callback: CallbackQuery, callback_data: EditStatusCD):
    success = google_sheets.update_source_field(callback_data.id, 'stage', callback_data.new_status)
    if success:
        await render_source_card(callback.message.chat.id, callback_data.id, callback_data.project, callback.message)
    else:
        await callback.message.edit_text("❌ Ошибка.")
    await callback.answer()


# --- УДАЛЕНИЕ ---
@dp.callback_query(DeleteSourceCD.filter())
async def delete_source(callback: CallbackQuery, callback_data: DeleteSourceCD):
    success = google_sheets.hard_delete_source(callback_data.id)
    if success:
        projects = google_sheets.get_projects()
        text = "🗑 Удалено.\n\n📊 <b>Выберите проект:</b>\n\n"
        for proj, count in projects.items():
            text += f"🔹 <b>{escape_html(proj)}</b>: {count} ист.\n"
        keyboard = get_project_select_keyboard(projects)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await callback.message.edit_text("❌ Ошибка удаления.")
    await callback.answer()


# --- ПАГИНАЦИЯ ---
@dp.callback_query(PaginationCD.filter())
async def handle_pagination(callback: CallbackQuery, callback_data: PaginationCD):
    if callback_data.action == "projects":
        projects = google_sheets.get_projects()
        text = "📊 <b>Выберите проект:</b>\n\n"
        for proj, count in projects.items(): text += f"🔹 <b>{escape_html(proj)}</b>: {count} ист.\n"
        keyboard = get_project_select_keyboard(projects)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        return

    if callback_data.action == "back_to_list":
        project = callback_data.project
        items, total_pages, total_items = google_sheets.get_sources_by_project(project, 1, config.ITEMS_PER_PAGE)
        text = f"📊 <b>{escape_html(project)}</b>\n(Стр. 1/{total_pages})\n\n"
        source_ids = [(str(item.get('id')), escape_html(item.get('source_name'))) for item in items]
        for item in items:
            text += f"• {escape_html(item.get('source_name'))} [{escape_html(item.get('stage'))}]\n"
        keyboard = get_pagination_keyboard(1, total_pages, project, source_ids)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        return

    page = callback_data.page
    project = callback_data.project
    items, total_pages, total_items = google_sheets.get_sources_by_project(project, page, config.ITEMS_PER_PAGE)

    text = f" <b>{escape_html(project)}</b>\n(Стр. {page}/{total_pages})\n\n"
    source_ids = [(str(item.get('id')), escape_html(item.get('source_name'))) for item in items]
    for item in items:
        text += f"• {escape_html(item.get('source_name'))} [{escape_html(item.get('stage'))}]\n"

    keyboard = get_pagination_keyboard(page, total_pages, project, source_ids)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


async def main():
    print("✅ Бот запущен! Меню и команды настроены.")
    dp.message.middleware(AdminAccessMiddleware())
    dp.callback_query.middleware(AdminAccessMiddleware())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())