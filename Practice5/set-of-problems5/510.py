import re
txt = input()
x = re.findall("dog|cat", txt)
if x:
    print("Yes")
else:
    print("No")