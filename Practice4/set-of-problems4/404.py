def squares(n):
    for i in range(n, k+1):
        yield i * i
n, k = map(int, input().split())
for sqr in squares(n):
    print(sqr)