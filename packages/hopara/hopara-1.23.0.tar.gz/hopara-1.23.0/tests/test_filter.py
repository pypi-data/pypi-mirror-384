import unittest

from hopara.filter import Filter


class FilterCase(unittest.TestCase):
    def test_filter_json(self):
        self.assertDictEqual(Filter("column1") <= [1, 2, 3],
                             {'column': 'column1', 'comparisonType': 'LESS_EQUALS_THAN', 'values': [1, 2, 3]})
        self.assertDictEqual(Filter("column1") < [1, 2, 3],
                             {'column': 'column1', 'comparisonType': 'LESS_THAN', 'values': [1, 2, 3]})
        self.assertDictEqual(Filter("column1") >= [1, 2, 3],
                             {'column': 'column1', 'comparisonType': 'GREATER_EQUALS_THAN', 'values': [1, 2, 3]})
        self.assertDictEqual(Filter("column1") > [1, 2, 3],
                             {'column': 'column1', 'comparisonType': 'GREATER_THAN', 'values': [1, 2, 3]})
        self.assertDictEqual(Filter("column1") == [1, 2, 3],
                             {'column': 'column1', 'comparisonType': 'EQUALS', 'values': [1, 2, 3]})

    def test_filter_with_no_list_of_values(self):
        self.assertDictEqual(Filter("column1") <= 123,
                             {'column': 'column1', 'comparisonType': 'LESS_EQUALS_THAN', 'values': [123]})
