#ex1
def get_greeting():
  return "Hello from a function"

message = get_greeting()
print(message)

#ex2
def get_greeting():
  return "Hello from a function"

print(get_greeting())

#ex3
def my_function():
  pass

#ex4
def my_function():
  return ["apple", "banana", "cherry"]

fruits = my_function()
print(fruits[0])
print(fruits[1])
print(fruits[2])

#ex5
def my_function():
  return (10, 20)

x, y = my_function()
print("x:", x)
print("y:", y)