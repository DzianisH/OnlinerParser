from onliner_parser import fetch_links

file = open("parseme.html", "r", encoding="utf8")
html = file.read()
file.close()

links = fetch_links(html)

print(*links, sep='\n', file=open("out/links.txt", "w"))
print(links.__len__(), 'links found')