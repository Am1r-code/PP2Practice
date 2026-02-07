n = int(input())
numbers = list(map(int, input().split()))
max_value = numbers[0]
position = 1   
for i in range(1, n):
    if numbers[i] > max_value:
        max_value = numbers[i]
        position = i + 1
print(position)
