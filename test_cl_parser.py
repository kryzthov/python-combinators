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



def main(args):
    args = list(args)
    args.insert(0, sys.argv[0])
    unittest.main(argv=args)


if __name__ == '__main__':
    base.run(main)
