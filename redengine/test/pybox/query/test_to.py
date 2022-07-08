
import pytest
from redengine.pybox import query

@pytest.mark.parametrize('qry_dict,expected',
    [
        pytest.param(
            {
                'mykey$min': 10,
                'mykey$max': 20,
            },
            {'mykey': (10, 20)},
            id='min-max'
        ),
        pytest.param({'mykey': 10}, {'mykey': 10}, id='equal'),
        pytest.param({'mykey$min': 10}, {'mykey': (10, None)}, id='min'),
        pytest.param({'mykey$max': 10}, {'mykey': (None, 10)}, id='max'),
        pytest.param({'mykey1$min': 10, 'mykey1$max': 20, 'mykey2': 30}, {'mykey1': (10, 20), 'mykey2': 30}, id='combined'),
        pytest.param({}, {}, id='none'),
    ]
)
def test_to_pynative(qry_dict, expected):
    qry = query.from_dict_string(qry_dict)
    kwargs = qry.to_pykwargs()
    assert kwargs == expected