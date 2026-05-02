import re
s = input()
p = input()
p = re.escape(p)
x = re.findall(p, s)
print(len(x))