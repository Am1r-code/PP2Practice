import re
txt = input()
x = re.search(r"[^@\s]+@[^.\s]+\.[^\s]+", txt)
if x:
    print(x.group())
else:
    print("No email")