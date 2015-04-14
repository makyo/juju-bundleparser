#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_parse
----------------------------------

Tests for `parse` module.
"""

import unittest

from bundleparser import parse


class TestParsePlacements(unittest.TestCase):

    def test_parse_v3(self):
        self.assertEqual(
            parse._parse_v3_unit_placement(''),
            parse.UnitPlacement('', '', '', ''),
        )
        self.assertEqual(
            parse._parse_v3_unit_placement('0'),
            parse.UnitPlacement('', '0', '', ''),
        )
        self.assertEqual(
            parse._parse_v3_unit_placement('mysql'),
            parse.UnitPlacement('', '', 'mysql', ''),
        )
        self.assertEqual(
            parse._parse_v3_unit_placement('lxc:0'),
            parse.UnitPlacement('lxc', '0', '', ''),
        )
        self.assertEqual(
            parse._parse_v3_unit_placement('mysql=1'),
            parse.UnitPlacement('', '', 'mysql', '1'),
        )
        self.assertEqual(
            parse._parse_v3_unit_placement('lxc:mysql=1'),
            parse.UnitPlacement('lxc', '', 'mysql', '1'),
        )

    def test_parse_v4(self):
        self.assertEqual(
            parse._parse_v4_unit_placement(''),
            parse.UnitPlacement('', '', '', ''),
        )
        self.assertEqual(
            parse._parse_v4_unit_placement('0'),
            parse.UnitPlacement('', '0', '', ''),
        )
        self.assertEqual(
            parse._parse_v4_unit_placement('mysql'),
            parse.UnitPlacement('', '', 'mysql', ''),
        )
        self.assertEqual(
            parse._parse_v4_unit_placement('lxc:0'),
            parse.UnitPlacement('lxc', '0', '', ''),
        )
        self.assertEqual(
            parse._parse_v4_unit_placement('mysql/1'),
            parse.UnitPlacement('', '', 'mysql', '1'),
        )
        self.assertEqual(
            parse._parse_v4_unit_placement('lxc:mysql/1'),
            parse.UnitPlacement('lxc', '', 'mysql', '1'),
        )


class TestChangeSet(unittest.TestCase):

    def setUp(self):
        self.cs = parse.ChangeSet({
            'services': {},
            'machines': {},
            'relations': {},
            'series': 'trusty',
        })

    def test_send_receive(self):
        self.cs.send('foo')
        self.cs.send('bar')
        self.assertEqual(self.cs._changeset, ['foo', 'bar'])
        self.assertEqual(self.cs.recv(), ['foo', 'bar'])
        self.assertEqual(self.cs._changeset, [])


class TestParse(unittest.TestCase):

    def handler1(self, changeset):
        for i in range(3):
            changeset.send((1, i))
        return self.handler2

    def handler2(self, changeset):
        for i in range(3):
            changeset.send((2, i))
        return None

    def test_parse(self):
        bundle = {
            'services': {},
            'machines': {},
            'relations': {},
            'series': 'trusty',
        }
        accumulated = []
        for i in parse.parse(bundle, handler=self.handler1):
            accumulated.append(i)
        self.assertEqual(
            accumulated,
            [
                (1, 0),
                (1, 1),
                (1, 2),
                (2, 0),
                (2, 1),
                (2, 2),
            ]
        )

if __name__ == '__main__':
    unittest.main()
