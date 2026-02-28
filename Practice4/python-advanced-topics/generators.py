#ex1
mytuple = ("apple", "banana", "cherry")
myit = iter(mytuple)
print(next(myit))
print(next(myit))
print(next(myit))

#ex2
mystr = "banana"
myit = iter(mystr)
print(next(myit))
print(next(myit))
print(next(myit))
print(next(myit))
print(next(myit))
print(next(myit))

#ex3
mytuple = ("apple", "banana", "cherry")
for x in mytuple:
  print(x)

#ex4
mystr = "banana"
for x in mystr:
  print(x)

#ex5
class MyNumbers:
  def __iter__(self):
    self.a = 1
    return self
  def __next__(self):
    x = self.a
    self.a += 1
    return x
myclass = MyNumbers()
myiter = iter(myclass)
print(next(myiter))
print(next(myiter))
print(next(myiter))
print(next(myiter))
print(next(myiter))

#ex6
class MyNumbers:
  def __iter__(self):
    self.a = 1
    return self
  def __next__(self):
    if self.a <= 20:
      x = self.a
      self.a += 1
      return x
    else:
      raise StopIteration
myclass = MyNumbers()
myiter = iter(myclass)
for x in myiter:
  print(x)

#ex7
def my_generator():
  yield 1
  yield 2
  yield 3

for value in my_generator():
  print(value)

#ex8
def count_up_to(n):
  count = 1
  while count <= n:
    yield count
    count += 1

for num in count_up_to(5):
  print(num)

#ex9
def large_sequence(n):
  for i in range(n):
    yield i
gen = large_sequence(1000000)
print(next(gen))
print(next(gen))
print(next(gen))

#ex10
def simple_gen():
  yield "Emil"
  yield "Tobias"
  yield "Linus"
gen = simple_gen()
print(next(gen))
print(next(gen))
print(next(gen))

#ex11
list_comp = [x * x for x in range(5)]
print(list_comp)
gen_exp = (x * x for x in range(5))
print(gen_exp)
print(list(gen_exp))

#ex12
total = sum(x * x for x in range(10))
print(total)

#ex13
def fibonacci():
  a, b = 0, 1
  while True:
    yield a
    a, b = b, a + b
gen = fibonacci()
for _ in range(100):
  print(next(gen))

#ex14
def echo_generator():
  while True:
    received = yield
    print("Received:", received)
gen = echo_generator()
next(gen) 
gen.send("Hello")
gen.send("World")

#ex15
def my_gen():
  try:
    yield 1
    yield 2
    yield 3
  finally:
    print("Generator closed")
gen = my_gen()
print(next(gen))
gen.close()