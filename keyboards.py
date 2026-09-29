from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📁 Мои проекты", callback_data="list_projects")
    builder.button(text="➕ Добавить проект", callback_data="add_project_prompt")
    builder.button(text="❓ Помощь", callback_data="help")
    builder.adjust(1)
    return builder.as_markup()


def project_list_kb(projects):
    builder = InlineKeyboardBuilder()
    for proj_id, proj_name in projects:
        builder.button(text=f"📂 {proj_name}", callback_data=f"project_menu:{proj_id}")
    builder.button(text="🔙 Назад", callback_data="start")
    builder.adjust(1)
    return builder.as_markup()


def project_menu_kb(project_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить источник", callback_data=f"add_source_start:{project_id}")
    builder.button(text="📊 Список источников", callback_data=f"show_sources:{project_id}")
    builder.button(text="✏️ Переименовать проект", callback_data=f"edit_project:{project_id}")
    builder.button(text="🗑️ Удалить проект", callback_data=f"delete_project:{project_id}")
    builder.button(text="🔙 К списку проектов", callback_data="list_projects")
    builder.adjust(1)
    return builder.as_markup()


def platform_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="Telegram", callback_data="platform:TG")
    builder.button(text="ВКонтакте", callback_data="platform:VK")
    builder.button(text="Другое", callback_data="platform:OTHER")
    builder.adjust(1)
    return builder.as_markup()


def posting_type_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="✍️ Сам постю", callback_data="posting:self")
    builder.button(text="🤝 Пишу админу", callback_data="posting:admin")
    builder.adjust(1)
    return builder.as_markup()


def source_actions_kb(source_id, current_status):
    builder = InlineKeyboardBuilder()

    # Кнопки смены статуса (только если текущий статус другой)
    if current_status != "in_progress":
        builder.button(text="⏳ В работу", callback_data=f"status:{source_id}:in_progress")
    if current_status != "paid":
        builder.button(text="✅ Оплачено", callback_data=f"status:{source_id}:paid")
    if current_status != "rejected":
        builder.button(text="❌ Отмена", callback_data=f"status:{source_id}:rejected")

    builder.button(text="📝 Изменить заметку", callback_data=f"edit_note:{source_id}")
    builder.button(text="🗑️ Удалить источник", callback_data=f"delete_source:{source_id}")
    builder.adjust(3, 2)
    return builder.as_markup()


def sources_list_kb(project_id, sources):
    builder = InlineKeyboardBuilder()
    for src_id, src_name, *_ in sources:
        builder.button(text=f"⚙️ {src_name}", callback_data=f"source_menu:{src_id}")
    builder.button(text="🔙 Назад к проекту", callback_data=f"project_menu:{project_id}")
    builder.adjust(1)
    return builder.as_markup()


def source_menu_kb(source_id, project_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 К списку источников", callback_data=f"show_sources:{project_id}")
    builder.adjust(1)
    return builder.as_markup()


def confirm_delete_kb(entity_type, entity_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"confirm_delete:{entity_type}:{entity_id}")
    builder.button(text="❌ Отмена", callback_data=f"cancel_delete:{entity_type}:{entity_id}")
    builder.adjust(2)
    return builder.as_markup()