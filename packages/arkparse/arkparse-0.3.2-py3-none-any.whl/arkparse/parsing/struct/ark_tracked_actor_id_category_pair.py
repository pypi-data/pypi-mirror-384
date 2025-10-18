from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..ark_binary_parser import ArkBinaryParser

from arkparse.logging import ArkSaveLogger
from arkparse.enums.ark_enum import ArkEnumValue

@dataclass
class ArkTrackedActorIdCategoryPair:
    id_ : int
    cat_byte : int
    category : ArkEnumValue

    def __init__(self, byte_buffer: "ArkBinaryParser"):
        byte_buffer.validate_string("ID")
        byte_buffer.validate_string("IntProperty")
        byte_buffer.validate_uint32(0)
        byte_buffer.validate_uint32(4)
        byte_buffer.skip_bytes(1)

        self.id_ = byte_buffer.read_int()

        byte_buffer.validate_string("Category")
        byte_buffer.validate_string("ByteProperty")

        byte_buffer.read_uint32()
        
        byte_buffer.validate_string("ETrackedActorCategory")
        byte_buffer.validate_uint32(1)
        byte_buffer.validate_string("/Script/ShooterGame")
        byte_buffer.validate_uint32(0)
        self.cat_byte = byte_buffer.read_byte()
        byte_buffer.validate_uint32(0)
        self.category = ArkEnumValue(byte_buffer.read_string())

        byte_buffer.validate_string("None")

        ArkSaveLogger.parser_log(f"Read tracked actor id category pair with bool: {self}")

    def __str__(self) -> str:
        return f"id:{self.id_} cat_byte:{self.cat_byte} category:{self.category}"



