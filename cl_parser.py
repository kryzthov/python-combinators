#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python -*-
"""Parser for the Configuration Language."""

import collections

import parser

from parser import Branch
from parser import Opt
from parser import Ref
from parser import Rep
from parser import Rep1
from parser import Seq
from parser import Skip
from parser import Map
#from parser import Str
from parser import Token
from parser import TokenRegex
from parser import TokenStr

import clr


class Error(Exception):
    """Errors raised in this module."""
    pass


SPACES = parser.RE_CSTYLE_COMMENTS


def Str(str):
    """Token, skips spaces and C-style comments."""
    return parser.TokenStr(str, spaces=SPACES)


# Tokens:
Identifier = Token(parser.Identifier, spaces=SPACES)
Integer = Token(parser.AllInteger, spaces=SPACES)
Float = Token(parser.Float, spaces=SPACES)
Number = Token(parser.Number, spaces=SPACES)
String = Token(parser.AllString, spaces=SPACES)

BoolTrue = Map(Str("true"), lambda _: True)
BoolFalse = Map(Str("false"), lambda _: False)
Boolean = Token(Branch(BoolTrue, BoolFalse), SPACES)

LPAREN = Str('(')
RPAREN = Str(')')
LBRACKET = Str('[')
RBRACKET = Str(']')
COMMA = Str(',')
DOT = Str('.')

Type = Str("type")

# —————————————————————————————————————————————————————————————————————————————————————————————————

Expr = Ref()
Record = Ref()
Field = Ref()

# —————————————————————————————————————————————————————————————————————————————————————————————————
# Immediate expressions:
# Value is an Immediate expression.
ImmExpr = Branch(
    Boolean,
    Number,
    # Float,
    # Integer,
    String,
)
ImmExpr = Map(ImmExpr, lambda value: clr.Immediate(value))

# -----------------------------------------------------------------------------
# Reference or function call

def make_ref_expr(v):
    return clr.Ref(v)

RefExpr = Map(Identifier, make_ref_expr)

# —————————————————————————————————————————————————————————————————————————————————————————————————

ParenExpr = Map(Seq(LPAREN, Expr, RPAREN), lambda vs: vs[1])

# —————————————————————————————————————————————————————————————————————————————————————————————————

def make_list_expr(vs):
    if vs is None:
        return clr.List()

    [head, tail] = vs
    l = [head]
    for elem in tail:
        l.append(elem)
    return clr.List(*l)

ListExpr = Seq(Skip(LBRACKET), Opt(Seq(Expr, Rep(Seq(Skip(COMMA), Expr)), Skip(Opt(COMMA)))), Skip(RBRACKET))
ListExpr = Map(ListExpr, make_list_expr)

# —————————————————————————————————————————————————————————————————————————————————————————————————

IfExpr = Seq(Str("if"), Expr, Str("then"), Expr, Str("else"), Expr)
def make_if_expr(values):
    return clr.If(values[1], values[3], values[5])
IfExpr = Map(IfExpr, make_if_expr)

# —————————————————————————————————————————————————————————————————————————————————————————————————

NotExpr = Map(Seq(Str("not"), Expr), lambda vs: clr.UnaryOp("not", lambda v: not v, vs[1]))
NegExpr = Map(Seq(Str("-"), Expr), lambda vs: clr.UnaryOp("-", lambda v: -v, vs[1]))

UnaryExpr = Branch(
    NotExpr,
    NegExpr,
)

# —————————————————————————————————————————————————————————————————————————————————————————————————

SimpleExpr = Branch(
    ImmExpr,
    UnaryExpr,
    IfExpr,
    Record,
    ListExpr,
    ParenExpr,
    RefExpr,
)

# —————————————————————————————————————————————————————————————————————————————————————————————————

def make_field_expr(values):
    [simple, exts] = values
    for ext in exts:
        token = ext[0]
        if token == '.':
            [_, name] = ext
            simple = clr.FieldAccess(record=simple, name=name)
        elif token == '[':
            [_, index, _] = ext
            simple = clr.ListAccess(list=simple, index=index)
        elif token == '(':
            [_, param0, params, _, _] = ext
            params.insert(0, param0)
            param_map = dict()
            for param in params:
                [param_name, param_type, param_expr] = param
                param_map[param_name] = param_expr
            simple = clr.Call(fun=simple, params=param_map)
        else:
            raise Exception(f"Unexpected token: {token}")
    return simple


Param = Seq(Identifier, Str('='), Expr)


FieldExpr = \
    Seq(SimpleExpr,
        Rep(Branch(
            Seq(DOT, Identifier),
            Seq(LBRACKET, Expr, RBRACKET),
            Seq(LPAREN, Param, Rep(Seq(Skip(COMMA), Param)), Opt(COMMA), RPAREN),
        ))
    )

FieldExpr = Map(FieldExpr, make_field_expr)

# —————————————————————————————————————————————————————————————————————————————————————————————————
# Binary expressions:
Operator = collections.namedtuple('Operator', ('token', 'fn'))

# Operators, by decreasing priority:
OP_LEVELS = [
    [
        Operator(token="**", fn=lambda x, y: x ** y),
    ],
    [
        Operator(token="*", fn=lambda x, y: x * y),
        Operator(token="/", fn=lambda x, y: x / y),
    ],
    [
        Operator(token="+", fn=lambda x, y: x + y),
        Operator(token="-", fn=lambda x, y: x - y),
    ],
    [
        Operator(token="==", fn=lambda x, y: x == y),
        Operator(token="!=", fn=lambda x, y: x != y),
        Operator(token="<=", fn=lambda x, y: x <= y),
        Operator(token=">=", fn=lambda x, y: x >= y),
        Operator(token="<", fn=lambda x, y: x < y),
        Operator(token=">", fn=lambda x, y: x > y),
    ],
    [
        Operator(token="and", fn=lambda x, y: x and y),
        Operator(token="or", fn=lambda x, y: x or y),
    ],
]

def make_bin_expr_parser(levels, base_parser):
    if len(levels) == 0:
        return base_parser
    ops, levels = levels[0], levels[1:]

    op_parser = Branch(*map(lambda op: Str(op.token), ops))
    op_fn_map = dict(ops)
    def _make_bin_expr(values):
        [left, values] = values
        for value in values:
            [op, right] = value
            op_fn = op_fn_map[op]
            left = clr.BinOp(op, op_fn, left, right)
        return left
    parser = Map(Seq(base_parser, Rep(Seq(op_parser, base_parser))), _make_bin_expr)

    return make_bin_expr_parser(levels=levels, base_parser=parser)


BinExpr = make_bin_expr_parser(levels=OP_LEVELS, base_parser=FieldExpr)

# —————————————————————————————————————————————————————————————————————————————————————————————————

Expr.Bind(BinExpr)

# —————————————————————————————————————————————————————————————————————————————————————————————————
# Record field parser:
# Value is [field name: Identifier, field type, field value: Expression]
_Field = Seq(
    Identifier,
    Opt(Map(Seq(Str(":"), Type), lambda vs: vs[1])),
    Opt(Map(Seq(Str("="), Expr), lambda vs: vs[1])),
    Opt(Branch(Str(","), Str(";"))),
)
_Field = Map(_Field, lambda vs: vs[0:3])
Field.Bind(_Field)

# —————————————————————————————————————————————————————————————————————————————————————————————————
# Record parser:
# Value is a Record
_Record = Seq(Str("{"), Rep(Field), Str("}"))

def _make_record(fields):
    field_map = dict()
    for field in fields:
        [field_name, field_type, field_expr] = field
        field_map[field_name] = field_expr
    rec = clr.Record(**field_map)
    return rec

_Record = Map(_Record, lambda values: _make_record(values[1]))

Record.Bind(_Record)

# —————————————————————————————————————————————————————————————————————————————————————————————————

if __name__ == '__main__':
    raise Error('Not a standalone module')
