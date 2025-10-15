import warnings


def channel_to_response_topic(channel: str) -> str:
    assert isinstance(channel, str), "channel must be a string"
    return "rpc-rep-" + channel


def channel_to_request_topic(channel: str) -> str:
    assert isinstance(channel, str), "channel must be a string"
    return "rpc-req-" + channel
