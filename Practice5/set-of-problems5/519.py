import re
txt = input().strip()
x = re.compile(r"\b\w+\b")
y = x.findall(txt)
print(len(y))