str_to_digit = {
    "ZER": "0", "ONE": "1", "TWO": "2", "THR": "3",
    "FOU": "4", "FIV": "5", "SIX": "6",
    "SEV": "7", "EIG": "8", "NIN": "9"
}
digit_to_str = {v: k for k, v in str_to_digit.items()}
s = input().strip()
for op in ['+', '-', '*']:
    if op in s:
        left, right = s.split(op)
        operator = op
        break
def convert_to_number(part):
    digits = ""
    for i in range(0, len(part), 3):
        digits += str_to_digit[part[i:i+3]]
    return int(digits)
num1 = convert_to_number(left)
num2 = convert_to_number(right)
if operator == '+':
    result = num1 + num2
elif operator == '-':
    result = num1 - num2
else:
    result = num1 * num2
result_str = ""
for digit in str(result):
    result_str += digit_to_str[digit]
print(result_str)