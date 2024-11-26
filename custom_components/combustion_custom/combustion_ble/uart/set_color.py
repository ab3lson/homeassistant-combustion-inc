from ..ble_data.mode_id import ProbeColor
from .message_type import MessageType
from .request import Request
from .response import Response


class SetColorRequest(Request):
    def __init__(self, color: ProbeColor):
        payload = color.value.to_bytes(1)
        super().__init__(payload, message_type=MessageType.SET_COLOR)


class SetColorResponse(Response):
    pass
