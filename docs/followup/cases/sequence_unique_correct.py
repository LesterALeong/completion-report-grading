def unique_preserving_order(values):
    return [value for index, value in enumerate(values) if value not in values[:index]]
