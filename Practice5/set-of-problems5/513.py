import re
txt = input()
x = re.findall("[0-9a-zA-Z]+", txt)
print(len(x))