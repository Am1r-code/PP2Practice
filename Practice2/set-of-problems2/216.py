n = int(input())
arr = list(map(int, input().split()))
seen = []
for x in arr:
    if x in seen:
        print("NO")
    else:
        print("YES")
        seen.append(x)