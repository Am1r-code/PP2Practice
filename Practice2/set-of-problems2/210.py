n = int(input())
arr = list(map(int, input().split()))
arr.sort(reverse=True)
for x in arr:
    print(x, end=" ")
