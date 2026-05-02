import re
txt1 = input()
txt2 = input()
x = re.search(txt2, txt1)
if x:
  print("Yes")
else:
  print("No")