from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..ark_binary_parser import ArkBinaryParser

from arkparse.logging import ArkSaveLogger
from arkparse.enums.ark_enum import ArkEnumValue

@dataclass
class ArkTribeAlliance:
    name: str
    id: int
    member_names: list[str]
    member_ids: list[int]
    admin_ids: list[int]

    def __init__(self, byte_buffer: "ArkBinaryParser"):
        byte_buffer.validate_string("AllianceName")
        byte_buffer.validate_string("StrProperty")
        byte_buffer.validate_uint32(0)
        byte_buffer.skip_bytes(5)

        self.name = byte_buffer.read_string()

        byte_buffer.validate_string("AllianceID")
        byte_buffer.validate_string("UInt32Property")
        byte_buffer.validate_uint32(0)
        byte_buffer.validate_uint32(4)
        byte_buffer.skip_bytes(1)

        self.id = byte_buffer.read_uint32()

        byte_buffer.validate_string("MembersTribeName")
        byte_buffer.validate_string("ArrayProperty")
        byte_buffer.validate_uint32(1)
        byte_buffer.validate_string("StrProperty")
        byte_buffer.validate_uint32(0)
        byte_buffer.skip_bytes(5)
        member_count = byte_buffer.read_uint32()
        self.member_names = [byte_buffer.read_string() for _ in range(member_count)]

        byte_buffer.validate_string("MembersTribeID")
        byte_buffer.validate_string("ArrayProperty")
        byte_buffer.validate_uint32(1)
        byte_buffer.validate_string("UInt32Property")
        byte_buffer.validate_uint32(0)
        byte_buffer.skip_bytes(5)

        member_id_count = byte_buffer.read_uint32()
        self.member_ids = [byte_buffer.read_uint32() for _ in range(member_id_count)]

        byte_buffer.validate_string("AdminsTribeID")
        byte_buffer.validate_string("ArrayProperty")
        byte_buffer.validate_uint32(1)
        byte_buffer.validate_string("UInt32Property")
        byte_buffer.validate_uint32(0)
        byte_buffer.skip_bytes(5)
        admin_id_count = byte_buffer.read_uint32()
        self.admin_ids = [byte_buffer.read_uint32() for _ in range(admin_id_count)]

        byte_buffer.validate_string("None")


    def __str__(self) -> str:
        return f"name:{self.name} id:{self.id} members:{self.member_names} member_ids:{self.member_ids} admin_ids:{self.admin_ids}"



