import re
txt = input()
x = re.findall("[A-Z]", txt)
print(len(x))