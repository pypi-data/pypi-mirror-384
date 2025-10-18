from dataclasses import dataclass, field
from w.mixins.dataclasses_mixin import DataclassMixin

DEFAULT_FIELD_DELIMITER = ","
DEFAULT_LINE_TERMINATOR = "\n"


@dataclass
class CsvOptions(DataclassMixin):
    mapping_columns: dict = field(default_factory=dict)
    field_delimiter: str = DEFAULT_FIELD_DELIMITER
    line_terminator: str = DEFAULT_LINE_TERMINATOR
