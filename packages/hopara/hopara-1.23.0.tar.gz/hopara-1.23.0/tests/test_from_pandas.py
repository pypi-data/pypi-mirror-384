import unittest
from datetime import datetime
import pandas as pd
from hopara.from_pandas import get_table, get_rows


class FromPandasCase(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({'int': [1, 2, 3],
                                'str': ['a', 'b', 'c'],
                                'float': [1.2, 1.5, 1.7],
                                'bool': [True, False, False],
                                'datetime': [datetime(2022, 1, 7), datetime(2022, 4, 6), datetime(2022, 1, 23)]
                                })

    def test_get_table(self):
        table = get_table('from_pandas_test_table', self.df)
        columns = table.get_payload()['columns']
        self.assertListEqual(columns,[{'type': 'INTEGER', 'name': 'int'},
                                      {'type': 'STRING', 'name': 'str'},
                                      {'type': 'DECIMAL', 'name': 'float'},
                                      {'type': 'BOOLEAN', 'name': 'bool'},
                                      {'type': 'DATETIME', 'name': 'datetime'}])

    def test_get_rows(self):
        rows = get_rows(self.df)
        for row in rows:
            row['datetime'] = row['datetime'].rstrip('Z')
        self.assertListEqual(rows, [
            {'int': 1, 'str': 'a', 'float': 1.2, 'bool': True, 'datetime': '2022-01-07T00:00:00.000'},
            {'int': 2, 'str': 'b', 'float': 1.5, 'bool': False, 'datetime': '2022-04-06T00:00:00.000'},
            {'int': 3, 'str': 'c', 'float': 1.7, 'bool': False, 'datetime': '2022-01-23T00:00:00.000'}
        ])


if __name__ == '__main__':
    unittest.main()
