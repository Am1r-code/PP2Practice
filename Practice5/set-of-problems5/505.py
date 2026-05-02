import re
txt = input()
x = re.findall("^[a-zA-z]" and "[0-9]$", txt)
if x:
    print("Yes")
else:
    print("No")