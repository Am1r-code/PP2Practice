import re
txt = input()
x = re.search(r"Name:\s*(.+),\s*Age:\s*(\d+)", txt)
print(x.group(1), x.group(2))