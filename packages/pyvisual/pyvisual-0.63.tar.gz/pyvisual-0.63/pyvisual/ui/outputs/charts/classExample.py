def assginName():
    pass
class Person():
    def __init__(self,id):
        print(f"Person {id} Created")
        self.name="Ahmed"
        self.isAdult= True
        self.id = id

    def assginName(self,id):
        print(self.id, id)


person1 = Person(1)
person2 = Person(2)
person1.assginName(id="50")




class Employee(Person):
    def __init__(self):
        pass
