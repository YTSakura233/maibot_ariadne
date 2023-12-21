# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = moon_api_datayiyan_from_dict(json.loads(json_string))

from typing import Any, TypeVar, Type, cast


T = TypeVar("T")


def from_str(x: Any) -> str:
    #assert isinstance(x, str)
    return x


def from_int(x: Any) -> int:
    #assert isinstance(x, int) and not isinstance(x, bool)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    #assert isinstance(x, c)
    return cast(Any, x).to_dict()


class MoonAPIDatayiyan:
    status: str
    data: str
    description: str
    time: int
    code: str
    message: str

    def __init__(self, status: str, data: str, description: str, time: int, code: str, message: str) -> None:
        self.status = status
        self.data = data
        self.description = description
        self.time = time
        self.code = code
        self.message = message

    @staticmethod
    def from_dict(obj: Any) -> 'MoonAPIDatayiyan':
        #assert isinstance(obj, dict)
        status = from_str(obj.get("status"))
        data = from_str(obj.get("data"))
        description = from_str(obj.get("description"))
        time = from_int(obj.get("time"))
        code = from_str(obj.get("code"))
        message = from_str(obj.get("message"))
        return MoonAPIDatayiyan(status, data, description, time, code, message)

    def to_dict(self) -> dict:
        result: dict = {}
        result["status"] = from_str(self.status)
        result["data"] = from_str(self.data)
        result["description"] = from_str(self.description)
        result["time"] = from_int(self.time)
        result["code"] = from_str(self.code)
        result["message"] = from_str(self.message)
        return result


def moon_api_datayiyan_from_dict(s: Any) -> MoonAPIDatayiyan:
    return MoonAPIDatayiyan.from_dict(s)


def moon_api_datayiyan_to_dict(x: MoonAPIDatayiyan) -> Any:
    return to_class(MoonAPIDatayiyan, x)
