#!/usr/bin/env python3

from lark import Lark, Transformer

class Expr:
  def eval(self, table):
    if self in table:
      return table[self]
    else:
      return self
  def apply(self, args, table):
    raise Exception('Applying arguments "%s" to %s "%s" as if it was a function' % (args, self.__class__.__name__, self))

class Id(Expr, str):
  def __repr__(self):
    return '%s' % super().__str__()

class Num(Expr, float):
  def __repr__(self):
    return '%g' % self

class Str(Expr, str):
  def __str__(self):
    return '"%s"' % super().self

class List(Expr, tuple):
  def eval(self, table):
    return self.__class__(map(lambda x: x.eval(table), self))
  def __str__(self):
    if len(self) == 1:
      return '[%s]' % self[0]
    return '[' + super().__str__()[1:-1] + ']'

class Const(Expr):
  def __init__(self, name, value):
    self.name = name
    self.value = value
  def __str__(self):
    return self.name + ' = ' + str(self.value)

class Args(List):
  def __str__(self):
    return '(%s)' % super().__str__()[1:-1]

class Pars(Args):
  def table(self, args):
    if len(self) != len(args):
      raise Exception('Arguments length mismatch: expected "%s", got "%s")' % (self, args))
    return dict(zip(self, args))

class Fn(Expr):
  def __init__(self, pars, body):
    self.pars = pars
    self.body = body
  def __repr__(self):
    return '@%s{%s}' % (str(self.pars), str(self.body))
  def apply(self, args, table):
    r = self.body.eval(table | self.pars.table(args))
    #print('fn app "%s%s" -> "%s"' % (self, args, r))
    return r

class Case:
  def __init__(self, cond, body):
    self.cond = cond
    self.body = body
  def __str__(self):
    return '| %s = %s' % (str(self.cond), str(self.body))
  def matches(self, table):
    if self.cond.eval(table) == Id('true'):
      r = self.body.eval(table)
      return r
    return None

class Cases(List):
  def __str__(self):
    return ' '.join([str(i) for i in self])
  def eval(self, table):
    for i in self:
      r = i.matches(table)
      if r != None:
        return r
    raise Exception('No match for %s in %s' % (str(table), str(self)))

class App(Expr):
  def __init__(self, obj, args):
    self.obj = obj
    self.args = args
  def __str__(self):
    return str(self.obj) + str(self.args)
  def eval(self, table):
    obj = self.obj.eval(table)
    args = self.args.eval(table)
    #print('app self:"%s" obj:"%s" args:"%s"' % (self, obj, args))
    def conv_b(v):
      return Id('true') if v else Id('false')
    match self.obj:
      case Id('=='): return conv_b(args[0] == args[1])
      case Id('<>'): return conv_b(args[0] != args[1])
      case Id('<='): return conv_b(args[0] <= args[1])
      case Id('>='): return conv_b(args[0] >= args[1])
      case Id('<'): return conv_b(args[0] < args[1])
      case Id('>'): return conv_b(args[0] > args[1])
      case Id('+'): return Num(args[0] + args[1])
      case Id('-'): return Num(args[0] - args[1])
      case Id('*'): return Num(args[0] * args[1])
      case Id('/'): return Num(args[0] / args[1])
    return obj.apply(args, table)

class App_infix(App):
  def __str__(self):
    return '(%s %s %s)' % (self.args[0], self.obj, self.args[1])

class T(Transformer):
  def dfn_const(self, a):   return (a[0], a[1])
  def dfn_no_args(self, a): return (a[0], Fn(Pars(), a[1]))
  def dfn_simple(self, a):  return (a[0], Fn(a[1], a[2]))
  dfn_guards = dfn_simple
  def STR(self, a): return Str(a[1:-1])
  def guards(self, a): return Cases(Case(a[i], a[i+1]) for i in range(0, len(a), 2))
  def app(self, a): return App(a[0], a[1])
  def fn(self, a): return Fn(a[0], a[1])
  def fn_guards(self, a): return Fn_guards(a[0], a[1])
  def expr(self, a):
    if len(a) == 1:
      return a[0]
    else:
      return App_infix(Id(a[1]), Args((a[0], a[2])))
  i2 = i3 = expr
  args = Args
  pars = Pars
  NUM = Num
  NAME = Id
  lst = List
  start = dict

class Prog:
  lark = Lark(r'''
  start: (_NL | dfn)*
  dfn: NAME "=" expr _NL        -> dfn_const
    | NAME "(" ")" "=" expr _NL -> dfn_no_args
    | NAME pars "=" expr _NL    -> dfn_simple
    | NAME pars guards          -> dfn_guards
  guards: ("|" expr "=" expr _NL?)+
  args: "(" (expr ",")* expr ")"
  pars: "(" (NAME ",")* NAME ")"
  ?atom: NUM | NAME | "(" expr ")" | lst | STR
    | NAME args               -> app
    | "@" pars "{" expr "}"   -> fn
    | "@" pars "{" guards "}" -> fn_guards
  lst: "[" (expr ",")* expr "]"
  STR: /"(?:[^"\\]|\\.)*"/u
  ?!expr: i2 | expr ("=="|"<>"|"<="|">="|"<"|">") i2
  ?!i2: i3 | i2 ("+"|"-") i3
  ?!i3: atom | i3 ("*"|"/") atom

  %import common.CNAME -> NAME
  %import common.SIGNED_NUMBER -> NUM
  %import common.SH_COMMENT -> COMMENT
  %import common.NEWLINE -> _NL
  %import common.WS_INLINE
  %ignore (COMMENT _NL)
  %ignore WS_INLINE
  ''', parser='lalr', transformer = T())
  def __init__(self, text):
    self.defs = self.lark.parse(text)
  def __str__(self):
    return '\n'.join(['%s = %s' % (i, self.defs[i]) for i in self.defs])
  def eval(self, app = App(Id('main'), Args())):
    return app.eval(self.defs)

if __name__ == '__main__':
  import argparse
  from pprint import pp
  from datetime import datetime
  parser = argparse.ArgumentParser(
    prog='EFPL',
    description='Interpreter of educational functional programming language by A.M.',
    epilog='(prototype for school project presentation, April 2024)')
  parser.add_argument('filename')
  args = parser.parse_args()
  with open(args.filename, 'r') as file:
    print('#### Reading... ####')
    prog = file.read()
    print('#### Parsing... ####')
    t_p = datetime.now()
    prog = Prog(prog)
    t_p = datetime.now() - t_p
    print('#### Evaluating... ####')
    t_e = datetime.now()
    pp(prog.eval())
    t_e = datetime.now() - t_e
    print('#### End of evaluation ####')
    print('Parsing time:', t_p)
    print('Evaluation time:', t_e)

# НЕ УДАЛЯЙ!
# Больше медиа
# Тяжелое медиа в приложения
# В текстовой работе ДОБАВИТЬ СКРИНШОТ В АНТИПЛАГИАТЕ!
# Распечатанный проект в папку
# Текст программы в приложении
# В тексте написать TODO-шки (что можно доработать) (и что будешь дорабатывать)
# antiplagiat.ru
