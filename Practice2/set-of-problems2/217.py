n = int(input())
numbers = [input() for _ in range(n)]
freq = {}
for num in numbers:
    if num in freq:
        freq[num] += 1
    else:
        freq[num] = 1
count = sum(1 for v in freq.values() if v == 3)
print(count)