from dataclasses import dataclass, field
from typing import List

from w.mixins.dataclasses_mixin import DataclassMixin


@dataclass
class ImportRowError(DataclassMixin):
    num_row: int
    errors: List[str] = field(default_factory=list)


@dataclass
class ImportReport(DataclassMixin):
    nb_total: int = 0
    nb_imported: int = 0
    nb_ignored: int = 0
    nb_errors: int = 0
    errors: List[ImportRowError] = field(default_factory=list)
