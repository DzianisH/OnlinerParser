import re


def fetch_links(html):
    pattern = re.compile(r'<div class="schema-product__title">.*\n.*href="(.*)">', re.MULTILINE)
    links = pattern.findall(html)

    links = list(dict.fromkeys(links))
    links.sort()

    return links

