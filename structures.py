class Variable:
    def __init__(self, name, memory, argument):
        self.value = False
        self.memoryLocation = memory
        self.name = name
        self.argument = argument

    def setValue(self, value):
        self.value = value

    def setMemoryLocation(self, memoryLocation):
        self.memoryLocation = memoryLocation


class Array:
    def __init__(self, name, size, memory, argument):
        if size is None:
            self.memoryLocation = memory
            self.name = name
            self.size = None
            self.values = True
            self.argument = argument
        else:
            self.memoryLocation = memory
            self.name = name
            self.size = size
            self.values = [size]
            self.argument = argument


    def setValue(self, index, value):
        self.values[index] = value

    def getValue(self, index):
        return self.values[index]

    def setMemoryLocation(self, index):
        self.memoryLocation = index


class Procedure:
    def __init__(self, name, memory, start):
        self.name = name
        self.variables = {}
        self.arrays = {}
        self.memory = memory
        self.head = []
        self.start = start

    def setVariable(self, name, memory):
        if name in self.variables or name in self.arrays:
            return 1
        else:
            self.variables[name] = Variable(name, memory, False)
            return 0

    def setArray(self, name, size, memory):
        if name in self.variables or name in self.arrays:
            return 1
        else:
            self.arrays[name] = Array(name, size, memory, False)
            return 0

    def argumentArray(self, name, memory):
        if name in self.variables or name in self.arrays:
            return 1
        else:
            self.arrays[name] = Array(name, None, memory, True)
            self.head = [["T",name]] + self.head
            return 0

    def argumentVariable(self, name, memory):
        if name in self.variables or name in self.arrays:
            return 1
        else:
            self.variables[name] = Variable(name, memory, True)
            self.head = [["V",name]] + self.head
            return 0
    