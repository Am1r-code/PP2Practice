x = int(input())
numbers = list(map(int, input().split()))
count = 0
for y in numbers:
    if y > 0:
        count += 1
print(count)