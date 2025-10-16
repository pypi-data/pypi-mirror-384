def get_all_subclasses(cls):
    """
    Recursively get all subclasses of a given class.
    """
    subclasses = set(cls.__subclasses__())
    for subclass in cls.__subclasses__():
        subclasses.update(get_all_subclasses(subclass))
    return subclasses
