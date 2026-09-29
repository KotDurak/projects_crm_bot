from aiogram.fsm.state import State, StatesGroup

class AddProjectState(StatesGroup):
    name = State()

class EditProjectState(StatesGroup):
    project_id = State()
    new_name = State()

class AddSourceState(StatesGroup):
    project_id = State()
    name = State()
    url = State()
    platform = State()
    posting_type = State()
    note = State()

class EditSourceState(StatesGroup):
    source_id = State()
    field = State()  # 'note' или 'status'
    new_value = State()