from flask_wtf import FlaskForm
from wtforms import BooleanField, SubmitField, HiddenField, StringField, IntegerField
from markupsafe import Markup


class KimBooleanInputField(BooleanField):
    def __init__(self, *args, label=None, min_val=1, max_val=20, **kwargs):
        super().__init__(label, *args, **kwargs)
        self.min_val = min_val
        self.max_val = max_val

    def __call__(self, *args, **kwargs):
        num = kwargs.pop('num', None)
        if num is None:
            try:
                num = int(self.name.split('_')[1])
            except Exception:
                num = 0

        html = super().__call__(**{'id': f'kim-{num}', 'data-kim': num, **kwargs})
        return Markup(html)


class VariantGenerationForm(FlaskForm):
    kim_1 = KimBooleanInputField("Анализ информационных моделей")
    kim_2 = KimBooleanInputField("Таблицы истинности логических выражений")
    kim_3 = KimBooleanInputField("Поиск и сортировка в базах данных")
    kim_4 = KimBooleanInputField("Кодирование и декодирование данных. Условие Фано")
    kim_5 = KimBooleanInputField("Анализ алгоритмов для исполнителей")
    kim_6 = KimBooleanInputField("Циклические алгоритмы для Исполнителя")
    kim_7 = KimBooleanInputField("Кодирование графической и звуковой информации")
    kim_8 = KimBooleanInputField("Комбинаторика")
    kim_9 = KimBooleanInputField("Обработка числовой информации в электронных таблицах")
    kim_10 = KimBooleanInputField("Поиск слова в текстовом документе")
    kim_11 = KimBooleanInputField("Вычисление количества информации")
    kim_12 = KimBooleanInputField("Машина Тьюринга")
    kim_13 = KimBooleanInputField("IP адреса и маски")
    kim_14 = KimBooleanInputField("Позиционные системы счисления")
    kim_15 = KimBooleanInputField("Истинность логического выражения")
    kim_16 = KimBooleanInputField("Вычисление значения рекурсивной функции")
    kim_17 = KimBooleanInputField("Обработка целочисленных данных. Проверка делимости")
    kim_18 = KimBooleanInputField("Динамическое программирование в электронных таблицах")
    kim_19_21 = KimBooleanInputField("Теория игр (19-21)")
    kim_22 = KimBooleanInputField("Многопоточные вычисления")
    kim_23 = KimBooleanInputField("Динамическое программирование (количество программ)")
    kim_24 = KimBooleanInputField("Обработка символьных строк")
    kim_25 = KimBooleanInputField("Обработка целочисленных данных. Поиск делителей")
    kim_26 = KimBooleanInputField("Обработка данных с помощью сортировки")
    kim_27 = KimBooleanInputField("Анализ данных")

    submit = SubmitField('Сгенерировать случайный вариант')


class VariantEditForm(FlaskForm):
    variant_id = HiddenField()
    source = StringField('Источник')
    add_task_id = IntegerField('ID задачи')
    save = SubmitField('Сохранить')
    add_task = SubmitField('Добавить задачу')
