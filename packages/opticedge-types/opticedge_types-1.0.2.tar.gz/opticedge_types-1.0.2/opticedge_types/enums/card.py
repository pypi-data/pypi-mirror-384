from enum import IntEnum, Enum

class ApprovalStatus(IntEnum):
    RESCAN = -2
    PENDING = -1
    FAILED = 0
    APPROVED = 1
    APPROVING = 999

class GradingField(Enum):
    GRADING = "grading"
    CENTER  = "centering_grading"
    SURFACE = "surface_grading"
    EDGE    = "edge_grading"
    CORNER  = "corner_grading"
