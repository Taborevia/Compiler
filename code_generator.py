from lexer_parser import MyLexer, MyParser, print_ast
import sys
from structures import Variable, Array, Procedure
from queue import LifoQueue


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
            self.code[0][1]= self.procedures["main"].start
        if ast[0] == 'main':
            self.interpretMain(ast)
        self.code.append(["HALT",""])

    def interpretProcedures(self, procedures):
        lifo = LifoQueue()
        if procedures[0] == 'procedures':
            i = procedures
            while len(i)==3:
                lifo.put(i[2])
                i = i[1]
            self.interpretProcedure(i)
            while not lifo.empty():
                self.interpretProcedure(lifo.get())
        else:
            self.interpretProcedure(procedures)
        # if procedures[0] == 'procedures':
        #     for i in range(1, len(procedures)):
        #         self.interpretProcedure(procedures[i])
        # else:
        #     self.interpretProcedure(procedures)

    def interpretProcedure(self, procedure):
        # print(procedure)
        name = ""
        for i in procedure:
            if i[0] == "proc_head":
                # self.code.append(["#procedura ", str(i[1])])
                self.line += 1
                name = str(i[1])
                if str(i[1]) in self.procedures:
                    raise Exception(f"Powtórne użycie identyfikatora: {i[1]} w okolicy lini {self.line}")
                self.procedures[name] = Procedure(i[1],self.freeMemory, len(self.code))
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
            self.interpretWrite(command[1],name)
        if (command[1][0] == "proc_call"):
            self.interpretProcCall(command[1][1],name)
        if(command[1][0]== "if"):
            self.interpretIF(command[1],name)
        if(command[1][0]== "if_else"):
            self.interpretIfElse(command[1],name)
        if(command[1][0]== "while"):
            self.interpretWhile(command[1],name)
        if(command[1][0]== "repeat_until"):
            self.interpretRepeatUntil(command[1],name)
    
    def interpretRepeatUntil(self, command, name):
        # print(command)
        # print(len(command))
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
        # self.code.append(["JUMP ",str(lineStart)])
        # self.code[lineToAddValue][1] = str(len(self.code))
        self.interpretConductionRepeat(command[2],name)
        self.code[len(self.code)-1][1]= str(lineStart)
        self.line += 1

    def interpretWhile(self, command, name):
        lineStart = len(self.code)
        self.interpretConduction(command[1],name)
        lineToAddValue = len(self.code)-1
        self.line += 1
        j = command[2]
        lifo = LifoQueue()
        while len(j) > 2:
            lifo.put([j[0], j[2]])
            j = j[1]
        self.interpretCommand([j[0], j[1]], name)
        while not lifo.empty():
            self.interpretCommand(lifo.get(), name)
        self.code.append(["JUMP ",str(lineStart)])
        self.code[lineToAddValue][1] = str(len(self.code))
        self.line += 1


    def interpretIfElse(self,command,name):
        self.interpretConduction(command[1],name)
        lineToAddValue = len(self.code)-1
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
        self.code.append(["JUMP",""])
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
        self.interpretConduction(command[1],name)
        # print(command[2])
        lineToAddValue = len(self.code)-1
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
        # print(conduction)
        # print(conduction[2])
        self.getNumber(conduction[1],name)
        self.code.append(["PUT ","c"])
        self.getNumber(conduction[2],name)
        self.code.append(["PUT ","d"])
        if conduction[0]=='>':
            self.code.append(["GET ","c"])
            self.code.append(["SUB ","d"])
            self.code.append(["JPOS",""])
        if conduction[0]=='<':
            self.code.append(["GET ","d"])
            self.code.append(["SUB ","c"])
            self.code.append(["JPOS ",""])
        if conduction[0]=='>=':
            self.code.append(["GET ","d"])
            self.code.append(["SUB ","c"])
            self.code.append(["JZERO ",""])
        if conduction[0]=='<=':
            self.code.append(["GET ","c"])
            self.code.append(["SUB ","d"])
            self.code.append(["JZERO ",""])
        if conduction[0]=='=':
            self.code.append(["GET ","c"])
            self.code.append(["SUB ","d"])
            self.code.append(["PUT ","e"])
            self.code.append(["GET ","d"])
            self.code.append(["SUB ","c"])
            self.code.append(["ADD ","e"])
            self.code.append(["JZERO ",""])
            
        if conduction[0]=='!=':
            self.code.append(["GET ","c"])
            self.code.append(["SUB ","d"])
            self.code.append(["PUT ","e"])
            self.code.append(["GET ","d"])
            self.code.append(["SUB ","c"])
            self.code.append(["ADD ","e"])
            self.code.append(["JPOS ",""])

    def interpretConduction(self, conduction, name):
        # print(conduction)
        # print(conduction[2])
        self.getNumber(conduction[1],name)
        self.code.append(["PUT ","c"])
        self.getNumber(conduction[2],name)
        self.code.append(["PUT ","d"])
        if conduction[0]=='>':
            self.code.append(["GET ","c"])
            self.code.append(["SUB ","d"])
            self.code.append(["JZERO ",""])
        if conduction[0]=='<':
            self.code.append(["GET ","d"])
            self.code.append(["SUB ","c"])
            self.code.append(["JZERO ",""])
        if conduction[0]=='>=':
            self.code.append(["GET ","d"])
            self.code.append(["SUB ","c"])
            self.code.append(["JPOS ",""])
        if conduction[0]=='<=':
            self.code.append(["GET ","c"])
            self.code.append(["SUB ","d"])
            self.code.append(["JPOS ",""])
        if conduction[0]=='=':
            self.code.append(["GET ","c"])
            self.code.append(["SUB ","d"])
            self.code.append(["PUT ","e"])
            self.code.append(["GET ","d"])
            self.code.append(["SUB ","c"])
            self.code.append(["ADD ","e"])
            self.code.append(["JPOS ",""])
            
        if conduction[0]=='!=':
            self.code.append(["GET ","c"])
            self.code.append(["SUB ","d"])
            self.code.append(["PUT ","e"])
            self.code.append(["GET ","d"])
            self.code.append(["SUB ","c"])
            self.code.append(["ADD ","e"])
            self.code.append(["JZERO ",""])

    def interpretProcCall(self, procCall, name):
        procName = procCall[1]
        if procName==name:
            raise Exception(f"Wywolanie rekurencyjne funckji {procName} w okolicy lini {self.line}")
        if procName not in self.procedures:
            raise Exception(f"Zła nazwa funkcji {procName} w okolicy lini {self.line}")
        head = self.procedures[procName].head
        j = procCall[2]
        i = len(head)
        while len(j)==3:
            i-=1
            if i<0:
                raise Exception(f"Złe argumenty funkcji{procName} w okolicy lini {self.line}")
            if head[i][0]=='T':
                if j[2] not in self.procedures[name].arrays:
                    raise Exception(f"Złe argumenty funkcji {procName} w okolicy lini {self.line}")
            if head[i][0]=='V':
                if j[2] not in self.procedures[name].variables:
                    raise Exception(f"Złe argumenty funkcji {procName} w okolicy lini {self.line}")
            self.givePointer([head[i][0],procName, head[i][1], name, j[2]])
            j = j[1]
        i-=1
        if i<0:
            raise Exception(f"Złe argumenty funkcji {procName} w okolicy lini {self.line}")
        if i>0:
            raise Exception(f"Złe argumenty funkcji {procName} w okolicy lini {self.line}")
        if head[i][0]=='T':
            if j[1] not in self.procedures[name].arrays:
                raise Exception(f"Złe argumenty funkcji {procName} w okolicy lini {self.line}")
        if head[i][0]=='V':
            if j[1] not in self.procedures[name].variables:
                raise Exception(f"Złe argumenty funkcji {procName} w okolicy lini {self.line}")
        self.givePointer([head[i][0],procName, head[i][1], name, j[1]])
        recall = self.procedures[procName].memory
        start = self.procedures[procName].start
        self.iterateNum(recall,"b")
        self.iterateNum(4,"a")
        self.code.append(["STRK ", "c"])
        self.code.append(["ADD ","c"])
        self.code.append(["STORE ", "b"])
        self.code.append(["JUMP ", str(start)])

    def givePointer(self, command):
        if command[0]=='T':
            memory1 = self.procedures[command[1]].arrays[command[2]].memoryLocation
            memory2 = self.procedures[command[3]].arrays[command[4]].memoryLocation    
            self.iterateNum(memory1, "b")    
            self.iterateNum(memory2, "a")
            if self.procedures[command[3]].arrays[command[4]].argument:
                self.code.append(["LOAD ", "a"]) 
            self.code.append(["STORE ", "b"])    
        if command[0]=='V':
            memory1 = self.procedures[command[1]].variables[command[2]].memoryLocation
            memory2 = self.procedures[command[3]].variables[command[4]].memoryLocation    
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
            x = self.procedures[name].variables[read[1][1]].memoryLocation
            self.iterateNum(x, "b")
            if isItArgument:
                self.code.append(["LOAD ", "b"])
                self.code.append(["PUT ", "b"])
        if len(read[1])==3:
            if read[1][1] not in self.procedures[name].arrays:
                raise Exception(f"Niezdefiniowana tablica: {read[1][1]} w okolicy lini {self.line}")
            isItArgument = self.procedures[name].arrays[read[1][1]].argument
            x = self.procedures[name].arrays[read[1][1]].memoryLocation
            self.getArrayArgument(read[1][2][1],name,"c")
            # self.iterateNum(int(read[1][2][1]), "c")
            self.iterateNum(x, "b")
            if isItArgument:
                self.code.append(["LOAD ", "b"])
                self.code.append(["ADD ", "c"])
                self.code.append(["PUT ", "b"])
            else:
                self.code.append(["GET ", "b"])
                self.code.append(["ADD ", "c"])
                self.code.append(["PUT ", "b"])
        self.code.append(["READ",""])
        self.code.append(["STORE ","b"])
    def interpretWrite(self, write, name):
        self.getNumber(write[1], name)
        self.code.append(["WRITE",""])

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
            self.procedures[name].arrays[assign[1][1]].values=True
            x = self.procedures[name].arrays[assign[1][1]].memoryLocation
            # self.iterateNum(int(assign[1][2][1]), "c")
            self.getArrayArgument(assign[1][2][1],name,"c")
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
            self.getNumber(assign[2], name)
        if len(assign[2]) == 3:
            self.getCalc(assign[2], name)
        self.code.append(["STORE ", "b"])

    def getCalc(self, calc, name):
        self.getNumber(calc[2], name)
        self.code.append(["PUT ", "h"])
        self.getNumber(calc[1], name)
        # self.code.append(["PUT ", "h"])
        if calc[0] == "+":
            self.code.append(["ADD ", "h"])
        if calc[0] == "-":
            self.code.append(["SUB ", "h"])
        if calc[0] == "*":
            if len(calc[2]) == 2 and calc[2][1] == '2':
                self.code.append(["SHL ", "a"])
            else:
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
        if calc[0]=="/":
            if len(calc[2]) == 2 and calc[2][1] == '2':
                self.code.append(["SHR ", "a"])
            else:
                self.code.append(["PUT ", "g"])
                self.code.append(["RST ", "d"])
                lineNumber = len(self.code) 
                self.code.append(["GET ", "h"])
                self.code.append(["PUT ", "f"])
                self.code.append(["SUB ", "g"])
                self.code.append(["JZERO ", str(lineNumber+5)])
                self.code.append(["JUMP ", str(lineNumber+21)])
                self.code.append(["RST ", "e"]) #licznik
                self.code.append(["INC ", "e"])
                self.code.append(["SHL ", "e"])
                self.code.append(["SHL ", "f"])
                self.code.append(["GET ", "f"])
                self.code.append(["SUB ", "g"])
                self.code.append(["JZERO ", str(lineNumber+7)])
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
        if calc[0]=="%":
            if len(calc[2]) == 2 and calc[2][1] == '2':
                self.code.append(["PUT ", "d"])
                self.code.append(["SHR ", "d"])
                self.code.append(["SHL ", "d"])
                self.code.append(["SUB ", "d"])
            else:
                self.code.append(["PUT ", "g"])
                lineNumber = len(self.code) 
                self.code.append(["GET ", "h"])
                self.code.append(["PUT ", "f"])
                self.code.append(["SUB ", "g"])
                self.code.append(["JZERO ", str(lineNumber+5)])
                self.code.append(["JUMP ", str(lineNumber+18)])
                self.code.append(["RST ", "e"]) #licznik
                self.code.append(["INC ", "e"])
                self.code.append(["SHL ", "e"])
                self.code.append(["SHL ", "f"])
                self.code.append(["GET ", "f"])
                self.code.append(["SUB ", "g"])
                self.code.append(["JZERO ", str(lineNumber+7)])
                self.code.append(["SHR ", "e"])
                self.code.append(["SHR ", "f"])
                self.code.append(["GET ", "g"])
                self.code.append(["SUB ", "f"])
                self.code.append(["PUT ", "g"])
                self.code.append(["JUMP ", str(lineNumber)])
                self.code.append(["GET ", "g"])

    #ustawia wartosc number w adresie a
    def getNumber(self, number, name):
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
                self.iterateNum(x, "a")
                if isItArgument:
                    self.code.append(["LOAD ", "a"])
            if len(number[1]) == 3:
                if identifiactor not in self.procedures[name].arrays:
                    raise Exception(f"Niezdefiniowana tablica: {identifiactor} w okolicy lini {self.line}")
                isItArgument = self.procedures[name].arrays[identifiactor].argument
                x = self.procedures[name].arrays[identifiactor].memoryLocation
                self.getArrayArgument(number[1][2][1],name,"c")
                # self.iterateNum(int(number[1][2][1]), "c")
                # self.getNumber(number)
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
            self.iterateNum(int(number),register)
        else:
            if number not in self.procedures[name].variables:
                raise Exception(f"Niezdefiniowana zmienna: {number} w okolicy lini {self.line}")
            # if (not self.procedures[name].variables[number].value):#and (not self.procedures[name].variables[number].argument):
            #     raise Exception(f"Niezainicjalizowana zmienna: {number} w okolicy lini {self.line}")    
            isItArgument = self.procedures[name].variables[number].argument
            x = self.procedures[name].variables[number].memoryLocation
            self.iterateNum(x, register)
            if isItArgument:
                self.code.append(["LOAD ", register])
                self.code.append(["PUT ",register])
            self.code.append(["LOAD ", register])
            self.code.append(["PUT ",register])

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
        # self.code.append(["#main sie zaczyna",""])
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


# if __name__ == '__main__':
#     # Tworzenie instancji parsera i interpretera
#     lexer = MyLexer()
#     parser = MyParser()
#     interpreter = Interpreter()

#     # Przykładowy program w Twoim języku

#     data = '''
#     # PROCEDURE pa(T a, b,f, T i) IS
#     # c[5] , d[5], g, h, j[3] ,k[2]
#     # IN
#     # # b:=2;
#     # a[3]:=7+a[1];
#     # END
#     # PROCEDURE de(m,n,x,y,z) IS
#     #   a,b[1]
#     # IN
#     #   a:=m;
#     # END
#     PROGRAM IS
#     a[10],b, c, d, e
#     IN
#     READ b;
#     pa(a,b);
#     WRITE a[b];
#     END
#     '''

#     try:
#         ast = parser.parse(lexer.tokenize(data))
#     except Exception as e:
#         print(e)
#         sys.exit(1)
#     try:
#         interpreter.interpret(ast)
#     except Exception as e:
#         print(e)
#         sys.exit(1)
#     # print(ast)
#     print(interpreter.procedures['main'].variables)
#     print(interpreter.procedures['main'].arrays)
#     # print(interpreter.procedures['de'].variables)
#     # print(interpreter.procedures['de'].arrays)
#     print(interpreter.code)

#     # Wydruk wartości zmiennych po wykonaniu programu
#     # print("Wartość x po wykonaniu programu:", interpreter.variables['x'])
#     # print("Wartość y po wykonaniu programu:", interpreter.variables['y'])

# # data = '''# Równanie diofantyczne mx-ny=nwd(m,n) (z)
# #
# # PROCEDURE de(m,n,x,y,z) IS
# #   a,b,r,s,reszta,iloraz,rr,ss,tmp
# # IN
# #   a:=m;
# #   b:=n;
# #   x:=10;
# #   y:=0;
# #   r:=n;
# #   s:=m-1;
# #   WHILE b>0 DO
# #     # niezmiennik: NWD(m,n)=NWD(a,b) i a=mx-ny i b=mr-ns
# #     reszta:=a%b;
# #     iloraz:=a/b;
# #     a:=b;
# #     b:=reszta;
# #     rr:=r;
# #     tmp:=iloraz*r;
# #     IF x<tmp THEN
# #       r:=n*iloraz;
# #     ELSE
# #       r:=0;
# #     ENDIF
# #     r:=r+x;
# #     r:=r-tmp;
# #     ss:=s;
# #     tmp:=iloraz*s;
# #     IF y<tmp THEN
# #       s:=m*iloraz;
# #     ELSE
# #       s:=0;
# #     ENDIF
# #     s:=s+y;
# #     s:=s-tmp;
# #     x:=rr;
# #     y:=ss;
# #   ENDWHILE
# #   z:=a;
# # END
# #
# # PROGRAM IS
# #   m,n,x,y,nwd
# # IN
# #   READ m;
# #   READ n;
# #   de(m,n,x,y,nwd);
# #   WRITE x;
# #   WRITE y;
# #   WRITE nwd;
# # END
# #
# # '''
# #
# # lexer = MyLexer()
# # parser = MyParser()
# #
# # result = parser.parse(lexer.tokenize(data))
# # newFormat = []
# # result = astToNewFormat(result, newFormat)
# # print("Wynik:", result)
