crm_bot/
├── main.py              # Точка входа
├── config.py            # Конфигурация
├── database.py          # Работа с БД
├── keyboards.py         # Клавиатуры
├── states.py            # FSM-состояния
├── utils.py             # Утилиты (экранирование, ссылки)
├── handlers/
│   ├── __init__.py
│   ├── projects.py      # Хендлеры проектов
│   └── sources.py       # Хендлеры источников
├── crm.db               # SQLite-база (создаётся автоматически)
└── .env                 # Секреты (не коммитить!)

python3 -m venv venv
source venv/bin/activate

python3 -m venv venv
source venv/bin/activate

pip install aiogram aiosqlite python-dotenv

cd ~/python/crm_bot
source venv/bin/activate
python main.py