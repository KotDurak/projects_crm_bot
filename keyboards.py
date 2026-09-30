from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class ProjectCD(CallbackData, prefix="proj"):
    name: str


class PaginationCD(CallbackData, prefix="pag"):
    action: str  # 'next', 'prev', 'projects', 'back_to_list', 'page'
    page: int = 1
    project: str = ""


class SourceCardCD(CallbackData, prefix="src"):
    id: str
    project: str


class EditStatusCD(CallbackData, prefix="edit_st"):
    id: str
    new_status: str
    project: str


class EditFieldCD(CallbackData, prefix="edit_f"):
    id: str
    field: str
    project: str


class DeleteSourceCD(CallbackData, prefix="del"):
    id: str
    project: str


class ShowStatusCD(CallbackData, prefix="show_st"):
    id: str
    project: str


def get_pagination_keyboard(current_page: int, total_pages: int, project: str,
                            source_ids: list) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Кнопки источников (по одной на строку)
    for src_id, name in source_ids:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"📁 {name}", callback_data=SourceCardCD(id=src_id, project=project).pack())
        ])

    # Ряд с номерами страниц (умная пагинация)
    page_buttons = _generate_page_buttons(current_page, total_pages, project)
    if page_buttons:
        keyboard.inline_keyboard.append(page_buttons)

    # Ряд навигации: Назад | страница | Вперёд
    nav_row = []
    if current_page == 1:
        nav_row.append(InlineKeyboardButton(text="️ К проектам",
                                            callback_data=PaginationCD(action="projects", page=1, project="").pack()))
    else:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад",
                                            callback_data=PaginationCD(action="prev", page=current_page - 1,
                                                                       project=project).pack()))

    nav_row.append(InlineKeyboardButton(text=f" {current_page}/{total_pages} ", callback_data="ignore"))

    if current_page < total_pages:
        nav_row.append(InlineKeyboardButton(text="Вперёд ➡️",
                                            callback_data=PaginationCD(action="next", page=current_page + 1,
                                                                       project=project).pack()))

    keyboard.inline_keyboard.append(nav_row)
    return keyboard


def _generate_page_buttons(current_page: int, total_pages: int, project: str) -> list:
    """
    Генерирует кнопки с номерами страниц.
    На первой странице: [●1●] [2] [3] [4] [...] [13]
    В середине: [1] [...] [6] [●7●] [8] [...] [13]
    На последней: [1] [...] [10] [11] [12] [●13●]
    """
    if total_pages <= 1:
        return []

    buttons = []

    # Определяем диапазон отображаемых страниц
    if current_page <= 3:
        # Показываем первые 4 страницы
        display_range = list(range(1, min(5, total_pages + 1)))
    elif current_page >= total_pages - 2:
        # Показываем последние 4 страницы
        display_range = list(range(max(1, total_pages - 3), total_pages + 1))
    else:
        # Показываем текущую и соседние
        display_range = [current_page - 1, current_page, current_page + 1]

    # Добавляем первую страницу, если её нет в диапазоне
    if 1 not in display_range:
        display_range.insert(0, 1)

    # Добавляем последнюю страницу, если её нет в диапазоне
    if total_pages not in display_range:
        display_range.append(total_pages)

    # Убираем дубликаты и сортируем
    display_range = sorted(set(display_range))

    # Генерируем кнопки с "..." между разрывами
    prev_page = 0
    for page_num in display_range:
        if page_num - prev_page > 1:
            buttons.append(InlineKeyboardButton(text="...", callback_data="ignore"))

        if page_num == current_page:
            buttons.append(InlineKeyboardButton(
                text=f"●{page_num}●",
                callback_data="ignore"
            ))
        else:
            buttons.append(InlineKeyboardButton(
                text=str(page_num),
                callback_data=PaginationCD(action="page", page=page_num, project=project).pack()
            ))

        prev_page = page_num

    return buttons


def get_source_card_keyboard(source_id: str, project: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Имя",
                              callback_data=EditFieldCD(id=source_id, field="source_name", project=project).pack()),
         InlineKeyboardButton(text="️ Ссылка",
                              callback_data=EditFieldCD(id=source_id, field="link", project=project).pack())],
        [InlineKeyboardButton(text="✏️ Админ",
                              callback_data=EditFieldCD(id=source_id, field="admin_contact", project=project).pack()),
         InlineKeyboardButton(text="️ Тип",
                              callback_data=EditFieldCD(id=source_id, field="type", project=project).pack())],
        [InlineKeyboardButton(text="✏️ Цена",
                              callback_data=EditFieldCD(id=source_id, field="price", project=project).pack()),
         InlineKeyboardButton(text="✏️ Заметки",
                              callback_data=EditFieldCD(id=source_id, field="notes", project=project).pack())],
        [InlineKeyboardButton(text="✏️ Статус", callback_data=ShowStatusCD(id=source_id, project=project).pack())],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=DeleteSourceCD(id=source_id, project=project).pack())],
        [InlineKeyboardButton(text="⬅️ Назад к списку",
                              callback_data=PaginationCD(action="back_to_list", page=1, project=project).pack())]
    ])


def get_status_keyboard(source_id: str, project: str) -> InlineKeyboardMarkup:
    statuses = ['active', 'lead', 'negotiation']
    row = [InlineKeyboardButton(text=s, callback_data=EditStatusCD(id=source_id, new_status=s, project=project).pack())
           for s in statuses]
    row.append(InlineKeyboardButton(text="Отмена", callback_data=SourceCardCD(id=source_id, project=project).pack()))
    return InlineKeyboardMarkup(inline_keyboard=[row])


def get_project_select_keyboard(projects: dict) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    row = []
    for proj, count in projects.items():
        row.append(InlineKeyboardButton(text=f"{proj} ({count})", callback_data=ProjectCD(name=proj).pack()))
        if len(row) == 2:
            keyboard.inline_keyboard.append(row)
            row = []
    if row:
        keyboard.inline_keyboard.append(row)
    return keyboard