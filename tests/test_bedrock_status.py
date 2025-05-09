import sys
import time
from unittest import mock

import pytest

from mcstatus.address import Address
from mcstatus.bedrock_status import BedrockServerStatus
from mcstatus.responses import BedrockStatusResponse


def test_bedrock_response_is_expected_type():
    data = (
        b"\x1c\x00\x00\x00\x00\x00\x00\x00\x004GT\x00\xb8\x83D\xde\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd"
        b"\x124Vx\x00wMCPE;\xc2\xa7r\xc2\xa74G\xc2\xa7r\xc2\xa76a\xc2\xa7r\xc2\xa7ey\xc2\xa7r\xc2\xa72B\xc2\xa7r\xc2"
        b"\xa71o\xc2\xa7r\xc2\xa79w\xc2\xa7r\xc2\xa7ds\xc2\xa7r\xc2\xa74e\xc2\xa7r\xc2\xa76r;422;;1;69;376707197539105"
        b"3022;;Default;1;19132;-1;"
    )
    parsed = BedrockServerStatus.parse_response(data, 1)
    assert isinstance(parsed, BedrockStatusResponse)


@pytest.mark.flaky(reruns=5, condition=sys.platform.startswith("win32"))
def test_latency_is_real_number():
    """``time.perf_counter`` returns fractional seconds, we must convert it to milliseconds."""

    def mocked_read_status():
        time.sleep(0.001)
        return mock.DEFAULT

    pinger = BedrockServerStatus(Address("localhost", 25565))
    with (
        mock.patch.object(pinger, "_read_status") as mocked_read,
        mock.patch.object(pinger, "parse_response") as mocked_parse_response,
    ):
        mocked_read.side_effect = mocked_read_status

        pinger.read_status()

        # we slept 1ms, so this should be always ~1.
        assert mocked_parse_response.call_args[0][1] >= 1


@pytest.mark.asyncio
@pytest.mark.flaky(reruns=5, condition=sys.platform.startswith("win32"))
async def test_async_latency_is_real_number():
    """``time.perf_counter`` returns fractional seconds, we must convert it to milliseconds."""

    def mocked_read_status():
        time.sleep(0.001)
        return mock.DEFAULT

    pinger = BedrockServerStatus(Address("localhost", 25565))
    with (
        mock.patch.object(pinger, "_read_status_async") as mocked_read,
        mock.patch.object(pinger, "parse_response") as mocked_parse_response,
    ):
        mocked_read.side_effect = mocked_read_status

        await pinger.read_status_async()

        # we slept 1ms, so this should be always ~1.
        assert mocked_parse_response.call_args[0][1] >= 1
