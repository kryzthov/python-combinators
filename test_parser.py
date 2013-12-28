#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python -*-

import parser
import unittest


class TestParser(unittest.TestCase):

  def testStr(self):
    p = parser.Str('hello')

    result = p.Parse(parser.Input('failure'))
    self.assertFalse(result.success)
    self.assertEqual('failure', result.next.text)

    result = p.Parse(parser.Input('helloX'))
    self.assertTrue(result.success)
    self.assertEqual('hello', result.match)
    self.assertEqual('X', result.next.text)

  def testOpt(self):
    p = parser.Opt(parser.Str('hello'))

    result = p.Parse(parser.Input('failure'))
    self.assertTrue(result.success)
    self.assertEqual('failure', result.next.text)

    result = p.Parse(parser.Input('helloX'))
    self.assertTrue(result.success)
    self.assertEqual('hello', result.match)
    self.assertEqual('X', result.next.text)

  def testSeq(self):
    p = parser.Seq(parser.Str('hello'), parser.Str('world'))

    result = p.Parse(parser.Input('hello world'))
    self.assertFalse(result.success)
    self.assertEqual('hello world', result.next.text)

    result = p.Parse(parser.Input('hallo world'))
    self.assertFalse(result.success)
    self.assertEqual('hallo world', result.next.text)

    result = p.Parse(parser.Input('helloworld'))
    self.assertTrue(result.success)
    self.assertEqual('helloworld', result.match)
    self.assertEqual('', result.next.text)

    result = p.Parse(parser.Input('helloworldX'))
    self.assertTrue(result.success)
    self.assertEqual('helloworld', result.match)
    self.assertEqual('X', result.next.text)

  def testRep(self):
    p = parser.Rep(parser.Str('x'))

    result = p.Parse(parser.Input('A'))
    self.assertTrue(result.success)
    self.assertEqual(0, len(result.value))
    self.assertEqual('', result.match)
    self.assertEqual('A', result.next.text)

    result = p.Parse(parser.Input('xA'))
    self.assertTrue(result.success)
    self.assertEqual(1, len(result.value))
    self.assertEqual('x', result.match)
    self.assertEqual('A', result.next.text)

    result = p.Parse(parser.Input('xxxxxA'))
    self.assertTrue(result.success)
    self.assertEqual(5, len(result.value))
    self.assertEqual('xxxxx', result.match)
    self.assertEqual('A', result.next.text)

  def testRep1(self):
    p = parser.Rep(parser.Str('x'), nmin=1)

    result = p.Parse(parser.Input('A'))
    self.assertFalse(result.success)
    self.assertEqual('A', result.next.text)

    result = p.Parse(parser.Input('xA'))
    self.assertTrue(result.success)
    self.assertEqual(1, len(result.value))
    self.assertEqual('x', result.match)
    self.assertEqual('A', result.next.text)

    result = p.Parse(parser.Input('xxxxxA'))
    self.assertTrue(result.success)
    self.assertEqual(5, len(result.value))
    self.assertEqual('xxxxx', result.match)
    self.assertEqual('A', result.next.text)

  def testRep1_to_3(self):
    p = parser.Rep(parser.Str('x'), nmin=1, nmax=2)

    result = p.Parse(parser.Input('A'))
    self.assertFalse(result.success)
    self.assertEqual('A', result.next.text)

    result = p.Parse(parser.Input('xA'))
    self.assertTrue(result.success)
    self.assertEqual(1, len(result.value))
    self.assertEqual('x', result.match)
    self.assertEqual('A', result.next.text)

    result = p.Parse(parser.Input('xxA'))
    self.assertTrue(result.success)
    self.assertEqual(2, len(result.value))
    self.assertEqual('xx', result.match)
    self.assertEqual('A', result.next.text)

    result = p.Parse(parser.Input('xxxxxA'))
    self.assertTrue(result.success)
    self.assertEqual(2, len(result.value))
    self.assertEqual('xx', result.match)
    self.assertEqual('xxxA', result.next.text)

  def testRegex(self):
    p = parser.Regex(r'a+')

    result = p.Parse(parser.Input('xaaA'))
    self.assertFalse(result.success)
    self.assertEqual('xaaA', result.next.text)

    result = p.Parse(parser.Input('aaA'))
    self.assertTrue(result.success)
    self.assertEqual('aa', result.match)
    self.assertEqual('A', result.next.text)

  def testBranch(self):
    p = parser.Branch(parser.Str('a'), parser.Str('b'))

    result = p.Parse(parser.Input('aaA'))
    self.assertTrue(result.success)
    self.assertEqual('a', result.match)
    self.assertEqual('aA', result.next.text)

    result = p.Parse(parser.Input('baA'))
    self.assertTrue(result.success)
    self.assertEqual('b', result.match)
    self.assertEqual('aA', result.next.text)

    result = p.Parse(parser.Input('caA'))
    self.assertFalse(result.success)
    self.assertEqual('caA', result.next.text)

  def testInteger(self):
    result = parser.Integer().Parse(parser.Input('-314 is a number'))
    self.assertTrue(result.success)
    self.assertEqual('-314', result.match)
    self.assertEqual(-314, result.value)
    self.assertEqual(' is a number', result.next.text)

    result = parser.Integer(base=2).Parse(parser.Input('11110000 is a number'))
    self.assertTrue(result.success)
    self.assertEqual('11110000', result.match)
    self.assertEqual(0xf0, result.value)
    self.assertEqual(' is a number', result.next.text)

    result = (
        parser.Integer(base=2, prefix='0b')
            .Parse(parser.Input('0b11110000 is a number')))
    self.assertTrue(result.success)
    self.assertEqual('0b11110000', result.match)
    self.assertEqual(0xf0, result.value)
    self.assertEqual(' is a number', result.next.text)

  def testHexInteger(self):
    result = (parser.HexInteger
        .Parse(parser.Input('0x11110000 is a number')))
    self.assertTrue(result.success)
    self.assertEqual('0x11110000', result.match)
    self.assertEqual(0x11110000, result.value)
    self.assertEqual(' is a number', result.next.text)

  def testAllInteger(self):
    result = (parser.AllInteger
        .Parse(parser.Input('0x11110000 is a number')))
    self.assertTrue(result.success)
    self.assertEqual('0x11110000', result.match)
    self.assertEqual(0x11110000, result.value)
    self.assertEqual(' is a number', result.next.text)

  def testSingleQuoteStringLiteral(self):
    result = (parser.SingleQuoteStringLiteral()
        .Parse(parser.Input("'this string' is single-quoted")))
    self.assertTrue(result.success)
    self.assertEqual("'this string'", result.match)
    self.assertEqual('this string', result.value)
    self.assertEqual(' is single-quoted', result.next.text)

  def testDoubleQuoteStringLiteral(self):
    result = (parser.DoubleQuoteStringLiteral()
        .Parse(parser.Input('"this string" is double-quoted')))
    self.assertTrue(result.success)
    self.assertEqual('"this string"', result.match)
    self.assertEqual('this string', result.value)
    self.assertEqual(' is double-quoted', result.next.text)

  def testTripeQuoteStringLiteral(self):
    result = (parser.TripleQuoteStringLiteral()
        .Parse(parser.Input('"""this "\n string""" is triple """ quoted')))
    self.assertTrue(result.success)
    self.assertEqual('"""this "\n string"""', result.match)
    self.assertEqual('this "\n string', result.value)
    self.assertEqual(' is triple """ quoted', result.next.text)



if __name__ == '__main__':
  unittest.main()
