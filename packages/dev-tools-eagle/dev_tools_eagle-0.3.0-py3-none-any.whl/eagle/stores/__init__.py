
def get_store_class(store_type: str):
    """
    Get the store class based on the store type.
    """
    from eagle.stores.opensearch import OpenSearchStore

    stores = {
        "opensearch": OpenSearchStore
    }

    try:
        return stores.get(store_type)
    except KeyError:
        raise ValueError(f"Store type '{store_type}' not found. Available types: {', '.join(stores)}")