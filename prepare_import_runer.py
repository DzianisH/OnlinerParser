import math
from shutil import copyfile
import datetime
import base64

import pandas as pd

df_in = pd.read_csv('in/iphones.csv')  # prepared csv by Dimon
df_out = pd.DataFrame()


def copy_paste_attributes(df_out, df_in):
    SRC = 'src'
    DEST = 'dest'
    TRF = 'transformer'
    GLOBAL = 'global'

    coma_to_dot_notation = lambda str: str.replace(',', '.')

    configs = (
        {SRC: 'iPhone URL', DEST: 'Артикул', TRF: lambda url: url.split('/')[-2]},
        {SRC: 'H1', DEST: 'Имя', TRF: lambda str: str.replace(' в Гомеле', '')},
        {SRC: 'iPhone URL', DEST: 'Ярлык', TRF: lambda url: url.replace(
            'https://kupitiphone.by/', 'https://temp.kupitiphone.by/')},
        #      'Title': '', # title в <head> имя страницы
        #     'Description': '', # description в <head>
        {SRC: 'Description in content', DEST: 'Короткое описание'},
        {SRC: 'Description', DEST: 'Мета: _yoast_wpseo_metadesc'},
        {SRC: 'specs/Размеры и вес/Вес  (грамм)', DEST: 'Вес (kg)', TRF: lambda val: val / 1000},
        {SRC: 'specs/Размеры и вес/Длина  (см)', DEST: 'Длина (cm)', TRF: coma_to_dot_notation},
        {SRC: 'specs/Размеры и вес/Толщина  (см)', DEST: 'Ширина (cm)', TRF: coma_to_dot_notation},
        {SRC: 'specs/Размеры и вес/Ширина  (см)', DEST: 'Высота (cm)', TRF: coma_to_dot_notation},
        {SRC: 'Цена (руб)', DEST: 'Базовая цена'},
        {SRC: 'specs/Аккумулятор и время работы/Емкость аккумулятора (мА·ч)', DEST: 'Емкость аккумулятора (мА·ч)',
         GLOBAL: True},
        {SRC: 'specs/Основные/Версия операционной системы ', DEST: 'Операционная система', GLOBAL: True},
    )

    for config in configs:
        values = df_in[config[SRC]]
        if config.get(TRF) is not None:
            values = values.apply(config[TRF])
        if config.get(GLOBAL) is True:
            add_global_attribute(df_out, config[DEST], values)
        else:
            df_out[config[DEST]] = values

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

def combiner(x, y):
    if x is None or len(x) == 0:
        if y is None or len(y) == 0:
            return ''
        return y
    elif y is None or len(y) == 0:
        return x
    return "%s, %s" % (x, y)


def join_attributes(df_out, df_in):
    SRC = 'src'
    DEST = 'dest'
    SEP = 'sep'
    FILTER = 'filter'
    PATTERN = 'pattern'

    configs = (
        {
            SRC: ('specs/Аккумулятор и время работы/Время ожидания (часов)',
                  'specs/Аккумулятор и время работы/Время разговора (часов)'),
            DEST: 'Время разговор/ожидан (ч)',  # wtf
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
            DEST: 'Память рабочая/флэш (ГБ)',
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


def map_join_attributes(df_out, df_in):
    SRC = 'src'
    DEST = 'dest'
    COLUMN = 'column'
    MAPPER = 'mapper'

    def dust_and_water(value):
        if 'НЕТ' == value:
            return None
        return "пыле- и влагозащита (%s)" % value.strip()

    def num_of_main_cameras(value):
        if value > 1:
            return "основных камер: %dшт" % value
        return None

    def mp(value):
        value = str(value)
        if value is not None and len(value) > 0 and value != 'nan':
            return "%s Мп" % value
        return None

    def diagram(value):
        value = str(value)
        if value is not None and len(value) > 0 and value != 'nan':
            return "диафрагма: " + value
        return None

    def filter_empty(value):
        value = str(value)
        if value is not None and len(value) > 0 and value != 'nan':
            return value
        return None

    def video_resolution(value):
        value = str(value)
        if value is not None and len(value) > 0 and value != 'nan':
            return "разрешение видео до " + value
        return None

    def optical_zoom(value):
        if value is not None and not math.isnan(value) > 0:
            return "оптический зум x%d" % value
        return None

    def screen_protect(value):
        if value == 'ДА':
            return 'защита от царапин'
        return None

    def frequency(value):
        if value is not None and not math.isnan(value):
            return '%dМГц' % value
        return None

    def gpu(value):
        value = str(value)
        if value is not None and len(value) > 0 and value != 'nan':
            return 'GPU: ' + value
        return None

    def gpu_frequency(value):
        if value is not None and not math.isnan(value):
            return 'частота GPU: %d' % value
        return None

    configs = (
        {
            SRC: (
                {
                    COLUMN: 'specs/Конструкция/Конструкция корпуса ',
                    MAPPER: lambda str: "конструкция: " + str
                },
                {
                    COLUMN: 'specs/Конструкция/Материал корпуса ',
                    MAPPER: lambda str: str.replace(', ', ' и ')
                },
                {
                    COLUMN: 'specs/Конструкция/Пыле- и влагозащита ',
                    MAPPER: dust_and_water
                },
                {
                    COLUMN: 'specs/Конструкция/Цвет корпуса ',
                },
            ),
            DEST: 'Конструкция'
        },
        {
            SRC: (
                {
                    COLUMN: 'specs/Основные/Количество точек матрицы  (Мп)',
                    MAPPER: mp
                },
                {
                    COLUMN: 'specs/Основные/Количество основных камер ',
                    MAPPER: num_of_main_cameras
                },
                {
                    COLUMN: 'specs/Основные/Максимальное разрешение видео ',
                    MAPPER: video_resolution
                },
                {
                    COLUMN: 'specs/Основная камера/Диафрагма основной камеры ',
                    MAPPER: diagram
                },
                {
                    COLUMN: 'specs/Основная камера/Дополнительные модули камеры ',
                    MAPPER: filter_empty
                },
                {
                    COLUMN: 'specs/Основная камера/Оптический зум  (Х)',
                    MAPPER: optical_zoom
                },
            ),
            DEST: 'Основная камера'
        },
        {
            SRC: (
                {
                    COLUMN: 'specs/Фронтальная камера/Фронтальная камера  (Мп)',
                    MAPPER: mp
                },
                {
                    COLUMN: 'specs/Фронтальная камера/Максимальное разрешение видео ',
                    MAPPER: video_resolution
                },
                {
                    COLUMN: 'specs/Фронтальная камера/Диафрагма ',
                    MAPPER: diagram
                },
            ),
            DEST: 'Фронтальная камера'
        },
        {
            SRC: (
                {
                    COLUMN: 'specs/Основные/Размер экрана ',
                    MAPPER: lambda val: 'размер экрана ' + val
                },
                {
                    COLUMN: 'specs/Основные/Разрешение экрана ',
                    MAPPER: lambda str: str + " точек"
                },
                {
                    COLUMN: 'specs/Экран/Технология экрана ',
                },
                {
                    COLUMN: 'specs/Экран/Количество цветов экрана  (млн)',
                    MAPPER: lambda val: str(val) + "млн. цветов"
                },
                {
                    COLUMN: 'specs/Экран/Соотношение сторон ',
                },
                {
                    COLUMN: 'specs/Экран/Разрешающая способность экрана  (ppi)',
                    MAPPER: lambda val: str(val) + "ppi"
                },
                {
                    COLUMN: 'specs/Экран/Защита от царапин ',
                    MAPPER: screen_protect
                },
            ),
            DEST: 'Экран'
        },
        {
            SRC: (
                {
                    COLUMN: 'specs/Процессор/Процессор ',
                },
                {
                    COLUMN: 'specs/Процессор/Разрядность процессора  (Бит)',
                    MAPPER: lambda val: '%d бита' % val
                },
                {
                    COLUMN: 'specs/Процессор/Тактовая частота процессора  (МГц)',
                    MAPPER: frequency
                },
                {
                    COLUMN: 'specs/Процессор/Количество ядер ',
                    MAPPER: lambda val: str(val) + ' ядер'
                },
                {
                    COLUMN: 'specs/Процессор/Техпроцесс  (нм)',
                    MAPPER: lambda val: "на техпроцессе %dнм" % val
                },

                {
                    COLUMN: 'specs/Процессор/Графический ускоритель ',
                    MAPPER: gpu
                },
                {
                    COLUMN: 'specs/Процессор/Частота ГПУ  (МГц)',
                    MAPPER: gpu_frequency
                },
            ),
            DEST: 'Процессор и ГПУ'
        },
    )

    def post_proccess_row(row):
        if row is None or len(row.strip()) == 0:
            return None
        return row[0].upper() + row[1:]

    for config in configs:
        values = None
        for src in config[SRC]:
            col = df_in[src[COLUMN]]
            if src.get(MAPPER) is not None:  # Fix no value error
                col = col.apply(src.get(MAPPER))
            if values is None:
                values = col
            else:
                values = values.combine(col, combiner)
        values = values.apply(post_proccess_row)
        add_global_attribute(df_out, config[DEST], values)


def add_images(df_out, df_in):
    now = datetime.datetime.now()
    IMGS_IN_FOLDER = 'in/imgs/'
    IMGS_OUT_FOLDER = 'out/wp_imgs/'
    IMGS_URL_PREFIX = 'https://temp.kupitiphone.by/wp-content/uploads/%d/%02d/' % (now.year, now.month)

    DEST = 'Изображения'
    SRC = 'Img URL'
    IMG_TITLE = 'Img Title'
    IMG_ALT = 'Img Alt'

    src_imgs = df_in[SRC].apply(lambda link: link.split('/')[-1])
    target_props = df_in[IMG_TITLE].combine(df_in[IMG_ALT],
                                            lambda x, y: '%s###%s' % (x.strip(), y.strip()))
    target_props = target_props.apply(lambda props: base64.encodebytes(props.encode('utf-8'))
                                      .decode("utf-8").strip()
                                      .replace('/', '#').replace('=', '')
                                      .replace('\n', ''))

    def copy_img(src_name, prop):
        ext = src_name.split('.')[-1]
        dest_name = prop + '.' + ext
        copyfile(IMGS_IN_FOLDER + src_name, IMGS_OUT_FOLDER + dest_name)
        return IMGS_URL_PREFIX + dest_name

    df_out[DEST] = src_imgs.combine(target_props, copy_img)


attr_index = 0


def add_global_attribute(df_out, name, values):
    global attr_index
    index = str(attr_index)
    df_out['Имя атрибута ' + index] = name
    df_out['Значение(-я) аттрибута(-ов) ' + index] = values
    df_out['Видимость атрибута ' + index] = values.apply(lambda row: 1 - (row is None))
    df_out['Глобальный атрибут ' + index] = 1
    attr_index += 1

    return df_out


print('data prepared')

copy_paste_attributes(df_out, df_in)
print('copy_paste_attributes done')

add_images(df_out, df_in)
print('add_images done')

join_attributes(df_out, df_in)
print('join_attributes done')

join_flags(df_out, df_in)
print('join_flags done')

map_join_attributes(df_out, df_in)
print('map_join_attributes done')

df_out.to_csv('out/wp_iphones.csv')
