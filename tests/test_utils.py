from mcstatus.utils import or_none


def test_or_none_docstring():
    mydict = {"a": ""}
    assert (mydict.get("a") or mydict.get("b")) is None
    assert or_none(mydict.get("a"), mydict.get("b")) == ""
