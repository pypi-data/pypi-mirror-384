import io
import unittest
from unittest.mock import MagicMock, patch, ANY
import logging

import pandas as pd

from hopara.hopara import Hopara
from hopara.table import Table


logging.getLogger('pyhopara').setLevel(logging.WARNING)


class HoparaCase(unittest.TestCase):
    def setUp(self):
        self.hopara = Hopara()
        self.hopara.config = MagicMock()
        self.hopara.config.get_dataset_url = lambda: 'https://test.hopara.py/'
        self.hopara.config.get_resource_url = lambda: 'https://resource.test.hopara.py/'
        self.hopara.request = MagicMock()

    def test_urls(self):
        self.assertEqual(self.hopara.get_table_url(Table('table1')),
                         r"https://test.hopara.py/table/table1/")
        self.assertEqual(self.hopara.get_row_url(Table('table1')),
                         r"https://test.hopara.py/table/table1/row?dataSource=hopara")

    def test_upload_resource_from_memory(self):
        self.hopara.upload_resource_from_memory(io.BytesIO(b'any image buffer'), 'image', 'any_name', 'any_library')
        self.hopara.request.put.assert_called_with(
            'https://resource.test.hopara.py/tenant/hopara.io/image-library/any_library/image/any_name', None,
            {'file': ANY})

        self.hopara.upload_resource_from_memory(io.BytesIO(b'any icon buffer'), 'icon', 'any_name', 'any_library')
        self.hopara.request.put.assert_called_with(
            'https://resource.test.hopara.py/tenant/hopara.io/icon-library/any_library/icon/any_name', None,
            {'file': ANY})

        self.hopara.upload_resource_from_memory(io.BytesIO(b'any model buffer'), 'model', 'any_name', None)
        self.hopara.request.put.assert_called_with(
            'https://resource.test.hopara.py/tenant/hopara.io/model/any_name', None, {'file': ANY})

    def test_execute_query(self):
        df_rows = self.hopara.execute_query('test_query', 'test_data_source')
        self.hopara.request.get.assert_called_with(
            'https://test.hopara.py/view/test_query/row?dataSource=test_data_source', {})
        self.assertTrue(isinstance(df_rows, pd.DataFrame))


if __name__ == '__main__':
    unittest.main()
