import gspread
from oauth2client.service_account import ServiceAccountCredentials
import config
import random
from datetime import datetime, timedelta

SCOPES = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]


def seed_test_data():
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(config.SPREADSHEET_ID).sheet1

    print("⏳ Очищаю старые данные (это может занять пару секунд)...")
    try:
        # Удаляем всё, начиная со 2-й строки и до конца таблицы
        sheet.delete_rows(2, 2000)
    except Exception:
        pass

    print("⏳ Генерирую 500 тестовых записей...")

    projects = ["image_bot", "vk_flirt_bot", "tg_flirt_bot", "shira_neuro_bot"]
    stages = ["active", "lead", "negotiation"]
    types = ["organic", "paid"]

    test_data = []
    base_date = datetime(2026, 10, 1)

    for i in range(1, 501):
        project = random.choice(projects)
        src_type = random.choice(types)
        stage = random.choice(stages)

        # Генерируем реалистичные названия
        source_name = f"{project.split('_')[0]}_source_{i}"

        # Ссылки
        if "vk" in project:
            link = f"https://vk.com/{source_name}"
        else:
            link = f"https://t.me/{source_name}"

        admin = f"@admin_{i}"

        # Цена: 0 для organic, случайная от 100 до 5000 для paid
        price = "0" if src_type == "organic" else str(random.randint(100, 5000))

        # Дата: случайная в пределах последних 30 дней
        random_date = base_date - timedelta(days=random.randint(0, 30))
        date_str = random_date.strftime("%Y-%m-%d")

        notes = f"Тестовая запись #{i}"

        test_data.append([
            str(i), project, source_name, link, admin, src_type, stage, price, date_str, notes
        ])

    print("⏳ Загружаю 500 записей в Google Sheets (массовая вставка)...")
    # value_input_option='USER_ENTERED' гарантирует, что Google корректно распознает типы данных
    sheet.append_rows(test_data, value_input_option='USER_ENTERED')

    print("✅ УСПЕХ! 500 записей успешно добавлены в таблицу.")
    print("Теперь запустите бота (python main.py) и напишите /sources, чтобы увидеть магию пагинации!")


if __name__ == "__main__":
    seed_test_data()