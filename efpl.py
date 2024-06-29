#!/usr/bin/env python3

from lark import Lark, Transformer

class Expr: pass

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
  def __str__(self):
    if len(self) == 1:
      return '[%s]' % self[0]
    return '[' + super().__str__()[1:-1] + ']'

class Args(Expr, list):
  def __str__(self): return '(%s)' % super().__str__()[1:-1]

class Typed(tuple):
  def __str__(self):
    return '%s:%s' % (self[0], self[1])
  __repr__ = __str__

class Pars(Args):
  def __str__(self):
    return ' '.join(map(str, self))

class Fn(Expr):
  def __init__(self, pars, body):
    self.pars = pars
    self.body = body
  def __repr__(self):
    return '@{%s = %s}' % (str(self.pars), str(self.body))

class Case:
  def __init__(self, cond, body):
    self.cond = cond
    self.body = body
  def __str__(self):
    return '| %s = %s' % (str(self.cond), str(self.body))
  __repr__ = __str__

class Cases(List):
  def __str__(self):
    return ' '.join([str(i) for i in self])

class App(Expr):
  def __init__(self, obj, args):
    self.obj = obj
    self.args = args
  def __str__(self):
    return '%s%s' % (self.obj, self.args)
  __repr__ = __str__

class App_infix(App):
  def __str__(self):
    return '(%s%s%s)' % (self.args[0], self.obj, self.args[1])
  __repr__ = __str__

class T(Transformer):
  def dfn_const(self, a): return (a[0], a[1])
  def dfn_no_args(self, a): return (a[0], Fn(Pars(), a[1]))
  def dfn_simple(self, a): return (a[0], Fn(a[1], a[2]))
  dfn_guards = dfn_simple
  def STR(self, a): return Str(a[1:-1])
  def guards(self, a): return Cases(Case(a[i], a[i+1]) for i in range(0, len(a), 2))
  def app(self, a): return App(a[0], a[1])
  def fn(self, a): return Fn(a[0], a[1])
  def fn_guards(self, a): return Fn_guards(a[0], a[1])
  def expr(self, a):
    return a[0] if len(a) == 1 else\
      App_infix(Id(a[1]), Args((a[0], a[2])))
  i2 = i3 = expr
  typed = Typed
  args = Args
  pars = Pars
  NUM = Num
  NAME = Id
  lst = List
  start = dict

class Prog:
  lark = Lark(r'''
  TYPE: NAME
  typed: NAME ":" TYPE
  start: (_NL | dfn)*
  dfn: typed "=" [_NL] expr _NL        -> dfn_const
    | typed "(" ")" "=" [_NL] expr _NL -> dfn_no_args
    | typed pars "=" [_NL] expr _NL    -> dfn_simple
    | typed pars "=" [_NL] guards      -> dfn_guards
  guards: ("|" expr "=" expr _NL?)+
  args: "(" (expr ",")* expr ")"
  pars: typed+
  ?atom: NUM | NAME | "(" expr ")" | lst | STR
    | NAME args                 -> app
    | "@" "{" pars "=" expr "}" -> fn
    | "@" "{" pars guards "}"   -> fn_guards
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
''', parser='lalr', transformer=T())
  def __init__(self, text):
    self.defs = self.lark.parse(text)
    #TODO: check types
  def __str__(self):
    return '\n'.join(['%s = %s' % (i, self.defs[i]) for i in self.defs])
  __repr__ = __str__
  def optimize(self):
    pass
  def compile(self):
    for i in self.defs:
      print(i)

if __name__ == '__main__':
  import argparse
  from pprint import pp
  from datetime import datetime
  parser = argparse.ArgumentParser(
    prog='EFPL',
    description='Optimizing compiler (transpiler to C) prototype of educational functional programming language by A.M.',
    epilog='(efpl v0.0.1, June 2024)')
  parser.add_argument('filename')
  args = parser.parse_args()
  with open(args.filename, 'r') as file:
    print('#### Reading... ####')
    prog = file.read()
    print('#### Parsing... ####')
    t_p = datetime.now()
    prog = Prog(prog)
    t_p = datetime.now() - t_p
    pp(prog)
    print('#### Optimizing... ####')
    t_o = datetime.now()
    pp(prog.optimize())
    t_o = datetime.now() - t_o
    print('#### Compiling... ####')
    t_c = datetime.now()
    pp(prog.compile())
    t_c = datetime.now() - t_c
    print('Parsing time:', t_p)
    print('Optimization time:', t_o)
    print('Compilation time:', t_c)
