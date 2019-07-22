import pandas as pd


name_map = {
    'id': 'Артикул',
    'H1': 'Имя',
    'Description': 'Короткое описание',
    'Description in content': 'Описание',
    'specs/Размеры и вес/Вес  (грамм)': 'Вес (kg)',
    'specs/Размеры и вес/Длина  (см)': 'Длина (cm)',
    'specs/Размеры и вес/Толщина  (см)': 'Ширина (cm)',
    'specs/Размеры и вес/Ширина  (см)': 'Высота (cm)',
    'Цена (руб)': 'Базовая цена',
    'Img URL': 'Изображения',
}

coma_to_dot_notation = lambda str: str.replace(',', '.')
data_transformers = {
    'Вес (kg)': lambda val: val / 1000,
    'Изображения': lambda val: 'https://temp.kupitiphone.by' + val,
    'Длина (cm)': coma_to_dot_notation,
    'Ширина (cm)': coma_to_dot_notation,
    'Высота (cm)': coma_to_dot_notation,
}

df_in = pd.read_csv('in/iphones.csv')  # prepared csv by Dimon
df_out = pd.DataFrame()

transformers = data_transformers.keys()
for src, dest in name_map.items():
    df_out[dest] = df_in[src]
    if dest in transformers:
        df_out[dest] = df_out[dest].apply(data_transformers[dest])


df_out.to_csv('out/wp_iphones.csv')



