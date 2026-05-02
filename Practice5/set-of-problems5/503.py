import re
txt1 = input()
txt2 = input()
x = re.findall(txt2, txt1)
print(len(x))