#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python -*-
"""Tests for the Avro schema and value definition parser."""

import logging
import parser
import unittest
import sys

from base import base

import parser
import cl_parser


class TestRecordParser(unittest.TestCase):
    """Tests for CL parsers."""

    def test_empty_record(self):
        result = cl_parser.Record.Parse(parser.Input('{}'))
        self.assertTrue(result.success)
        self.assertEqual({}, result.value.export())

    def test_singleton(self):
        result = cl_parser.Record.Parse(parser.Input('{x = 1}'))
        self.assertTrue(result.success)
        self.assertEqual({'x': 1}, result.value.export())

    def test_singleton_type(self):
        result = cl_parser.Record.Parse(parser.Input('{x: type = 1}'))
        self.assertTrue(result.success)
        self.assertEqual({'x': 1}, result.value.export())

    def test_two_fields_no_sep(self):
        result = cl_parser.Record.Parse(parser.Input('{x = 1 y = 2}'))
        self.assertTrue(result.success)
        self.assertEqual({'x': 1, 'y': 2}, result.value.export())

    def test_two_fields_comma_sep(self):
        result = cl_parser.Record.Parse(parser.Input('{x = 1, y = 2}'))
        self.assertTrue(result.success)
        self.assertEqual({'x': 1, 'y': 2}, result.value.export())

    def test_two_fields_semicolon_sep(self):
        result = cl_parser.Record.Parse(parser.Input('{x = 1; y = 2;}'))
        self.assertTrue(result.success)
        self.assertEqual({'x': 1, 'y': 2}, result.value.export())

    def test_ref_field(self):
        result = cl_parser.Record.Parse(parser.Input('{x = 1; y = x;}'))
        self.assertTrue(result.success)
        self.assertEqual({'x': 1, 'y': 1}, result.value.export())

    def test_paren_expr(self):
        result = cl_parser.Record.Parse(parser.Input('{x = (2); y = x;}'))
        self.assertTrue(result.success)
        self.assertEqual({'x': 2, 'y': 2}, result.value.export())

    def test_bin_expr(self):
        result = cl_parser.Record.Parse(parser.Input('{x = 1 + 2 ** 3 * 3}'))
        self.assertTrue(result.success)
        self.assertEqual({'x': 25}, result.value.export())

    def test_bin_expr_paren(self):
        result = cl_parser.Record.Parse(parser.Input('{x = (3 - 1) ** 3}'))
        self.assertTrue(result.success)
        self.assertEqual({'x': 8}, result.value.export())

    def test_if_expr(self):
        result = cl_parser.Record.Parse(parser.Input('{x = true, y = if x then 5 else 10}'))
        self.assertTrue(result.success)
        self.assertEqual({'x': True, 'y': 5}, result.value.export())

    def test_unary_expr(self):
        result = cl_parser.Record.Parse(parser.Input('{x = true, y = not x, a = 1, b = -a}'))
        self.assertTrue(result.success)
        self.assertEqual({'x': True, 'y': False, 'a': 1, 'b': -1}, result.value.export())

    def test_nested_record(self):
        result = cl_parser.Record.Parse(parser.Input("""
        {
            x = {
                a = 1
                b = 3*a
            }
            y = x.a
        }
        """))
        self.assertTrue(result.success)
        self.assertEqual({'x': {'a': 1, 'b': 3}, 'y': 1}, result.value.export())

    def test_list(self):
        result = cl_parser.Record.Parse(parser.Input("""
        {
            empty = []
            singleton = [1]
            singleton2 = [1+1,]
            double = [1, 2]
            double2 = [1, 2,]
        }
        """))
        self.assertTrue(result.success)
        self.assertEqual(
            {
                'empty': [],
                'singleton': [1],
                'singleton2': [2],
                'double': [1, 2],
                'double2': [1, 2],
            },
            result.value.export())


    def test_call(self):
        result = cl_parser.Record.Parse(parser.Input("""
        {
            x = {
                z = y + 1
            }
            y = x(y=2)
        }
        """))
        self.assertTrue(result.success)
        self.assertEqual({'y': 2, 'z': 3}, result.value.get("y").export())

    def test_factorial(self):
        result = cl_parser.Record.Parse(parser.Input("""
        {
            fact = {
                result = if n <= 1 then 1 else n * fact(n=n-1, fact=fact).result
            }

            f0 = fact(n=0, fact=fact).result
            f1 = fact(n=1, fact=fact).result
            f2 = fact(n=2, fact=fact).result
            f3 = fact(n=3, fact=fact).result
            f10 = fact(n=10, fact=fact).result
        }
        """))
        self.assertTrue(result.success)
        self.assertEqual(1, result.value.get("f0"))
        self.assertEqual(1, result.value.get("f1"))
        self.assertEqual(2, result.value.get("f2"))
        self.assertEqual(6, result.value.get("f3"))
        self.assertEqual(3628800, result.value.get("f10"))

    def test_fibo(self):
        result = cl_parser.Record.Parse(parser.Input("""
        {
            fibo = {
                result = if (n <= 1) then 1 else fibo(n=n-1, fibo=fibo).result + fibo(n=n-2, fibo=fibo).result
            }

            f10 = fibo(n=10, fibo=fibo).result
        }
        """))
        self.assertTrue(result.success)
        self.assertEqual(89, result.value.get("f10"))


def main(args):
    args = list(args)
    args.insert(0, sys.argv[0])
    unittest.main(argv=args)


if __name__ == '__main__':
    base.run(main)
