n = int(input())
episodes = {}
for _ in range(n):
    line = input().split()
    dorama = line[0]
    k = int(line[1])
    if dorama in episodes:
        episodes[dorama] += k
    else:
        episodes[dorama] = k
for dorama in sorted(episodes):
    print(dorama, episodes[dorama])