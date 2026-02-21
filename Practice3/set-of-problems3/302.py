def isUsual(num):
    if num <= 0:
        return False
    for factor in (2, 3, 5):
        while num % factor == 0:
            num //= factor
    return num == 1
n = int(input())
print("Yes" if isUsual(n) else "No")