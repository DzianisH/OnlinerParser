import pandas as pd

from onliner_parser import fetch_links
from onliner_parser import fetch_products

file = open("parseme.html", "r", encoding="utf8")
html = file.read()
file.close()

links = fetch_links(html)

writer = pd.ExcelWriter('out/iphones.xlsx')

print(*links, sep='\n', file=open("out/links.txt", "w"))
print(links.__len__(), 'links found')

df = fetch_products(links)
df.to_excel(writer, sheet_name='parsed iphones')

writer.close()