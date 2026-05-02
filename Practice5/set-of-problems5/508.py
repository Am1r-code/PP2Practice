import re
s = input()
d = input()
x = re.split(d, s)
print(",".join(x))