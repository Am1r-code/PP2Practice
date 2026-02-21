import math
class Point:
    def __init__(self, x0, y0):
        self.x0 = x0
        self.y0 = y0
    def __init__(self, x1, y1):
        self.x1 = x1
        self.y1 = y1
    def __init__(self, x2, y2):
        self.x2 = x2
        self.y2 = y2
x0, y0 = map(int, input().split())
x1, y1 = map(int, input().split())
x2, y2 = map(int, input().split())
print ((x0, y0))
print((x1, y1))
print(f"{math.sqrt(pow(x2 - x1, 2) + pow(y2 - y1, 2)):.2f}")