from ..ble_data.mode_id import ProbeID
from .message_type import MessageType
from .request import Request
from .response import Response


class SetIDRequest(Request):
    def __init__(self, id: ProbeID):
        payload = id.value.to_bytes(1)
        super().__init__(payload, message_type=MessageType.SET_ID)


class SetIDResponse(Response):
    pass
