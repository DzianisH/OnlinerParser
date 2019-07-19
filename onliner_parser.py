import re
import urllib
from threading import Thread

import pandas as pd
from pyquery import PyQuery as pq

from stemmer import Porter


def fetch_links(html):
    pattern = re.compile(r'<div class="schema-product__title">.*\n.*href="(.*)">', re.MULTILINE)
    links = pattern.findall(html)

    links = list(dict.fromkeys(links))
    links.sort()

    return links


def fetch_products(links):
    df = pd.DataFrame()
    for index, link in enumerate(links):
        html = read_url(link).decode("utf8")
        df = parse_page(link, html, df)
        print("{:.2f}% parsed".format((index+1) * 100 / len(links)))
    return sort_cols(df)


def sort_cols(df):
    cols = [*df.axes[1]]
    ordered_cols = ['iPhone URL', 'Title', 'Description', 'H1', 'Img URL', 'Img Title',
                    'Img Alt', 'Code review', 'Description in content', 'Prices', 'Снят с производства']

    for col in ordered_cols:
        cols.remove(col)

    return df[ordered_cols + cols]


def read_url(address):
    fp = urllib.request.urlopen(address)
    mybytes = fp.read()
    fp.close()
    return mybytes


h1_pattern = re.compile(r'<h1 class="catalog-masthead__title" itemprop="name">\n *(.+?) *\n')
shirt_descr_pattern = re.compile(r'<p itemprop="description"> *(.+?) *</p>')
title_pattern = re.compile(r'<title>(.+?)</title>')
img_pattern = re.compile(r'<img.+id="device-header-image".+>')
img_url_pattern = re.compile(r'.*src="(.*?)".*')
img_title_pattern = re.compile(r'.*title="(.*?)".*')
img_alt_pattern = re.compile(r'.*alt="(.*?)".*')
descr_in_content_pattern = re.compile(r'<div class="product-specs__table-small i-faux-td">[\n\r]{1,2} *<p>(.*)</p>')
low_prices_pattern = re.compile(r'itemprop="lowPrice">(.*)<')
high_prices_pattern = re.compile(r'itemprop="highPrice">(.*)<')


def parse_page(url, html, df):
    return df.append({
        **parse_main_attributes(url, html),
        **parse_switchers(html),
        **parse_specs(html)
    }, ignore_index=True)


def parse_main_attributes(url, html):
    def apply_pattern(pattern, html=html):
        res = pattern.findall(html)
        if res is None or len(res) == 0:
            return ' '
        return res[0]

    img_html = apply_pattern(img_pattern)
    out_of_product = ' '
    if pq(html)('span.js-title'):
        out_of_product = 'ДА'

    img_url = apply_pattern(img_url_pattern, img_html)
    download_img(img_url)
    return {
        'iPhone URL': url,
        'Title': apply_pattern(title_pattern),
        'Description': apply_pattern(shirt_descr_pattern),
        'H1': apply_pattern(h1_pattern),
        'Img URL': img_url,
        'Img Title': apply_pattern(img_title_pattern, img_html),
        'Img Alt': apply_pattern(img_alt_pattern, img_html),
        'Code review': 'TODO: Грузится динамически',
        'Description in content': apply_pattern(descr_in_content_pattern),
        'Prices': apply_pattern(low_prices_pattern) + ' - ' + apply_pattern(high_prices_pattern),
        'Снят с производства': out_of_product
    }


def parse_switchers(html):
    switchers = pq(html)('.offers-description-filter__row')
    rows = {}
    for switch in switchers:
        switch = pq(switch)
        name = 'other options/' + switch('.offers-description-filter__sign').text()
        links = []

        for a in switch('a.offers-description-filter-control'):
            a = pq(a)
            links.append(a.attr('href'))

        links = '\n'.join(links)
        rows[name] = links

    return rows


# TODO: refactor, it takes lots of time
def parse_specs(html):
    table = pq(html)('table.product-specs__table')
    result_map = {}

    for tbody in table('tbody'):
        tbody = pq(tbody)
        tr = tbody('tr')
        col_prefix = 'specs/' + tbody('tr > td[colspan="2"] > div').text() + '/'
        for i in range(1, tr.length):
            td = pq(tr[i])('td')
            key = td.clone().children().remove().end().text()
            value_span = td.next()('span')
            value = value_span.text()
            if value is None or len(value.strip()) == 0:
                if value_span.has_class('i-tip'):
                    value = 'ДА'
                elif value_span.has_class('i-x'):
                    value = 'НЕТ'
            key, value = unify_units(key, value)
            result_map[col_prefix + key] = value

    return result_map


def download_img(url):
    def download_thread():
        img_name = url.split('/')[-1]
        bytes = read_url(url)
        f = open('out/imgs/' + img_name, 'wb')
        f.write(bytes)
        f.close()

    thread = Thread(target=download_thread)
    thread.setDaemon(False)
    thread.start()


space_split_pattern = re.compile(r'[\s]+')


def unify_units(column, value):
    lower_column = column.lower()
    if lower_column.find('время') > -1:
        return unify_time_units(column, value)
    elif lower_column.find('длина') > -1 \
            or lower_column.find('толщина') > -1\
            or lower_column.find('ширина') > -1:
        return unity_length_units(column, value)
    elif lower_column.find('память') > -1:
        return unify_memory_units(column, value)
    # elif lower_column.find('частот') > -1:  2 490 Мгц
    #     return unify_freq_units(column, value)
    elif lower_column.find('вес') > -1:
        return unify_weight_units(column, value)
    return column, value


def unify_time_units(column, value):
    units_map = {
        'недел': 7 * 24,
        'ден': 24,
        'дне': 24,
        'дня': 24,
        'дням': 24,
        'суток': 24,
        'сутк': 24,
        'час': 1,
        'минут': 1 / 60
    }

    return column + ' (часов)', sum_up_units(units_map, value)


def unify_memory_units(column, value):
    units_map = {
        'тб': 1024,
        'гб': 1,
        'мб': 1 / 1024,
        'кб': 1 / (1024 * 1024),
    }

    return column + ' (ГБ)', sum_up_units(units_map, value)


def unify_freq_units(column, value):
    units_map = {
        'ггц': 1000,
        'мгц': 1,
        'кгц': 1 / 1000,
    }

    return column + ' (МГц)', sum_up_units(units_map, value)


def unify_weight_units(column, value):
    units_map = {
        'кг': 1000,
        'г': 1,
        'мг': 1 / 1000,
    }

    return column + ' (грамм)', sum_up_units(units_map, value)


def unity_length_units(column, value):
    units_map = {
        'мм': 0.1,
        'см': 1,
        'дм': 10,
        'м': 100,
    }

    return column + ' (см)', sum_up_units(units_map, value)


def sum_up_units(units_map, value):
    value = value.strip()
    unified_value = 0
    try:
        for chunk in value.split(', '):
            val, unit = space_split_pattern.split(chunk)
            val = float(val)
            unified_value += val * units_map[Porter.stem(unit)]
    except:
        print('wtf has been faced while parsing', value)
    return value
