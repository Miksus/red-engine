
import pytest
from redengine.pybox import query

def test_str_statement():
    qry = query.parser.from_dict({
        'mydate$min': '2021-07-01',
        'mydate$max': '2021-07-15',
        'mykey1': 10,
        'mystring$regex': r'all of .+',
        'mykey2$not': 'not this',
    })
    assert str(qry) == "((<mydate> >= '2021-07-01') & (<mydate> <= '2021-07-15') & (<mykey1> == 10) & re.match('all of .+', <mystring>) & (<mykey2> != 'not this'))"

@pytest.mark.parametrize('obj,expected',
    [
        pytest.param(query.Any(query.Key('mykey1') == 1, query.Key('mykey2') == 2), '((<mykey1> == 1) | (<mykey2> == 2))', id="any"),
        pytest.param(query.All(query.Key('mykey1') != 1, query.Key('mykey2') != 2), '((<mykey1> != 1) & (<mykey2> != 2))', id="all"),
        pytest.param(query.Key('mykey') < 1, '(<mykey> < 1)', id="less"),
        pytest.param(query.Key('mykey') <= 1, '(<mykey> <= 1)', id="less equal"),
        pytest.param(query.Key('mykey') > 1, '(<mykey> > 1)', id="greater"),
        pytest.param(query.Key('mykey') >= 1, '(<mykey> >= 1)', id="greater equal"),
        pytest.param(~(query.Key('mykey') == 1), '~(<mykey> == 1)', id="not"),
        pytest.param(query.Regex(query.Key('mykey'), r'.+ is good'), "re.match('.+ is good', <mykey>)", id="regex"),
    ]
)
def test_expr(obj, expected):
    assert str(obj) == expected

@pytest.mark.parametrize('obj,data,expected',
    [
        pytest.param(query.Any(query.Key('mykey1') == 1, query.Key('mykey2') == 2), {'mykey1': 1, 'mykey2': 2}, True, id="any-true"),
        pytest.param(query.All(query.Key('mykey1') != 1, query.Key('mykey2') != 2), {'mykey1': 2, 'mykey2': 1}, True, id="all-true"),
        pytest.param(query.Key('mykey') < 1, {'mykey': 0}, True, id="less true"),
        pytest.param(query.Key('mykey') <= 1, {'mykey': 1}, True, id="less-equal true"),
        pytest.param(query.Key('mykey') > 1, {'mykey': 2}, True, id="greater true"),
        pytest.param(query.Key('mykey') >= 1, {'mykey': 1}, True, id="greater-equal true"),
        pytest.param(~(query.Key('mykey') == 1), {'mykey': 2}, True, id="not true"),
    ]
)
def test_match(obj, data, expected):
    assert obj.match(data) if expected else not obj.match(data)