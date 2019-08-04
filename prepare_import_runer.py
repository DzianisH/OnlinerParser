import math

import pandas as pd

df_in = pd.read_csv('in/iphones.csv')  # prepared csv by Dimon
df_out = pd.DataFrame()


def copy_paste_attributes(df_out, df_in):
    copy_paste_map = {
        'id': 'Артикул',
        'Title': 'Имя',
        'Description': 'Короткое описание',
        'Description in content': 'Описание',
        'specs/Размеры и вес/Вес  (грамм)': 'Вес (kg)',
        'specs/Размеры и вес/Длина  (см)': 'Длина (cm)',
        'specs/Размеры и вес/Толщина  (см)': 'Ширина (cm)',
        'specs/Размеры и вес/Ширина  (см)': 'Высота (cm)',
        'Цена (руб)': 'Базовая цена',
        'Img URL': 'Изображения',
        'specs/Аккумулятор и время работы/Емкость аккумулятора (мА·ч)': 'Емкость аккумулятора (мА·ч)',
        'specs/Основные/Версия операционной системы ': 'Операционная система',
    }

    coma_to_dot_notation = lambda str: str.replace(',', '.')
    copy_paste_transformers = {
        'Вес (kg)': lambda val: val / 1000,
        'Изображения': lambda val: 'https://temp.kupitiphone.by' + val,
        'Длина (cm)': coma_to_dot_notation,
        'Ширина (cm)': coma_to_dot_notation,
        'Высота (cm)': coma_to_dot_notation,
    }

    transformers = copy_paste_transformers.keys()
    for src, dest in copy_paste_map.items():
        df_out[dest] = df_in[src]
        if dest in transformers:
            df_out[dest] = df_out[dest].apply(copy_paste_transformers[dest])

    return df_out

# for index, spec in enumerate(list(filter(lambda x: x.startswith('specs/'), df_in.keys()))):
#     index = str(index + 1)
#     name = spec.split('/')[-1].strip()
#     if len(name) < 4:
#         name = spec.split('/')[-2].strip() + '/' + name
#     if len(name) <= 25:
#         df_out['Имя атрибута ' + index] = name
#         df_out['Значение(-я) аттрибута(-ов) ' + index] = df_in[spec]
#         df_out['Видимость атрибута ' + index] = 1
#         df_out['Глобальный атрибут ' + index] = 1
#     print(len(name), name)


def join_attributes(df_out, df_in):
    SRC = 'src'
    DEST = 'dest'
    SEP = 'sep'
    FILTER = 'filter'
    PATTERN = 'pattern'

    configs = (
        {
            SRC: ('specs/Аккумулятор и время работы/Время ожидания (часов)', 'specs/Аккумулятор и время работы/Время разговора (часов)'),
            DEST: 'Время разговара/ожидания (часов)',
            SEP: '/',
            FILTER: lambda x, y: math.isnan(x) or math.isnan(y),
            PATTERN: '%.0f%s%.0f'
        },
        {
            SRC: ('specs/Основные/Формат SIM-карты ', 'specs/Основные/Количество SIM-карт '),
            DEST: 'SIM-карта',
            SEP: ' x',
            PATTERN: '%s%s%s'
        },
        {
            SRC: ('specs/Основные/Оперативная память  (ГБ)', 'specs/Основные/Флэш-память  (ГБ)'),
            DEST: 'Память оперативная/флэш (ГБ)',
            SEP: '/',
            FILTER: lambda x, y: math.isnan(x) or math.isnan(y),
            PATTERN: '%d%s%d'
        },
    )

    def joiner(config):
        filter = config.get(FILTER)
        if filter is None:
            filter = lambda x, y: False

        def join(x, y):
            if x is None or y is None or filter(x, y):
                return None
            return config[PATTERN] % (x, config[SEP], y)
        return join

    for config in configs:
        values = None
        for index, column in enumerate(config[SRC]):
            if index == 0:
                values = df_in[column]
            else:
                values = values.combine(df_in[column], joiner(config))
        add_global_attribute(df_out, config[DEST], values)

def join_flags(df_out, df_in):
    SRC = 'src'
    DEST = 'dest'

    configs = (
        {
            SRC: ('specs/Датчики/Акселерометр ', 'specs/Датчики/Барометр ', 'specs/Датчики/Гироскоп ',
                  'specs/Датчики/Датчик освещенности '),
            DEST: 'Датчики'
        },
        {
            SRC: ('specs/Навигация/Beidou ', 'specs/Навигация/GPS ', 'specs/Навигация/ГЛОНАСС ',
                  'specs/Интерфейсы/Bluetooth ', 'specs/Интерфейсы/HDMI-выход ', 'specs/Интерфейсы/NFC ',
                  'specs/Интерфейсы/Wi-Fi ', 'specs/Интерфейсы/Аудиовыход ', 'specs/Интерфейсы/Разъём подключения ',
                  'specs/Интерфейсы/NFC (только для Apple Pay)', 'specs/Интерфейсы/NFC (Apple Pay)'
                  ),
            DEST: 'Интерфейсы'
        },
        {
            SRC: ('specs/Передача данных/EDGE ', 'specs/Передача данных/HSPA ', 'specs/Передача данных/HSPA+ ',
                  'specs/Передача данных/LTE ',
                  ),
            DEST: 'Передача данных'
        },
        {
            SRC: ('specs/Функции/FM-приёмник ', 'specs/Функции/Беспроводная зарядка ', 'specs/Функции/ИК-передатчик ',
                  'specs/Функции/Работа в перчатках ', 'specs/Функции/Стереодинамики ',
                  'specs/Функции/Сканер отпечатка пальца ', 'specs/Функции/Быстрая зарядка ',
                  'specs/Функции/Сканер карты лица или радужки глаза (Face ID)', 'specs/Функции/Разблокировка по лицу '

                  ),
            DEST: 'Дополнительные функции'
        },
    )

    def mapper(column):
        column = column.strip().split('/')[-1]
        chunk = column[1:]
        if chunk == chunk.lower():
            column = column.lower()

        def mapper1(src):
            if src == 'ДА':
                return column
            return ''
        return mapper1

    def combiner(x, y):
        if x is None or len(x) == 0:
            if y is None or len(y) == 0:
                return ''
            return y
        elif y is None or len(y) == 0:
            return x
        return "%s, %s" % (x, y)

    for config in configs:
        values = None
        for column in config[SRC]:
            col = df_in[column].apply(mapper(column))
            if values is None:
                values = col
            else:
                values = values.combine(col, combiner)
        values = values.apply(lambda str: str[0:1].upper() + str[1:])
        add_global_attribute(df_out, config[DEST], values)

attr_index = 0
def add_global_attribute(df_out, name, values):
    global attr_index
    index = str(attr_index)
    df_out['Имя атрибута ' + index] = name
    df_out['Значение(-я) аттрибута(-ов) ' + index] = values
    df_out['Видимость атрибута ' + index] = 1
    df_out['Глобальный атрибут ' + index] = 1
    attr_index += 1

    return df_out


print('data prepared')

copy_paste_attributes(df_out, df_in)
print('copy_paste_attributes done')

join_attributes(df_out, df_in)
print('join_attributes done')

join_flags(df_out, df_in)
print('join_flags done')

df_out.to_csv('out/wp_iphones.csv')



