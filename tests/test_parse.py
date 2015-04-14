#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_parse
----------------------------------

Tests for `parse` module.
"""

from collections import OrderedDict
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
        self.assertEqual(self.cs.recv(), ['foo', 'bar'])
        self.assertEqual([], self.cs.recv())


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
        changes = list(parse.parse(bundle, handler=self.handler1))
        self.assertEqual(
            [
                (1, 0),
                (1, 1),
                (1, 2),
                (2, 0),
                (2, 1),
                (2, 2),
            ],
            changes,
        )


class TestHandleServices(unittest.TestCase):

    def test_handler(self):
        cs = parse.ChangeSet({
            # Use an ordered dict so that changes' ids can be predicted
            # deterministically.
            'services': OrderedDict((
                ('django', {
                    'charm': 'cs:trusty/django-42',
                }),
                ('mysql-master', {
                    'charm': 'cs:utopic/mysql-47',
                }),
                ('mysql-slave', {
                    'charm': 'cs:utopic/mysql-47',
                    'options': {
                        'key1': 'value1',
                        'key2': 'value2',
                    }
                }),
            ))
        })
        handler = parse.handle_services(cs)
        self.assertEqual(parse.handle_machines, handler)
        self.assertEqual(
            [
                {
                    'id': 'addCharm-0',
                    'method': 'addCharm',
                    'args': ['cs:trusty/django-42'],
                    'requires': []
                },
                {
                    'id': 'addService-1',
                    'method': 'deploy',
                    'args': ['cs:trusty/django-42', 'django', {}],
                    'requires': ['addCharm-0']
                },
                {
                    'id': 'addCharm-2',
                    'method': 'addCharm',
                    'args': ['cs:utopic/mysql-47'],
                    'requires': []
                },
                {
                    'id': 'addService-3',
                    'method': 'deploy',
                    'args': ['cs:utopic/mysql-47', 'mysql-master', {}],
                    'requires': ['addCharm-2']
                },
                {
                    'id': 'addService-4',
                    'method': 'deploy',
                    'args': ['cs:utopic/mysql-47', 'mysql-slave', {
                        'key1': 'value1',
                        'key2': 'value2',
                    }],
                    'requires': ['addCharm-2']
                },
            ],
            cs.recv())

    def test_no_services(self):
        cs = parse.ChangeSet({'services': {}})
        parse.handle_services(cs)
        self.assertEqual([], cs.recv())


class TestHandleMachines(unittest.TestCase):

    def test_handler(self):
        cs = parse.ChangeSet({
            # Use an ordered dict so that changes' ids can be predicted
            # deterministically.
            'machines': OrderedDict((
                ('1', {'series': 'vivid'}),
                ('2', {}),
                ('42', {'constraints': {'cpu-cores': 4}}),
            ))
        })
        handler = parse.handle_machines(cs)
        self.assertEqual(parse.handle_units, handler)
        self.assertEqual(
            [
                {
                    'id': 'addMachine-0',
                    'method': 'addMachine',
                    'args': ['vivid', {}],
                    'requires': []
                },
                {
                    'id': 'addMachine-1',
                    'method': 'addMachine',
                    'args': ['', {}],
                    'requires': []
                },
                {
                    'id': 'addMachine-2',
                    'method': 'addMachine',
                    'args': ['', {'cpu-cores': 4}],
                    'requires': []
                },
            ],
            cs.recv())

    def test_no_machines(self):
        cs = parse.ChangeSet({'services': {}})
        parse.handle_machines(cs)
        self.assertEqual([], cs.recv())
