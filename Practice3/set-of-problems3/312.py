class Employee:
    def __init__(self, name, base_salary):
        self.name = name
        self.base_salary = base_salary
    def total_salary(self):
        return self.base_salary
class Manager(Employee):
    def __init__(self, name, base_salary, bonus_percent):
        super().__init__(name, base_salary)
        self.bonus_percent = bonus_percent
    def total_salary(self):
        return self.base_salary + (self.base_salary * self.bonus_percent / 100)
class Developer(Employee):
    def __init__(self, name, base_salary, completed_projects):
        super().__init__(name, base_salary)
        self.completed_projects = completed_projects
    def total_salary(self):
        return self.base_salary + self.completed_projects * 500
class Intern(Employee):
    pass
data = input().split()
role = data[0]
if role == "Manager":
    _, name, base_salary, bonus_percent = data
    employee = Manager(name, int(base_salary), int(bonus_percent))
elif role == "Developer":
    _, name, base_salary, completed_projects = data
    employee = Developer(name, int(base_salary), int(completed_projects))
elif role == "Intern":
    _, name, base_salary = data
    employee = Intern(name, int(base_salary))
print(f"Name: {employee.name}, Total: {employee.total_salary():.2f}")