import unittest

import pandas as pd

from hopara.table import Table, ColumnType, TypeParam
from hopara.from_pandas import get_table


class TableCase(unittest.TestCase):
    def setUp(self):
        self.data = {'a': [1, 2, 3],
                     'b': ['a', 'b', 'c'],
                     'c': [1.2, 1.5, 1.7],
                     'd': ['aa', 'bb', 'cc']}
        self.expected_body = {'columns': [{'name': 'a', 'type': 'INTEGER'},
                                            {'name': 'b', 'type': 'STRING'},
                                            {'name': 'c', 'type': 'JSON'},
                                            {'name': 'd', 'type': 'STRING'}],
                              'dataSource': 'hopara'}

    def test_create_table_with_pandas_df(self):
        df = pd.DataFrame(self.data)

        table = get_table('table1', df)
        table.add_column('c', ColumnType.JSON)

        self.assertDictEqual(self.expected_body, table.get_payload())
        self.assertDictEqual(self.expected_body, table.get_payload())

    def test_create_table_manually(self):
        table = Table('table1')
        table.add_column('a', ColumnType.INTEGER)
        table.add_column('b', ColumnType.STRING)
        table.add_column('c', ColumnType.JSON)
        table.add_column('d', ColumnType.STRING)

        self.assertDictEqual(self.expected_body, table.get_payload())

    def test_add_column_checking_column_type(self):
        table = Table('table1')
        table.add_column('a', ColumnType.INTEGER)
        table.add_column('a', None)
        self.assertRaises(AttributeError, table.add_column, 'a', 'INVALID')

    def test_add_column_with_type_param(self):
        table = Table('table1')
        table.add_columns(['a', 'b'], ColumnType.GEOMETRY, TypeParam.GEOMETRY.LINESTRING)
        self.assertListEqual([{'name': 'a', 'type': 'GEOMETRY', 'typeParam': 'LINESTRING'},
                              {'name': 'b', 'type': 'GEOMETRY', 'typeParam': 'LINESTRING'}],
                             table.get_payload()['columns'])
