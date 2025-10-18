from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..ark_binary_parser import ArkBinaryParser

from arkparse.logging import ArkSaveLogger
from arkparse.enums.ark_enum import ArkEnumValue

@dataclass
class ArkDinoOrderID:
    id1 : int
    id2: int
    dino_name : str

    def __init__(self, byte_buffer: "ArkBinaryParser"):
        byte_buffer.validate_string("DinoID1")
        byte_buffer.validate_string("IntProperty")
        byte_buffer.validate_uint32(0)
        byte_buffer.validate_uint32(4)
        byte_buffer.skip_bytes(1)

        self.id1 = byte_buffer.read_int()

        byte_buffer.validate_string("DinoID2")
        byte_buffer.validate_string("IntProperty")
        byte_buffer.validate_uint32(0)
        byte_buffer.validate_uint32(4)
        byte_buffer.skip_bytes(1)

        self.id2 = byte_buffer.read_int()

        byte_buffer.validate_string("DinoName")
        byte_buffer.validate_string("StrProperty")
        byte_buffer.validate_uint32(0)
        byte_buffer.skip_bytes(5)
        self.dino_name = byte_buffer.read_string()

        byte_buffer.validate_string("None")

        ArkSaveLogger.parser_log(f"Read dino order id1:{self.id1} id2:{self.id2} name:{self.dino_name}")

    def __str__(self) -> str:
        return f"id1:{self.id1} id2:{self.id2} name:{self.dino_name}"



