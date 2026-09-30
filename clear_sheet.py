import gspread
from oauth2client.service_account import ServiceAccountCredentials
import config

SCOPES = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]


def clear_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(config.SPREADSHEET_ID).sheet1

    # Вместо удаления строк, просто очищаем диапазон ячеек.
    # A2:J1000 покрывает ваши 10 колонок и с запасом на 1000 строк.
    sheet.batch_clear(["A2:J1000"])
    print("✅ Таблица очищена! Заголовки на месте, фейки уничтожены.")


if __name__ == "__main__":
    clear_sheet()