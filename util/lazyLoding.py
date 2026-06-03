def lazy_schema(factory):
    cached = None

    def inner():
        nonlocal cached
        if cached is None:
            cached = factory()
        return cached

    return inner