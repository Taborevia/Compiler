from lexer_parser import MyLexer, MyParser, print_ast
from code_generator import Interpreter
import sys

lexer = MyLexer()
parser = MyParser()
interpreter = Interpreter()

# Przykładowy program w Twoim języku

data = '''
# PROCEDURE pa(T a, b,f, T i) IS
# c[5] , d[5], g, h, j[3] ,k[2]
# IN
# # b:=2;
# a[3]:=7+a[1];
# END
# PROCEDURE de(m,n,x,y,z) IS
#   a,b[1]
# IN
#   a:=m;
# END
PROGRAM IS
a[10],b, c, d, e
IN
READ b;
pa(a,b);
WRITE a[b];
END
'''
importFileName = sys.argv[1]
exportFileName = sys.argv[2]
importFile = open(importFileName, 'r')
exportFile = open(exportFileName, 'w')
data = importFile.read()
try:
    ast = parser.parse(lexer.tokenize(data))
except Exception as e:
    print(e)
    sys.exit(1)
try:
    interpreter.interpret(ast)
except Exception as e:
    print(e)
    sys.exit(1)
# print(ast)
# print(interpreter.procedures['de'].head)
# print(interpreter.procedures['main'].head)
# print(interpreter.procedures['de'].variables)
# print(interpreter.procedures['de'].arrays)
# print(interpreter.code)
for i in interpreter.code:
    exportFile.write(str(i[0])+str(i[1])+"\n")
