import gspread
from oauth2client.service_account import ServiceAccountCredentials
import config
import time

SCOPES = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

# Кэш: {timestamp: records}
_cache = {'timestamp': 0, 'data': None}
CACHE_TTL = 300  # 5 минут


def get_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(config.SPREADSHEET_ID).sheet1


def get_records():
    """Возвращает все записи с кэшированием"""
    now = time.time()
    if _cache['data'] is not None and (now - _cache['timestamp']) < CACHE_TTL:
        return _cache['data']

    sheet = get_sheet()
    records = sheet.get_all_records()
    _cache['data'] = records
    _cache['timestamp'] = now
    return records


def clear_cache():
    """Очищает кэш после изменений"""
    _cache['data'] = None
    _cache['timestamp'] = 0


def get_projects():
    """Возвращает словарь {проект: количество} на основе конфига и таблицы"""
    records = get_records()
    projects = {}

    # Инициализируем все проекты из конфига нулями
    for proj in config.PROJECTS:
        projects[proj] = 0

    # Считаем источники из таблицы
    for row in records:
        proj = str(row.get('project', '')).strip()
        if proj in projects:
            projects[proj] += 1

    return projects


def get_sources_by_project(project: str, page: int = 1, items_per_page: int = None):
    if items_per_page is None:
        items_per_page = config.ITEMS_PER_PAGE

    records = get_records()
    filtered = [
        row for row in records
        if str(row.get('project', '')).strip().lower() == str(project).strip().lower()
    ]

    total_items = len(filtered)
    total_pages = (total_items + items_per_page - 1) // items_per_page or 1
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page

    return filtered[start_idx:end_idx], total_pages, total_items


def get_row_index_by_id(source_id):
    sheet = get_sheet()
    cell = sheet.find(str(source_id), in_column=1)
    if cell:
        return cell.row
    return None


def add_source(data: dict):
    sheet = get_sheet()
    all_ids = sheet.col_values(1)[1:]
    max_id = max([int(x) for x in all_ids if x.isdigit()], default=0)
    new_id = max_id + 1

    row = [
        new_id,
        data.get('project', ''),
        data.get('source_name', ''),
        data.get('link', ''),
        data.get('admin_contact', ''),
        data.get('type', 'organic'),
        data.get('stage', 'lead'),
        data.get('price', '0'),
        data.get('date_added', ''),
        data.get('notes', '')
    ]
    sheet.append_row(row, value_input_option='USER_ENTERED')
    clear_cache()  # Очищаем кэш после изменения
    return new_id


def update_source_field(source_id, column_name, new_value):
    row_idx = get_row_index_by_id(source_id)
    if not row_idx:
        return False

    sheet = get_sheet()
    col_map = {
        'project': 2, 'source_name': 3, 'link': 4, 'admin_contact': 5,
        'type': 6, 'stage': 7, 'price': 8, 'date_added': 9, 'notes': 10
    }
    col_idx = col_map.get(column_name)
    if col_idx:
        sheet.update_cell(row_idx, col_idx, new_value)
        clear_cache()  # Очищаем кэш после изменения
        return True
    return False


def hard_delete_source(source_id):
    row_idx = get_row_index_by_id(source_id)
    if row_idx:
        sheet = get_sheet()
        sheet.delete_rows(row_idx)
        clear_cache()  # Очищаем кэш после изменения
        return True
    return False