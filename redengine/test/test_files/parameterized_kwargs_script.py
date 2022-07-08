

def main(**kwargs):
    assert {} != kwargs
    assert isinstance(kwargs['integer'], int)
    assert isinstance(kwargs['string'], str)
    assert isinstance(kwargs['optional_float'], float)