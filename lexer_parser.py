from sly import Lexer, Parser
#lexer and parser which creat AST tree
class MyLexer(Lexer):
    tokens = {PROCEDURE, IS, IN, END, PROGRAM, IF, THEN, ELSE, ENDIF, WHILE, DO, ENDWHILE, REPEAT, UNTIL, READ, WRITE, NUM, PIDENTIFIER, EQ, NEQ, GT, LT, GEQ, LEQ, ASSIGN, T}
    literals = {'+','-','*','/','%',',',';','(',')','[',']'}
    ignore = ' \t'

    PROCEDURE = r'PROCEDURE'
    IS = r'IS'
    IN = r'IN'
    ENDIF = r'ENDIF'
    ENDWHILE = r'ENDWHILE'
    END = r'END'
    PROGRAM = r'PROGRAM'
    IF = r'IF'
    THEN = r'THEN'
    ELSE = r'ELSE'
    WHILE = r'WHILE'
    DO = r'DO'
    REPEAT = r'REPEAT'
    UNTIL = r'UNTIL'
    READ = r'READ'
    WRITE = r'WRITE'
    NUM = r'\d+'
    PIDENTIFIER = r'[_a-z]+'
    NEQ = r'!='
    EQ = r'='
    GEQ = r'>='
    LEQ = r'<='
    GT = r'>'
    LT = r'<'
    ASSIGN = r':='
    T = r'T'


    #komentarze
    @_(r'#.*\n')
    def COMMENT(self, t):
        self.lineno += 1
        # Obsługa komentarzy

    # Obsługa końca linii
    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)

class MyParser(Parser):
    tokens = MyLexer.tokens

    # Grammar rules

    @_('PROGRAM IS declarations IN commands END')
    def program_all(self, p):
        return ('main', p.declarations, p.commands)

    @_('procedures main')
    def program_all(self, p):
        return ('program_all', p.procedures, p.main)

    @_('procedures PROCEDURE proc_head IS declarations IN commands END')
    def procedures(self, p):
        return ('procedures', p.procedures, ('procedure', p.proc_head, p.declarations, p.commands))

    @_('procedures PROCEDURE proc_head IS IN commands END')
    def procedures(self, p):
        return ('procedures', p.procedures, ('procedure', p.proc_head, 'None', p.commands))

    @_('PROCEDURE proc_head IS declarations IN commands END')
    def procedures(self, p):
        return ('procedure', p.proc_head, p.declarations, p.commands)

    @_('PROCEDURE proc_head IS IN commands END')
    def procedures(self, p):
        return ('procedure', p.proc_head, 'None', p.commands)

    @_('PROGRAM IS declarations IN commands END')
    def main(self, p):
        return ('main', p.declarations, p.commands)

    @_('PROGRAM IS IN commands END')
    def main(self, p):
        return ('main', 'None', p.commands)

    @_('commands command')
    def commands(self, p):
        return ('commands', p.commands, p.command)

    @_('command')
    def commands(self, p):
        return ('commands', p.command)

    @_('identifier ASSIGN expression ";"')
    def command(self, p):
        return ('assign', p.identifier, p.expression)

    @_('IF condition THEN commands ELSE commands ENDIF')
    def command(self, p):
        return ('if_else', p.condition, p.commands0, p.commands1)

    @_('IF condition THEN commands ENDIF')
    def command(self, p):
        return ('if', p.condition, p.commands)

    @_('WHILE condition DO commands ENDWHILE')
    def command(self, p):
        return ('while', p.condition, p.commands)

    @_('REPEAT commands UNTIL condition ";"')
    def command(self, p):
        return ('repeat_until', p.commands, p.condition)

    @_('proc_call ";"')
    def command(self, p):
        return ('proc_call', p.proc_call)

    @_('READ identifier ";"')
    def command(self, p):
        return ('read', p.identifier)

    @_('WRITE value ";"')
    def command(self, p):
        return ('write', p.value)
    @_('PIDENTIFIER "(" args_decl ")"')
    def proc_head(self, p):
        return('proc_head', p.PIDENTIFIER, p.args_decl)

    @_('PIDENTIFIER "(" args ")"')
    def proc_call(self, p):
        return ('proc_call', p.PIDENTIFIER, p.args)

    @_('declarations "," PIDENTIFIER')
    def declarations(self, p):
        return ('declarations', p.declarations, p.PIDENTIFIER)

    @_('declarations "," PIDENTIFIER "[" NUM "]"')
    def declarations(self, p):
        return ('declarations', p.declarations, ("T", p.PIDENTIFIER, p.NUM))

    @_('PIDENTIFIER "[" NUM "]"')
    def declarations(self, p):
        return ('declarations', ("T", p.PIDENTIFIER, p.NUM))

    @_('PIDENTIFIER')
    def declarations(self, p):
        return ('declarations', p.PIDENTIFIER)

    @_('args_decl "," PIDENTIFIER')
    def args_decl(self, p):
        return ('args_decl', p.args_decl, p.PIDENTIFIER)

    @_('args_decl "," T PIDENTIFIER')
    def args_decl(self, p):
        return ('args_decl', p.args_decl, ('T', p.PIDENTIFIER))

    @_('PIDENTIFIER')
    def args_decl(self, p):
        return ('args_decl', p.PIDENTIFIER)

    @_('T PIDENTIFIER')
    def args_decl(self, p):
        return ('args_decl', ('T', p.PIDENTIFIER))

    @_('args "," PIDENTIFIER')
    def args(self, p):
        return ('args', p.args, p.PIDENTIFIER)

    @_('PIDENTIFIER')
    def args(self, p):
        return ('args', p.PIDENTIFIER)

    @_('value "+" value')
    def expression(self, p):
        return ('+', p.value0, p.value1)

    @_('value "-" value')
    def expression(self, p):
        return ('-', p.value0, p.value1)

    @_('value "*" value')
    def expression(self, p):
        return ('*', p.value0, p.value1)

    @_('value "/" value')
    def expression(self, p):
        return ('/', p.value0, p.value1)

    @_('value "%" value')
    def expression(self, p):
        return ('%', p.value0, p.value1)

    @_('value')
    def expression(self, p):
        return p.value

    @_('value EQ value')
    def condition(self, p):
        return ('=', p.value0, p.value1)

    @_('value NEQ value')
    def condition(self, p):
        return ('!=', p.value0, p.value1)

    @_('value GT value')
    def condition(self, p):
        return ('>', p.value0, p.value1)

    @_('value LT value')
    def condition(self, p):
        return ('<', p.value0, p.value1)

    @_('value GEQ value')
    def condition(self, p):
        return ('>=', p.value0, p.value1)

    @_('value LEQ value')
    def condition(self, p):
        return ('<=', p.value0, p.value1)

    @_('NUM')
    def value(self, p):
        return ('num', p.NUM)

    @_('identifier')
    def value(self, p):
        return ('identifier', p.identifier)
    @_('PIDENTIFIER')
    def identifier(self,p):
        return ('pidentifier', p.PIDENTIFIER)
    @_('PIDENTIFIER "[" NUM "]"')
    def identifier(self,p):
        return ('pidentifier', p.PIDENTIFIER, ("T", p.NUM))

    @_('PIDENTIFIER "[" PIDENTIFIER "]"')
    def identifier(self, p):
        return ('pidentifier', p.PIDENTIFIER0, ("T", p.PIDENTIFIER1))

    def error(self, t):
        raise Exception(f"Syntax error: '{t.value}' in line {t.lineno}")

def print_ast(node, indent=0):
    if isinstance(node, tuple):
        print('  ' * indent + node[0])  # Wypisz nazwę węzła
        for child in node[1:]:
            print_ast(child, indent + 1)  # Przejdź do dzieci
    else:
        print('  ' * indent + str(node))  # Wypisz liść

