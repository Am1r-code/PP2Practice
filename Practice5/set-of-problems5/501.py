import re
txt = input()
x = re.match("Hello", txt)
if x:
  print("Yes")
else:
  print("No")