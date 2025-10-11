from typing import List


def get_username(first_name: str, last_name: str, middle_name: str | None = None) -> str:
    """
    Генерация имени пользователя на основе ФИО.
    :param first_name: Имя
    :param last_name: Фамилия
    :param middle_name: Отчество
    :return: Имя пользователя
    """
    fst = transliterate_impl(first_name)[0]
    mid = transliterate_impl(middle_name)[0] if middle_name else ''
    lst = transliterate(last_name)
    return f'{fst}{mid}_{lst}'


def transliterate_impl(name: str) -> List[str]:
    """
    Возвращает по символам транслитерацию имени по стандарту ГОСТ Р 52535.1-2006.
    :param name: Имя на русском
    :return: Список символов имени на английском
    """
    mapping = {
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D',
        'Е': 'E', 'Ё': 'E', 'Ж': 'ZH', 'З': 'Z', 'И': 'I',
        'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
        'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
        'У': 'U', 'Ф': 'F', 'Х': 'KH', 'Ц': 'TS', 'Ч': 'CH',
        'Ш': 'SH', 'Щ': 'SHCH', 'Ы': 'Y', 'Э': 'E', 'Ю': 'YU', 'Я': 'YA',
        'Ь': '', 'Ъ': '', ' ': ' ', '-': '-',
    }

    name = name.strip().upper()
    vowels = 'АЕЁИОУЫЭЮЯ'

    result: List[str] = []
    capitalize_next = True

    i = 0
    while i < len(name):
        ch = name[i]

        if ch in (' ', '-'):
            result.append(ch)
            capitalize_next = True
            i += 1
            continue

        if ch == 'Е' and i > 0 and name[i - 1] in vowels + 'ЪЬ':
            translit = 'YE'
        elif ch == 'Ё' and i > 0 and name[i - 1] in vowels + 'ЪЬ':
            translit = 'YO'
        else:
            translit = mapping.get(ch, ch)

        for j, sym in enumerate(translit):
            if capitalize_next and j == 0:
                result.append(sym.upper())
                capitalize_next = False
            else:
                result.append(sym.lower())

        i += 1

    return result


def transliterate(name: str) -> str:
    """
    Возвращает готовую транслитерацию имени цельной строкой.
    :param name: Имя на русском
    :return: Имя на английским
    """
    return ''.join(transliterate_impl(name))
