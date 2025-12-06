from bs4 import BeautifulSoup
from markupsafe import Markup, escape


def make_snippet(html: str, max_chars: int = 600) -> str:
    """
    Принимает HTML условия (trusted or untrusted). Возвращает безопасный HTML-сниппет:
    - удаляем теги <script> и т.д.
    - берем текст (с сохранением минимального форматирования: <b>, <i>, <code> — опционально)
    - обрезаем по символам и добавляем '...'
    """
    if not html:
        return ''

    # Используем BeautifulSoup (pip install beautifulsoup4) — безопасно убрать скрипты, стиль и т.п.
    soup = BeautifulSoup(html, 'html.parser')

    # удаляем скрипты/styles
    for bad in soup(['script', 'style']):
        bad.decompose()

    text = soup.get_text(separator=' ', strip=True)

    if len(text) <= max_chars:
        safe = escape(text)
    else:
        safe = escape(text[:max_chars].rsplit(' ', 1)[0] + '…')

    # Можно доп. завернуть в <p>
    return Markup(f'<p>{safe}</p>')
