import re
date = input()
x = re.findall(r"\d{2}/\d{2}/\d{4}", date)
print(len(x))