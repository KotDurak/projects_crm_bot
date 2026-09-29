def escape_md(text: str) -> str:
    """Экранирует спецсимволы только для обычного текста (имя, заметка)"""
    if not text:
        return ""
    for char in ("_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"):
        text = text.replace(char, f"\\{char}")
    return text


def make_clickable(url: str) -> str:
    """Делает ссылку кликабельной. Это автоматически решает проблему с символами _ и ."""
    if not url or url.lower() == "skip":
        return ""

    url = url.strip()
    # Если это юзернейм телеграма (начинается с @)
    if url.startswith('@'):
        return f"[{url}](https://t.me/{url[1:]})"
    # Если это уже полная ссылка
    if url.startswith('http'):
        return f"[{url}]({url})"
    # Если просто домен, добавляем https://
    return f"[{url}](https://{url})"