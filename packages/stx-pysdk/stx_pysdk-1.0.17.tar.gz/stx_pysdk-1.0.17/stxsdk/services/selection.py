class Selection:
    """
    This is plain class for setting args as values and kwargs as nested_values
    The selection object is used to auto generate schema fields for user without
    the user interaction with schema fields
    """

    def __init__(self, *args, **kwargs):
        self.values = args
        self.nested_values = kwargs
