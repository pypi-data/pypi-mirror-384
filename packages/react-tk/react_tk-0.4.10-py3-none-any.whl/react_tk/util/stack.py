from dataclasses import dataclass
import sys
from types import FrameType

from funcy import first


@dataclass
class ReactTkFrameInfo:
    filename: str
    line: int
    column: int
    function_name: str


def get_react_tk_frame_info(frame: FrameType) -> ReactTkFrameInfo:
    co_positions = frame.f_code.co_positions()
    first_co_position = first(co_positions)
    if first_co_position is None:
        raise RuntimeError("No code positions found")
    start_line = frame.f_lineno
    return ReactTkFrameInfo(
        filename=frame.f_code.co_filename,
        line=start_line,
        column=0,
        function_name=frame.f_code.co_name,
    )


def get_first_non_ctor_frame(skip: int = 0):
    frame = sys._getframe(1 + skip)
    if not frame:
        raise RuntimeError("No frame found")
    tracked = []
    while frame.f_code.co_name in ("__init__", "__new__"):
        frame = frame.f_back
        if not frame:
            raise RuntimeError("No non-__init__ frame found")
        tracked.append(frame)
    return frame


def get_first_non_ctor_frame_info(skip: int = 0) -> ReactTkFrameInfo:
    frame = get_first_non_ctor_frame(skip + 1)
    return get_react_tk_frame_info(frame)
