import re
text = input()
result = re.sub(r"\d", lambda m: m.group()*2, text)
print(result)