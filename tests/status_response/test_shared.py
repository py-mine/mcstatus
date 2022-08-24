from pytest import mark, raises

from mcstatus.status_response import BaseStatusResponse, _validate_data


class TestValidateDataFunction:
    @mark.parametrize("raw", [{"foo": "bar"}, {"foo": 123, "bar": 1.4, "baz": True}])
    @mark.parametrize("required_key", ["foo", "bar", "baz"])
    @mark.parametrize("required_type", [str, int, object])
    def test_invalid_data(self, raw, required_key, required_type):
        if required_key in raw and isinstance(raw[required_key], required_type):
            return
        elif required_key in raw and not isinstance(raw[required_key], required_type):
            error = TypeError
        elif required_key not in raw:
            error = ValueError
        else:
            raise ValueError("Unknown parametrize")

        with raises(error) as exc:
            _validate_data(raw, "test", [(required_key, required_type)])

        if error == ValueError:
            assert exc.match(f"no '{required_key}' value")
        else:
            assert exc.match(f"'{required_key}' to be {required_type}, was {type(raw[required_key])}")

    @mark.parametrize("who", ["status", "server", "player", "just"])
    def test_who_parameter(self, who):
        with raises(ValueError) as exc:
            _validate_data({"foo": "bar"}, who, [("not exist", object)])

        exc.match(r"^Invalid {} object".format(who))


class TestMCStatusResponse:
    def test_raises_not_implemented_error_on_build(self):
        with raises(NotImplementedError):
            BaseStatusResponse.build({"foo": "bar"})
