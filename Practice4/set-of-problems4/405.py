def squares(n):
    for i in range(n, 0):
        yield i
n = int(input())
for sqr in squares(n):
    print(sqr)