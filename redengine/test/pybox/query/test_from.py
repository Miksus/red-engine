
import pytest
from redengine.pybox import query

@pytest.mark.parametrize('qry_dict,data,expected',
    [
        pytest.param(
            {
                'mykey$min': 10,
                'mykey$max': 20,
            },
            [{'mykey': 5}, {'mykey': 30}, {'mykey': 15}, {'mykey': 10}, {'mykey': 20}],
            [{'mykey': 15}, {'mykey': 10}, {'mykey': 20}],
            id='min-max'
        ),
        pytest.param(
            {
                'mykey': 10,
            },
            [{'mykey': 5}, {'mykey': 30}, {'mykey': 15}, {'mykey': 10}, {'mykey': 20}],
            [{'mykey': 10}],
            id='equal'
        ),
        pytest.param(
            {
                'mykey$not': 10,
            },
            [{'mykey': 5}, {'mykey': 30}, {'mykey': 15}, {'mykey': 10}, {'mykey': 20}],
            [{'mykey': 5}, {'mykey': 30}, {'mykey': 15}, {'mykey': 20}],
            id='not-equal'
        ),
        pytest.param(
            {
                'mykey$regex': '.+ or .+',
            },
            [{'mykey': 'foo or bar'}, {'mykey': 'bar or foo'}, {'mykey': ''}, {'mykey': 'foo and bar'}],
            [{'mykey': 'foo or bar'}, {'mykey': 'bar or foo'}],
            id='regex'
        ),
    ]
)
def test_from_dict_string(qry_dict, data, expected):
    qry = query.parser.from_dict(qry_dict)
    actual = qry.filter(data)
    assert list(actual) == expected


@pytest.mark.parametrize('qry_dict,data,expected',
    [
        pytest.param(
            [
                ('mykey$min', 10),
                ('mykey$max', 20),
            ],
            [{'mykey': 5}, {'mykey': 30}, {'mykey': 15}, {'mykey': 10}, {'mykey': 20}],
            [{'mykey': 15}, {'mykey': 10}, {'mykey': 20}],
            id='min-max'
        ),
        pytest.param(
            [
                ('mykey', 10),
            ],
            [{'mykey': 5}, {'mykey': 30}, {'mykey': 15}, {'mykey': 10}, {'mykey': 20}],
            [{'mykey': 10}],
            id='equal'
        ),
        pytest.param(
            [
                ('mykey$not', 10),
            ],
            [{'mykey': 5}, {'mykey': 30}, {'mykey': 15}, {'mykey': 10}, {'mykey': 20}],
            [{'mykey': 5}, {'mykey': 30}, {'mykey': 15}, {'mykey': 20}],
            id='not-equal'
        ),
        pytest.param(
            [
                ('mykey$regex', '.+ or .+'),
            ],
            [{'mykey': 'foo or bar'}, {'mykey': 'bar or foo'}, {'mykey': ''}, {'mykey': 'foo and bar'}],
            [{'mykey': 'foo or bar'}, {'mykey': 'bar or foo'}],
            id='regex'
        ),
        pytest.param(
            [
                ('mykey', 'bad'),
                ('mykey', 'good'),
            ],
            [{'mykey': 'bad'}, {'mykey': 'neutral'}, {'mykey': 'good'}],
            [{'mykey': 'bad'}, {'mykey': 'good'}],
            id='in'
        ),
        pytest.param(
            [
                ('mykey1', 'bad'),
                ('mykey1', 'good'),
                ('mykey2', 'happy'),
            ],
            [{'mykey1': 'bad', 'mykey2': 'sad'}, {'mykey1': 'neutral', 'mykey2': 'happy'}, {'mykey1': 'good', 'mykey2': 'happy'}],
            [{'mykey1': 'good', 'mykey2': 'happy'}],
            id='combined'
        ),
    ]
)
def test_from_tuples(qry_dict, data, expected):
    qry = query.parser.from_tuples(qry_dict)
    actual = qry.filter(data)
    assert list(actual) == expected


@pytest.mark.parametrize('qry_kwargs,data,expected',
    [
        pytest.param(
            {'mykey': (10, 15)},
            [{'mykey': 5}, {'mykey': 10}, {'mykey': 12}, {'mykey': 15}, {'mykey': 30}],
            [{'mykey': 10}, {'mykey': 12}, {'mykey': 15}],
            id='min-max'
        ),
        pytest.param(
            {'mykey': (10, None)},
            [{'mykey': 5}, {'mykey': 10}, {'mykey': 12}, {'mykey': 15}, {'mykey': 30}],
            [{'mykey': 10}, {'mykey': 12}, {'mykey': 15}, {'mykey': 30}],
            id='min'
        ),
        pytest.param(
            {'mykey': (None, 15)},
            [{'mykey': 5}, {'mykey': 10}, {'mykey': 12}, {'mykey': 15}, {'mykey': 30}],
            [{'mykey': 5}, {'mykey': 10}, {'mykey': 12}, {'mykey': 15}],
            id='max'
        ),
        pytest.param(
            {'mykey': ['good', 'bad']},
            [{'mykey': 'good'}, {'mykey': 'bad'}, {'mykey': 'ugly'}],
            [{'mykey': 'good'}, {'mykey': 'bad'}],
            id='in'
        ),
    ]
)
def test_from_kwargs(qry_kwargs, data, expected):
    qry = query.parser.from_kwargs(**qry_kwargs)
    actual = qry.filter(data)
    assert list(actual) == expected