def assert_error(expected: float, actual: float, error: float):
    min_range = expected * (1-error)
    max_range = expected * (1+error)
    assert min_range < actual < max_range, f"{min_range=} < {actual=} < {max_range}"