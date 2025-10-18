from dataclasses import dataclass
from typing import TYPE_CHECKING
from arkparse.logging import ArkSaveLogger
from .ark_vector import ArkVector

if TYPE_CHECKING:   
    from arkparse.parsing import ArkBinaryParser

@dataclass
class ArkPaintingKeyValue:
    key: int = 0
    value: int = 0

    def __init__(self, ark_binary_data: "ArkBinaryParser"):
        self.key = ark_binary_data.parse_int32_property("Key")
        self.value = ark_binary_data.parse_int32_property("Value")
        ark_binary_data.validate_name("None")

        ArkSaveLogger.parser_log(f"ArkPaintingKeyValue: {self.key}, {self.value}")