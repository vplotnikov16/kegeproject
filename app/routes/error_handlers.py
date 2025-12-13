import inspect

from flask import render_template, Blueprint, abort
from werkzeug.exceptions import default_exceptions

error_bp = Blueprint("error", __name__)


@error_bp.route("/<int:error_code>")
def error_test(error_code: int):
    if error_code not in _get_all_handled_codes():
        return abort(404)
    abort(error_code)


def _get_all_handled_codes():
    if not hasattr(_get_all_handled_codes, "codes"):
        codes = {}
        for name, obj in globals().items():
            if not name.startswith("handle_"):
                continue
            if not inspect.isfunction(obj):
                continue

            code_str = name.removeprefix("handle_")
            # смотрим только числовые коды
            if not code_str.isdigit():
                continue

            code = int(code_str)
            # пропускаем коды, которые Flask не поддерживает
            if code not in default_exceptions:
                continue

            codes[code] = obj
            _get_all_handled_codes.codes = codes

    return _get_all_handled_codes.codes


def register_error_handlers(app):
    for code, obj in _get_all_handled_codes().items():
        app.register_error_handler(code, obj)


def _handle_impl(template: str = "error.html", title: str = "Ошибка", error=None, **kwargs):
    if error is not None:
        title = f"Ошибка {error.code}: {title}"
    return render_template(template, title=title, **kwargs)


def handle_400(error):
    title = "Некорректный запрос"
    text1 = "Неправильный или неполный запрос"
    text2 = "Сервер сделал вид, что понял, но на самом деле ничего не понял :/"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_401(error):
    title = "Нет доступа"
    text1 = "Требуется авторизация"
    text2 = "Покажите, пожалуйста, паспорт... то есть логин и пароль :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_402(error):
    title = "Нужна оплата"
    text1 = "Для доступа требуется оплата"
    text2 = "Бесплатно только сыр в мышеловке и эта страница с ошибкой :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_403(error):
    title = "Запрещено"
    text1 = "У вас нет прав для доступа"
    text2 = "Даже если очень хочется, сюда всё равно нельзя :("
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_404(error):
    title = "Не найдено"
    text1 = "Страница не найдена"
    text2 = "Искали всем сервером, но так ничего и не нашли :/"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_405(error):
    title = "Метод не поддерживается"
    text1 = "Этот HTTP-метод здесь не работает"
    text2 = "Попробуйте постучаться другим способом, этот сервер не понимает :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_406(error):
    title = "Неприемлемо"
    text1 = "Сервер не может отдать подходящий ответ"
    text2 = "Вы такой избирательный, что сервер растерялся и отказался отвечать :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_407(error):
    title = "Нужна аутентификация прокси"
    text1 = "Требуется авторизация на прокси-сервере"
    text2 = "Сначала договоритесь с прокси, а потом уже с этим сервером :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_408(error):
    title = "Таймаут запроса"
    text1 = "Истекло время ожидания запроса"
    text2 = "Сервер заждался и ушёл пить чай, попробуйте ещё раз :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_409(error):
    title = "Конфликт"
    text1 = "Запрос конфликтует с текущим состоянием ресурса"
    text2 = "Кажется, ваши планы не совпали с планами сервера :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_410(error):
    title = "Ресурс удалён"
    text1 = "Запрошенный ресурс больше не существует"
    text2 = "Он был, но ушёл в лучшее цифровое место и не вернётся :("
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_411(error):
    title = "Нужна длина"
    text1 = "Не указана длина содержимого запроса"
    text2 = "Сервер любит всё измерять, а вы не сказали, сколько байт принесли :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_412(error):
    title = "Условие не выполнено"
    text1 = "Предусловия для запроса не выполнены"
    text2 = "Если бы условия были верны, всё бы сработало, а так увы :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_413(error):
    title = "Слишком большой запрос"
    text1 = "Полезная нагрузка запроса слишком велика"
    text2 = "Запрос такой тяжёлый, что серверу понадобился бы спортзал :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_414(error):
    title = "Слишком длинный адрес"
    text1 = "URI запроса слишком длинный"
    text2 = "Такой длинный адрес даже сервер не в силах запомнить :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_415(error):
    title = "Тип не поддерживается"
    text1 = "Формат переданных данных не поддерживается"
    text2 = "Серверу этот формат так же незнаком, как вам prolog :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_416(error):
    title = "Неверный диапазон"
    text1 = "Запрошенный диапазон данных недостижим"
    text2 = "Вы запросили то, чего в файле нет, сервер в лёгком недоумении :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_417(error):
    title = "Ожидания не оправдались"
    text1 = "Сервер не смог выполнить ожидания из заголовка"
    text2 = "К сожалению, сервер не волшебник и выполнить это ожидание не может :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_418(error):
    title = "Я — чайник"
    text1 = "Сервер притворяется чайником"
    text2 = "Кофе не сварит, максимум заварит чай и вернёт эту ошибку :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_419(error):
    title = "Сессия истекла"
    text1 = "Срок действия аутентификации истёк"
    text2 = "Пока вы думали над запросом, сервер успел всё забыть :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_421(error):
    title = "Неверный адресат"
    text1 = "Запрос попал не на тот сервер"
    text2 = "Запрос перепутал дверь и постучался не туда :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_422(error):
    title = "Необрабатываемый объект"
    text1 = "Сервер не может обработать переданные данные"
    text2 = "Данные вроде есть, но сервер не понимает, что с ними делать :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_423(error):
    title = "Ресурс заблокирован"
    text1 = "Запрошенный ресурс заблокирован"
    text2 = "Ресурс закрылся изнутри и делает вид, что его нет дома :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_424(error):
    title = "Зависимость не выполнена"
    text1 = "Связанный с запросом ресурс не выполнил операции"
    text2 = "Одна часть системы подвела другую — классика микросервисов :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_425(error):
    title = "Слишком рано"
    text1 = "Запрос выполнен преждевременно"
    text2 = "Вы торопитесь, а сервер ещё не проснулся и не готов отвечать :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_426(error):
    title = "Нужно обновление"
    text1 = "Для продолжения требуется обновить протокол или клиент"
    text2 = "Обновитесь, и сервер сразу станет добрее и разговорчивее :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_428(error):
    title = "Нужно предусловие"
    text1 = "Для этого запроса требуется предусловие"
    text2 = "Сервер ждёт, что вы скажете «если», а уже потом будете что-то менять :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_429(error):
    title = "Слишком много запросов"
    text1 = "Вы отправили слишком много запросов"
    text2 = "Серверу нужно немного передохнуть, а вам — поменьше флуда :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_431(error):
    title = "Слишком большие заголовки"
    text1 = "Поля заголовков запроса слишком велики"
    text2 = "Ваши заголовки такие объёмные, что серверу стало тесно в памяти :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_449(error):
    title = "Повторите запрос"
    text1 = "Нужно повторить запрос с другими условиями"
    text2 = "Сервер предлагает попробовать ещё раз, но уже по-умному :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_451(error):
    title = "Заблокировано законом"
    text1 = "Доступ ограничен по юридическим причинам"
    text2 = "Здесь могла быть ваша страница, но юристы были против :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_499(error):
    title = "Клиент закрыл соединение"
    text1 = "Клиент прервал запрос до ответа сервера"
    text2 = "Вы ушли раньше, чем сервер успел что-то сказать :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_500(error):
    title = "Внутренняя ошибка"
    text1 = "На сервере произошла непредвиденная ошибка"
    text2 = "В серверной сейчас кого-то оттарабанят и все заработает :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_501(error):
    title = "Не реализовано"
    text1 = "Сервер не поддерживает эту функциональность"
    text2 = "Идея хорошая, но код до неё ещё не дорос :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_502(error):
    title = "Плохой шлюз"
    text1 = "Сервер получил некорректный ответ от вышестоящего сервера"
    text2 = "Кто-то из соседних серверов сказал что-то невнятное, и всё сломалось :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_503(error):
    title = "Сервис недоступен"
    text1 = "Сервер временно не может обработать запрос"
    text2 = "Сервер ушёл на технический перекус, зайдите чуть позже :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_504(error):
    title = "Таймаут шлюза"
    text1 = "Вышестоящий сервер не ответил вовремя"
    text2 = "Шлюз ждал-ждал ответа и устал, как вы в очереди :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_505(error):
    title = "Версия HTTP не поддерживается"
    text1 = "Используемая версия HTTP не поддерживается сервером"
    text2 = "Серверу нравятся современные стандарты, а не этот исторический экспонат :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_506(error):
    title = "Ошибка переговоров"
    text1 = "Вариант ресурса тоже требует согласования"
    text2 = "Сервер запутался в вариантах ответа и решил отказаться совсем :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_507(error):
    title = "Нет места"
    text1 = "На сервере недостаточно места для обработки запроса"
    text2 = "Диск забит под завязку, как ваш рабочий стол ярлыками :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_508(error):
    title = "Цикл обнаружен"
    text1 = "Обнаружено бесконечное перенаправление или цикл"
    text2 = "Запрос ходит по кругу, как забытый разработчик по документации :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_509(error):
    title = "Превышен трафик"
    text1 = "Исчерпана пропускная способность канала"
    text2 = "Похоже, ваш сайт стал слишком популярным, сервер не вывез :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_510(error):
    title = "Не расширено"
    text1 = "Для запроса не указаны необходимые расширения"
    text2 = "Сервер ждёт особых условий в запросе, а их там нет :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_511(error):
    title = "Нужна сетевая авторизация"
    text1 = "Требуется авторизация в сети перед доступом"
    text2 = "Сначала войдите в сеть, а уже потом в эту страницу :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_520(error):
    title = "Неизвестная ошибка"
    text1 = "Произошла неизвестная ошибка на промежуточном узле"
    text2 = "Даже сервер толком не понял, что случилось, но выглядит это подозрительно :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_521(error):
    title = "Веб-сервер не работает"
    text1 = "Промежуточный узел не может подключиться к веб-серверу"
    text2 = "Похоже, веб-сервер ушёл погулять и забыл вернуться :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_522(error):
    title = "Таймаут соединения"
    text1 = "Превышено время ожидания ответа от сервера"
    text2 = "Соединение так долго думало, что в итоге передумало существовать :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_523(error):
    title = "Источник недоступен"
    text1 = "Промежуточный узел не может добраться до исходного сервера"
    text2 = "Где-то по пути к серверу дорогу размыло и пакеты не дошли :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_524(error):
    title = "Истёк таймаут"
    text1 = "Сервер не успел ответить в отведённое время"
    text2 = "Запрос завис так надолго, что даже сервер устал ждать :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_525(error):
    title = "Ошибка SSL-рукопожатия"
    text1 = "Не удалось установить защищённое соединение"
    text2 = "Сервер попытался пожать вам руку по SSL, но что-то пошло не так :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)


def handle_526(error):
    title = "Неверный SSL-сертификат"
    text1 = "Сертификат SSL недействителен или некорректен"
    text2 = "Сертификат показали, а сервер не поверил и вежливо отказал :)"
    return _handle_impl(title=title, text1=text1, text2=text2, error=error)
