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

    @property
    def expr(self):
        return self._expr

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

    def __str__(self):
        return f"Field({self.name}={self.expr})"


class Expr(object):
    def Eval(self, record):
        raise Error("Not implemented")


class Immediate(Expr):
    def __init__(self, value):
        self._value = value

    def Eval(self, record):
        return self._value

    def __str__(self):
        return str(self._value)

    def __repr__(self):
        return f"Immediate({self._value})"


class Ref(Expr):
    def __init__(self, ref):
        self._ref = ref

    def Eval(self, record):
        return record.get(self._ref)

    def __str__(self):
        return self._ref

    def __repr__(self):
        return f"Ref({self._ref})"


class List(Expr):
    def __init__(self, *elems):
        self._elems = elems

    def Eval(self, record):
        # return list(map(lambda e: e.Eval(record), self._elems))
        return self

    def __str__(self):
        return '[{}]'.format(','.join(map(str, self._elems)))

    def __repr__(self):
        return f'List(elems={self._elems!r})'

    def __add__(self, other):
        return List(*(self._elems + other._elems))

    def get(self, index, context):
        return self._elems[index].Eval(context)

    def export(self, context):
        return list(map(lambda e: export(e.Eval(context), context), self._elems))


class ListAccess(Expr):
    def __init__(self, list, index):
        self._list = list
        self._index = index

    def __str__(self):
        return f"{self._list}[{self._index}]"

    def __repr__(self):
        return f"List({self._list}, index={self._index}"

    def Eval(self, context):
        return self._list.Eval(context).get(self._index.Eval(context), context=context)


class UnaryOp(Expr):
    def __init__(self, op, op_fn, operand):
        self._op = op
        self._op_fn = op_fn
        self._operand = operand

    def Eval(self, record):
        return self._op_fn(self._operand.Eval(record))


class BinOp(Expr):
    def __init__(self, op, op_fn, left, right):
        self._op = op
        self._op_fn = op_fn
        self._left = left
        self._right = right

    def Eval(self, record):
        return self._op_fn(self._left.Eval(record), self._right.Eval(record))

    def __str__(self):
        return f"{self._left} {self._op} {self._right}"

    def __repr__(self):
        return f"BinOp(op={self._op}, left={self._left}, right={self._right})"


class If(Expr):
    def __init__(self, cond, etrue, efalse):
        self._cond = cond
        self._etrue = etrue
        self._efalse = efalse

    def Eval(self, record):
        return (self._etrue if self._cond.Eval(record) else self._efalse).Eval(record)

    def __str__(self):
        return f"if {self._cond} then {self._etrue} else {self._efalse}"

    def __repr__(self):
        return f"If(cond={self._cond}, etrue={self._etrue}, efalse={self._efalse})"


class FieldAccess(Expr):
    def __init__(self, record, name):
        self._record = record
        self._name = name

    def Eval(self, record):
        rec = self._record.Eval(record)
        # Notes:
        #  - the record's field evaluates in the context of its enclosing record
        #  - the field name doesn't resolve
        return rec.get(self._name)

    def __str__(self):
        return f"{self._record}.{self._name}"


def export(value, context):
    if isinstance(value, Record) or isinstance(value, List):
        return value.export(context=context)

    return value


class Record(object):
    def __init__(self, **kwargs):
        self._fields = dict()
        for name, expr in kwargs.items():
            self._fields[name] = Field(name, expr)

    def Eval(self, record):
        return self

    def get(self, field_name):
        assert (field_name in self._fields), f"Field {field_name!r} missing in {self._fields!r}"
        return self._fields[field_name].Eval(self)

    def __add__(self, rec):
        merged = Record()
        def merge_fields():
            for name, field in self._fields.items():
                yield name, field.clone()
            for name, field in rec._fields.items():
                yield name, field.clone()
        merged._fields = dict(merge_fields())
        return merged

    def export(self, context=None):
        def _export():
            for name, field in self._fields.items():
                if field._exported:
                    yield (name, export(field.Eval(self), context=self))
        return dict(_export())

    def __str__(self):
        return "{" + ",".join(map(lambda f: f"{f.name}={f.expr}", self._fields.values())) + "}"

    def __repr__(self):
        return "Record({})".format(",".join(map(lambda f: f"{f.name}={f.expr!r}", self._fields.values())))


class Call(object):
    def __init__(self, fun, params):
        self._fun = fun
        self._params = dict()
        for name, expr in params.items():
            self._params[name] = Field(name, expr)

    def Eval(self, record):
        #print("\nEvaluating call: {}({})".format(self._fun, ",".join(map(lambda p: f"{p.name}={p.expr}", self._params.values()))))
        #print(f"self = {record!s}")
        fun = self._fun.Eval(record)
        params = dict()
        for name, expr in self._params.items():
            #print(f"params[{name}] = {expr!r}")
            params[name] = Immediate(expr.clone().Eval(record))  # clone the Field to avoid caching
            #print(f"params[{name}] = {params[name]}")
        params = Record(**params)
        #print(f"merging {fun!s}\n    and {params!s}")
        result = fun + params
        #print(f"result = {result!s}")
        return result

    def __str__(self):
        return "{}({})".format(
            self._fun,
            ",".join(map(lambda p: f"{p.name}={p.expr}", self._params.values())))

    def __repr__(self):
        return "Call(fun={!r}, params=({}))".format(
            self._fun,
            ",".join(map(lambda p: f"{p.name}={p.expr!r}", self._params.values())))
