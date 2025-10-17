class View:
    """Hopara View type.
    """
    def __init__(self, name: str, data_source: str = "hopara"):
        """Initialize a table with a name.
        :param name: name of the table.
        :type name: str
        """
        self.name = name
        self.data_source = data_source