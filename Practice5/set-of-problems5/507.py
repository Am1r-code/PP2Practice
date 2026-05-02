import re
txt1 = input()
txt2 = input()
txt3 = input()
x = re.sub(txt2, txt3, txt1)
print(x)