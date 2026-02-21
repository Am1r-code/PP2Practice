class Circle:
    def __init__(self, r):
        self.r = r
        self.pi = 3.14159
    def area(self):
        return self.pi * self.r ** 2
r = int(input())
circle = Circle(r)
area = circle.area()
print(f"{area:.2f}")