import re
txt = input()
x = re.findall("[0-9][0-9]+", txt)
if x:
    print(" ".join(x))
else:
    print()