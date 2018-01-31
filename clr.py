#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python -*-
"""Configuration Language Runtime."""


class Error(Exception):
    pass


_VOID = object()


class Field(object):
    def __init__(self, name, expr, exported=True):
        self._name = name
        self._expr = expr
        self._value = _VOID
        self._exported = exported

    @property
    def name(self):
        """The name of this field."""
        return self._name

    def Eval(self, record):
        if self._value is _VOID:
            self._value = self._expr.Eval(record)
        return self._value

    def clone(self):
        return Field(
            name=self._name,
            expr=self._expr,
            exported=self._exported,
        )

    def __repr__(self):
        return (
            f"Field(name={self.name!r}, "
            f"expr={self._expr!r}, "
            f"value={self._value!r}, "
            f"exported={self._exported!r})"
        )

    __str__ = __repr__


class Expr(object):
    def Eval(self, record):
        raise Error("Not implemented")


class Immediate(Expr):
    def __init__(self, value):
        self._value = value

    def Eval(self, record):
        return self._value


class Ref(Expr):
    def __init__(self, ref):
        self._ref = ref

    def Eval(self, record):
        return record.get(self._ref)


class UnaryOp(Expr):
    def __init__(self, op, operand):
        self._op = op
        self._operand = operand

    def Eval(self, record):
        return self._op(self._operand.Eval(record))


class BinOp(Expr):
    def __init__(self, op, left, right):
        self._op = op
        self._left = left
        self._right = right

    def Eval(self, record):
        return self._op(self._left.Eval(record), self._right.Eval(record))


class If(Expr):
    def __init__(self, cond, etrue, efalse):
        self._cond = cond
        self._etrue = etrue
        self._efalse = efalse

    def Eval(self, record):
        return (self._etrue if self._cond.Eval(record) else self._efalse).Eval(record)


class FieldAccess(Expr):
    def __init__(self, record, name):
        self._record = record
        self._name = name

    def Eval(self, record):
        rec = self._record.Eval(record)
        # Note: the record's field evaluates in the context of its enclosing record
        return rec.get(self._name.Eval(record))


class Record(object):
    def __init__(self, **kwargs):
        self._fields = dict()
        for name, expr in kwargs.items():
            self._fields[name] = Field(name, expr)

    def Eval(self, record):
        return self

    def get(self, field_name):
        return self._fields[field_name].Eval(self)

    def __add__(self, rec):
        def merge_fields():
            for name, field in self._fields.items():
                yield name, field.clone()
            for name, field in rec._fields.items():
                yield name, field.clone()
        return Record(**dict(merge_fields()))

    def export(self):
        def _export():
            for name, field in self._fields.items():
                if field._exported:
                    value = field.Eval(self)
                    if isinstance(value, Record):
                        value = value.export()
                    yield (name, value)
        return dict(_export())
