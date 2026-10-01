import gspread
from oauth2client.service_account import ServiceAccountCredentials
import config

SCOPES = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]


def restore_validation():
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
    sheet = spreadsheet.sheet1

    # ID листа (обычно 0 для первого листа)
    sheet_id = sheet.id

    # Настройки правил (индексы столбцов начинаются с 0: A=0, B=1...)
    rules = {
        1: {  # Столбец B (project)
            "options": ["image_bot", "vk_flirt_bot", "tg_flirt_bot", "shira_neuro_bot"]
        },
        5: {  # Столбец F (type)
            "options": ["organic", "paid"]
        },
        6: {  # Столбец G (stage)
            "options": ["active", "lead", "negotiation"]
        }
    }

    requests = []

    # 1. Добавляем выпадающие списки (Dropdowns)
    for col_index, data in rules.items():
        requests.append({
            "setDataValidation": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 1,  # Пропускаем заголовок (строка 1)
                    "startColumnIndex": col_index,
                    "endColumnIndex": col_index + 1
                },
                "rule": {
                    "condition": {
                        "type": "ONE_OF_LIST",
                        "values": [{"userEnteredValue": val} for val in data["options"]]
                    },
                    "showCustomUi": True,  # Показывать выпадающий список в UI
                    "strict": True  # Запретить ввод других значений
                }
            }
        })

    # 2. Добавляем проверку даты для столбца I (index 8)
    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 1,
                "startColumnIndex": 8,
                "endColumnIndex": 9
            },
            "rule": {
                "condition": {
                    "type": "DATE_IS_VALID"
                },
                "showCustomUi": True,
                "strict": False
            }
        }
    })

    # Отправляем все правила одним пакетом
    if requests:
        body = {"requests": requests}
        spreadsheet.batch_update(body)
        print("✅ Правила проверки данных (селекты и даты) успешно восстановлены!")
    else:
        print("Нечего восстанавливать.")


if __name__ == "__main__":
    restore_validation()