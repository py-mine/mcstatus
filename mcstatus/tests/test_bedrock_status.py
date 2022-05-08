from mcstatus.bedrock_status import BedrockServerStatus
from mcstatus.status_response import BedrockServerPlayers, BedrockServerResponse, BedrockServerVersion


def test_bedrock_response_contains_expected_fields():
    data = (
        b"\x1c\x00\x00\x00\x00\x00\x00\x00\x004GT\x00\xb8\x83D\xde\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd"
        b"\x124Vx\x00wMCPE;\xc2\xa7r\xc2\xa74G\xc2\xa7r\xc2\xa76a\xc2\xa7r\xc2\xa7ey\xc2\xa7r\xc2\xa72B\xc2\xa7r\xc2"
        b"\xa71o\xc2\xa7r\xc2\xa79w\xc2\xa7r\xc2\xa7ds\xc2\xa7r\xc2\xa74e\xc2\xa7r\xc2\xa76r;422;;1;69;376707197539105"
        b"3022;;Default;1;19132;-1;"
    )
    parsed = BedrockServerStatus.parse_response(data, 1)
    assert "motd" in parsed.__dict__
    assert "latency" in parsed.__dict__
    assert "map_name" in parsed.__dict__
    assert "gamemode" in parsed.__dict__
    assert "players" in parsed.__dict__
    assert "version" in parsed.__dict__

    assert "online" in parsed.players.__dict__
    assert "max" in parsed.players.__dict__

    assert "name" in parsed.version.__dict__
    assert "protocol" in parsed.version.__dict__
    assert "brand" in parsed.version.__dict__


def test_bedrock_response_have_right_types():
    data = (
        b"\x1c\x00\x00\x00\x00\x00\x00\x00\x004GT\x00\xb8\x83D\xde\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd"
        b"\x124Vx\x00wMCPE;\xc2\xa7r\xc2\xa74G\xc2\xa7r\xc2\xa76a\xc2\xa7r\xc2\xa7ey\xc2\xa7r\xc2\xa72B\xc2\xa7r\xc2"
        b"\xa71o\xc2\xa7r\xc2\xa79w\xc2\xa7r\xc2\xa7ds\xc2\xa7r\xc2\xa74e\xc2\xa7r\xc2\xa76r;422;;1;69;376707197539105"
        b"3022;;Default;1;19132;-1;"
    )
    parsed = BedrockServerStatus.parse_response(data, 1)
    assert isinstance(parsed, BedrockServerResponse)
    assert type(parsed.motd) is str
    assert type(parsed.latency) is float or type(parsed.latency) is int
    assert type(parsed.map_name) is str
    assert type(parsed.gamemode) is str
    assert type(parsed.players) is BedrockServerPlayers
    assert type(parsed.version) is BedrockServerVersion

    assert type(parsed.players.online) is int
    assert type(parsed.players.max) is int

    assert type(parsed.version.name) is str
    assert type(parsed.version.protocol) is int
    assert type(parsed.version.brand) is str
