import re
import urllib

import pandas as pd
from pyquery import PyQuery as pq


def fetch_links(html):
    pattern = re.compile(r'<div class="schema-product__title">.*\n.*href="(.*)">', re.MULTILINE)
    links = pattern.findall(html)

    links = list(dict.fromkeys(links))
    links.sort()

    return links


def fetch_products(links):
    df = pd.DataFrame()
    for index, link in enumerate(links):
        html = read_page(link)
        df = parse_page(link, html, df)
        print("{:.2f}% parsed".format((index+1) * 100 / len(links)))
    return df


def read_page(address):
    fp = urllib.request.urlopen(address)
    mybytes = fp.read()
    fp.close()
    return mybytes.decode("utf8")


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

    return {
        'iPhone URL': url,
        'Title': apply_pattern(title_pattern),
        'Description': apply_pattern(shirt_descr_pattern),
        'H1': apply_pattern(h1_pattern),
        'Img URL': apply_pattern(img_url_pattern, img_html),
        'Img Title': apply_pattern(img_title_pattern, img_html),
        'Img Alt': apply_pattern(img_alt_pattern, img_html),
        'Code review': 'TODO: Грузится динамически',
        'Description in content': apply_pattern(descr_in_content_pattern),
        'Prices': apply_pattern(low_prices_pattern) + ' - ' + apply_pattern(high_prices_pattern),
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


#TODO: refactor, it takes lots of time
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
            result_map[col_prefix + key] = value

    return result_map

