n = int(input().strip())
first = True
for i in range(0, n + 1, 2):
    if first:
        print(i, end="")
        first = False
    else:
        print(f",{i}", end="")
print()