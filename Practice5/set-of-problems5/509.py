import re
txt = input()
x = re.findall(r'\b[a-zA-Z]{3}\b', txt)
print(len(x))