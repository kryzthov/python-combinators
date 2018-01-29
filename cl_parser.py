#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python -*-
"""Parser for the Configuration Language."""

import parser

from parser import Branch
from parser import Opt
from parser import Rep
from parser import Rep1
from parser import Seq
from parser import Map
from parser import Str
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

Expr = Branch(_ImmExpr, _RefExpr)

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
Record = _Record


class CLParser(object):
    """Parser for a Configuration Language document."""

    def __init__(self):
        names = schema.Names()
        self._names = names

        # Forward define the schema parser to allow recursive definitions:
        avro_schema = parser.Ref()
        avro_value = parser.Ref()

        primitives = tuple(
            map(self._MakePrimitiveParser, schema.PRIMITIVE_TYPES))

        array_parser = Seq(Token('array'), Token('<'), avro_schema, Token('>')) \
            .Map(lambda parsed: schema.ArraySchema(items=parsed[2]))

        map_parser = Seq(Token('map'), Token('<'), avro_schema, Token('>')) \
            .Map(lambda parsed: schema.MapSchema(values=parsed[2]))

        union_parser = \
            Seq(Token('union'), Token('{'),
                Rep1(Seq(avro_schema, Opt(Token(','))).Map(lambda m: m[0])),
                Token('}')) \
            .Map(lambda m: schema.UnionSchema(m[2]))

        separator = TokenRegex(r'[,;]?')

        enum_parser = \
            Seq(Token('enum'), AvroName, Token('{'),
                Rep(Seq(Identifier, separator).Map(lambda m: m[0])),
                Token('}')) \
            .Map(lambda m: schema.EnumSchema(
                name = m[1].simple_name,
                namespace = m[1].namespace,
                names = names,
                symbols = m[3],
            ))

        fixed_parser = \
            Seq(Token('fixed'), AvroName, Token('('), Integer, Token(')')) \
            .Map(lambda m: schema.FixedSchema(
                name = m[1].simple_name,
                namespace = m[1].namespace,
                names = names,
                size = m[3],
            ))

        class _RecordParser(parser.ParserBase):
            """Custom parser for records.

            This parser is custom to allow recursive record definitions.
            """

            def __init__(self):
                self._prefix = Seq(Token('record'), AvroName, Token('{')) \
                    .Map(lambda m: m[1])

            def Parse(self, input):
                result = self._prefix.Parse(input)
                if result.success:
                    record_name = result.value
                    self._field_counter = 0

                    def _MakeRecordFields(names):
                        """Parses and constructs the record fields.

                        Args:
                          names: schema.Names registry with the record registered,
                              in order to allow recursive records.
                        Returns:
                          Ordered collection of schema.Field.
                        """

                        def _MakeField(m):
                            field = schema.Field(
                                type=m[0],
                                name=m[1],
                                index=self._field_counter,
                                has_default=False,
                            )
                            self._field_counter += 1
                            return field

                        field = \
                            Seq(avro_schema, Identifier,
                                Opt(Seq(Token('='), avro_value)),
                                separator) \
                            .Map(_MakeField)

                        fields_parser = Seq(Rep(field),
                                            Token('}')).Map(lambda m: m[0])
                        self._fields_result = fields_parser.Parse(result.next)
                        assert self._fields_result.success, \
                            ('Invalid record definition: %r' % input)
                        return self._fields_result.value

                    record = schema.RecordSchema(
                        name=record_name.simple_name,
                        namespace=record_name.namespace,
                        names=names,
                        make_fields=_MakeRecordFields,
                    )

                    return parser.Success(
                        match=(result.match + self._fields_result.match),
                        next=self._fields_result.next,
                        value=record,
                    )
                else:
                    return result

        record_parser = _RecordParser()

        def _LookupSchemaByName(name):
            """Gets a schema by name.

            Args:
                name: schema.Name object for the schema to retrieve.
            Returns:
                The avro Schema object.
            """
            schema = names.GetSchema(name=name.fullname)
            if schema is None:
                raise Error('No known schema with name: %r' % name.fullname)
            return schema

        schema_by_name = AvroName.Map(_LookupSchemaByName)

        branches = list()
        branches.extend(primitives)
        branches.extend([
            array_parser,
            map_parser,
            union_parser,
            enum_parser,
            fixed_parser,
            record_parser,
            schema_by_name,
        ])

        avro_schema.Bind(parser.Branch(*branches))
        self._parser = avro_schema

    def Parse(self, text):
        """Parses an IDL schema representation into a Schema object.

        Args:
            text: IDL schema representation to parse.
        Returns:
            Parsed Schema object.
        """
        input = parser.Input(text)
        result = self._parser.Parse(input)
        if result.success:
            assert (len(result.next) == 0), ('Input remaining: %r' % result.next)
            return result.value
        raise Error('Invalid schema definition: %r\n%s' % (text, result))


if __name__ == '__main__':
    raise Error('Not a standalone module')
