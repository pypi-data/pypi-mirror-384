import pytest

from durable_dot_dict.collection import first
from durable_dot_dict.dotdict import DotDict


def test_init():

    # No SqlDB style
    assert DotDict(
        {
            'b': {'a': None},
            'c': {'a': 1},
            'd': {'a': ''},
            'e': {'a': {'b': 1}},
            'f': {'a': [{'a': 1}, 1]},
            'list': [1],
            'set': set()}
    ) == {'b': {'a': None}, 'c': {'a': 1}, 'd': {'a': ''}, 'e': {'a': {'b': 1}}, 'f': {'a': [{'a': 1}, 1]}, 'list': [1],
          'set': set()}

    # FlatDB style
    assert DotDict() << {
        "b.a": None,
        'c.a': 1,
        'd.a': "",
        'e.a': {"b": 1},
        'f.a': [{"a": 1}, 1],
        "list": [1],
        "set": set()
    } == {'b': {'a': None}, 'c': {'a': 1}, 'd': {'a': ''}, 'e': {'a': {'b': 1}}, 'f': {'a': [{'a': 1}, 1]}, 'list': [1],
          'set': set()}

    # FlatDB style
    assert DotDict() << [
        ("b.a",  None),
        ('c.a', 1),
        ('d.a', ""),
        ('e.a', {"b": 1}),
        ('f.a', [{"a": 1}, 1]),
        ("list", [1]),
        ("set", set())
    ] == {'b': {'a': None}, 'c': {'a': 1}, 'd': {'a': ''}, 'e': {'a': {'b': 1}}, 'f': {'a': [{'a': 1}, 1]}, 'list': [1],
          'set': set()}


def test_flat():
    data = DotDict({
        "b.a": None,
        'c.a': 1,
        'd.a': "",
        'e.a': {"b": 1},
        'f.a': [{"a": 1}, 1],
        "list": [1],
        "set": set()
    }) << [
               ('list[1]', 2)
           ]
    assert data.flat() == {'b.a': None, 'c.a': 1, 'd.a': '', 'e.a.b': 1, 'f.a': [{'a': 1}, 1], 'list': [1, 2],
                           "set": set()}



def test_set_attrib():
    data = DotDict()
    with pytest.raises(KeyError):
        data.atr = 1

def test_none():
    data = DotDict({
        "b": None,
        'c': 1,
        'd': "",
        'e': {},
        'f': []
    })

    assert bool(data)
    assert data.empty('a')
    assert data.empty('a.c')
    assert data.empty('b')
    assert not data.empty('c')
    assert data.empty('d')
    assert data.empty('e')
    assert data.empty('f')

    assert not bool(DotDict())


def test_first():
    a1 = {}
    a2 = {"b": 1}
    data = DotDict({})
    data['a'] = first(lambda: a1["a"], lambda: a2["b"])
    assert data == {'a': 1}


def test_map_key_value():
    data = DotDict()
    data << [
        ('a', 1),
        ('b.c', 2)
    ]
    assert data == {'a': 1, 'b': {'c': 2}}

    assert DotDict() << [('a', 1), ('b.c', 2)] == {'a': 1, 'b': {'c': 2}}

    dot = DotDict() << [('a', 1), ('b.c', 2)]
    assert dot >> [
        ("a", 'a'),
        ("b_c", 'b.c')
    ] == {'a': 1, 'b_c': 2}


def test_dotdict_deep_set():
    data = DotDict({})
    data['data.bookings[0].services[0].details.airline'] = 'Air France'
    assert data == {'data': {'bookings': [{'services': [{'details': {'airline': 'Air France'}}]}]}}

    data = DotDict({})
    data['data[0][0].detail'] = 'Air France'
    assert data == {'data': [[{'detail': 'Air France'}]]}

    data = DotDict({})
    data['data[0][0]'] = 'Air France'
    assert data == {'data': [['Air France']]}

    data = DotDict({})
    data['data.list[0][0]'] = {1}
    assert data == {'data': {"list": [[{1}]]}}


def test_embedded_dotdict():
    d = DotDict({
        "data": {
            "list": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
            "bookings": [
                {
                    "services": [
                        {
                            "details": {
                                "airline": "Air France",
                            }
                        }
                    ]
                }
            ]
        }
    })

    assert d['data.bookings[0].services[0].details.airline'] == 'Air France'
    assert 'data.bookings[1].services[0]' not in d
    assert 'data.bookings[0].services[0]' in d
    assert 'data.bookings[0].services' in d
    assert 'data.list[0][1]' in d
    assert d['data.list[0][1]'] == 2


def test_dotdict_spread():
    d1 = DotDict({
        "a": "1"
    })
    d2 = DotDict({
        "b": "2"
    })

    print({**d1, **d2})


def test_dotdict_set_as_dotdict():
    d = DotDict({
        "a": "1"
    })

    with pytest.raises(TypeError):
        cd = DotDict(d)

    d = DotDict({"a": 1})
    d['a'] = DotDict({"b": {"c": [2, 1]}})
    assert isinstance(d['a'], dict)
    assert d['a.b.c.0'] == 2
    assert d['a']['b']['c'][0] == 2


# Define tests for DotDict functionality
def test_dotdict_set_get_delete_check():
    d = {
        "a": {"b": ["c", 0]},
        "a1": {"b": ["c", 0]},
        "a2": {"b": ["c", 0]},
        "a3": {"b": ["c", 0, {"c"}, ("x", 10)]}
    }

    cd = DotDict(d)

    # Test setting and getting using unified path notation
    cd['a3.b[3]'] = "new_value"
    assert cd['a3.b[3]'] == "new_value", "Failed to set or get value using unified path notation"
    assert cd['a3']['b'][3] == "new_value", "Failed to set or get value using unified path notation"

    # Test setting and getting using attribute-style notation
    cd['a3.b'].append("another_value")
    assert cd['a3.b[4]'] == "another_value"

    # Test deletion using unified path notation

    # assert cd.a3.b == DotDict(['c', 0, {'c'}, 'new_value', 'another_value'])
    assert cd['a3.b'] == ['c', 0, {'c'}, 'new_value', 'another_value']

    del cd['a3.b[2]']
    assert cd['a3.b'] == ['c', 0, 'new_value', 'another_value']
    print(cd['a3.b'])
    # Test checking existence using unified path notation
    assert 'a3.b[2]' in cd, "Membership test for 'a3.b[1]' failed"
    assert 'a3.b[10]' not in cd, "Non-membership test for 'a3.b[10]' failed"


def test_dotdict_get():
    d = {
        "a": {"b": ["c", 0]},
        "b": [{"$c": "here"}],
        "A": {"a b c": 1}
    }

    data = DotDict(d)
    with pytest.raises(TypeError):
        x = data['a.b[]']

    assert data["b.0['$c']"] == 'here'
    assert data['A["a b c"]'] == 1


def test_dotdict_get_default():
    d = {}

    data = DotDict(d)
    x = data.get('xx.xx', "default")
    assert x == 'default'
    x = data.get('xx.xx', None)
    assert x is None


def test_dotdict_has():
    d = {
        "a": {"b": ["c", 0]},
    }

    data = DotDict(d)
    assert 'a.b' in data
    assert 'a.d' not in data
    assert 'a[1].d' not in data
    assert 'a[]' not in data
    assert 'a.b[1]' in data


def test_dotdict_set():
    data = DotDict({})

    # Test setting and getting using unified path notation
    data['a.b[0]'] = 123
    assert data['a.b[0]'] == 123
    data['a.b'].append("1")
    data['a.b'].append("2")
    assert data['a.b'] == [123, "1", "2"]
    with pytest.raises(TypeError):
        data['a.b[0].c'] = 123


def test_equal():
    x = DotDict({'id': '1', 'active': True, 'metadata': {
        'time': {'insert': '2025-01-10T17:13:28.620880+00:00', 'create': '2004-01-12T17:13:28.620880+00:00',
                 'update': '2025-03-20T10:53:41.924819+00:00'}}, 'operation': {'new': False, 'update': False},
                 'ids': []})
    y = DotDict({'id': '1', 'active': True, 'metadata': {
        'time': {'insert': '2025-01-10T17:13:28.620880+00:00', 'create': '2004-01-12T17:13:28.620880+00:00',
                 'update': '2025-03-20T10:53:41.924819+00:00'}}, 'operation': {'new': False, 'update': False},
                 'ids': []})
    assert x == y


# Define tests for invalid data paths
def test_invalid_paths_handling():
    d = {
        "a": {"b": ["c", 0]},
        "a3": {"b": ["c", 0, {"c"}, ("x", 10)]}
    }

    cd = DotDict(d)

    invalid_paths = [
        ".leadingDot",  # Leading dot
        "trailingDot.",  # Trailing dot
        "a..b",  # Multiple consecutive dots
        "a[\"b-\"c0\"]",  # Invalid string key in bracket
        "a[\"b-\"c0\"][0]",
        "a[\"b-\"c0\"].ala.",
        "",
        "a[\"b-\"c0\".ala",  # Unclosed bracket
    ]

    for path in invalid_paths:
        with pytest.raises((ValueError, KeyError)):
            _ = cd[path]


def test_get_or_none():
    d = {
        "a": {"b": ["c", 0]},
        "a3": {"b": ["c", 0, {"c"}, ("x", 10)]}
    }

    cd = DotDict(d)

    assert (cd | 'a') == {"b": ["c", 0]}
    assert (cd | "none") is None

def test_reference():
    d = {
        "a": None,
    }

    cd = DotDict(d)
    assert ('a' in cd) is True
    assert ('a.b' in cd) is False


def test_error_handling():
    # Cannot assign string-key 'email' to non-dict: http://localhost/1
    d = DotDict({'name': 'http://localhost/1'}, override_data=False)
    d['name.my'] = {"a":"test"}
    assert d['name.my'] == {"a":"test"}

# Run all tests when executed via pytest
if __name__ == "__main__":
    pytest.main()

