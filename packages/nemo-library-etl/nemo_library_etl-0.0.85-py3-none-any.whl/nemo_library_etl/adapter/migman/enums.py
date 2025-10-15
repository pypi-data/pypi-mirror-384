from enum import Enum


class MigManTransformStep(Enum):
    JOINS = "10_joins"
    NONEMPTY = "20_nonempty"
    DUPLICATES = "30_duplicates"
    