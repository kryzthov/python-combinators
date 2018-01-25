#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python -*-

import clr
import unittest


class TestRuntime(unittest.TestCase):
    def test_basic(self):
        rec = clr.Record(
            x=clr.Immediate(1),
            y=clr.BinOp(lambda x, y: x+y, clr.Ref('x'), clr.Immediate(1)),
        )
        try:
            rec.get('a')
            self.fail()
        except KeyError:
            pass

        self.assertEqual(1, rec.get('x'))
        self.assertEqual(2, rec.get('y'))
        self.assertEqual({'x': 1, 'y': 2}, rec.export())

    def test_add_record(self):
        rec1 = clr.Record(
            x=clr.Immediate(1),
            y=clr.BinOp(lambda x, y: x+y, clr.Ref('x'), clr.Immediate(1)),
        )
        rec2 = clr.Record(
            x=clr.Immediate(2),
        )
        rec3 = rec1 + rec2
        self.assertEqual({'x': 1, 'y': 2}, rec1.export())
        self.assertEqual({'x': 2}, rec2.export())
        self.assertEqual({'x': 2, 'y': 3}, rec3.export())

    def test_nested_record(self):
        nested = clr.Record(
            x=clr.Immediate(1),
        )

        rec = clr.Record(
            nested=nested,
            y=clr.BinOp(lambda x, y: x+y,
                        clr.FieldAccess(clr.Ref('nested'), clr.Immediate('x')),
                        clr.Immediate(1)),
        )
        self.assertEqual(2, rec.get('y'))
        self.assertEqual({'nested': {'x': 1}, 'y': 2}, rec.export())



if __name__ == '__main__':
    unittest.main()
