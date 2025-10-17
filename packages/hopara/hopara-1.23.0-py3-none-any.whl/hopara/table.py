from typing import Union
from hopara.type import ColumnType, TypeParam


class Table:
    """Hopara Table type.
    """
    def __init__(self, name: str, data_source: str = "hopara"):
        """Initialize a table with a name.
        :param name: name of the table.
        :type name: str
        """
        self.name = name
        self.data_source = data_source
        self.__table = {}
        self.__columns = {}

    def get_payload(self) -> dict:
        self.__table['columns'] = [dict(properties, **{'name': name}) for name, properties in self.__columns.items()]
        self.__table['dataSource'] = self.data_source
        return self.__table

    def add_column(self, column_name: str, column_type: ColumnType, type_param: TypeParam = None):
        """Add a new column to the table. If the column already exists, it will be updated.
        :param column_name: name of the column
        :type column_name: str
        :param column_type: type of the column. See more details about these types at hopara.type.ColumnType.
        :type column_type: hopara.type.ColumnType
        :param type_param: subtype of the column. See more details about these types at hopara.type.TypeParam.
        :type type_param: hopara.type.TypeParam
        """
        self.__columns[column_name] = {}
        if column_type:
            self.__columns[column_name]['type'] = column_type.name
            if type_param:
                self.__columns[column_name]['typeParam'] = type_param.name
        if column_name.startswith('_'):
            self.__columns[column_name]['label'] = column_name.lstrip('_')

    def add_columns(self, column_names: list, column_type: ColumnType, type_param: TypeParam = None):
        """Add a list of columns to the table. If the columns already exists, it will be updated.
        :param column_names: list of column names
        :type column_names: list of str
        :param column_type: type of the column. See more details about these types at hopara.type.ColumnType.
        :type column_type: hopara.type.ColumnType
        :param type_param: subtype of the column. See more details about these types at hopara.type.TypeParam.
        :type type_param: hopara.type.TypeParam
        """
        for column_name in column_names:
            self.add_column(column_name, column_type, type_param)

    def __update_column_properties(self, column_name: Union[str, list], properties: dict):
        if isinstance(column_name, str):
            self.__columns[column_name].update(properties)
        else:
            for col_name in column_name:
                self.__columns[col_name].update(properties)

    def set_searchable_columns(self, column_name: Union[str, list]):
        """Set a column as searchable, which means an index will be created to speed up the queries
         :param column_name: column or list of column that must have an index created
         :type column_name: str | list
         """
        self.__update_column_properties(column_name, {'searchable': True})
