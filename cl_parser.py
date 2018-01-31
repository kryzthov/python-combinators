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
String = Token(parser.AllString, spaces=SPACES)

BoolTrue = Map(Str("true"), lambda _: True)
BoolFalse = Map(Str("false"), lambda _: False)
Boolean = Token(Branch(BoolTrue, BoolFalse), SPACES)

Type = Str("type")

Expr = Ref()
Record = Ref()

# Immediate expression parser:
# Value is an Immediate expression.
_ImmExpr = Branch(
    Boolean,
    Integer,
    Float,
    String,
)
_ImmExpr = Map(_ImmExpr, lambda value: clr.Immediate(value))

_RefExpr = Map(Identifier, lambda value: clr.Ref(value))

# -----------------------------------------------------------------------------
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
        Operator(token="and", fn=lambda x, y: x and y),
        Operator(token="or", fn=lambda x, y: x or y),
    ],
]

_ParenExpr = Map(Seq(Str("("), Expr, Str(")")), lambda vs: vs[1])

_NotExpr = Map(Seq(Str("not"), Expr), lambda vs: clr.UnaryOp(lambda v: not v, vs[1]))
_NegExpr = Map(Seq(Str("-"), Expr), lambda vs: clr.UnaryOp(lambda v: -v, vs[1]))

_UnaryExpr = Branch(
    _NotExpr,
    _NegExpr,
)

_SimpleExpr = Branch(_ImmExpr, _ParenExpr, _UnaryExpr, _RefExpr)

def make_field_expr(values):
    [left, values] = values
    for value in values:
        [op, right] = value
        left = clr.FieldAccess(left, right)
    return left

_FieldExpr = Map(Seq(_SimpleExpr, Rep(Seq(Str("."), _SimpleExpr))), make_field_expr)

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
            op = op_fn_map[op]
            left = clr.BinOp(op, left, right)
        return left
    parser = Map(Seq(base_parser, Rep(Seq(op_parser, base_parser))), _make_bin_expr)

    return make_bin_expr_parser(levels=levels, base_parser=parser)


_BinExpr = make_bin_expr_parser(levels=OP_LEVELS, base_parser=_FieldExpr)


_IfExpr = Seq(Str("if"), Expr, Str("then"), Expr, Str("else"), Expr)
def _make_if_expr(values):
    return clr.If(values[1], values[3], values[5])
_IfExpr = Map(_IfExpr, _make_if_expr)

Expr.Bind(Branch(_IfExpr, Record, _BinExpr))

# Field parser:
# Value is [field name: Identifier, field type, field value: Expression]
_Field = Seq(
    Identifier,
    Opt(Map(Seq(Str(":"), Type), lambda vs: vs[1])),
    Opt(Map(Seq(Str("="), Expr), lambda vs: vs[1])),
    Opt(Branch(Str(","), Str(";"))),
)
_Field = Map(_Field, lambda vs: vs[0:3])
Field = _Field

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


if __name__ == '__main__':
    raise Error('Not a standalone module')
