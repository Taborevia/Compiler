from lexer_parser import MyLexer, MyParser, print_ast
from code_generator import Interpreter
import sys
#simple code for UI
lexer = MyLexer()
parser = MyParser()
interpreter = Interpreter()
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
for i in interpreter.code:
    exportFile.write(str(i[0])+str(i[1])+"\n")
