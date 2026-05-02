import re
txt = input()
x = re.findall("[0-9]", txt)
print(" ".join(x))