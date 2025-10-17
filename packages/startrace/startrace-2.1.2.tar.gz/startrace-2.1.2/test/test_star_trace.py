# This file contains a few tests to run before pushing a new version

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pytest

from startrace.star_trace import *



def test_inputs():
    tok = ConstToken("test")
    assert tok.value == "test"
    assert str(tok) == "test"
    assert len(tok) == len("test")
    assert repr(tok) == "ConstToken(test)"
    assert tok.to_dict() == {"type": "const", "value": "test"}
    assert tok.evaluate() == "test"
    assert tok.next() == False
    assert tok.last() == False
    tok = ConstToken(1)
    assert tok.value == "1"
    assert tok.evaluate() == "1"
    assert len(tok) == len("1")
    assert repr(tok) == "ConstToken(1)"
    assert tok.to_dict() == {"type": "const", "value": "1"}

    tok = ListToken([1, 2, 3])
    assert tok.values == [1, 2, 3]
    assert tok.iter.value == 0
    assert tok.iter.start == 0
    assert tok.iter.end == 2
    assert tok.iter.step == 1
    assert tok.evaluate() == "1"
    assert len(tok) == len([1, 2, 3])
    assert repr(tok) == "ListToken([1, 2, 3])"
    assert tok.to_dict() == {"type": "list", "values": [1, 2, 3]}
    assert tok.next() == True
    assert tok.last() == True
    assert tok.last() == False

    tok = RangeToken(1, 3, 1)
    assert tok.iter.value == 1
    assert tok.iter.start == 1
    assert tok.iter.end == 3
    assert tok.iter.step == 1
    assert tok.evaluate() == "1"
    assert len(tok) == len([1, 2, 3])
    assert repr(tok) == "RangeToken(1, 3, 1)"
    assert tok.to_dict() == {"type": "range", "start": 1, "end": 3, "step": 1}
    assert tok.next() == True
    assert tok.last() == True
    assert tok.last() == False

    tok = RangeToken(3, 1, -1)
    assert tok.iter.value == 3
    assert tok.next() == True
    assert tok.last() == True
    assert tok.last() == False

    tok = TimeToken("date")
    assert tok.mode == "date"
    assert tok.fmt == "%Y-%m-%d"
    assert tok.evaluate() == datetime.now().strftime("%Y-%m-%d")
    assert len(tok) == 0
    assert repr(tok) == 'TimeToken("date")'
    assert tok.to_dict() == {"type": "time", "mode": "date"}
    assert tok.next() == False
    assert tok.last() == False
    tok = TimeToken("time")
    assert tok.mode == "time"
    assert tok.fmt == "%H:%M:%S"
    tok = TimeToken("datetime")
    assert tok.mode == "datetime"
    assert tok.fmt == "%Y-%m-%d_%H:%M:%S"
    tok = TimeToken("iso")
    assert tok.mode == "iso"
    assert tok.fmt == "%Y-%m-%dT%H:%M:%S"
    tok = TimeToken("custom", "%Y-%m-%d_%H:%M:%S")
    assert tok.mode == "custom"
    assert tok.fmt == "%Y-%m-%d_%H:%M:%S"

    def x() -> float:
        return 3.14
    links = {"x": x}
    tok = LinkToken("x()", links, True)
    assert tok._link == "x()"
    assert tok._context == links
    assert tok._eval_allowed == True
    assert tok.evaluate() == "3.14"
    assert tok.next() == False
    assert tok.last() == False
    x = 10
    def y(x: int) -> int:
        return x * 2
    links = {"x": x, "y": y}
    tok = LinkToken("y(x)", links, True)
    assert tok.evaluate() == "20"

    z = []
    links = {"z": z}
    tok = LinkToken("z[0]", links, True, False)
    z.append(2)
    assert tok.evaluate() == "2"

    z = Link([])
    links = {"z": z}
    tok = LinkToken("z.v[0]", links, True, False)
    z.v.append(2)
    assert tok.evaluate() == "2"

def test_alts():
    tok = Token("test")
    assert isinstance(tok, ConstToken)
    tok = Token(1)
    assert isinstance(tok, ConstToken)

    tok = Token([1, 2, 3])
    assert isinstance(tok, ListToken)

    tok = Token(1, 3, 1)
    assert isinstance(tok, RangeToken)

    tok = Token("date")
    assert isinstance(tok, TimeToken)
    tok = Token("time")
    assert isinstance(tok, TimeToken)
    tok = Token("datetime")
    assert isinstance(tok, TimeToken)
    tok = Token("iso")
    assert isinstance(tok, TimeToken)
    tok = Token("custom", "%Y-%m-%d_%H:%M:%S")
    assert isinstance(tok, TimeToken)

    tok = Token("x()", {"x": lambda: 3.14}, True)
    assert isinstance(tok, LinkToken)
    tok = Token("y(x)", {"x": 10, "y": lambda x: x * 2}, True)
    assert isinstance(tok, LinkToken)

def test_errors():
    class No_Str:
        value = 1
        another_Value = 2

        def __str__(self):
            raise ValueError

    with pytest.raises(TypeError):
        ConstToken(No_Str())

    with pytest.raises(TypeError):
        ListToken([No_Str(), No_Str()])
    with pytest.raises(ValueError):
        ListToken([])

    with pytest.raises(TypeError):
        RangeToken(No_Str(), No_Str(), No_Str())
    with pytest.raises(ValueError):
        RangeToken(1, 3, 0)
    with pytest.raises(ValueError):
        RangeToken(3, 1, 1)
    with pytest.raises(ValueError):
        RangeToken(1, 3, -1)

    with pytest.raises(ValueError):
        TimeToken("test")
    with pytest.raises(ValueError):
        TimeToken("custom")
    with pytest.raises(ValueError):
        TimeToken("custom", No_Str())

    with pytest.raises(ValueError):
        LinkToken("x()", {}, False)
    with pytest.raises(ValueError):
        LinkToken("", {}, True)
    with pytest.raises(ValueError):
        LinkToken("y()", {"x": lambda: 3.14}, True)
    with pytest.raises(ValueError):
        LinkToken("No_Str()", {"No_Str": No_Str}, True)

    with pytest.raises(ValueError):
        Token()
    with pytest.raises(TypeError):
        Token(1, 2, 3, 4)

def test_pattern():
    pat = Pattern([
        ConstToken("test"),
        ListToken([1, 2, 3]),
        RangeToken(1, 3, 1)
    ])
    assert len(pat) == 3
    assert pat.evaluate() == "test11"
    assert pat.next() == True
    assert pat.last() == True
    assert pat.next() == True
    assert pat.evaluate() == "test12"
    assert pat.next() == True
    assert pat.evaluate() == "test13"
    assert pat.next() == True
    assert pat.evaluate() == "test21"
    for i in range(5):
        assert pat.next() == True
    assert pat.next() == False

def test_dict():
    t_dict = {
        "type": "const", "value": "test"
    }
    tok = Token(t_dict)
    assert isinstance(tok, ConstToken)
    assert tok.value == "test"
    assert tok.to_dict() == t_dict

    t_dict = {
        "tokens": [
            {"type": "const", "value": "test"},
            {"type": "list", "values": [1, 2, 3]}
        ]
    }
    pat = Pattern(t_dict)
    assert len(pat) == 2
    assert pat.evaluate() == "test1"

    x = 10
    y = Link(lambda x: x * 2)
    test_context = {
        "x": x,
        "y": y
    }
    z = 20
    test_link_context = {
        "z": z
    }
    t_dict = {
        "tokens": [
            {"type": "link", "link": "y(x)", "context": {}},
            {"type": "const", "value": " "},
            {"type": "link", "link": "y(z)", "context": test_link_context}
        ],
        "global_context": test_context,
        "eval_allowed": True
    }
    pat = Pattern(t_dict)
    assert len(pat) == 3
    assert pat.evaluate() == "20 40"
    y.set(lambda x: x * 3)
    assert pat.evaluate() == "30 60"

    x = 10
    y = lambda x: x * 2
    test_context = {
        "x": x,
        "y": y
    }
    z = 20
    test_link_context = {
        "z": z
    }
    t_dict = {
        "tokens": [
            {"type": "link", "link": "y(x)"},
            {"type": "const", "value": " "},
            {"type": "link", "link": "y(z)", "context": test_link_context}
        ],
        "global_context": {},
        "eval_allowed": True
    }
    pat = Pattern(t_dict, test_context, True)