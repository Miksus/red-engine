
import pytest
import pandas as pd
from redengine.pybox import query

@pytest.mark.parametrize('qry,data,expected',
    [
        pytest.param(
            query.Key('mykey') == 10,
            [
                {'mykey': 5},
                {'mykey': 10},
                {'mykey': 11},
            ],
            [{'mykey': 10}],
            id="equal"
        ),
        pytest.param(
            query.Key('mydate') == '2021-01-01',
            [
                {'mydate': pd.Timestamp('2020-12-31')},
                {'mydate': pd.Timestamp('2021-01-01')},
                {'mydate': pd.Timestamp('2020-01-02')},
            ],
            [{'mydate': pd.Timestamp('2021-01-01')}],
            id="string to datetime"
        ),
    ]
)
def test_filter(qry, data, expected):
    assert list(qry.filter(data)) == expected