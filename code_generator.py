import math
from lexer_parser import MyLexer, MyParser, print_ast
import sys
from structures import Variable, Array, Procedure
from queue import LifoQueue


# funcja pomocnicza sprawdza czy liczba jest potega 2
def isPowerOfTwo(liczba):
    return (liczba & (liczba - 1)) == 0 and liczba != 0


class Interpreter:
    def __init__(self):
        self.procedures = {}
        self.line = 0
        self.freeMemory = 0
        self.code = []
        self.memory = {}
        self.jumps = {}

    def interpret(self, ast):
        if ast[0] == 'program_all':
            self.code.append(["JUMP ", 0])
            self.interpretProcedures(ast[1])
            self.interpretMain(ast[2])
            self.code[0][1] = self.procedures["main"].start
        if ast[0] == 'main':
            self.interpretMain(ast)
        self.code.append(["HALT", ""])

    def interpretProcedures(self, procedures):
        lifo = LifoQueue()
        if procedures[0] == 'procedures':
            i = procedures
            while len(i) == 3:
                lifo.put(i[2])
                i = i[1]
            self.interpretProcedure(i)
            while not lifo.empty():
                self.interpretProcedure(lifo.get())
        else:
            self.interpretProcedure(procedures)

    def interpretProcedure(self, procedure):
        name = ""
        for i in procedure:
            if i[0] == "proc_head":
                self.line += 1
                name = str(i[1])
                if str(i[1]) in self.procedures:
                    raise Exception(f"Powtórne użycie identyfikatora: {i[1]} w okolicy lini {self.line}")
                self.procedures[name] = Procedure(i[1], self.freeMemory, len(self.code))
                self.freeMemory += 1
                self.jumps[name] = len(self.code)

                j = i[2]
                while len(j) > 2:
                    if j[2][0] == "T":
                        if self.procedures[str(i[1])].argumentArray(j[2][1], self.freeMemory):
                            raise Exception(f"Powtórne użycie identyfikatora: {j[2][1]} w okolicy lini {self.line}")
                        self.freeMemory += 1
                    else:
                        if self.procedures[str(i[1])].argumentVariable(j[2], self.freeMemory):
                            raise Exception(f"Powtórne użycie identyfikatora: '{j[2]} w okolicy lini {self.line}'")
                        self.freeMemory += 1
                    j = j[1]
                if j[1][0] == "T":
                    if self.procedures[str(i[1])].argumentArray(j[1][1], self.freeMemory):
                        raise Exception(f"Powtórne użycie identyfikatora: {j[1][1]} w okolicy lini {self.line}")
                    self.freeMemory += 1
                else:
                    if self.procedures[str(i[1])].argumentVariable(j[1], self.freeMemory):
                        raise Exception(f"Powtórne użycie identyfikatora: {j[1]} w okolicy lini {self.line}")
                    self.freeMemory += 1
            if i[0] == "declarations":
                self.line += 1
                j = i
                while len(j) > 2:
                    if j[2][0] == "T":
                        if self.procedures[name].setArray(j[2][1], j[2][2], self.freeMemory):
                            raise Exception(f"Powtórne użycie identyfikatora: {j[2][1]} w okolicy lini {self.line}")
                        self.freeMemory += int(j[2][2])
                    else:
                        if self.procedures[name].setVariable(j[2], self.freeMemory):
                            raise Exception(f"Powtórne użycie identyfikatora: {j[2]} w okolicy lini '{self.line}")
                        self.freeMemory += 1
                    j = j[1]
                if j[1][0] == "T":
                    if self.procedures[name].setArray(j[1][1], j[1][2], self.freeMemory):
                        raise Exception(f"Powtórne użycie identyfikatora: {j[1][1]} w okolicy lini {self.line}")
                    self.freeMemory += int(j[1][2])
                else:
                    if self.procedures[name].setVariable(j[1], self.freeMemory):
                        raise Exception(f"Powtórne użycie identyfikatora: {j[1]} w okolicy lini {self.line}")
                    self.freeMemory += 1
            if i[0] == "commands":
                self.line += 1
                j = i
                lifo = LifoQueue()
                while len(j) > 2:
                    lifo.put([j[0], j[2]])
                    j = j[1]
                self.interpretCommand([j[0], j[1]], name)
                while not lifo.empty():
                    self.interpretCommand(lifo.get(), name)
                self.line += 1
        recall = self.procedures[name].memory
        self.iterateNum(recall, "a")
        self.code.append(["LOAD ", "a"])
        self.code.append(["JUMPR ", "a"])

    def interpretCommand(self, command, name):
        self.line += 1
        if (command[1][0] == "assign"):
            self.interpretAssign(command[1], name)
        if (command[1][0] == "read"):
            self.interpretRead(command[1], name)
        if (command[1][0] == "write"):
            self.interpretWrite(command[1], name)
        if (command[1][0] == "proc_call"):
            self.interpretProcCall(command[1][1], name)
        if (command[1][0] == "if"):
            self.interpretIF(command[1], name)
        if (command[1][0] == "if_else"):
            self.interpretIfElse(command[1], name)
        if (command[1][0] == "while"):
            self.interpretWhile(command[1], name)
        if (command[1][0] == "repeat_until"):
            self.interpretRepeatUntil(command[1], name)

    def interpretRepeatUntil(self, command, name):
        lineStart = len(self.code)
        self.line += 1
        j = command[1]
        lifo = LifoQueue()
        while len(j) > 2:
            lifo.put([j[0], j[2]])
            j = j[1]
        self.interpretCommand([j[0], j[1]], name)
        while not lifo.empty():
            self.interpretCommand(lifo.get(), name)
        self.interpretConductionRepeat(command[2], name)
        self.code[len(self.code) - 1][1] = str(lineStart)
        self.line += 1

    def interpretWhile(self, command, name):
        lineStart = len(self.code)
        self.interpretConduction(command[1], name)
        lineToAddValue = len(self.code) - 1
        self.line += 1
        j = command[2]
        lifo = LifoQueue()
        while len(j) > 2:
            lifo.put([j[0], j[2]])
            j = j[1]
        self.interpretCommand([j[0], j[1]], name)
        while not lifo.empty():
            self.interpretCommand(lifo.get(), name)
        self.code.append(["JUMP ", str(lineStart)])
        self.code[lineToAddValue][1] = str(len(self.code))
        self.line += 1

    def interpretIfElse(self, command, name):
        self.interpretConduction(command[1], name)
        lineToAddValue = len(self.code) - 1
        self.line += 1
        j = command[2]
        lifo = LifoQueue()
        while len(j) > 2:
            lifo.put([j[0], j[2]])
            j = j[1]
        self.interpretCommand([j[0], j[1]], name)
        while not lifo.empty():
            self.interpretCommand(lifo.get(), name)
        lineToAddValue2 = len(self.code)
        self.code.append(["JUMP", ""])
        self.code[lineToAddValue][1] = str(len(self.code))
        self.line += 1
        self.line += 1
        j = command[3]
        lifo = LifoQueue()
        while len(j) > 2:
            lifo.put([j[0], j[2]])
            j = j[1]
        self.interpretCommand([j[0], j[1]], name)
        while not lifo.empty():
            self.interpretCommand(lifo.get(), name)
        self.code[lineToAddValue2][1] = str(len(self.code))
        self.line += 1

    def interpretIF(self, command, name):
        self.interpretConduction(command[1], name)
        lineToAddValue = len(self.code) - 1
        self.line += 1
        j = command[2]
        lifo = LifoQueue()
        while len(j) > 2:
            lifo.put([j[0], j[2]])
            j = j[1]
        self.interpretCommand([j[0], j[1]], name)
        while not lifo.empty():
            self.interpretCommand(lifo.get(), name)
        self.code[lineToAddValue][1] = str(len(self.code))
        self.line += 1

    def interpretConductionRepeat(self, conduction, name):
        self.getNumber(conduction[1], name, 'in')
        self.code.append(["PUT ", "c"])
        self.getNumber(conduction[2], name, 'in')
        self.code.append(["PUT ", "d"])
        if conduction[0] == '<=':
            self.code.append(["GET ", "c"])
            self.code.append(["SUB ", "d"])
            self.code.append(["JPOS ", ""])
        if conduction[0] == '>=':
            self.code.append(["GET ", "d"])
            self.code.append(["SUB ", "c"])
            self.code.append(["JPOS ", ""])
        if conduction[0] == '<':
            self.code.append(["GET ", "d"])
            self.code.append(["SUB ", "c"])
            self.code.append(["JZERO ", ""])
        if conduction[0] == '>':
            self.code.append(["GET ", "c"])
            self.code.append(["SUB ", "d"])
            self.code.append(["JZERO ", ""])
        if conduction[0] == '!=':
            self.code.append(["GET ", "c"])
            self.code.append(["SUB ", "d"])
            self.code.append(["PUT ", "e"])
            self.code.append(["GET ", "d"])
            self.code.append(["SUB ", "c"])
            self.code.append(["ADD ", "e"])
            self.code.append(["JZERO ", ""])

        if conduction[0] == '=':
            self.code.append(["GET ", "c"])
            self.code.append(["SUB ", "d"])
            self.code.append(["PUT ", "e"])
            self.code.append(["GET ", "d"])
            self.code.append(["SUB ", "c"])
            self.code.append(["ADD ", "e"])
            self.code.append(["JPOS ", ""])

    def interpretConduction(self, conduction, name):
        self.getNumber(conduction[1], name, 'in')
        self.code.append(["PUT ", "c"])
        self.getNumber(conduction[2], name, 'in')
        self.code.append(["PUT ", "d"])
        if conduction[0] == '>':
            self.code.append(["GET ", "c"])
            self.code.append(["SUB ", "d"])
            self.code.append(["JZERO ", ""])
        if conduction[0] == '<':
            self.code.append(["GET ", "d"])
            self.code.append(["SUB ", "c"])
            self.code.append(["JZERO ", ""])
        if conduction[0] == '>=':
            self.code.append(["GET ", "d"])
            self.code.append(["SUB ", "c"])
            self.code.append(["JPOS ", ""])
        if conduction[0] == '<=':
            self.code.append(["GET ", "c"])
            self.code.append(["SUB ", "d"])
            self.code.append(["JPOS ", ""])
        if conduction[0] == '=':
            self.code.append(["GET ", "c"])
            self.code.append(["SUB ", "d"])
            self.code.append(["PUT ", "e"])
            self.code.append(["GET ", "d"])
            self.code.append(["SUB ", "c"])
            self.code.append(["ADD ", "e"])
            self.code.append(["JPOS ", ""])

        if conduction[0] == '!=':
            self.code.append(["GET ", "c"])
            self.code.append(["SUB ", "d"])
            self.code.append(["PUT ", "e"])
            self.code.append(["GET ", "d"])
            self.code.append(["SUB ", "c"])
            self.code.append(["ADD ", "e"])
            self.code.append(["JZERO ", ""])

    def interpretProcCall(self, procCall, name):
        procName = procCall[1]
        if procName == name:
            raise Exception(f"Wywolanie rekurencyjne funckji {procName} w okolicy lini {self.line}")
        if procName not in self.procedures:
            raise Exception(f"Zła nazwa funkcji {procName} w okolicy lini {self.line}")
        head = self.procedures[procName].head
        j = procCall[2]
        i = len(head)
        while len(j) == 3:
            i -= 1
            if i < 0:
                raise Exception(f"Złe argumenty funkcji{procName} w okolicy lini {self.line}")
            if head[i][0] == 'T':
                if j[2] not in self.procedures[name].arrays:
                    raise Exception(f"Złe argumenty funkcji {procName} w okolicy lini {self.line}")
            if head[i][0] == 'V':
                if j[2] not in self.procedures[name].variables:
                    raise Exception(f"Złe argumenty funkcji {procName} w okolicy lini {self.line}")
            self.givePointer([head[i][0], procName, head[i][1], name, j[2]])
            j = j[1]
        i -= 1
        if i < 0:
            raise Exception(f"Złe argumenty funkcji {procName} w okolicy lini {self.line}")
        if i > 0:
            raise Exception(f"Złe argumenty funkcji {procName} w okolicy lini {self.line}")
        if head[i][0] == 'T':
            if j[1] not in self.procedures[name].arrays:
                raise Exception(f"Złe argumenty funkcji {procName} w okolicy lini {self.line}")
        if head[i][0] == 'V':
            if j[1] not in self.procedures[name].variables:
                raise Exception(f"Złe argumenty funkcji {procName} w okolicy lini {self.line}")
        self.givePointer([head[i][0], procName, head[i][1], name, j[1]])
        recall = self.procedures[procName].memory
        start = self.procedures[procName].start
        self.iterateNum(recall, "b")
        self.iterateNum(4, "a")
        self.code.append(["STRK ", "c"])
        self.code.append(["ADD ", "c"])
        self.code.append(["STORE ", "b"])
        self.code.append(["JUMP ", str(start)])

    def givePointer(self, command):
        if command[0] == 'T':
            memory1 = self.procedures[command[1]].arrays[command[2]].memoryLocation
            memory2 = self.procedures[command[3]].arrays[command[4]].memoryLocation
            self.procedures[command[3]].arrays[command[4]].values = True
            self.iterateNum(memory1, "b")
            self.iterateNum(memory2, "a")
            if self.procedures[command[3]].arrays[command[4]].argument:
                self.code.append(["LOAD ", "a"])
            self.code.append(["STORE ", "b"])
        if command[0] == 'V':
            memory1 = self.procedures[command[1]].variables[command[2]].memoryLocation
            memory2 = self.procedures[command[3]].variables[command[4]].memoryLocation
            self.procedures[command[3]].variables[command[4]].value = True
            self.iterateNum(memory1, "b")
            self.iterateNum(memory2, "a")
            if self.procedures[command[3]].variables[command[4]].argument:
                self.code.append(["LOAD ", "a"])
            self.code.append(["STORE ", "b"])

    def interpretRead(self, read, name):
        if len(read[1]) == 2:
            if read[1][1] not in self.procedures[name].variables:
                raise Exception(f"Niezdefiniowana zmienna: {read[1][1]} w okolicy lini {self.line}")
            isItArgument = self.procedures[name].variables[read[1][1]].argument
            self.procedures[name].variables[read[1][1]].value = True
            x = self.procedures[name].variables[read[1][1]].memoryLocation
            self.iterateNum(x, "b")
            if isItArgument:
                self.code.append(["LOAD ", "b"])
                self.code.append(["PUT ", "b"])
        if len(read[1]) == 3:
            if read[1][1] not in self.procedures[name].arrays:
                raise Exception(f"Niezdefiniowana tablica: {read[1][1]} w okolicy lini {self.line}")
            isItArgument = self.procedures[name].arrays[read[1][1]].argument
            self.procedures[name].arrays[read[1][1]].values = True
            x = self.procedures[name].arrays[read[1][1]].memoryLocation
            self.getArrayArgument(read[1][2][1], name, "c")
            self.iterateNum(x, "b")
            if isItArgument:
                self.code.append(["LOAD ", "b"])
                self.code.append(["ADD ", "c"])
                self.code.append(["PUT ", "b"])
            else:
                self.code.append(["GET ", "b"])
                self.code.append(["ADD ", "c"])
                self.code.append(["PUT ", "b"])
        self.code.append(["READ", ""])
        self.code.append(["STORE ", "b"])

    def interpretWrite(self, write, name):
        self.getNumber(write[1], name, 'in')
        self.code.append(["WRITE", ""])

    def interpretAssign(self, assign, name):
        if len(assign[1]) == 2:
            if assign[1][1] not in self.procedures[name].variables:
                raise Exception(f"Niezdefiniowana zmienna: {assign[1][1]} w okolicy lini {self.line}")
            isItArgument = self.procedures[name].variables[assign[1][1]].argument
            self.procedures[name].variables[assign[1][1]].value = True
            x = self.procedures[name].variables[assign[1][1]].memoryLocation
            self.iterateNum(x, "b")
            if isItArgument:
                self.code.append(["LOAD ", "b"])
                self.code.append(["PUT ", "b"])

        if len(assign[1]) == 3:
            if assign[1][1] not in self.procedures[name].arrays:
                raise Exception(f"Niezdefiniowana tablica: {assign[1][1]} w okolicy lini {self.line}")
            isItArgument = self.procedures[name].arrays[assign[1][1]].argument
            self.procedures[name].arrays[assign[1][1]].values = True
            x = self.procedures[name].arrays[assign[1][1]].memoryLocation
            self.getArrayArgument(assign[1][2][1], name, "c")
            self.iterateNum(x, "b")
            if isItArgument:
                self.code.append(["LOAD ", "b"])
                self.code.append(["ADD ", "c"])
                self.code.append(["PUT ", "b"])
            else:
                self.code.append(["GET ", "b"])
                self.code.append(["ADD ", "c"])
                self.code.append(["PUT ", "b"])
        if len(assign[2]) == 2:
            self.getNumber(assign[2], name, 'in')
        if len(assign[2]) == 3:
            self.getCalc(assign[2], name)
        self.code.append(["STORE ", "b"])

    def getCalc(self, calc, name):
        stala = 0
        if calc[2][0] == 'num':
            stala = 2
        elif calc[1][0] == 'num' and calc[0] != '-' and calc[0] != '%' and calc[0] != '/':
            stala = 1
        if calc[0] == "+":
            if stala == 1:
                self.getNumber(calc[2], name, 'in')
            elif stala == 2:
                self.getNumber(calc[1], name, 'in')
            else:
                self.getNumber(calc[2], name, 'in')
                self.code.append(["PUT ", "h"])
                self.getNumber(calc[1], name, 'in')
            if stala != 0:
                if int(calc[stala][1]) < 8:
                    for iterator in range(0, int(calc[stala][1])):
                        self.code.append(["INC ", "a"])
                else:
                    self.code.append(["PUT ", "h"])
                    self.getNumber(calc[stala], name, 'in')
                    self.code.append(["ADD ", "h"])
            else:
                self.code.append(["ADD ", "h"])
        if calc[0] == "-":
            if stala == 2:
                if int(calc[stala][1]) < 8:
                    self.getNumber(calc[1], name, 'in')
                    for iterator in range(0, int(calc[stala][1])):
                        self.code.append(["DEC ", "a"])
                else:
                    self.getNumber(calc[2], name, 'in')
                    self.code.append(["PUT ", "h"])
                    self.getNumber(calc[1], name, 'in')
                    self.code.append(["SUB ", "h"])
            else:
                self.getNumber(calc[2], name, 'in')
                self.code.append(["PUT ", "h"])
                self.getNumber(calc[1], name, 'in')
                self.code.append(["SUB ", "h"])
        if calc[0] == "*":
            if stala == 1:
                self.getNumber(calc[2], name, 'in')
            elif stala == 2:
                self.getNumber(calc[1], name, 'in')
            else:
                self.getNumber(calc[2], name, 'in')
                self.code.append(["PUT ", "h"])
                self.getNumber(calc[1], name, 'in')
            done = False
            if calc[2][1] == 0 or calc[1][1] == 0:
                self.code.append(["RST ", "a"])
                done = True
            if done == False and stala != 0 and isPowerOfTwo(int(calc[stala][1])):
                wykladnik = int(math.log2(int(calc[stala][1])))
                if wykladnik == 0:
                    done = True
                else:
                    for _ in range(wykladnik):
                        self.code.append(["SHL ", "a"])
                    done = True
            if done == False and stala != 0:
                self.code.append(["PUT ", "h"])
                self.getNumber(calc[stala], name, 'in')
            if done == False:
                self.code.append(["RST ", "e"])
                self.code.append(["PUT ", "g"])
                lineNumber = str(len(self.code) + 14)
                startLine = len(self.code)
                self.code.append(["JZERO ", lineNumber])
                self.code.append(["GET ", "h"])
                self.code.append(["SHR ", "h"])
                self.code.append(["SHL ", "h"])
                self.code.append(["SUB ", "h"])
                lineNumber = str(len(self.code) + 4)
                self.code.append(["JZERO ", lineNumber])
                self.code.append(["GET ", "e"])
                self.code.append(["ADD ", "g"])
                self.code.append(["PUT ", "e"])
                self.code.append(["INC ", "h"])
                self.code.append(["SHL ", "g"])
                self.code.append(["SHR ", "h"])
                self.code.append(["GET ", "h"])
                self.code.append(["JPOS ", str(startLine)])
                self.code.append(["GET ", "e"])
        if calc[0] == "/":
            done = False
            if calc[2][1] == '0' or calc[1][1] == '0':
                print(calc)
                self.code.append(["RST ", "a"])
                done = True
            if done == False and stala == 2 and isPowerOfTwo(int(calc[stala][1])):
                self.getNumber(calc[1], name, 'in')
                wykladnik = int(math.log2(int(calc[stala][1])))
                if wykladnik == 0:
                    done = True
                else:
                    for _ in range(wykladnik):
                        self.code.append(["SHR ", "a"])
                    done = True
            elif done == False:
                self.getNumber(calc[2], name, 'in')
                self.code.append(["JPOS ", str(len(self.code) + 3)])
                self.code.append(["RST ", "a"])
                lineToRepair = len(self.code)
                self.code.append(["JUMP ", ""])
                self.code.append(["PUT ", "h"])
                self.getNumber(calc[1], name, 'in')
            if done == False:
                self.code.append(["PUT ", "g"])
                self.code.append(["RST ", "d"])
                lineNumber = len(self.code)
                self.code.append(["GET ", "h"])
                self.code.append(["PUT ", "f"])
                self.code.append(["SUB ", "g"])
                self.code.append(["JZERO ", str(lineNumber + 5)])
                self.code.append(["JUMP ", str(lineNumber + 21)])
                self.code.append(["RST ", "e"])
                self.code.append(["INC ", "e"])
                self.code.append(["SHL ", "e"])
                self.code.append(["SHL ", "f"])
                self.code.append(["GET ", "f"])
                self.code.append(["SUB ", "g"])
                self.code.append(["JZERO ", str(lineNumber + 7)])
                self.code.append(["SHR ", "e"])
                self.code.append(["SHR ", "f"])
                self.code.append(["GET ", "d"])
                self.code.append(["ADD ", "e"])
                self.code.append(["PUT ", "d"])
                self.code.append(["GET ", "g"])
                self.code.append(["SUB ", "f"])
                self.code.append(["PUT ", "g"])
                self.code.append(["JUMP ", str(lineNumber)])
                self.code.append(["GET ", "d"])
                self.code[lineToRepair][1] = str(len(self.code) + 1)
        if calc[0] == "%":
            done = False
            if calc[2][1] == '0' or calc[1][1] == '0' or calc[2][1] == '1':
                print(calc)
                self.code.append(["RST ", "a"])
                done = True
            if done == False and stala == 2 and isPowerOfTwo(int(calc[stala][1])):
                self.getNumber(calc[1], name, 'in')
            elif done == False:
                self.getNumber(calc[2], name, 'in')
                self.code.append(["JPOS ", str(len(self.code)+3)])
                self.code.append(["RST ", "a"])
                lineToRepair = len(self.code)
                self.code.append(["JUMP ", ""])
                self.code.append(["PUT ", "h"])
                self.getNumber(calc[1], name, 'in')
            if done == False and stala == 2 and isPowerOfTwo(int(calc[stala][1])):
                self.code.append(["PUT ", "d"])
                wykladnik = int(math.log2(int(calc[stala][1])))
                for _ in range(wykladnik):
                    self.code.append(["SHR ", "d"])
                for _ in range(wykladnik):
                    self.code.append(["SHL ", "d"])
                self.code.append(["SUB ", "d"])
                done = True
            elif done == False:
                self.code.append(["PUT ", "g"])
                lineNumber = len(self.code)
                self.code.append(["GET ", "h"])
                self.code.append(["PUT ", "f"])
                self.code.append(["SUB ", "g"])
                self.code.append(["JZERO ", str(lineNumber + 5)])
                self.code.append(["JUMP ", str(lineNumber + 18)])
                self.code.append(["RST ", "e"])   #licznik
                self.code.append(["INC ", "e"])
                self.code.append(["SHL ", "e"])
                self.code.append(["SHL ", "f"])
                self.code.append(["GET ", "f"])
                self.code.append(["SUB ", "g"])
                self.code.append(["JZERO ", str(lineNumber + 7)])
                self.code.append(["SHR ", "e"])
                self.code.append(["SHR ", "f"])
                self.code.append(["GET ", "g"])
                self.code.append(["SUB ", "f"])
                self.code.append(["PUT ", "g"])
                self.code.append(["JUMP ", str(lineNumber)])
                self.code.append(["GET ", "g"])
                self.code[lineToRepair][1] = str(len(self.code)+1)

    # ustawia wartosc number w adresie a
    def getNumber(self, number, name, inOrOut):

        if number[0] == "num":
            num = int(number[1])
            self.iterateNum(num, "a")
        if number[0] == "identifier":
            identifiactor = number[1][1]
            if len(number[1]) == 2:
                if identifiactor not in self.procedures[name].variables:
                    raise Exception(f"Niezdefiniowana zmienna: {identifiactor} w okolicy lini {self.line}")
                isItArgument = self.procedures[name].variables[identifiactor].argument
                x = self.procedures[name].variables[identifiactor].memoryLocation
                if inOrOut == 'in':
                    try:
                        if not self.procedures[name].variables[identifiactor].value and not isItArgument:
                            raise Exception(
                                f"WARNING: Niezainicjalizowana zmienna: {identifiactor} w okolicy lini {self.line}")
                    except Exception as e:
                        print(e)
                self.iterateNum(x, "a")
                if isItArgument:
                    self.code.append(["LOAD ", "a"])
            if len(number[1]) == 3:
                if identifiactor not in self.procedures[name].arrays:
                    raise Exception(f"Niezdefiniowana tablica: {identifiactor} w okolicy lini {self.line}")
                isItArgument = self.procedures[name].arrays[identifiactor].argument
                x = self.procedures[name].arrays[identifiactor].memoryLocation
                if inOrOut == 'in':
                    try:
                        if not self.procedures[name].arrays[identifiactor].values and not isItArgument:
                            raise Exception(
                                f"WARNING: Niezainicjalizowana tablica: {identifiactor} w okolicy lini {self.line}")
                    except Exception as e:
                        print(e)
                self.getArrayArgument(number[1][2][1], name, "c")
                self.iterateNum(x, "d")
                if isItArgument:
                    self.code.append(["LOAD ", "d"])
                    self.code.append(["ADD ", "c"])
                else:
                    self.code.append(["GET ", "d"])
                    self.code.append(["ADD ", "c"])
            self.code.append(["LOAD ", "a"])

    def getArrayArgument(self, number, name, register):
        if number.isdigit():
            self.iterateNum(int(number), register)
        else:
            if number not in self.procedures[name].variables:
                raise Exception(f"Niezdefiniowana zmienna: {number} w okolicy lini {self.line}")
            isItArgument = self.procedures[name].variables[number].argument
            try:
                if (not self.procedures[name].variables[number].value) and (not isItArgument):
                    raise Exception(f"WARNING: Niezainicjalizowana zmienna: {number} w okolicy lini {self.line}")
            except Exception as e:
                print(e)
            x = self.procedures[name].variables[number].memoryLocation
            self.iterateNum(x, register)
            if isItArgument:
                self.code.append(["LOAD ", register])
                self.code.append(["PUT ", register])
            self.code.append(["LOAD ", register])
            self.code.append(["PUT ", register])

    def iterateNum(self, num, register):
        binary = bin(num)[3:]
        self.code.append(["RST ", register])
        if num == 0:
            return
        else:
            self.code.append(["INC ", register])
        for i in binary:
            self.code.append(["SHL ", register])
            if int(i) == 1:
                self.code.append(["INC ", register])

    def interpretMain(self, main):
        name = "main"
        self.procedures[name] = Procedure(name, self.freeMemory, len(self.code))
        self.freeMemory += 1
        for i in main:
            if i[0] == "declarations":
                self.line += 1
                j = i
                while len(j) > 2:
                    if j[2][0] == "T":
                        if self.procedures[name].setArray(j[2][1], j[2][2], self.freeMemory):
                            raise Exception(f"Powtórne użycie identyfikatora: {j[2][1]} w okolicy lini {self.line}")

                        self.freeMemory += int(j[2][2])
                    else:
                        if self.procedures[name].setVariable(j[2], self.freeMemory):
                            raise Exception(f"Powtórne użycie identyfikatora: {j[2]} w okolicy lini '{self.line}")
                        self.freeMemory += 1
                    j = j[1]
                if j[1][0] == "T":
                    if self.procedures[name].setArray(j[1][1], j[1][2], self.freeMemory):
                        raise Exception(f"Powtórne użycie identyfikatora: {j[1][1]} w okolicy lini {self.line}")
                    self.freeMemory += int(j[1][2])
                else:
                    if self.procedures[name].setVariable(j[1], self.freeMemory):
                        raise Exception(f"Powtórne użycie identyfikatora: {j[1]} w okolicy lini {self.line}")
                    self.freeMemory += 1
            if i[0] == "commands":
                self.line += 1
                j = i
                lifo = LifoQueue()
                while len(j) > 2:
                    lifo.put([j[0], j[2]])
                    j = j[1]
                self.interpretCommand([j[0], j[1]], name)
                while not lifo.empty():
                    self.interpretCommand(lifo.get(), name)
                self.line += 1
