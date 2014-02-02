#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python -*-

"""Tests for the Avro schema and value definition parser."""

import logging
import parser
import unittest
import sys

from base import base

from avro import schema


import avro_parser


class TestAvroParser(unittest.TestCase):
  """Tests for AvroParser."""

  def setUp(self):
    self._parser = avro_parser.AvroParser()

  def testAvroName(self):
    result = avro_parser.AvroName.Parse(parser.Input('.ns.comp.Name'))
    self.assertTrue(result.success)
    name = result.value
    self.assertEqual('ns.comp', name.namespace)
    self.assertEqual('Name', name.simple_name)

    result = avro_parser.AvroName.Parse(parser.Input('ns.comp.Name'))
    self.assertTrue(result.success)
    name = result.value
    self.assertEqual('ns.comp', name.namespace)
    self.assertEqual('Name', name.simple_name)

    result = avro_parser.AvroName.Parse(parser.Input('.Name'))
    self.assertTrue(result.success)
    name = result.value
    self.assertEqual('', name.namespace)
    self.assertEqual('Name', name.simple_name)

    result = avro_parser.AvroName.Parse(parser.Input('Name'))
    self.assertTrue(result.success)
    name = result.value
    self.assertEqual('', name.namespace)  # FIXME??
    self.assertEqual('Name', name.simple_name)

  def testPrimitive(self):
    parsed = self._parser.Parse('int')
    logging.info('Parsed schema: %s', parsed.ToIDLString())
    self.assertEqual(schema.INT, parsed.type)

  def testArray(self):
    parsed = self._parser.Parse('array<int>')
    logging.info('Parsed schema: %s', parsed.ToIDLString())
    self.assertEqual(schema.ARRAY, parsed.type)
    self.assertEqual(schema.INT, parsed.items.type)

  def testDefWithSpaces(self):
    parsed = self._parser.Parse('array < int >')
    logging.info('Parsed schema: %s', parsed.ToIDLString())
    self.assertEqual(schema.ARRAY, parsed.type)
    self.assertEqual(schema.INT, parsed.items.type)

  def testDefWithComments(self):
    parsed = self._parser.Parse('array < /* comment*/ int >')
    logging.info('Parsed schema: %s', parsed.ToIDLString())
    self.assertEqual(schema.ARRAY, parsed.type)
    self.assertEqual(schema.INT, parsed.items.type)

  def testMap(self):
    parsed = self._parser.Parse('map<array<int>>')
    logging.info('Parsed schema: %s', parsed.ToIDLString())
    self.assertEqual(schema.MAP, parsed.type)
    self.assertEqual(schema.ARRAY, parsed.values.type)
    self.assertEqual(schema.INT, parsed.values.items.type)

  def testUnion(self):
    parsed = self._parser.Parse('union { null, string, int, float }')
    logging.info('Parsed schema: %s', parsed.ToIDLString())
    self.assertEqual(schema.UNION, parsed.type)
    self.assertEqual(schema.NULL, parsed.schemas[0].type)
    self.assertEqual(schema.STRING, parsed.schemas[1].type)
    self.assertEqual(schema.INT, parsed.schemas[2].type)
    self.assertEqual(schema.FLOAT, parsed.schemas[3].type)

  def testRecord(self):
    parsed = self._parser.Parse('record ns.Rec { int x; float y double t }')
    logging.info('Parsed schema: %s', parsed.ToIDLString())
    self.assertEqual(schema.RECORD, parsed.type)

  def testEnum(self):
    parsed = self._parser.Parse('enum ns.Enum { Symbol1, Symbol2 }')
    logging.info('Parsed schema: %s', parsed.ToIDLString())
    self.assertEqual(schema.ENUM, parsed.type)
    self.assertEqual(('Symbol1', 'Symbol2'), parsed.symbols)

  def testFixed(self):
    parsed = self._parser.Parse('fixed ns.MD5(16)')
    logging.info('Parsed schema: %s', parsed.ToIDLString())
    self.assertEqual(schema.FIXED, parsed.type)

  def testComposed(self):
    parsed = self._parser.Parse(base.StripMargin("""
        |record ns.Record {
        |  int x;
        |  enum ns.Enum { Sym1, Sym2 } enum_field;
        |}""")
    )
    logging.info('Parsed schema: %s', parsed.ToIDLString())
    self.assertEqual(schema.RECORD, parsed.type)

  def testRecursiveRecord(self):
    parsed = self._parser.Parse(base.StripMargin("""
        |record IntList {
        |  int head;
        |  union { null, IntList } tail;
        |}""")
    )
    # logging.info('Parsed schema: %s', parsed.ToIDLString())
    logging.info('Parsed schema: %s', parsed.to_json())
    self.assertEqual(schema.RECORD, parsed.type)


def Main(args):
  args = list(args)
  args.insert(0, sys.argv[0])
  unittest.main(argv=args)


if __name__ == '__main__':
  base.Run(Main)
