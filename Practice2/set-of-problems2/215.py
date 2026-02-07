n = int(input())
surnames = set()
for _ in range(n):
    surname = input()
    surnames.add(surname)
print(len(surnames))